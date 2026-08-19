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
        b_bar.pack(fill="x", pady=(12, 0))

        UIBuilder.button(b_bar, "✕ Cancelar", self.win.destroy, color=BG3, width=14).pack(side="left")
        UIBuilder.button(b_bar, "🛡️ Abrir Chamado de Garantia", self._salvar, color="#22C55E", width=26).pack(side="right")

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
            UIBuilder.button(c_row, "📋 Copiar Tel", lambda: self.app._copiar_codigo_clipboard(d[29]), color=BG2, width=12).pack(side="right", padx=4)

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
        UIBuilder.entry(f1_a, var=self.vl["rev_cli"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        f1_b = UIBuilder.frame(l1, bg=BG3)
        f1_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f1_b, "2. Rastreio Correios (Cliente ➔ Loja):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f1_b, var=self.vl["rast_cli_loja"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        # Linha 2: Fornecedor (Nome e Protocolo RMA)
        l2 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l2.pack(fill="x")
        f2_a = UIBuilder.frame(l2, bg=BG3)
        f2_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f2_a, "3. Fabricante / Fornecedor:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f2_a, var=self.vl["forn_nome"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        f2_b = UIBuilder.frame(l2, bg=BG3)
        f2_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f2_b, "4. Protocolo RMA Fornecedor:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f2_b, var=self.vl["forn_proto"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        # Linha 3: Loja -> Fornecedor (Reversa Fornecedor e Rastreio)
        l3 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l3.pack(fill="x")
        f3_a = UIBuilder.frame(l3, bg=BG3)
        f3_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f3_a, "5. Cód. Reversa Fornecedor:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f3_a, var=self.vl["rev_forn"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        f3_b = UIBuilder.frame(l3, bg=BG3)
        f3_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f3_b, "6. Rastreio (Loja ➔ Fornecedor):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f3_b, var=self.vl["rast_loja_forn"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        # Linha 4: Retorno e Expedição Final
        l4 = UIBuilder.frame(card_log, bg=BG3, pady=3)
        l4.pack(fill="x")
        f4_a = UIBuilder.frame(l4, bg=BG3)
        f4_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        UIBuilder.label(f4_a, "7. Rastreio Retorno (Fornecedor ➔ Loja):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f4_a, var=self.vl["rast_forn_loja"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        f4_b = UIBuilder.frame(l4, bg=BG3)
        f4_b.pack(side="left", fill="x", expand=True, padx=(6, 0))
        UIBuilder.label(f4_b, "8. Rastreio Final (Loja ➔ Cliente):", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f4_b, var=self.vl["rast_loja_cli"], width=20).pack(fill="x", ipady=2, pady=(2, 0))

        # 4. Observações Internas
        UIBuilder.label(inner, "📝  Observações Internas & Laudo Técnico:", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(6, 2))
        self.txt_obs_edit = tk.Text(inner, bg=BG3, fg=TEXT, font=FONT_SMALL, height=3, relief="flat", bd=4, wrap="word")
        self.txt_obs_edit.insert("1.0", d[22] or "")
        self.txt_obs_edit.pack(fill="x", pady=(0, 10))

        # ═══════════════════════════════════════════
        # Rodapé de Ações
        # ═══════════════════════════════════════════
        b_bar = UIBuilder.frame(main_fm, bg=BG2)
        b_bar.pack(fill="x", pady=(10, 0))

        UIBuilder.button(b_bar, "🗑️ Excluir Chamado", self._excluir, color=DANGER, width=16).pack(side="left")
        UIBuilder.button(b_bar, "✕ Fechar", self.win.destroy, color=BG3, width=12).pack(side="left", padx=8)

        UIBuilder.button(b_bar, "💾 Salvar Alterações", self._salvar_edicao, color="#22C55E", width=20).pack(side="right")

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
