"""
Popups para Criação e Gestão Detalhada de Chamados de Garantia & RMA.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from config import (
    BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER,
    FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE
)
from ui.components.base import UIBuilder
from core.database import (
    get_conn,
    obter_catalogo_completo,
    salvar_hierarquia,
    gerar_protocolo_garantia
)
from core.cache import cache
from utils.helpers import agora, brl, txt_para_float, NUMERACAO_POR_TIPO
from utils.formatters import CurrencyFormatter


ETAPAS_GARANTIA = [
    ("solicitacao_cliente", "1. Solicitação Cliente & Reversa", "#3B82F6"),
    ("aguardando_produto_cliente", "2. Cliente ➔ Loja (Trânsito)", "#F59E0B"),
    ("solicitacao_fornecedor", "3. Acionamento Fornecedor / RMA", "#8B5CF6"),
    ("enviando_fornecedor", "4. Loja ➔ Fornecedor (Análise)", "#EC4899"),
    ("fornecedor_loja", "5. Fornecedor ➔ Loja (Retorno)", "#06B6D4"),
    ("loja_cliente", "6. Loja ➔ Cliente (Expedição)", "#22C55E"),
]


class PopupNovaGarantia:
    """Modal de abertura de novo chamado de garantia com seleção de cliente e atributos completos do produto."""

    def __init__(self, app, callback_sucesso):
        self.app = app
        self.callback = callback_sucesso
        self._build()

    def _build(self):
        self.win = tk.Toplevel(self.app)
        self.win.title("Abertura de Chamado de Garantia & RMA")
        self.win.geometry("1060x720")
        self.win.minsize(960, 640)
        self.win.configure(bg=BG)
        self.win.grab_set()

        main_fm = UIBuilder.card(self.win, bg=BG2, px=22, py=18)
        main_fm.pack(fill="both", expand=True, padx=15, pady=15)

        split = UIBuilder.frame(main_fm, bg=BG2)
        split.pack(fill="both", expand=True)

        # ═══════════════════════════════════════════
        # Coluna Esquerda - Seleção do Cliente (Solicitante)
        # ═══════════════════════════════════════════
        col_e = UIBuilder.frame(split, bg=BG2, width=380)
        col_e.pack(side="left", fill="both", expand=True, padx=(0, 15))
        col_e.pack_propagate(False)

        UIBuilder.label(col_e, "1. Cliente Solicitante *", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 5))

        f_b = UIBuilder.frame(col_e, bg=BG2)
        f_b.pack(fill="x", pady=5)
        v_b = tk.StringVar()
        UIBuilder.label(f_b, "🔍", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 4))
        UIBuilder.entry(f_b, var=v_b, width=28).pack(side="left", fill="x", expand=True, ipady=3)

        tf_cli = UIBuilder.frame(col_e, bg=BG2)
        tf_cli.pack(fill="both", expand=True, pady=5)
        self.tv_cli = UIBuilder.make_tree(tf_cli, ("ID", "Nome", "CPF", "Telefone"), [40, 150, 95, 95], ["center", "w", "center", "center"])

        # Carrega clientes em memória
        try:
            with get_conn() as conn:
                self._todos_clientes = conn.execute("SELECT id, nome, cpf, telefone FROM clientes ORDER BY nome").fetchall()
        except Exception:
            self._todos_clientes = []

        def filtrar(*_):
            t = v_b.get().strip().lower()
            for r in self.tv_cli.get_children():
                self.tv_cli.delete(r)
            for r in self._todos_clientes:
                if t and (t not in r[1].lower() and (not r[2] or t not in r[2].lower()) and (not r[3] or t not in r[3].lower())):
                    continue
                self.tv_cli.insert("", "end", iid=str(r[0]), values=(r[0], r[1], r[2] or "—", r[3] or "—"))

        v_b.trace_add("write", filtrar)
        filtrar()

        # ═══════════════════════════════════════════
        # Coluna Direita - Detalhes do Produto & Defeito
        # ═══════════════════════════════════════════
        col_d = UIBuilder.frame(split, bg=BG2, width=580)
        col_d.pack(side="right", fill="both", expand=True, padx=(15, 0))
        col_d.pack_propagate(False)

        UIBuilder.label(col_d, "2. Dados do Produto & Ocorrência", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 6))

        scroll_fm = UIBuilder.frame(col_d, bg=BG2)
        scroll_fm.pack(fill="both", expand=True)
        canvas, inner_d = UIBuilder.scrolled_canvas(scroll_fm)

        # Variáveis
        self.vs = {
            "tipo": tk.StringVar(value=""),
            "marca": tk.StringVar(value=""),
            "modelo": tk.StringVar(value=""),
            "grafico": tk.StringVar(value=""),
            "cor": tk.StringVar(value=""),
            "numeracao": tk.StringVar(value=""),
            "serial": tk.StringVar(value=""),
            "nf": tk.StringVar(value=""),
            "valor": tk.StringVar(value=""),
            "fornecedor": tk.StringVar(value=""),
            "reversa_cli": tk.StringVar(value=""),
        }

        # Carrega catálogo em memória
        try:
            with get_conn() as conn:
                rows = conn.execute("SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM catalogo_produtos UNION SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM produtos_outlet").fetchall()
                self._catalogo_local = [(r[0] or "", r[1] or "", r[2] or "") for r in rows]
        except Exception:
            self._catalogo_local = []

        # 1. Categoria/Tipo e Marca
        r1 = UIBuilder.frame(inner_d, bg=BG2, pady=3)
        r1.pack(fill="x")

        f_tipo = UIBuilder.frame(r1, bg=BG2)
        f_tipo.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f_tipo, "Categoria / Tipo *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        tipos_salvos = sorted(list({r[0] for r in self._catalogo_local if r[0]}))
        self.cb_tipo = ttk.Combobox(f_tipo, textvariable=self.vs["tipo"], values=tipos_salvos, font=FONT_BODY)
        self.cb_tipo.pack(fill="x", ipady=3, pady=(2, 0))

        f_marca = UIBuilder.frame(r1, bg=BG2)
        f_marca.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f_marca, "Marca *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        marcas_iniciais = sorted(list({r[1] for r in self._catalogo_local if r[1]}))
        self.cb_marca = ttk.Combobox(f_marca, textvariable=self.vs["marca"], values=marcas_iniciais, font=FONT_BODY)
        self.cb_marca.pack(fill="x", ipady=3, pady=(2, 0))

        # 2. Modelo e Gráfico
        r2 = UIBuilder.frame(inner_d, bg=BG2, pady=3)
        r2.pack(fill="x")

        f_mod = UIBuilder.frame(r2, bg=BG2)
        f_mod.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f_mod, "Modelo / Edição *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        modelos_iniciais = sorted(list({r[2] for r in self._catalogo_local if r[2]}))
        self.cb_mod = ttk.Combobox(f_mod, textvariable=self.vs["modelo"], values=modelos_iniciais, font=FONT_BODY)
        self.cb_mod.pack(fill="x", ipady=3, pady=(2, 0))

        f_graf = UIBuilder.frame(r2, bg=BG2)
        f_graf.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f_graf, "Gráfico / Estampa", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_graf, var=self.vs["grafico"], width=18).pack(fill="x", ipady=3, pady=(2, 0))

        # 3. Cor e Numeração
        r3 = UIBuilder.frame(inner_d, bg=BG2, pady=3)
        r3.pack(fill="x")

        f_cor = UIBuilder.frame(r3, bg=BG2)
        f_cor.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f_cor, "Cor Dominante", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        cores_lista = ["Preto", "Branco", "Vermelho", "Azul", "Verde", "Amarelo", "Cinza", "Roxo", "Natural / Madeira", "Multicolor"]
        cb_cor = ttk.Combobox(f_cor, textvariable=self.vs["cor"], values=cores_lista, font=FONT_BODY)
        cb_cor.pack(fill="x", ipady=3, pady=(2, 0))

        f_num = UIBuilder.frame(r3, bg=BG2)
        f_num.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f_num, "Numeração / Tamanho", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        self.cb_num = ttk.Combobox(f_num, textvariable=self.vs["numeracao"], font=FONT_BODY)
        self.cb_num.pack(fill="x", ipady=3, pady=(2, 0))

        # 4. Número de Série / Lote e Nota Fiscal
        r4 = UIBuilder.frame(inner_d, bg=BG2, pady=3)
        r4.pack(fill="x")

        f_ser = UIBuilder.frame(r4, bg=BG2)
        f_ser.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f_ser, "Nº Série / IMEI / Lote", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_ser, var=self.vs["serial"], width=18).pack(fill="x", ipady=3, pady=(2, 0))

        f_nf = UIBuilder.frame(r4, bg=BG2)
        f_nf.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f_nf, "Nota Fiscal / Pedido", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_nf, var=self.vs["nf"], width=18).pack(fill="x", ipady=3, pady=(2, 0))

        # 5. Fornecedor e Código Reversa Inicial (Correios)
        r5 = UIBuilder.frame(inner_d, bg=BG2, pady=3)
        r5.pack(fill="x")

        f_forn = UIBuilder.frame(r5, bg=BG2)
        f_forn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f_forn, "Fabricante / Fornecedor", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_forn, var=self.vs["fornecedor"], width=18).pack(fill="x", ipady=3, pady=(2, 0))

        f_rev = UIBuilder.frame(r5, bg=BG2)
        f_rev.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f_rev, "Cód. Postagem Reversa (Cliente)", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_rev, var=self.vs["reversa_cli"], width=18).pack(fill="x", ipady=3, pady=(2, 0))

        # 6. Defeito Relatado (Obrigatório)
        UIBuilder.label(inner_d, "Defeito Relatado / Problema do Cliente *", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w", pady=(8, 2))
        self.txt_defeito = tk.Text(inner_d, bg=BG3, fg=TEXT, font=FONT_BODY, height=3, relief="flat", bd=4, wrap="word")
        self.txt_defeito.pack(fill="x", pady=(0, 6))

        # 7. Observações Internas
        UIBuilder.label(inner_d, "Observações Técnicas / Internas", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(4, 2))
        self.txt_obs = tk.Text(inner_d, bg=BG3, fg=TEXT, font=FONT_SMALL, height=2, relief="flat", bd=4, wrap="word")
        self.txt_obs.pack(fill="x", pady=(0, 10))

        # Cascata reativa
        def atualizar_cascata(*_):
            tipo_sel = self.vs["tipo"].get().strip().lower()
            if tipo_sel:
                marcas_filtradas = sorted(list({r[1] for r in self._catalogo_local if r[1] and r[0].lower() == tipo_sel}))
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel}))
            else:
                marcas_filtradas = sorted(list({r[1] for r in self._catalogo_local if r[1]}))
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2]}))

            self.cb_marca.config(values=marcas_filtradas)
            self.cb_mod.config(values=modelos_filtrados)

            # Numerações pré-definidas
            nums = NUMERACAO_POR_TIPO.get(self.vs["tipo"].get().strip(), [])
            self.cb_num.config(values=nums)

        self.vs["tipo"].trace_add("write", atualizar_cascata)

        # ═══════════════════════════════════════════
        # Rodapé de Ações
        # ═══════════════════════════════════════════
        b_bar = UIBuilder.frame(main_fm, bg=BG2)
        b_bar.pack(fill="x", pady=(14, 0))

        UIBuilder.button(b_bar, "✕ Cancelar", self.win.destroy, color=BG3, width=14).pack(side="left", ipady=5)
        UIBuilder.button(b_bar, "🛡️ Abrir Chamado de Garantia", self._salvar, color="#22C55E", width=26).pack(side="right", ipady=5)

    def _salvar(self):
        sel_cli = self.tv_cli.selection()
        if not sel_cli:
            messagebox.showwarning("Aviso", "Selecione o Cliente solicitante na lista à esquerda!", parent=self.win)
            return

        cliente_id = int(sel_cli[0])
        tipo = self.vs["tipo"].get().strip()
        marca = self.vs["marca"].get().strip()
        modelo = self.vs["modelo"].get().strip()
        defeito = self.txt_defeito.get("1.0", tk.END).strip()

        if not tipo or not marca or not modelo:
            messagebox.showwarning("Aviso", "Preencha Categoria, Marca e Modelo do produto!", parent=self.win)
            return

        if not defeito:
            messagebox.showwarning("Aviso", "Descreva o Defeito Relatado pelo cliente!", parent=self.win)
            return

        grafico = self.vs["grafico"].get().strip()
        cor = self.vs["cor"].get().strip()
        numeracao = self.vs["numeracao"].get().strip()
        serial = self.vs["serial"].get().strip()
        nf = self.vs["nf"].get().strip()
        fornecedor = self.vs["fornecedor"].get().strip()
        reversa_cli = self.vs["reversa_cli"].get().strip()
        obs = self.txt_obs.get("1.0", tk.END).strip()

        # Salva hierarquia no catálogo
        salvar_hierarquia(tipo, marca, modelo)

        def _task_db():
            with get_conn() as conn:
                proto = gerar_protocolo_garantia(conn)
                conn.execute("""
                    INSERT INTO garantias (
                        protocolo, cliente_id, status, tipo_produto, marca, modelo,
                        grafico, cor, numeracao, tamanho, numero_serie, nota_fiscal,
                        defeito_relatado, fornecedor_nome, codigo_reversa_cliente,
                        observacoes, criado, atualizado
                    ) VALUES (
                        %s, %s, 'solicitacao_cliente', %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    proto, cliente_id, tipo, marca, modelo,
                    grafico, cor, numeracao, numeracao, serial, nf,
                    defeito, fornecedor, reversa_cli,
                    obs, agora(), agora()
                ))
                conn.commit()
                cache.invalidate_prefix("garantias")
                return proto

        def _ao_concluir(proto):
            self.app.toast.show(f"Garantia {proto} aberta com sucesso!", "sucesso")
            self.win.destroy()
            if self.callback:
                self.callback()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_concluir,
            mensagem="Registrando garantia..."
        )


