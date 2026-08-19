"""
Tela de Controle de Garantias & RMA - Workflow Kanban com Drag-and-Drop, Card Fantasma e Cache de Alta Performance.
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
    """Tela Kanban de Gestão de Garantias com Drag-and-Drop e Card Fantasma."""

    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._garantias = []
        self._colunas = {}
        self._col_frames = {}
        self._card_widgets = {}
        self._drag_data = {
            "id": None,
            "origem": None,
            "card": None,
            "ghost": None,
            "is_dragging": False,
            "start_x": 0,
            "start_y": 0,
            "item_data": None
        }
        self.v_busca = tk.StringVar()

    def show(self, **kwargs):
        # Utiliza cache para renderizacao instantanea sem travamentos
        cached_data = cache.get("garantias:list")
        if cached_data is not None:
            self._garantias = cached_data
            self.clear()
            self._build()
            self._renderizar_kanban()
            # Atualiza silenciosamente em background se necessario
            self._sincronizar_background(silent=True)
        else:
            self._carregar_dados()

    def _carregar_dados(self):
        """Busca do banco de dados com feedback visual caso o cache esteja vazio."""
        def _task_db():
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
                cache.set("garantias:list", rows, ttl=60)
                return rows

        def _ao_carregar(rows):
            self._garantias = rows or []
            self.clear()
            self._build()
            self._renderizar_kanban()

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_carregar,
            mensagem="Carregando quadro de garantias..."
        )

    def _sincronizar_background(self, silent=True):
        """Atualizacao assincrona silenciosa em background."""
        def _task():
            with get_conn() as conn:
                return conn.execute("""
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

        def _callback(rows):
            if rows != self._garantias:
                self._garantias = rows or []
                cache.set("garantias:list", self._garantias, ttl=60)
                self._renderizar_kanban()

        self.app.executar_async(
            funcao_task=_task,
            callback_sucesso=_callback,
            show_global_loading=False
        )

    def _build(self):
        # Header com Busca e Botão
        h = self.build_header("🛡️  Controle de Garantias & RMA (Workflow)", fg=GOLD)

        # Barra Superior
        f_top = UIBuilder.frame(self.content, padx=20, pady=6)
        f_top.pack(fill="x")

        # Campo de Busca
        f_search = UIBuilder.frame(f_top, bg=BG)
        f_search.pack(side="left", fill="x", expand=True)

        UIBuilder.label(f_search, "🔍", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="left", padx=(0, 4))
        e_busca = UIBuilder.entry(f_search, var=self.v_busca, width=32)
        e_busca.pack(side="left", ipady=3)
        self.v_busca.trace_add("write", lambda *_: self._renderizar_kanban())

        UIBuilder.label(
            f_top,
            "💡 Dica: Arraste o card para mover entre colunas • Clique para ver detalhes.",
            font=FONT_SMALL,
            bg=BG,
            fg=TEXT_DIM
        ).pack(side="left", padx=16)

        UIBuilder.button(
            f_top,
            "➕ Nova Solicitação",
            self._abrir_nova_garantia,
            color="#22C55E",
            width=20
        ).pack(side="right")

        # ═══════════════════════════════════════════
        # Container Kanban com 6 Colunas
        # ═══════════════════════════════════════════
        self.kanban_container = UIBuilder.frame(self.content, padx=12, pady=6)
        self.kanban_container.pack(fill="both", expand=True)

        for i, (key, label, color) in enumerate(ETAPAS_GARANTIA):
            self.kanban_container.columnconfigure(i, weight=1, uniform="kanban_col")

            # Coluna externa
            col_box = UIBuilder.card(self.kanban_container, bg=BG2, px=6, py=6)
            col_box.grid(row=0, column=i, sticky="nsew", padx=3, pady=2)
            self._col_frames[key] = col_box

            # Header da Coluna
            col_hdr = UIBuilder.frame(col_box, bg=BG2)
            col_hdr.pack(fill="x", pady=(0, 4))

            t_box = UIBuilder.frame(col_hdr, bg=BG2)
            t_box.pack(side="left", fill="x", expand=True)

            dot = tk.Label(t_box, text="■", font=("Segoe UI", 9), bg=BG2, fg=color)
            dot.pack(side="left", padx=(0, 3))

            lbl_t = tk.Label(t_box, text=label, font=("Segoe UI", 8, "bold"), bg=BG2, fg=TEXT, wraplength=120, justify="left", anchor="w")
            lbl_t.pack(side="left")

            badge_cnt = tk.Label(col_hdr, text="0", font=("Segoe UI", 8, "bold"), bg=BG3, fg=color, padx=5, pady=1)
            badge_cnt.pack(side="right", anchor="ne")

            UIBuilder.separator(col_box, bg=BG3).pack(fill="x", pady=(3, 4))

            # Canvas com Scroll Suave Integrado no Tema Escuro
            scroll_area = UIBuilder.frame(col_box, bg=BG2)
            scroll_area.pack(fill="both", expand=True)

            canvas = tk.Canvas(scroll_area, bg=BG2, highlightthickness=0)
            vsb = tk.Scrollbar(scroll_area, orient="vertical", command=canvas.yview, width=8, bg=BG2, troughcolor=BG2, relief="flat", bd=0)
            canvas.configure(yscrollcommand=vsb.set)

            canvas.pack(side="left", fill="both", expand=True)

            inner_col = UIBuilder.frame(canvas, bg=BG2)
            cw = canvas.create_window((0, 0), window=inner_col, anchor="nw")

            # Redimensionamento e ajuste de scrollbar responsivo
            def _ajustar_coluna(e, c=canvas, sc_inner=inner_col, sb=vsb, win_id=cw):
                if not c.winfo_exists(): return
                c.itemconfig(win_id, width=e.width)
                c.update_idletasks()
                c.configure(scrollregion=c.bbox("all"))
                # Mostra scrollbar apenas se o conteudo ultrapassar a altura visivel
                req_h = sc_inner.winfo_reqheight()
                if req_h > c.winfo_height():
                    sb.pack(side="right", fill="y")
                else:
                    sb.pack_forget()

            canvas.bind("<Configure>", _ajustar_coluna)
            inner_col.bind("<Configure>", lambda e, c=canvas, sc=inner_col, sb=vsb: (
                c.configure(scrollregion=c.bbox("all")),
                sb.pack(side="right", fill="y") if sc.winfo_reqheight() > c.winfo_height() else sb.pack_forget()
            ))

            self._colunas[key] = {
                "inner": inner_col,
                "badge": badge_cnt,
                "canvas": canvas,
                "color": color,
                "box": col_box,
                "vsb": vsb
            }

        self.kanban_container.rowconfigure(0, weight=1)

    def _renderizar_kanban(self):
        """Preenche e organiza os cards filtrados nas colunas."""
        termo = self.v_busca.get().strip().lower()

        # Limpa cards existentes
        for key, col in self._colunas.items():
            for child in col["inner"].winfo_children():
                child.destroy()

        contadores = {k: 0 for k, _, _ in ETAPAS_GARANTIA}
        self._card_widgets.clear()

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
            col_canvas = self._colunas[status]["canvas"]
            col_color = self._colunas[status]["color"]

            # Card Container
            card = tk.Frame(
                inner_col,
                bg=BG3,
                padx=9,
                pady=7,
                highlightbackground="#2A2A34",
                highlightthickness=1,
                cursor="hand2"
            )
            card.pack(fill="x", pady=3, padx=1)
            self._card_widgets[g_id] = (card, status)

            # Header: Protocolo com destaque dourado
            c_hdr = tk.Frame(card, bg=BG3)
            c_hdr.pack(fill="x", pady=(0, 2))

            lbl_proto = tk.Label(c_hdr, text=proto, font=("Segoe UI", 9, "bold"), bg=BG3, fg=GOLD)
            lbl_proto.pack(side="left")

            # Produto
            prod_str = f"{marca} {modelo}" if marca else (tipo or "Produto")
            lbl_prod = tk.Label(card, text=prod_str, font=("Segoe UI", 9, "bold"), bg=BG3, fg=TEXT, anchor="w", wraplength=135)
            lbl_prod.pack(fill="x", pady=(0, 2))

            # Cliente
            lbl_cli = tk.Label(card, text=f"👤 {cli_nome[:18]}", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM, anchor="w")
            lbl_cli.pack(fill="x", pady=(0, 2))

            # Defeito resumido
            if defeito:
                def_res = (defeito[:38] + "...") if len(defeito) > 38 else defeito
                lbl_def = tk.Label(card, text=f"⚠️ {def_res}", font=("Segoe UI", 8), bg=BG3, fg="#FF8C94", anchor="w", justify="left")
                lbl_def.pack(fill="x", pady=(0, 3))

            # Pílula de Rastreio / Reversa
            rast_ativo = rast_final or rast_forn or rast_cli or reversa_cli
            if rast_ativo:
                f_pill = tk.Frame(card, bg=BG2, padx=4, pady=2)
                f_pill.pack(fill="x", pady=(2, 2))
                lbl_pill = tk.Label(f_pill, text=f"📦 {rast_ativo[:18]}", font=("Consolas", 8, "bold"), bg=BG2, fg=SUCCESS)
                lbl_pill.pack(side="left")

            # Hover visual no Card
            def on_enter(e, c=card):
                if not self._drag_data["is_dragging"]:
                    c.config(bg="#262630", highlightbackground=GOLD, highlightthickness=1)
                    for child in c.winfo_children():
                        if child.cget("bg") == BG3:
                            child.config(bg="#262630")
                            for sub in child.winfo_children():
                                if sub.cget("bg") == BG3: sub.config(bg="#262630")

            def on_leave(e, c=card):
                if not self._drag_data["is_dragging"]:
                    c.config(bg=BG3, highlightbackground="#2A2A34", highlightthickness=1)
                    for child in c.winfo_children():
                        if child.cget("bg") == "#262630":
                            child.config(bg=BG3)
                            for sub in child.winfo_children():
                                if sub.cget("bg") == "#262630": sub.config(bg=BG3)

            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            # Binds de Drag and Drop com Card Fantasma e Suporte a MouseWheel
            self._conectar_drag_drop_e_scroll(card, g_id, status, g, col_canvas)

        # Atualiza contadores
        for key, col in self._colunas.items():
            col["badge"].config(text=str(contadores.get(key, 0)))

    def _conectar_drag_drop_e_scroll(self, widget, garantia_id, status_origem, item_data, col_canvas):
        """Conecta eventos de clique, drag-and-drop com card fantasma e scroll suave."""
        
        def on_press(event):
            self._drag_data = {
                "id": garantia_id,
                "origem": status_origem,
                "card": widget,
                "ghost": None,
                "is_dragging": False,
                "start_x": event.x_root,
                "start_y": event.y_root,
                "item_data": item_data
            }

        def on_motion(event):
            dx = abs(event.x_root - self._drag_data["start_x"])
            dy = abs(event.y_root - self._drag_data["start_y"])

            # Se moveu mais de 6 pixels, ativa o modo de arrastar
            if not self._drag_data["is_dragging"] and (dx > 6 or dy > 6):
                self._drag_data["is_dragging"] = True
                self._criar_card_fantasma(event.x_root, event.y_root, item_data)
                widget.config(bg="#15151A", highlightbackground="#202028")

            if self._drag_data["is_dragging"] and self._drag_data["ghost"]:
                # Move a janela fantasma junto com o cursor
                self._drag_data["ghost"].geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

                # Realce visual na coluna candidata
                for key, col_box in self._col_frames.items():
                    box_x = col_box.winfo_rootx()
                    box_w = col_box.winfo_width()
                    if box_x <= event.x_root <= box_x + box_w:
                        col_box.config(highlightbackground="#FF1E27", highlightthickness=2)
                    else:
                        col_box.config(highlightbackground=BG2, highlightthickness=0)

        def on_release(event):
            was_dragging = self._drag_data["is_dragging"]
            ghost = self._drag_data["ghost"]

            # Destroi a janela fantasma
            if ghost:
                try:
                    ghost.destroy()
                except Exception:
                    pass
                self._drag_data["ghost"] = None

            # Restaura bordas das colunas
            for col_box in self._col_frames.values():
                col_box.config(highlightbackground=BG2, highlightthickness=0)

            widget.config(bg=BG3, highlightbackground="#2A2A34")

            if was_dragging:
                # Localiza a coluna onde foi solto
                nova_etapa = None
                for key, col_box in self._col_frames.items():
                    box_x = col_box.winfo_rootx()
                    box_w = col_box.winfo_width()
                    if box_x <= event.x_root <= box_x + box_w:
                        nova_etapa = key
                        break

                if nova_etapa and nova_etapa != status_origem:
                    self._mover_garantia(garantia_id, nova_etapa)
            else:
                # Foi um clique simples -> Abre os detalhes da garantia
                self._abrir_detalhes(garantia_id)

            self._drag_data = {
                "id": None, "origem": None, "card": None, "ghost": None,
                "is_dragging": False, "start_x": 0, "start_y": 0, "item_data": None
            }

        # Scroll com MouseWheel no canvas da coluna
        def on_mouse_wheel(event):
            if col_canvas.winfo_exists():
                col_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Aplica os eventos no card e em todos os seus elementos filhos
        todos_elementos = [widget] + widget.winfo_children()
        for elem in todos_elementos:
            elem.bind("<Button-1>", on_press, add="+")
            elem.bind("<B1-Motion>", on_motion, add="+")
            elem.bind("<ButtonRelease-1>", on_release, add="+")
            elem.bind("<MouseWheel>", on_mouse_wheel, add="+")

    def _criar_card_fantasma(self, x, y, item):
        """Cria uma janela flutuante semi-transparente estilo 'Card Fantasma' sob o cursor."""
        ghost = tk.Toplevel(self.app)
        ghost.overrideredirect(True)
        ghost.attributes("-topmost", True)
        try:
            ghost.attributes("-alpha", 0.88)
        except Exception:
            pass

        # Estilo do Card Fantasma
        g_box = tk.Frame(ghost, bg=BG2, padx=10, pady=8, highlightbackground="#FF1E27", highlightthickness=2)
        g_box.pack(fill="both", expand=True)

        proto = item[1] or ""
        marca = item[4] or ""
        modelo = item[5] or ""
        cli_nome = item[26] or "Sem Cliente"

        tk.Label(g_box, text=f"🛡️ {proto}", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD).pack(anchor="w")
        tk.Label(g_box, text=f"{marca} {modelo}", font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT).pack(anchor="w")
        tk.Label(g_box, text=f"👤 {cli_nome[:18]}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

        ghost.geometry(f"+{x + 12}+{y + 12}")
        self._drag_data["ghost"] = ghost

    def _mover_garantia(self, garantia_id, novo_status):
        """Atualização otimista imediata em memória + persistência assíncrona no Neon DB."""
        # Atualização Otimista Instantânea (0ms de resposta visual)
        nova_lista = []
        for row in self._garantias:
            if row[0] == garantia_id:
                row_list = list(row)
                row_list[2] = novo_status
                row_list[24] = agora()
                if novo_status == "loja_cliente":
                    row_list[25] = agora()
                nova_lista.append(tuple(row_list))
            else:
                nova_lista.append(row)

        self._garantias = nova_lista
        cache.set("garantias:list", self._garantias, ttl=60)
        self._renderizar_kanban()

        # Persistência assíncrona no PostgreSQL
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

        def _ao_persistir(_):
            self.app.toast.show("Garantia movida com sucesso!", "sucesso")

        self.app.executar_async(
            funcao_task=_task_db,
            callback_sucesso=_ao_persistir,
            show_global_loading=False
        )

    def _abrir_nova_garantia(self):
        """Abre modal para criação de novo chamado."""
        PopupNovaGarantia(self.app, callback_sucesso=self._recarregar_completo)

    def _abrir_detalhes(self, garantia_id):
        """Abre modal de detalhes completos e edição da garantia ao clicar."""
        PopupDetalhesGarantia(self.app, garantia_id, callback_atualizado=self._recarregar_completo)

    def _recarregar_completo(self):
        """Invalida cache e recarrega dados do banco."""
        cache.invalidate_prefix("garantias")
        self._carregar_dados()
