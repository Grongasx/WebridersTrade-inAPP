"""
Tela de Controle de Garantias & RMA - Visualização Kanban Interativa com Drag-and-Drop.
"""

import tkinter as tk
from tkinter import ttk
from config import (
    BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER,
    FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE
)
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from ui.screens.popup_garantia import PopupNovaGarantia, PopupDetalhesGarantia, ETAPAS_GARANTIA
from core.database import get_conn
from core.cache import cache
from utils.helpers import agora


class GarantiasScreen(BaseScreen):
    """Tela Kanban de Gestão de Garantias e RMA com Drag-and-Drop."""

    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._garantias = []
        self._colunas = {}
        self._col_frames = {}
        self._card_widgets = {}
        self._drag_data = {"id": None, "origem": None, "card": None, "ghost": None}
        self.v_busca = tk.StringVar()

    def show(self, **kwargs):
        self._carregar_dados()

    def _carregar_dados(self):
        def _task_db():
            cached = cache.get("garantias:list")
            if cached is not None:
                return cached

            with get_conn() as conn:
                rows = conn.execute("""
                    SELECT g.id, g.protocolo, g.status, g.tipo_produto, g.marca, g.modelo,
                           g.grafico, g.cor, g.numeracao, g.tamanho, g.numero_serie, g.nota_fiscal,
                           g.valor_produto, g.defeito_relatado, g.fornecedor_nome, g.protocolo_fornecedor,
                           g.codigo_reversa_cliente, g.rastreio_cliente_loja, g.codigo_reversa_fornecedor,
                           g.rastreio_loja_fornecedor, g.rastreio_fornecedor_loja, g.rastreio_loja_cliente,
                           g.observacoes, g.criado, g.atualizado,
                           c.id as cli_id, c.nome as cli_nome, c.telefone as cli_tel
                    FROM garantias g
                    LEFT JOIN clientes c ON g.cliente_id = c.id
                    ORDER BY g.criado DESC
                """).fetchall()
                cache.set("garantias:list", rows, ttl=30)
                return rows

        def _ao_carregar(rows):
            self._garantias = rows or []
            self.clear()
            self._build()
            self._renderizar_kanban()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_carregar,
            mensagem="Carregando workflow de garantias..."
        )

    def _build(self):
        # ═══════════════════════════════════════════
        # Header com Busca e Botão de Abertura
        # ═══════════════════════════════════════════
        h = self.build_header("🛡️  Controle de Garantias & RMA (Workflow)", fg=GOLD)

        # Barra de Ações Superior
        f_top = UIBuilder.frame(self.content, padx=20, pady=6)
        f_top.pack(fill="x")

        # Campo de Busca Rápida
        f_search = UIBuilder.frame(f_top, bg=BG)
        f_search.pack(side="left", fill="x", expand=True)

        UIBuilder.label(f_search, "🔍", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="left", padx=(0, 4))
        e_busca = UIBuilder.entry(f_search, var=self.v_busca, width=32)
        e_busca.pack(side="left", ipady=3)
        self.v_busca.trace_add("write", lambda *_: self._renderizar_kanban())

        # Legenda de Dica
        UIBuilder.label(
            f_top,
            "💡 Dica: Arraste os cards entre as colunas ou use os botões ◀ / ▶ para avançar.",
            font=FONT_SMALL,
            bg=BG,
            fg=TEXT_DIM
        ).pack(side="left", padx=18)

        # Botão Nova Garantia
        UIBuilder.button(
            f_top,
            "➕ Nova Solicitação de Garantia",
            self._abrir_nova_garantia,
            color="#22C55E",
            width=28
        ).pack(side="right")

        # ═══════════════════════════════════════════
        # Quadro Kanban (Horizontal com 6 Colunas)
        # ═══════════════════════════════════════════
        self.kanban_container = UIBuilder.frame(self.content, padx=14, pady=8)
        self.kanban_container.pack(fill="both", expand=True)

        # Configura as 6 colunas proporcionais
        for i, (key, label, color) in enumerate(ETAPAS_GARANTIA):
            self.kanban_container.columnconfigure(i, weight=1, uniform="kanban_col")

            # Coluna Card Container
            col_box = UIBuilder.card(self.kanban_container, bg=BG2, px=8, py=8)
            col_box.grid(row=0, column=i, sticky="nsew", padx=4, pady=2)
            self._col_frames[key] = col_box

            # Header da Coluna com Badge e Contador
            col_hdr = UIBuilder.frame(col_box, bg=BG2)
            col_hdr.pack(fill="x", pady=(0, 6))

            # Dot colorido + Título
            t_box = UIBuilder.frame(col_hdr, bg=BG2)
            t_box.pack(side="left", fill="x", expand=True)

            dot = tk.Label(t_box, text="■", font=("Segoe UI", 10), bg=BG2, fg=color)
            dot.pack(side="left", padx=(0, 4))

            lbl_t = tk.Label(t_box, text=label, font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT, wraplength=125, justify="left", anchor="w")
            lbl_t.pack(side="left")

            # Badge Contador
            badge_cnt = tk.Label(col_hdr, text="0", font=("Segoe UI", 9, "bold"), bg=BG3, fg=color, padx=6, pady=1)
            badge_cnt.pack(side="right", anchor="ne")

            UIBuilder.separator(col_box).pack(fill="x", pady=(4, 6))

            # Container com scroll vertical para os cards da coluna
            scroll_area = UIBuilder.frame(col_box, bg=BG2)
            scroll_area.pack(fill="both", expand=True)

            canvas, inner_col = UIBuilder.scrolled_canvas(scroll_area)
            self._colunas[key] = {
                "inner": inner_col,
                "badge": badge_cnt,
                "canvas": canvas,
                "color": color,
                "box": col_box
            }

        self.kanban_container.rowconfigure(0, weight=1)

    def _renderizar_kanban(self):
        """Distribui os cards de garantias filtrados pelas 6 colunas do Kanban."""
        termo = self.v_busca.get().strip().lower()

        # Limpa cards existentes em todas as colunas
        for key, col in self._colunas.items():
            for child in col["inner"].winfo_children():
                child.destroy()

        contadores = {k: 0 for k, _, _ in ETAPAS_GARANTIA}
        self._card_widgets.clear()

        # Etapas ordenadas para botoes rapidos de avancar/voltar
        chaves_etapas = [k for k, _, _ in ETAPAS_GARANTIA]

        for g in self._garantias:
            g_id = g[0]
            proto = g[1] or ""
            status = g[2] or "solicitacao_cliente"
            tipo = g[3] or ""
            marca = g[4] or ""
            modelo = g[5] or ""
            defeito = g[13] or ""
            reversa_cli = g[16] or ""
            rast_cli = g[17] or ""
            rast_forn = g[19] or g[20] or ""
            rast_final = g[21] or ""
            cli_nome = g[26] or "Sem Cliente"
            cli_tel = g[27] or ""
            serial = g[10] or ""

            # Filtro de busca
            if termo:
                match_proto = termo in proto.lower()
                match_cli = termo in cli_nome.lower()
                match_prod = termo in f"{tipo} {marca} {modelo}".lower()
                match_ser = termo in serial.lower()
                match_rast = termo in f"{reversa_cli} {rast_cli} {rast_forn} {rast_final}".lower()
                if not (match_proto or match_cli or match_prod or match_ser or match_rast):
                    continue

            if status not in self._colunas:
                status = "solicitacao_cliente"

            contadores[status] += 1
            inner_col = self._colunas[status]["inner"]
            col_color = self._colunas[status]["color"]

            # ═══════════════════════════════════════════
            # Construção do Card Visual
            # ═══════════════════════════════════════════
            card = tk.Frame(
                inner_col,
                bg=BG3,
                padx=10,
                pady=8,
                highlightbackground="#33333D",
                highlightthickness=1,
                cursor="hand2"
            )
            card.pack(fill="x", pady=4, padx=2)
            self._card_widgets[g_id] = (card, status)

            # Header do Card: Protocolo + Badge
            c_hdr = tk.Frame(card, bg=BG3)
            c_hdr.pack(fill="x", pady=(0, 3))

            lbl_proto = tk.Label(c_hdr, text=proto, font=("Segoe UI", 9, "bold"), bg=BG3, fg=GOLD)
            lbl_proto.pack(side="left")

            # Produto (Tipo Marca Modelo)
            prod_str = f"{marca} {modelo}" if marca else (tipo or "Produto")
            lbl_prod = tk.Label(card, text=prod_str, font=("Segoe UI", 9, "bold"), bg=BG3, fg=TEXT, anchor="w", wraplength=140)
            lbl_prod.pack(fill="x", pady=(0, 2))

            # Cliente
            lbl_cli = tk.Label(card, text=f"👤 {cli_nome[:18]}", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM, anchor="w")
            lbl_cli.pack(fill="x", pady=(0, 2))

            # Defeito resumido
            if defeito:
                def_res = (defeito[:36] + "...") if len(defeito) > 36 else defeito
                lbl_def = tk.Label(card, text=f"⚠️ {def_res}", font=("Segoe UI", 8), bg=BG3, fg="#FF8C94", anchor="w", justify="left")
                lbl_def.pack(fill="x", pady=(0, 4))

            # Pílula de Rastreio / Reversa ativa
            rast_ativo = rast_final or rast_forn or rast_cli or reversa_cli
            if rast_ativo:
                f_pill = tk.Frame(card, bg=BG2, padx=4, pady=2)
                f_pill.pack(fill="x", pady=(2, 4))
                lbl_pill = tk.Label(f_pill, text=f"📦 {rast_ativo[:18]}", font=("Consolas", 8, "bold"), bg=BG2, fg=SUCCESS)
                lbl_pill.pack(side="left")

            # ═══════════════════════════════════════════
            # Ações Rápidas (Avançar / Voltar Etapa)
            # ═══════════════════════════════════════════
            c_actions = tk.Frame(card, bg=BG3)
            c_actions.pack(fill="x", pady=(4, 0))

            idx_atual = chaves_etapas.index(status)

            if idx_atual > 0:
                etapa_ant = chaves_etapas[idx_atual - 1]
                btn_prev = tk.Button(
                    c_actions,
                    text="◀",
                    font=("Segoe UI", 8, "bold"),
                    bg=BG2,
                    fg=TEXT_DIM,
                    activebackground=BG3,
                    activeforeground=TEXT,
                    relief="flat",
                    bd=0,
                    padx=6,
                    pady=1,
                    cursor="hand2",
                    command=lambda gid=g_id, nova_etapa=etapa_ant: self._mover_garantia(gid, nova_etapa)
                )
                btn_prev.pack(side="left")

            btn_detalhes = tk.Button(
                c_actions,
                text="Ver Detalhes",
                font=("Segoe UI", 8),
                bg=BG2,
                fg=TEXT,
                activebackground=BG3,
                activeforeground=GOLD,
                relief="flat",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=lambda gid=g_id: self._abrir_detalhes(gid)
            )
            btn_detalhes.pack(side="left", padx=4, expand=True, fill="x")

            if idx_atual < len(chaves_etapas) - 1:
                etapa_prox = chaves_etapas[idx_atual + 1]
                btn_next = tk.Button(
                    c_actions,
                    text="▶",
                    font=("Segoe UI", 8, "bold"),
                    bg=BG2,
                    fg="#22C55E",
                    activebackground=BG3,
                    activeforeground="#FFFFFF",
                    relief="flat",
                    bd=0,
                    padx=6,
                    pady=1,
                    cursor="hand2",
                    command=lambda gid=g_id, nova_etapa=etapa_prox: self._mover_garantia(gid, nova_etapa)
                )
                btn_next.pack(side="right")

            # Binds de Drag and Drop e Duplo Clique
            self._bind_drag_and_drop(card, g_id, status)
            card.bind("<Double-1>", lambda e, gid=g_id: self._abrir_detalhes(gid))

        # Atualiza os badges contadores de cada coluna
        for key, col in self._colunas.items():
            col["badge"].config(text=str(contadores.get(key, 0)))

    def _bind_drag_and_drop(self, widget, garantia_id, status_origem):
        """Conecta eventos de mouse para arrastar e soltar cards entre as colunas do Kanban."""
        def on_press(event):
            self._drag_data["id"] = garantia_id
            self._drag_data["origem"] = status_origem
            self._drag_data["card"] = widget
            widget.config(highlightbackground=ACCENT, highlightthickness=2)

        def on_motion(event):
            x_root = event.x_root
            # Destaque visual sutil nas colunas sob o mouse
            for key, col_box in self._col_frames.items():
                box_x = col_box.winfo_rootx()
                box_w = col_box.winfo_width()
                if box_x <= x_root <= box_x + box_w:
                    col_box.config(highlightbackground=GOLD, highlightthickness=1)
                else:
                    col_box.config(highlightbackground=BG2, highlightthickness=0)

        def on_release(event):
            x_root = event.x_root
            widget.config(highlightbackground="#33333D", highlightthickness=1)

            # Restaura bordas das colunas
            for col_box in self._col_frames.values():
                col_box.config(highlightbackground=BG2, highlightthickness=0)

            # Identifica qual coluna recebeu o drop
            nova_etapa = None
            for key, col_box in self._col_frames.items():
                box_x = col_box.winfo_rootx()
                box_w = col_box.winfo_width()
                if box_x <= x_root <= box_x + box_w:
                    nova_etapa = key
                    break

            if nova_etapa and nova_etapa != status_origem:
                self._mover_garantia(garantia_id, nova_etapa)

            self._drag_data = {"id": None, "origem": None, "card": None, "ghost": None}

        # Aplica os binds no card e em seus filhos
        for w in [widget] + widget.winfo_children():
            # Não sobrepõe ações de botões internos
            if not isinstance(w, tk.Button):
                w.bind("<Button-1>", on_press, add="+")
                w.bind("<B1-Motion>", on_motion, add="+")
                w.bind("<ButtonRelease-1>", on_release, add="+")

    def _mover_garantia(self, garantia_id, novo_status):
        """Move o chamado de garantia para uma nova etapa do workflow e persiste no Neon DB."""
        def _task_db():
            concluido = agora() if novo_status == "loja_cliente" else None
            with get_conn() as conn:
                conn.execute("""
                    UPDATE garantias SET
                        status = %s,
                        atualizado = %s,
                        concluido_em = COALESCE(%s, concluido_em)
                    WHERE id = %s
                """, (novo_status, agora(), concluido, garantia_id))
                conn.commit()
                cache.invalidate_prefix("garantias")

        def _ao_mover(_):
            self.app.toast.show(f"Garantia movida para nova etapa!", "sucesso")
            self._carregar_dados()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_mover,
            mensagem="Atualizando status da garantia...",
            show_global_loading=False
        )

    def _abrir_nova_garantia(self):
        """Abre modal para criação de novo chamado."""
        PopupNovaGarantia(self.app, callback_sucesso=self._carregar_dados)

    def _abrir_detalhes(self, garantia_id):
        """Abre modal de detalhes completos e edição da garantia."""
        PopupDetalhesGarantia(self.app, garantia_id, callback_atualizado=self._carregar_dados)