class PopupDetalhesGarantia:
    """Modal completo para visualização, edição, avanço de etapas e gestão logística da garantia."""

    def __init__(self, app, garantia_id, callback_atualizado):
        self.app = app
        self.garantia_id = garantia_id
        self.callback = callback_atualizado
        self._carregar_dados()

    def _carregar_dados(self):
        def _task_db():
            with get_conn() as conn:
                row = conn.execute("""
                    SELECT g.id, g.protocolo, g.status, g.tipo_produto, g.marca, g.modelo,
                           g.grafico, g.cor, g.numeracao, g.tamanho, g.numero_serie, g.nota_fiscal,
                           g.valor_produto, g.defeito_relatado, g.fornecedor_nome, g.protocolo_fornecedor,
                           g.codigo_reversa_cliente, g.rastreio_cliente_loja, g.codigo_reversa_fornecedor,
                           g.rastreio_loja_fornecedor, g.rastreio_fornecedor_loja, g.rastreio_loja_cliente,
                           g.observacoes, g.criado, g.atualizado, g.concluido_em,
                           c.id as cli_id, c.nome as cli_nome, c.cpf as cli_cpf, c.telefone as cli_tel, c.email as cli_email
                    FROM garantias g
                    LEFT JOIN clientes c ON g.cliente_id = c.id
                    WHERE g.id = %s
                """, (self.garantia_id,)).fetchone()
                return row

        def _ao_carregar(row):
            if not row:
                self.app.toast.show("Garantia não encontrada!", "erro")
                return
            self.dados = row
            self._build_ui()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_carregar,
            mensagem="Carregando detalhes da garantia..."
        )

    def _build_ui(self):
        d = self.dados
        self.win = tk.Toplevel(self.app)
        self.win.title(f"Garantia {d[1]} — {d[4]} {d[5]}")
        self.win.geometry("980x740")
        self.win.minsize(880, 620)
        self.win.configure(bg=BG)
        self.win.grab_set()

        main_fm = UIBuilder.card(self.win, bg=BG2, px=24, py=18)
        main_fm.pack(fill="both", expand=True, padx=15, pady=15)

        # ═══════════════════════════════════════════
        # Header do Chamado
        # ═══════════════════════════════════════════
        hdr = UIBuilder.frame(main_fm, bg=BG2)
        hdr.pack(fill="x", pady=(0, 10))

        # Protocolo e Titulo
        h_left = UIBuilder.frame(hdr, bg=BG2)
        h_left.pack(side="left", fill="x", expand=True)

        UIBuilder.label(h_left, f"🛡️  Protocolo: {d[1]}", font=("Segoe UI Black", 16, "bold"), bg=BG2, fg=GOLD).pack(anchor="w")
        data_str = d[23].strftime("%d/%m/%Y às %H:%M") if hasattr(d[23], 'strftime') else str(d[23])
        UIBuilder.label(h_left, f"Aberto em: {data_str} • Cliente: {d[27] or 'Sem Cliente'} (CPF: {d[28] or '—'})", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

        # Status Atual Badge & Seletor
        self.v_status = tk.StringVar(value=d[2])
        f_st = UIBuilder.frame(hdr, bg=BG2)
        f_st.pack(side="right")

        if d[2] in ("finalizada", "cancelada", "concluida"):
            badge_cor = SUCCESS if d[2] in ("finalizada", "concluida") else DANGER
            badge_txt = "🏁 FINALIZADA (Histórico)" if d[2] in ("finalizada", "concluida") else "🚫 CANCELADA (Histórico)"
            concl_str = d[25].strftime("%d/%m/%Y às %H:%M") if (d[25] and hasattr(d[25], 'strftime')) else (str(d[25]) if d[25] else "—")
            
            UIBuilder.label(f_st, badge_txt, font=("Segoe UI", 11, "bold"), bg=BG2, fg=badge_cor).pack(anchor="e")
            UIBuilder.label(f_st, f"Concluído em: {concl_str}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="e")
        else:
            UIBuilder.label(f_st, "Etapa Atual do Fluxo:", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="e")
            cb_st = ttk.Combobox(
                f_st,
                textvariable=self.v_status,
                values=[k for k, _, _ in ETAPAS_GARANTIA],
                state="readonly",
                font=("Segoe UI", 10, "bold"),
                width=26
            )
            cb_st.pack(anchor="e", pady=(2, 0))

        # Mapeia nomes legiveis
        status_labels = {k: lbl for k, lbl, _ in ETAPAS_GARANTIA}

        UIBuilder.separator(main_fm).pack(fill="x", pady=(8, 12))

        # ═══════════════════════════════════════════
        # Container Rolável com Seções
        # ═══════════════════════════════════════════
        scroll_fm = UIBuilder.frame(main_fm, bg=BG2)
        scroll_fm.pack(fill="both", expand=True)
        canvas, inner = UIBuilder.scrolled_canvas(scroll_fm)

        # 1. Cartão de Informações do Cliente & Contato
        card_cli = UIBuilder.card(inner, bg=BG3, px=16, py=12)
        card_cli.pack(fill="x", pady=(0, 10))

        UIBuilder.label(card_cli, "👤  Dados do Solicitante", font=FONT_H2, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 6))
        c_row = UIBuilder.frame(card_cli, bg=BG3)
        c_row.pack(fill="x")

        UIBuilder.label(c_row, f"Nome: {d[27] or '—'}\nCPF: {d[28] or '—'}", font=FONT_BODY, bg=BG3, fg=TEXT).pack(side="left", padx=(0, 20))
        UIBuilder.label(c_row, f"Telefone: {d[29] or '—'}\nE-mail: {d[30] or '—'}", font=FONT_BODY, bg=BG3, fg=TEXT).pack(side="left", padx=(0, 20))

        if d[29]:
            UIBuilder.button(c_row, "📋 Copiar Tel", lambda: self.app._copiar_codigo_clipboard(d[29]), color=BG2, width=12).pack(side="right", padx=4, ipady=3)

        # 2. Cartão de Detalhes do Produto
        card_prod = UIBuilder.card(inner, bg=BG3, px=16, py=12)
        card_prod.pack(fill="x", pady=(0, 10))

        UIBuilder.label(card_prod, "🏷️  Dados do Produto", font=FONT_H2, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 6))
        prod_txt = (
            f"• Categoria: {d[3] or '—'}  |  Marca: {d[4] or '—'}  |  Modelo: {d[5] or '—'}\n"
            f"• Gráfico/Estampa: {d[6] or '—'}  |  Cor: {d[7] or '—'}  |  Tamanho: {d[8] or d[9] or '—'}\n"
            f"• Nº de Série / IMEI: {d[10] or '—'}  |  Nota Fiscal: {d[11] or '—'}"
        )
        UIBuilder.label(card_prod, prod_txt, font=FONT_BODY, bg=BG3, fg=TEXT, justify="left").pack(anchor="w", pady=(0, 6))

        # Defeito Relatado
        UIBuilder.label(card_prod, "Defeito / Ocorrência:", font=("Segoe UI", 10, "bold"), bg=BG3, fg=DANGER).pack(anchor="w", pady=(4, 2))
        UIBuilder.label(card_prod, d[13] or "Nenhuma descrição.", font=FONT_BODY, bg=BG2, fg=TEXT, justify="left", padx=10, pady=6).pack(fill="x")

        # 3. Cartão de Logística, Rastreamento & Reversas (Editável)
        card_log = UIBuilder.card(inner, bg=BG3, px=16, py=12)
        card_log.pack(fill="x", pady=(0, 10))

        UIBuilder.label(card_log, "📦  Controle Logístico & Códigos de Rastreamento", font=FONT_H2, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 8))

        from ui.screens.popup_rastreio import PopupRastreioCorreios

        def rastrear_campo(var_obj):
            cod = var_obj.get().strip()
            if cod:
                PopupRastreioCorreios(self.app, cod)
            else:
                self.app.toast.show("Preencha o código para rastrear!", "aviso")

        self.vl = {
            "rev_cli": tk.StringVar(value=d[16] or ""),
            "rast_cli_loja": tk.StringVar(value=d[17] or ""),
            "forn_nome": tk.StringVar(value=d[14] or ""),
            "forn_proto": tk.StringVar(value=d[15] or ""),
            "rev_forn": tk.StringVar(value=d[18] or ""),
            "rast_loja_forn": tk.StringVar(value=d[19] or ""),
            "rast_forn_loja": tk.StringVar(value=d[20] or ""),
            "rast_loja_cli": tk.StringVar(value=d[21] or ""),
        }

        # Linha 1: Cliente -> Loja (Reversa e Rastreio)
        l1 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l1.pack(fill="x")
        
        f1_a = UIBuilder.frame(l1, bg=BG3)
        f1_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f1_a, "1. Cód. Postagem Reversa (Cliente):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        row_1a = UIBuilder.frame(f1_a, bg=BG3)
        row_1a.pack(fill="x", pady=(2, 0))
        UIBuilder.entry(row_1a, var=self.vl["rev_cli"], width=16).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row_1a, text="🔍 Rastrear", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD, activebackground=BG, activeforeground=GOLD, relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: rastrear_campo(self.vl["rev_cli"])).pack(side="left", padx=(6, 0), ipady=2)

        f1_b = UIBuilder.frame(l1, bg=BG3)
        f1_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f1_b, "2. Rastreio Correios (Cliente ➔ Loja):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        row_1b = UIBuilder.frame(f1_b, bg=BG3)
        row_1b.pack(fill="x", pady=(2, 0))
        UIBuilder.entry(row_1b, var=self.vl["rast_cli_loja"], width=16).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row_1b, text="🔍 Rastrear", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD, activebackground=BG, activeforeground=GOLD, relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: rastrear_campo(self.vl["rast_cli_loja"])).pack(side="left", padx=(6, 0), ipady=2)

        # Linha 2: Fornecedor (Nome e Protocolo RMA)
        l2 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l2.pack(fill="x")
        f2_a = UIBuilder.frame(l2, bg=BG3)
        f2_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f2_a, "3. Fabricante / Fornecedor:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f2_a, var=self.vl["forn_nome"], width=20).pack(fill="x", ipady=3, pady=(2, 0))

        f2_b = UIBuilder.frame(l2, bg=BG3)
        f2_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f2_b, "4. Protocolo RMA Fornecedor:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f2_b, var=self.vl["forn_proto"], width=20).pack(fill="x", ipady=3, pady=(2, 0))

        # Linha 3: Loja -> Fornecedor (Reversa Fornecedor e Rastreio)
        l3 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l3.pack(fill="x")
        f3_a = UIBuilder.frame(l3, bg=BG3)
        f3_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f3_a, "5. Cód. Reversa Fornecedor:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        row_3a = UIBuilder.frame(f3_a, bg=BG3)
        row_3a.pack(fill="x", pady=(2, 0))
        UIBuilder.entry(row_3a, var=self.vl["rev_forn"], width=16).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row_3a, text="🔍 Rastrear", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD, activebackground=BG, activeforeground=GOLD, relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: rastrear_campo(self.vl["rev_forn"])).pack(side="left", padx=(6, 0), ipady=2)

        f3_b = UIBuilder.frame(l3, bg=BG3)
        f3_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f3_b, "6. Rastreio (Loja ➔ Fornecedor):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        row_3b = UIBuilder.frame(f3_b, bg=BG3)
        row_3b.pack(fill="x", pady=(2, 0))
        UIBuilder.entry(row_3b, var=self.vl["rast_loja_forn"], width=16).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row_3b, text="🔍 Rastrear", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD, activebackground=BG, activeforeground=GOLD, relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: rastrear_campo(self.vl["rast_loja_forn"])).pack(side="left", padx=(6, 0), ipady=2)

        # Linha 4: Retorno e Expedição Final
        l4 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l4.pack(fill="x")
        f4_a = UIBuilder.frame(l4, bg=BG3)
        f4_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f4_a, "7. Rastreio Retorno (Fornecedor ➔ Loja):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        row_4a = UIBuilder.frame(f4_a, bg=BG3)
        row_4a.pack(fill="x", pady=(2, 0))
        UIBuilder.entry(row_4a, var=self.vl["rast_forn_loja"], width=16).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row_4a, text="🔍 Rastrear", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD, activebackground=BG, activeforeground=GOLD, relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: rastrear_campo(self.vl["rast_forn_loja"])).pack(side="left", padx=(6, 0), ipady=2)

        f4_b = UIBuilder.frame(l4, bg=BG3)
        f4_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f4_b, "8. Rastreio Final (Loja ➔ Cliente):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        row_4b = UIBuilder.frame(f4_b, bg=BG3)
        row_4b.pack(fill="x", pady=(2, 0))
        UIBuilder.entry(row_4b, var=self.vl["rast_loja_cli"], width=16).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row_4b, text="🔍 Rastrear", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD, activebackground=BG, activeforeground=GOLD, relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: rastrear_campo(self.vl["rast_loja_cli"])).pack(side="left", padx=(6, 0), ipady=2)

        # 4. Observações Internas
        UIBuilder.label(inner, "📝  Observações Internas & Laudo Técnico:", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(6, 2))
        self.txt_obs_edit = tk.Text(inner, bg=BG3, fg=TEXT, font=FONT_SMALL, height=3, relief="flat", bd=4, wrap="word")
        self.txt_obs_edit.insert("1.0", d[22] or "")
        self.txt_obs_edit.pack(fill="x", pady=(0, 10))

        # ═══════════════════════════════════════════
        # Rodapé de Ações
        # ═══════════════════════════════════════════
        b_bar = UIBuilder.frame(main_fm, bg=BG2)
        b_bar.pack(fill="x", pady=(14, 0))

        UIBuilder.button(b_bar, "🗑️ Excluir Chamado", self._excluir, color=DANGER, width=18).pack(side="left", ipady=5)
        UIBuilder.button(b_bar, "✕ Fechar", self.win.destroy, color=BG3, width=12).pack(side="left", padx=8, ipady=5)

        if d[2] in ("finalizada", "cancelada", "concluida"):
            UIBuilder.button(b_bar, "🔄 Reabrir para Kanban", self._reabrir_chamado, color=GOLD, fg="#000", width=22).pack(side="right", padx=(8, 0), ipady=5)
            UIBuilder.button(b_bar, "💾 Salvar Observações", self._salvar_edicao, color="#22C55E", width=20).pack(side="right", ipady=5)
        else:
            UIBuilder.button(b_bar, "🏁 Finalizar Garantia", self._abrir_finalizar, color=GOLD, fg="#000", width=20).pack(side="right", padx=(8, 0), ipady=5)
            UIBuilder.button(b_bar, "💾 Salvar Alterações", self._salvar_edicao, color="#22C55E", width=20).pack(side="right", ipady=5)

    def _abrir_finalizar(self):
        PopupFinalizarGarantia(self.app, self.garantia_id, self.dados[1], self._ao_concluir_finalizacao)

    def _ao_concluir_finalizacao(self):
        self.win.destroy()
        if self.callback:
            self.callback()

    def _reabrir_chamado(self):
        if not messagebox.askyesno("Reabrir Chamado", f"Deseja reabrir o chamado {self.dados[1]} de volta para o quadro Kanban ativo?", parent=self.win):
            return

        def _task_db():
            with get_conn() as conn:
                conn.execute("""
                    UPDATE garantias SET
                        status = 'solicitacao_cliente',
                        concluido_em = NULL,
                        atualizado = %s
                    WHERE id = %s
                """, (agora(), self.garantia_id))
                conn.commit()
                cache.invalidate_prefix("garantias")

        def _ao_concluir(_):
            self.app.toast.show("Chamado reaberto no Kanban com sucesso!", "sucesso")
            self.win.destroy()
            if self.callback:
                self.callback()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_concluir,
            mensagem="Reabrindo chamado..."
        )

    def _salvar_edicao(self):
        novo_status = self.v_status.get()
        rev_cli = self.vl["rev_cli"].get().strip()
        rast_cli_loja = self.vl["rast_cli_loja"].get().strip()
        forn_nome = self.vl["forn_nome"].get().strip()
        forn_proto = self.vl["forn_proto"].get().strip()
        rev_forn = self.vl["rev_forn"].get().strip()
        rast_loja_forn = self.vl["rast_loja_forn"].get().strip()
        rast_forn_loja = self.vl["rast_forn_loja"].get().strip()
        rast_loja_cli = self.vl["rast_loja_cli"].get().strip()
        obs = self.txt_obs_edit.get("1.0", tk.END).strip()

        concluido_em = agora() if novo_status == "loja_cliente" else None

        def _task_db():
            with get_conn() as conn:
                conn.execute("""
                    UPDATE garantias SET
                        status = %s,
                        codigo_reversa_cliente = %s,
                        rastreio_cliente_loja = %s,
                        fornecedor_nome = %s,
                        protocolo_fornecedor = %s,
                        codigo_reversa_fornecedor = %s,
                        rastreio_loja_fornecedor = %s,
                        rastreio_fornecedor_loja = %s,
                        rastreio_loja_cliente = %s,
                        observacoes = %s,
                        atualizado = %s,
                        concluido_em = COALESCE(%s, concluido_em)
                    WHERE id = %s
                """, (
                    novo_status, rev_cli, rast_cli_loja, forn_nome, forn_proto,
                    rev_forn, rast_loja_forn, rast_forn_loja, rast_loja_cli,
                    obs, agora(), concluido_em, self.garantia_id
                ))
                conn.commit()
                cache.invalidate_prefix("garantias")

        def _ao_concluir(_):
            self.app.toast.show("Garantia atualizada com sucesso!", "sucesso")
            self.win.destroy()
            if self.callback:
                self.callback()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_concluir,
            mensagem="Salvando alterações..."
        )

    def _excluir(self):
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o chamado {self.dados[1]}?", parent=self.win):
            return

        def _task_db():
            with get_conn() as conn:
                conn.execute("DELETE FROM garantias WHERE id = %s", (self.garantia_id,))
                conn.commit()
                cache.invalidate_prefix("garantias")

        def _ao_concluir(_):
            self.app.toast.show("Chamado de garantia excluído!", "aviso")
            self.win.destroy()
            if self.callback:
                self.callback()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_concluir,
            mensagem="Excluindo chamado..."
        )


