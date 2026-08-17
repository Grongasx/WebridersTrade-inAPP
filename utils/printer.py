"""
Módulo de impressão de etiquetas térmicas e gerenciamento de fila.
"""

import os
import json
from typing import List, Dict, Any, Tuple, Optional, cast

try:
    import win32print
    import win32ui
    import win32gui
    import win32con
    from PIL import Image, ImageDraw, ImageFont, ImageWin
except ImportError:
    win32print = None
    win32ui = None
    win32gui = None
    win32con = None
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageWin = None

from core.database import get_conn
from core.config_local import carregar_config_local
from utils.helpers import gerar_imagem_barcode_sku


class PDFPrinter:
    """
    Controlador de impressão direta de etiquetas térmicas em impressoras Zebra/Windows.
    Suporta carreiras multi-colunas com compensação de offset e códigos Code39/EAN.
    """

    def processar_impressao_multi_colunas(self, ids_selecionados: List[int]) -> Tuple[bool, str]:
        """
        Processa os registros selecionados na fila de impressão e envia à impressora configurada.
        """
        if not ids_selecionados:
            return False, "Nenhum item selecionado para impressão."

        cfgs = carregar_config_local()
        nome_impressora = cfgs.get("nome_impressora", "").strip()

        if not nome_impressora:
            return False, "Nenhuma impressora selecionada nas configurações locais."

        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, texto_etiqueta, quantidade, produto_id FROM fila_impressao WHERE id = ANY(%s)",
                (list(ids_selecionados),)
            ).fetchall()

            if not rows:
                return False, "Nenhum item válido encontrado na fila."

            lista_dados: List[Dict[str, Any]] = []
            for row in rows:
                try:
                    dados_prod = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or {})
                    if not isinstance(dados_prod, dict):
                        dados_prod = {}

                    item_id = dados_prod.get("id") or dados_prod.get("produto_id") or row[3] or row[0]
                    dados_prod["id_banco"] = str(item_id)

                    # Prioriza SKU interno ou código de barras cadastrado
                    codigo_atual = (
                        dados_prod.get("sku")
                        or dados_prod.get("codigo")
                        or dados_prod.get("codigo_barras")
                        or dados_prod.get("codigo_ean")
                    )
                    if not codigo_atual:
                        codigo_atual = f"WR-{int(item_id):06d}"

                    dados_prod["codigo"] = str(codigo_atual)

                    qtd = int(row[2] or 1)
                    for _ in range(qtd):
                        lista_dados.append(dados_prod)
                except Exception:
                    continue

        if not lista_dados:
            return False, "Falha ao processar os dados das etiquetas."

        try:
            self.imprimir_etiquetas_direto(lista_dados, nome_impressora, cfgs)

            # Atualiza status de todos os itens impressos em lote
            with get_conn() as conn:
                conn.execute(
                    "UPDATE fila_impressao SET status = 'Impresso' WHERE id = ANY(%s)",
                    (list(ids_selecionados),)
                )
                conn.commit()

            return True, f"Impresso com sucesso {len(lista_dados)} etiqueta(s)!"

        except Exception as e:
            return False, f"Erro ao enviar para a impressora: {str(e)}"

    def imprimir_etiquetas_direto(
        self,
        lista_dados: List[Dict[str, Any]],
        nome_impressora: str,
        cfgs: Dict[str, Any]
    ) -> None:
        """
        Renderiza e transmite os dados para o Device Context (DC) da impressora Windows.
        """
        if not win32print or not win32ui or not win32con or not Image:
            raise RuntimeError(
                "Módulos pywin32 ou Pillow não estão disponíveis para impressão GDI no Windows."
            )

        if not nome_impressora or not nome_impressora.strip():
            raise ValueError("Nenhuma impressora foi selecionada nas configurações.")

        nome_impressora = nome_impressora.strip()

        try:
            impressoras_instaladas = [
                p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            ]
        except Exception:
            impressoras_instaladas = []

        if impressoras_instaladas and nome_impressora not in impressoras_instaladas:
            lista_str = "\n• " + "\n• ".join(impressoras_instaladas)
            raise RuntimeError(
                f"A impressora '{nome_impressora}' não está cadastrada no Windows.\n\n"
                f"Impressoras disponíveis na máquina:{lista_str}\n\n"
                f"Acesse a tela de Configurações no app, selecione a impressora e clique em Salvar."
            )

        hdc = None
        erro_dc = None

        # Tentativa 1: Via win32ui CreateDC e CreatePrinterDC
        try:
            hdc_temp = win32ui.CreateDC()
            if hdc_temp is not None:
                hdc_temp.CreatePrinterDC(nome_impressora)
                hdc = hdc_temp
        except Exception as e:
            erro_dc = str(e)
            hdc = None

        # Tentativa 2: Fallback via Win32 GDI direto (win32gui.CreateDC)
        if hdc is None and win32gui is not None:
            try:
                raw_hdc = win32gui.CreateDC("WINSPOOL", nome_impressora, cast(Any, None))
                if raw_hdc:
                    hdc = win32ui.CreateDCFromHandle(raw_hdc)
            except Exception as e:
                erro_dc = str(e)
                hdc = None

        if hdc is None:
            detalhe = f": {erro_dc}" if erro_dc else ""
            raise RuntimeError(
                f"Falha ao conectar à impressora '{nome_impressora}'{detalhe}. "
                f"Verifique se o spooler do Windows está ativo e se o driver está instalado."
            )

        w_tot_mm = float(cfgs.get("etiq_largura_mm", 108))
        h_tot_mm = float(cfgs.get("etiq_altura_mm", 22))
        cols_por_linha = int(cfgs.get("etiq_por_linha", 3))

        dpi_x = hdc.GetDeviceCaps(win32con.LOGPIXELSX) or 203
        dpi_y = hdc.GetDeviceCaps(win32con.LOGPIXELSY) or 203
        px_mm_x = dpi_x / 25.4
        px_mm_y = dpi_y / 25.4

        # Leitura dos offsets físicos de hardware da impressora
        try:
            offset_x_px = hdc.GetDeviceCaps(win32con.PHYSICALOFFSETX) or 0
            offset_y_px = hdc.GetDeviceCaps(win32con.PHYSICALOFFSETY) or 0
        except Exception:
            offset_x_px = 0
            offset_y_px = 0

        w_px = int(w_tot_mm * px_mm_x)
        h_px = int(h_tot_mm * px_mm_y)

        try:
            cast(Any, hdc).StartDoc("Impressao_Etiquetas_Outlet")
            hdc_handle = self._obter_hdc_handle(hdc)

            for i in range(0, len(lista_dados), cols_por_linha):
                grupo_carreira = lista_dados[i : i + cols_por_linha]

                img_carreira = self.gerar_imagem_carreira(
                    grupo_carreira, w_px, h_px, cfgs, px_mm_x, px_mm_y, dpi_y
                )

                hdc.StartPage()
                dib = ImageWin.Dib(img_carreira)

                # Compensação dos offsets físicos do hardware na renderização
                dest_rect = (
                    -offset_x_px,
                    -offset_y_px,
                    w_px - offset_x_px,
                    h_px - offset_y_px
                )
                dib.draw(hdc_handle, dest_rect)
                hdc.EndPage()

            hdc.EndDoc()
        finally:
            try:
                hdc.DeleteDC()
            except Exception:
                pass

    def _obter_hdc_handle(self, hdc: Any) -> Any:
        """Obtém o identificador HDC seguro para desenho com PIL ImageWin."""
        if hasattr(hdc, "GetHandleOutput"):
            return hdc.GetHandleOutput()
        elif hasattr(hdc, "GetSafeHdc"):
            return hdc.GetSafeHdc()
        return hdc

    def gerar_imagem_carreira(
        self,
        grupo: List[Dict[str, Any]],
        w_px: int,
        h_px: int,
        cfgs: Dict[str, Any],
        px_mm_x: float,
        px_mm_y: float,
        dpi_y: int = 203
    ) -> Any:
        """
        Gera a imagem de uma carreira de etiquetas com distribuição uniforme,
        eliminando o desvio acumulativo horizontal.
        """
        if not Image or not ImageDraw or not ImageFont:
            raise RuntimeError("Módulo PIL/Pillow não disponível.")

        img = Image.new("RGB", (w_px, h_px), "white")
        draw = ImageDraw.Draw(img)

        w_tot_mm = float(cfgs.get("etiq_largura_mm", 108))
        w_indiv_mm = float(cfgs.get("etiq_indiv_largura_mm", 34))
        m_esq_mm = float(cfgs.get("etiq_margem_esq", 2))
        m_dir_mm = float(cfgs.get("etiq_margem_dir", 2))
        m_top_mm = float(cfgs.get("etiq_margem_top", 0.5))
        gap_manual_mm = float(cfgs.get("etiq_espaco_colunas_mm", 2))
        cols = int(cfgs.get("etiq_por_linha", 3))

        # CÁLCULO DE PASSO E GAP SEM ERRO ACUMULATIVO:
        if cols > 1:
            espaco_gaps_mm = w_tot_mm - m_esq_mm - m_dir_mm - (cols * w_indiv_mm)
            if espaco_gaps_mm >= 0:
                gap_efetivo_mm = espaco_gaps_mm / float(cols - 1)
            else:
                gap_efetivo_mm = gap_manual_mm
        else:
            gap_efetivo_mm = 0.0

        layout_cfg = cfgs.get("layout", {})
        layout_default = {
            "nome": {"tipo": "texto", "x_mm": 1.0, "y_mm": 0.5, "font_size": 7, "max_w_mm": 32.0},
            "preco": {"tipo": "texto", "x_mm": 1.0, "y_mm": 5.5, "font_size": 11, "max_w_mm": 32.0},
            "codigo": {"tipo": "barcode", "x_mm": 1.0, "y_mm": 11.0, "max_w_mm": 32.0, "height_mm": 9.0}
        }

        for col, item in enumerate(grupo):
            col_x_start_mm = m_esq_mm + (col * (w_indiv_mm + gap_efetivo_mm))

            nome = str(item.get("nome") or item.get("descricao") or "PRODUTO")

            preco = item.get("preco") or item.get("preco_outlet") or "R$ 0,00"
            if isinstance(preco, (int, float)):
                preco = f"R$ {preco:.2f}".replace(".", ",")
            else:
                preco = str(preco)
                if not preco.startswith("R$") and preco.strip():
                    preco = f"R$ {preco}"

            codigo = str(
                item.get("codigo")
                or item.get("sku")
                or item.get("codigo_barras")
                or item.get("codigo_ean")
                or item.get("id_banco")
                or "WR-000001"
            )

            elementos_dados = {
                "nome": nome,
                "preco": preco,
                "codigo": codigo
            }

            for key, texto in elementos_dados.items():
                cfg_elem = layout_cfg.get(key, layout_default.get(key, {}))

                x_mm = float(cfg_elem.get("x_mm", 1.0))
                y_mm = float(cfg_elem.get("y_mm", 0.5))
                max_w_mm = float(cfg_elem.get("max_w_mm", 32.0))

                # Trava rígida: impede o elemento de vazar a borda da etiqueta individual
                max_w_disponivel_mm = max(1.0, w_indiv_mm - x_mm)
                max_w_efetivo_mm = min(max_w_mm, max_w_disponivel_mm)

                pos_x = int((col_x_start_mm + x_mm) * px_mm_x)
                pos_y = int((m_top_mm + y_mm) * px_mm_y)
                max_w_px = max(20, int(max_w_efetivo_mm * px_mm_x))

                if key == "codigo" or cfg_elem.get("tipo") == "barcode":
                    h_bar_mm = float(cfg_elem.get("height_mm", 9.0))
                    h_bar_px = max(15, int(h_bar_mm * px_mm_y))

                    bar_pil = gerar_imagem_barcode_sku(texto, max_w_px, h_bar_px)
                    img.paste(bar_pil, (pos_x, pos_y))
                else:
                    font_pt = int(cfg_elem.get("font_size", 7))
                    px_font = int(font_pt * (dpi_y / 72.0))

                    try:
                        font_file = "arialbd.ttf" if key in ["nome", "preco"] else "arial.ttf"
                        font = ImageFont.truetype(font_file, px_font)
                    except IOError:
                        font = ImageFont.load_default()

                    texto_formatado = self._aplicar_quebra_de_linha(draw, texto, font, max_w_px)
                    draw.multiline_text((pos_x, pos_y), texto_formatado, fill="black", font=font, spacing=1)

        return img

    def _aplicar_quebra_de_linha(self, draw: Any, texto: str, font: Any, max_w_px: int) -> str:
        """Aplica quebra de linha restringindo o texto ao limite em pixels com suporte a múltiplos parágrafos."""
        linhas_resultado: List[str] = []

        for paragrafo in str(texto).split("\n"):
            palavras = paragrafo.split(" ")
            linha_atual = ""

            for palavra in palavras:
                test_line = f"{linha_atual} {palavra}".strip() if linha_atual else palavra

                if hasattr(draw, "textlength"):
                    w_text = draw.textlength(test_line, font=font)
                else:
                    bbox = font.getbbox(test_line)
                    w_text = bbox[2] - bbox[0]

                if w_text <= max_w_px:
                    linha_atual = test_line
                else:
                    if linha_atual:
                        linhas_resultado.append(linha_atual)
                    linha_atual = palavra

            if linha_atual:
                linhas_resultado.append(linha_atual)

        return "\n".join(linhas_resultado) if linhas_resultado else str(texto)