MAPA_ETAPAS_CAMPOS = {
    "solicitacao_cliente": {
        "titulo": "1. Solicitação Cliente & Reversa",
        "cor": "#3B82F6",
        "icone": "📝",
        "campos": [
            {
                "chave": "codigo_reversa_cliente",
                "label": "Código de Postagem Reversa (Cliente):",
                "placeholder": "Ex: 123456789 ou Código PAC Reverso",
                "tipo": "reversa"
            }
        ],
        "ajuda": "Código de postagem reversa gerado para o cliente enviar o produto à loja."
    },
    "aguardando_produto_cliente": {
        "titulo": "2. Cliente ➔ Loja (Trânsito)",
        "cor": "#F59E0B",
        "icone": "🚚",
        "campos": [
            {
                "chave": "rastreio_cliente_loja",
                "label": "Código de Rastreio Correios (Cliente ➔ Loja):",
                "placeholder": "Ex: AA123456789BR",
                "tipo": "correios"
            }
        ],
        "ajuda": "Código de rastreamento do pacote enviado pelo cliente para a loja."
    },
    "solicitacao_fornecedor": {
        "titulo": "3. Acionamento Fornecedor / RMA",
        "cor": "#8B5CF6",
        "icone": "🏭",
        "campos": [
            {
                "chave": "fornecedor_nome",
                "label": "Nome do Fabricante / Fornecedor:",
                "placeholder": "Ex: Fox Racing, Alpinestars...",
                "tipo": "texto"
            },
            {
                "chave": "protocolo_fornecedor",
                "label": "Protocolo RMA do Fornecedor:",
                "placeholder": "Ex: RMA-2026-9871",
                "tipo": "texto"
            },
            {
                "chave": "codigo_reversa_fornecedor",
                "label": "Cód. Reversa do Fornecedor (se houver):",
                "placeholder": "Ex: 987654321",
                "tipo": "reversa"
            }
        ],
        "ajuda": "Dados de acionamento do processo junto à fábrica ou distribuidor."
    },
    "enviando_fornecedor": {
        "titulo": "4. Loja ➔ Fornecedor (Análise)",
        "cor": "#EC4899",
        "icone": "📦",
        "campos": [
            {
                "chave": "rastreio_loja_fornecedor",
                "label": "Código de Rastreio (Loja ➔ Fornecedor):",
                "placeholder": "Ex: AA123456789BR",
                "tipo": "correios"
            }
        ],
        "ajuda": "Código de rastreamento do envio da loja para a fábrica/fornecedor."
    },
    "fornecedor_loja": {
        "titulo": "5. Fornecedor ➔ Loja (Retorno)",
        "cor": "#06B6D4",
        "icone": "🔄",
        "campos": [
            {
                "chave": "rastreio_fornecedor_loja",
                "label": "Código de Rastreio Retorno (Fornecedor ➔ Loja):",
                "placeholder": "Ex: AA123456789BR",
                "tipo": "correios"
            }
        ],
        "ajuda": "Código de rastreamento do produto reparado/trocado vindo do fornecedor."
    },
    "loja_cliente": {
        "titulo": "6. Loja ➔ Cliente (Expedição)",
        "cor": "#22C55E",
        "icone": "🎉",
        "campos": [
            {
                "chave": "rastreio_loja_cliente",
                "label": "Código de Rastreio Final (Loja ➔ Cliente):",
                "placeholder": "Ex: AA123456789BR",
                "tipo": "correios"
            }
        ],
        "ajuda": "Código de rastreamento da expedição final com o produto devolvido ao cliente."
    }
}


class PopupMoverEtapaGarantia:
    """
    Modal de confirmação e captura contextual dos códigos de rastreamento / reversa / RMA
    ao mover um card entre etapas do Kanban de Garantias.
    """

    def __init__(self, app, item_data, status_origem, status_destino, callback_confirmar, callback_cancelar=None):
        self.app = app
        self.item_data = item_data
        self.status_origem = status_origem
        self.status_destino = status_destino
        self.callback_confirmar = callback_confirmar
        self.callback_cancelar = callback_cancelar
        self._variaveis = {}
        self.confirmado = False
        self._build_ui()

    def _obter_campo(self, chave):
        if isinstance(self.item_data, dict):
            return self.item_data.get(chave, "")
        idx_map = {
            "id": 0, "protocolo": 1, "status": 2, "tipo_produto": 3, "marca": 4, "modelo": 5,
            "grafico": 6, "cor": 7, "numeracao": 8, "tamanho": 9, "numero_serie": 10,
            "nota_fiscal": 11, "valor_produto": 12, "defeito_relatado": 13, "fornecedor_nome": 14,
            "protocolo_fornecedor": 15, "codigo_reversa_cliente": 16, "rastreio_cliente_loja": 17,
            "codigo_reversa_fornecedor": 18, "rastreio_loja_fornecedor": 19, "rastreio_fornecedor_loja": 20,
            "rastreio_loja_cliente": 21, "observacoes": 22, "criado": 23, "atualizado": 24,
            "concluido_em": 25, "cli_id": 26, "cli_nome": 27, "cli_tel": 28
        }
        if isinstance(self.item_data, (list, tuple)):
            idx = idx_map.get(chave)
            if idx is not None and idx < len(self.item_data):
                return self.item_data[idx] or ""
        return ""

    def _build_ui(self):
        info_origem = MAPA_ETAPAS_CAMPOS.get(self.status_origem, {
            "titulo": self.status_origem, "cor": TEXT_DIM, "icone": "📍"
        })
        info_destino = MAPA_ETAPAS_CAMPOS.get(self.status_destino, {
            "titulo": self.status_destino, "cor": GOLD, "icone": "🎯", "campos": [], "ajuda": ""
        })

        proto = self._obter_campo("protocolo") or "Garantia"
        marca = self._obter_campo("marca") or ""
        modelo = self._obter_campo("modelo") or ""
        cli_nome = self._obter_campo("cli_nome") or "Sem Cliente"

        self.win = tk.Toplevel(self.app)
        self.win.title(f"Avançar Etapa — Protocolo {proto}")
        self.win.geometry("580x530")
        self.win.minsize(540, 460)
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.grab_set()

        # Centraliza sobre a janela principal
        self.win.update_idletasks()
        try:
            x = self.app.winfo_x() + (self.app.winfo_width() // 2) - (580 // 2)
            y = self.app.winfo_y() + (self.app.winfo_height() // 2) - (530 // 2)
            self.win.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        main_fm = UIBuilder.card(self.win, bg=BG2, px=20, py=16)
        main_fm.pack(fill="both", expand=True, padx=14, pady=14)

        # ═══════════════════════════════════════════
        # Header do Modal: Protocolo + Produto
        # ═══════════════════════════════════════════
        hdr = UIBuilder.frame(main_fm, bg=BG2)
        hdr.pack(fill="x", pady=(0, 10))

        UIBuilder.label(hdr, f"🛡️  Mover Chamado: {proto}", font=("Segoe UI Black", 14, "bold"), bg=BG2, fg=GOLD).pack(anchor="w")
        UIBuilder.label(hdr, f"Produto: {marca} {modelo}  •  Cliente: {cli_nome[:25]}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

        UIBuilder.separator(main_fm, bg=BG3).pack(fill="x", pady=(4, 10))

        # ═══════════════════════════════════════════
        # Transição de Etapa Visual (Origem ➔ Destino)
        # ═══════════════════════════════════════════
        f_transicao = UIBuilder.card(main_fm, bg=BG3, px=12, py=10)
        f_transicao.pack(fill="x", pady=(0, 12))

        # Origem
        lbl_origem = tk.Label(
            f_transicao,
            text=f"{info_origem['icone']} {info_origem['titulo']}",
            font=("Segoe UI", 9, "bold"),
            bg=BG3,
            fg=info_origem.get("cor", TEXT_DIM)
        )
        lbl_origem.pack(side="left")

        # Seta
        tk.Label(f_transicao, text="  ➔  ", font=("Segoe UI", 11, "bold"), bg=BG3, fg=GOLD).pack(side="left")

        # Destino
        lbl_dest = tk.Label(
            f_transicao,
            text=f"{info_destino['icone']} {info_destino['titulo']}",
            font=("Segoe UI", 9, "bold"),
            bg=BG3,
            fg=info_destino.get("cor", GOLD)
        )
        lbl_dest.pack(side="left")

        # ═══════════════════════════════════════════
        # Campos Dinâmicos da Etapa de Destino
        # ═══════════════════════════════════════════
        campos = info_destino.get("campos", [])
        f_campos = UIBuilder.frame(main_fm, bg=BG2)
        f_campos.pack(fill="x", pady=(0, 6))

        primeiro_entry = None
        from ui.screens.popup_rastreio import PopupRastreioCorreios

        for cmp_info in campos:
            chave = cmp_info["chave"]
            label_txt = cmp_info["label"]
            tipo_cmp = cmp_info.get("tipo", "texto")
            val_atual = self._obter_campo(chave)

            var = tk.StringVar(value=str(val_atual) if val_atual is not None else "")
            self._variaveis[chave] = var

            f_linha = UIBuilder.frame(f_campos, bg=BG2, pady=4)
            f_linha.pack(fill="x")

            UIBuilder.label(f_linha, label_txt, font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT).pack(anchor="w")

            f_input = UIBuilder.frame(f_linha, bg=BG2)
            f_input.pack(fill="x", pady=(2, 0))

            ent = UIBuilder.entry(f_input, var=var, width=28)
            ent.pack(side="left", fill="x", expand=True, ipady=3)

            if primeiro_entry is None:
                primeiro_entry = ent

            # Botão de Teste de Rastreio (se for campo de correios ou reversa)
            if tipo_cmp in ("correios", "reversa"):
                def _consultar(v=var):
                    c = v.get().strip()
                    if c:
                        PopupRastreioCorreios(self.app, c)
                    else:
                        self.app.toast.show("Preencha o código para rastrear!", "aviso")

                btn_test = tk.Button(
                    f_input,
                    text="🔍 Testar Rastreio",
                    font=("Segoe UI", 9, "bold"),
                    bg=BG3,
                    fg=GOLD,
                    activebackground=BG,
                    activeforeground=GOLD,
                    relief="flat",
                    bd=0,
                    padx=12,
                    pady=6,
                    cursor="hand2",
                    command=_consultar
                )
                btn_test.pack(side="left", padx=(8, 0), ipady=3)

        # Texto de ajuda da etapa
        ajuda_txt = info_destino.get("ajuda", "")
        if ajuda_txt:
            UIBuilder.label(
                main_fm,
                f"💡 {ajuda_txt}",
                font=FONT_SMALL,
                bg=BG2,
                fg=TEXT_DIM,
                wraplength=480,
                justify="left"
            ).pack(anchor="w", pady=(2, 8))

        # ═══════════════════════════════════════════
        # Campo Opcional: Adicionar Nota de Ocorrência
        # ═══════════════════════════════════════════
        UIBuilder.label(main_fm, "📝 Nota / Atualização de Histórico (Opcional):", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(2, 2))
        self.txt_nota = tk.Text(main_fm, bg=BG3, fg=TEXT, font=FONT_SMALL, height=2, relief="flat", bd=3, wrap="word")
        self.txt_nota.pack(fill="x", pady=(0, 10))

        # ═══════════════════════════════════════════
        # Rodapé com Botões
        # ═══════════════════════════════════════════
        b_bar = UIBuilder.frame(main_fm, bg=BG2)
        b_bar.pack(fill="x", side="bottom", pady=(10, 0))

        UIBuilder.button(
            b_bar,
            "✕ Cancelar",
            self._cancelar,
            color=BG3,
            width=14
        ).pack(side="left", ipady=5)

        UIBuilder.button(
            b_bar,
            "✓ Confirmar e Mover",
            self._confirmar,
            color="#22C55E",
            width=22
        ).pack(side="right", ipady=5)

        # Foco inicial no primeiro campo
        if primeiro_entry:
            self.win.after(100, primeiro_entry.focus_set)

        # Atalhos de Teclado
        self.win.bind("<Return>", lambda _: self._confirmar())
        self.win.bind("<Escape>", lambda _: self._cancelar())
        self.win.protocol("WM_DELETE_WINDOW", self._cancelar)

    def _confirmar(self):
        dados_atualizados = {}
        for chave, var in self._variaveis.items():
            dados_atualizados[chave] = var.get().strip()

        nota = self.txt_nota.get("1.0", tk.END).strip()
        if nota:
            obs_existente = self._obter_campo("observacoes") or ""
            data_hora = agora().strftime("%d/%m/%Y %H:%M")
            nova_obs = f"{obs_existente}\n[{data_hora} - {self.status_destino}]: {nota}".strip()
            dados_atualizados["observacoes"] = nova_obs

        self.confirmado = True
        self.win.destroy()
        if self.callback_confirmar:
            self.callback_confirmar(dados_atualizados)

    def _cancelar(self):
        self.confirmado = False
        self.win.destroy()
        if self.callback_cancelar:
            self.callback_cancelar()


class PopupFinalizarGarantia:
    """Modal para concluir ou cancelar um chamado de garantia com registro de desfecho e nota."""

    def __init__(self, app, garantia_id, protocolo, callback_concluido=None):
        self.app = app
        self.garantia_id = garantia_id
        self.protocolo = protocolo
        self.callback = callback_concluido
        self._build()

    def _build(self):
        self.win = tk.Toplevel(self.app)
        self.win.title(f"Finalizar Processo de Garantia — {self.protocolo}")
        self.win.geometry("560x510")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.grab_set()

        card = UIBuilder.card(self.win, bg=BG2, px=26, py=20)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Cabeçalho
        UIBuilder.label(card, f"🏁 Finalizar Garantia: {self.protocolo}", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 4))
        UIBuilder.label(
            card, 
            "Ao finalizar ou cancelar, este chamado sairá das colunas ativas do Kanban e será arquivado no Histórico Global.",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT_DIM,
            wraplength=480,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        # 1. Tipo de Desfecho (Finalizada vs Cancelada)
        v_tipo = tk.StringVar(value="finalizada")
        f_tipo = UIBuilder.frame(card, bg=BG2)
        f_tipo.pack(fill="x", pady=(0, 12))

        UIBuilder.label(f_tipo, "Desfecho do Processo *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))
        
        r_box = UIBuilder.frame(f_tipo, bg=BG2)
        r_box.pack(fill="x")
        tk.Radiobutton(
            r_box, text="✅ Finalizada / Concluída", variable=v_tipo, value="finalizada",
            bg=BG2, fg=SUCCESS, selectcolor=BG3, activebackground=BG2, activeforeground=SUCCESS, font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            r_box, text="🚫 Cancelada / Encerrada", variable=v_tipo, value="cancelada",
            bg=BG2, fg=DANGER, selectcolor=BG3, activebackground=BG2, activeforeground=DANGER, font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        # 2. Motivo / Resolução
        UIBuilder.label(card, "Motivo / Resolução Principal *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(0, 2))
        v_motivo = tk.StringVar(value="Produto trocado por novo")
        motivos_opcoes = [
            "Produto trocado por novo",
            "Produto reparado com sucesso pelo fabricante",
            "Crédito / Vale gerado para o cliente",
            "Reembolso financeiro efetuado",
            "Cancelado a pedido do cliente",
            "Garantia recusada (fora de prazo / mau uso)",
            "Processo finalizado com sucesso",
            "Outro / Ver parecer detalhado"
        ]
        cb_motivo = ttk.Combobox(card, textvariable=v_motivo, values=motivos_opcoes, font=FONT_BODY)
        cb_motivo.pack(fill="x", ipady=4, pady=(0, 12))

        # 3. Parecer / Parecer Final
        UIBuilder.label(card, "Parecer Final / Observações de Encerramento (Opcional):", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(0, 2))
        txt_obs = tk.Text(card, bg=BG3, fg=TEXT, font=FONT_SMALL, height=4, relief="flat", bd=4, wrap="word")
        txt_obs.pack(fill="x", pady=(0, 16))

        # Rodapé de Ações
        f_botoes = UIBuilder.frame(card, bg=BG2)
        f_botoes.pack(fill="x", side="bottom")

        def _confirmar():
            status_final = v_tipo.get()
            motivo_sel = v_motivo.get().strip() or "Finalizado"
            parecer = txt_obs.get("1.0", tk.END).strip()

            data_hora = agora().strftime("%d/%m/%Y %H:%M")
            nota_fechamento = f"[{data_hora} - {status_final.upper()}]: Motivo: {motivo_sel}"
            if parecer:
                nota_fechamento += f" | Obs: {parecer}"

            self.win.destroy()

            def _task_db():
                with get_conn() as conn:
                    obs_antiga = conn.execute("SELECT COALESCE(observacoes, '') FROM garantias WHERE id=%s", (self.garantia_id,)).fetchone()[0]
                    obs_completa = f"{obs_antiga}\n{nota_fechamento}".strip() if obs_antiga else nota_fechamento

                    conn.execute("""
                        UPDATE garantias SET
                            status = %s,
                            concluido_em = %s,
                            observacoes = %s,
                            atualizado = %s
                        WHERE id = %s
                    """, (status_final, agora(), obs_completa, agora(), self.garantia_id))
                    conn.commit()
                    cache.invalidate_prefix("garantias")

            def _ao_fim(_):
                self.app.toast.show(f"Garantia {self.protocolo} finalizada e arquivada no histórico!", "sucesso")
                if self.callback:
                    self.callback()

            self.app.executar_async(
                funcao_task=_task_db,
                callback_sucesso=_ao_fim,
                mensagem=f"Finalizando garantia {self.protocolo}..."
            )

        UIBuilder.button(f_botoes, "✕ Cancelar", self.win.destroy, color=BG3, width=12).pack(side="left")
        UIBuilder.button(f_botoes, "🏁 Confirmar Encerramento", _confirmar, color=SUCCESS, fg="#000", width=24).pack(side="right")


class PopupHistoricoGarantias:
    """Modal do Histórico Global de Garantias Finalizadas e Canceladas."""

    def __init__(self, app, callback_atualizar_pai=None):
        self.app = app
        self.callback = callback_atualizar_pai
        self.win = None
        self._todos_historico = []
        self.v_busca = tk.StringVar()
        self.v_filtro_status = tk.StringVar(value="Todos")
        self._build()
        self._carregar_dados()

    def _build(self):
        self.win = tk.Toplevel(self.app)
        self.win.title("📜 Histórico Global de Garantias — Finalizadas & Canceladas")
        self.win.geometry("1140x690")
        self.win.minsize(980, 560)
        self.win.configure(bg=BG)
        self.win.grab_set()

        main_fm = UIBuilder.card(self.win, bg=BG2, px=22, py=18)
        main_fm.pack(fill="both", expand=True, padx=14, pady=14)

        # Cabeçalho
        h_row = UIBuilder.frame(main_fm, bg=BG2)
        h_row.pack(fill="x", pady=(0, 10))

        UIBuilder.label(h_row, "📜 Histórico Global de Garantias", font=FONT_TITLE, bg=BG2, fg=GOLD).pack(side="left")
        self.lbl_contagem = UIBuilder.label(h_row, "Carregando...", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM)
        self.lbl_contagem.pack(side="right")

        # Barra de Filtros e Busca
        f_filtros = UIBuilder.frame(main_fm, bg=BG2)
        f_filtros.pack(fill="x", pady=(0, 10))

        UIBuilder.label(f_filtros, "🔍 Buscar:", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 4))
        e_busca = UIBuilder.entry(f_filtros, var=self.v_busca, width=32)
        e_busca.pack(side="left", ipady=3)
        self.v_busca.trace_add("write", lambda *_: self._popular_tree())

        UIBuilder.label(f_filtros, "Status:", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(18, 4))
        cb_f = ttk.Combobox(
            f_filtros,
            textvariable=self.v_filtro_status,
            values=["Todos", "Finalizadas", "Canceladas"],
            state="readonly",
            font=FONT_BODY,
            width=16
        )
        cb_f.set("Todos")
        cb_f.pack(side="left")
        cb_f.bind("<<ComboboxSelected>>", lambda *_: self._popular_tree())

        # Tabela Treeview
        tf = UIBuilder.frame(main_fm, bg=BG2)
        tf.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("ID", "Protocolo", "Status", "Cliente", "Produto", "Fornecedor", "Data Abertura", "Data Conclusão")
        widths = [45, 110, 115, 180, 200, 140, 115, 115]
        anchors = ["center", "center", "center", "w", "w", "w", "center", "center"]

        self.tv = UIBuilder.make_tree(tf, cols, widths, anchors)
        self.tv.tag_configure("tag_finalizada", foreground=SUCCESS)
        self.tv.tag_configure("tag_cancelada", foreground=DANGER)

        self.tv.bind("<Double-1>", self._abrir_detalhe)

        # Rodapé de Ações
        b_bar = UIBuilder.frame(main_fm, bg=BG2)
        b_bar.pack(fill="x")

        UIBuilder.button(b_bar, "👁️ Ver Detalhes", self._abrir_detalhe, color=BG3, width=16).pack(side="left", padx=(0, 6))
        UIBuilder.button(b_bar, "🔄 Reabrir para Kanban", self._reabrir_selecionado, color=GOLD, fg="#000", width=22).pack(side="left", padx=6)
        UIBuilder.button(b_bar, "🗑️ Excluir Registro", self._excluir_selecionado, color=DANGER, width=18).pack(side="left", padx=6)
        UIBuilder.button(b_bar, "✕ Fechar", self.win.destroy, color=BG3, width=12).pack(side="right")

    def _carregar_dados(self):
        def _task():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT g.id, g.protocolo, g.status,
                           COALESCE(c.nome, 'Sem Cliente') as cli_nome,
                           CONCAT(COALESCE(g.marca, ''), ' ', COALESCE(g.modelo, g.tipo_produto, '')) as prod_nome,
                           COALESCE(g.fornecedor_nome, '—') as fornecedor,
                           g.criado, g.concluido_em,
                           COALESCE(c.cpf, '') as cli_cpf,
                           COALESCE(g.numero_serie, '') as serial
                    FROM garantias g
                    LEFT JOIN clientes c ON g.cliente_id = c.id
                    WHERE g.status IN ('finalizada', 'cancelada', 'concluida')
                    ORDER BY COALESCE(g.concluido_em, g.atualizado, g.criado) DESC
                """).fetchall()

        def _ao_carregar(rows):
            self._todos_historico = rows or []
            self._popular_tree()

        self.app.executar_async(
            funcao_task=_task,
            callback_sucesso=_ao_carregar,
            mensagem="Carregando histórico global de garantias..."
        )

    def _popular_tree(self):
        if not self.tv:
            return

        for child in self.tv.get_children():
            self.tv.delete(child)

        termo = self.v_busca.get().strip().lower()
        filtro_st = self.v_filtro_status.get().lower()

        filtrados = 0
        for r in self._todos_historico:
            # r = (id, protocolo, status, cli_nome, prod_nome, fornecedor, criado, concluido_em, cli_cpf, serial)
            g_id, proto, status, cli_nome, prod_nome, fornecedor, criado, concluido_em, cli_cpf, serial = r

            # Filtro por Status
            if filtro_st == "finalizadas" and status not in ("finalizada", "concluida"):
                continue
            if filtro_st == "canceladas" and status != "cancelada":
                continue

            # Filtro de Busca
            if termo:
                match = (
                    termo in proto.lower() or
                    termo in cli_nome.lower() or
                    termo in prod_nome.lower() or
                    termo in fornecedor.lower() or
                    termo in cli_cpf.lower() or
                    termo in serial.lower()
                )
                if not match:
                    continue

            tag = "tag_finalizada" if status in ("finalizada", "concluida") else "tag_cancelada"
            status_txt = "✅ Finalizada" if status in ("finalizada", "concluida") else "🚫 Cancelada"

            dt_abertura = criado.strftime("%d/%m/%Y %H:%M") if hasattr(criado, 'strftime') else str(criado)
            dt_conclusao = concluido_em.strftime("%d/%m/%Y %H:%M") if (concluido_em and hasattr(concluido_em, 'strftime')) else (str(concluido_em) if concluido_em else "—")

            self.tv.insert(
                "",
                "end",
                iid=str(g_id),
                values=(g_id, proto, status_txt, cli_nome, prod_nome, fornecedor, dt_abertura, dt_conclusao),
                tags=(tag,)
            )
            filtrados += 1

        self.lbl_contagem.config(text=f"{filtrados} chamado(s) no histórico")

    def _sel_id(self):
        sel = self.tv.selection()
        if not sel:
            self.app.toast.show("Selecione um chamado no histórico.", "aviso")
            return None
        return int(sel[0])

    def _abrir_detalhe(self, event=None):
        if event and self.tv.identify_region(event.x, event.y) != "cell":
            return
        gid = self._sel_id()
        if not gid:
            return
        PopupDetalhesGarantia(self.app, gid, lambda: (self._carregar_dados(), self.callback and self.callback()))

    def _reabrir_selecionado(self):
        gid = self._sel_id()
        if not gid:
            return

        if not messagebox.askyesno("Reabrir Chamado", "Deseja reabrir este chamado e movê-lo de volta para o quadro Kanban ativo?", parent=self.win):
            return

        def _task():
            with get_conn() as conn:
                conn.execute("""
                    UPDATE garantias SET
                        status = 'solicitacao_cliente',
                        concluido_em = NULL,
                        atualizado = %s
                    WHERE id = %s
                """, (agora(), gid))
                conn.commit()
                cache.invalidate_prefix("garantias")

        def _fim(_):
            self.app.toast.show("Garantia reaberta no Kanban ativo!", "sucesso")
            self._carregar_dados()
            if self.callback:
                self.callback()

        self.app.executar_async(funcao_task=_task, callback_sucesso=_fim, mensagem="Reabrindo garantia...")

    def _excluir_selecionado(self):
        gid = self._sel_id()
        if not gid:
            return

        if not messagebox.askyesno("Excluir", "Excluir permanentemente este chamado do histórico?", parent=self.win):
            return

        def _task():
            with get_conn() as conn:
                conn.execute("DELETE FROM garantias WHERE id = %s", (gid,))
                conn.commit()
                cache.invalidate_prefix("garantias")

        def _fim(_):
            self.app.toast.show("Garantia excluída do histórico!", "aviso")
            self._carregar_dados()
            if self.callback:
                self.callback()

        self.app.executar_async(funcao_task=_task, callback_sucesso=_fim, mensagem="Excluindo...")

