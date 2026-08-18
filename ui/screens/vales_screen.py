"""
Tela Vales - Listagem geral de todos os vales presentes emitidos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_CODE
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from core.cache import cache
from utils.helpers import brl, agora, vencido, creditar_cliente
from ui.screens.popup_cliente import PopupLoadingOverlay


class ValesScreen(BaseScreen):
    """Tela de listagem, busca e resgate de vales presentes."""

    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._busca_var = None
        self._filtro_status = None
        self._inner = None
        self._todos_vales = []
        self._e_busca = None

    def show(self, **kwargs):
        focus_search = kwargs.get("focus_search", False)
        # Dispara o carregamento assíncrono mantendo a tela sob o esmaecimento
        self._carregar_vales(focus_search=focus_search)

    def _carregar_vales(self, focus_search=False):
        """Busca a lista completa de vales no banco em segundo plano com suporte a cache."""

        def _buscar_db():
            cached = cache.get("vales:list")
            if cached is not None:
                return cached

            with get_conn() as conn:
                rows = conn.execute("""
                    SELECT v.codigo, v.valor, v.usado, v.validade, v.criado, v.observacao, v.usado_em, c.nome
                    FROM vales v
                    LEFT JOIN clientes c ON c.id = v.cliente_id
                    ORDER BY v.criado DESC
                """).fetchall()
                cache.set("vales:list", rows, ttl=60)
                return rows

        def _ao_concluir(rows):
            self._todos_vales = rows
            self.clear()
            self._build(focus_search=focus_search)
            self._popular_lista()

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem="Carregando vales presentes..."
        )

    def _build(self, focus_search=False):
        h = UIBuilder.frame(self.content, pady=20, padx=28)
        h.pack(fill="x", side="top")
        UIBuilder.label(h, "🎟️ Vale Presentes", font=FONT_TITLE, fg=GOLD).pack(side="left")
        UIBuilder.button(h, "✨ Novo Vale", lambda: self.app.show("novo_vale"), color=GOLD, fg="#000", width=16).pack(side="right")
        UIBuilder.separator(self.content).pack(fill="x", padx=28, side="top")

        fb = UIBuilder.frame(self.content, bg=BG, padx=28, pady=12)
        fb.pack(fill="x", side="top")

        UIBuilder.label(fb, "🔍 Buscar (código ou cliente)", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")
        row_busca = UIBuilder.frame(fb, bg=BG)
        row_busca.pack(fill="x", pady=(2, 0))

        self._busca_var = tk.StringVar()
        self._e_busca = UIBuilder.entry(row_busca, var=self._busca_var, width=30)
        self._e_busca.pack(side="left", ipady=6, fill="x", expand=True)

        self._filtro_status = tk.StringVar(value="Todos")
        combo = ttk.Combobox(
            row_busca, textvariable=self._filtro_status,
            values=["Todos", "Disponível", "Resgatado", "Vencido"],
            state="readonly", font=FONT_BODY, width=14
        )
        combo.pack(side="left", padx=(10, 0))

        # Filtra instantaneamente em memória sem fazer novas requisições SQL
        self._busca_var.trace_add("write", lambda *a: self._popular_lista())
        combo.bind("<<ComboboxSelected>>", lambda e: self._popular_lista())

        sf = UIBuilder.frame(self.content, padx=28, pady=6)
        sf.pack(fill="both", expand=True, side="top")
        _, self._inner = UIBuilder.scrolled_canvas(sf)

        if focus_search and self._e_busca:
            self._e_busca.focus_set()

    @staticmethod
    def _status_vale(usado, validade):
        if usado:
            return "Resgatado"
        if vencido(validade):
            return "Vencido"
        return "Disponível"

    def _popular_lista(self):
        """Filtra e exibe os vales armazenados na memória."""
        if not self._inner:
            return

        for w in self._inner.winfo_children():
            w.destroy()

        busca = (self._busca_var.get() or "").strip().lower() if self._busca_var else ""
        filtro = self._filtro_status.get() if self._filtro_status else "Todos"

        cores = {"Disponível": SUCCESS, "Resgatado": TEXT_DIM, "Vencido": DANGER}
        encontrados = 0

        for codigo, valor, usado, validade, criado, obs, usado_em, nome_cliente in self._todos_vales:
            status = self._status_vale(usado, validade)
            if filtro != "Todos" and status != filtro:
                continue
            if busca and busca not in codigo.lower() and not (nome_cliente and busca in nome_cliente.lower()):
                continue

            encontrados += 1
            cor = cores[status]

            vf = UIBuilder.frame(self._inner, bg=BG2, pady=10, padx=14)
            vf.pack(fill="x", pady=3)

            top = UIBuilder.frame(vf, bg=BG2)
            top.pack(fill="x")
            UIBuilder.label(top, codigo, font=FONT_CODE, bg=BG2, fg=GOLD if status == "Disponível" else TEXT_DIM).pack(side="left")
            UIBuilder.label(top, brl(valor), font=("Segoe UI", 12, "bold"), bg=BG2, fg=cor).pack(side="left", padx=(10, 0))
            UIBuilder.button(top, "📋 Copiar", lambda cod=codigo: self.app._copiar_codigo_clipboard(cod), color=BG3, width=8, pady=2, padx=5).pack(side="left", padx=10)
            UIBuilder.label(top, status, font=FONT_SMALL, bg=BG2, fg=cor).pack(side="right")

            bot = UIBuilder.frame(vf, bg=BG2)
            bot.pack(fill="x")
            if nome_cliente:
                UIBuilder.label(bot, f"👤 {nome_cliente}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")
            if validade:
                UIBuilder.label(bot, f"  válido até {validade}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")
            if usado_em:
                UIBuilder.label(bot, f"  resgatado em {str(usado_em)[:10]}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")
            if obs:
                UIBuilder.label(vf, f"📝 {obs}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

            if status == "Disponível":
                UIBuilder.button(
                    vf, "🎁 Resgatar",
                    lambda cod=codigo, val=valor: PopupSelecionarClienteResgate(
                        self.app, cod, val, on_sucesso=self._carregar_vales
                    ),
                    color=GOLD, fg="#000", width=14
                ).pack(anchor="e", pady=(4, 0))

        if encontrados == 0:
            UIBuilder.label(self._inner, "Nenhum vale encontrado.", fg=TEXT_DIM).pack(pady=20)


class PopupSelecionarClienteResgate:
    """Popup para escolher o cliente que vai receber o crédito do vale."""

    def __init__(self, app, codigo, valor, on_sucesso=None):
        self.app = app
        self.codigo = codigo
        self.valor = valor
        self.on_sucesso = on_sucesso
        self._cliente_sel = None
        self._build()

    def _build(self):
        win = tk.Toplevel(self.app)
        win.title("Resgatar Vale")
        win.geometry("440x460")
        win.configure(bg=BG)
        win.grab_set()

        h = UIBuilder.frame(win, bg=BG2, padx=24, pady=16)
        h.pack(fill="x")
        UIBuilder.label(h, f"🎁 Resgatar {self.codigo}", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w")
        UIBuilder.label(h, f"Valor: {brl(self.valor)}", font=("Segoe UI", 13, "bold"), bg=BG2, fg=SUCCESS).pack(anchor="w", pady=(2, 0))
        UIBuilder.separator(win).pack(fill="x")

        body = UIBuilder.frame(win, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        UIBuilder.label(body, "Buscar cliente (nome ou CPF)", font=FONT_SMALL, fg=TEXT_DIM).pack(anchor="w")
        busca_var = tk.StringVar()
        e_busca = UIBuilder.entry(body, var=busca_var, width=32)
        e_busca.pack(fill="x", ipady=6, pady=(0, 10))
        e_busca.focus_set()

        lista_frame = UIBuilder.frame(body, bg=BG)
        lista_frame.pack(fill="both", expand=True)

        sel_var = tk.StringVar()
        UIBuilder.label(body, textvariable=sel_var, font=FONT_SMALL, fg=SUCCESS, wraplength=360, justify="left").pack(anchor="w", pady=(6, 0))

        def selecionar(cid, nome):
            self._cliente_sel = (cid, nome)
            sel_var.set(f"✓ Selecionado: {nome}")

        def buscar(*_a):
            for w in lista_frame.winfo_children():
                w.destroy()
            termo = busca_var.get().strip().lower()
            if not termo:
                return
            with get_conn() as conn:
                clientes = conn.execute(
                    "SELECT id, nome, cpf FROM clientes WHERE lower(nome) LIKE %s OR cpf LIKE %s ORDER BY nome LIMIT 15",
                    (f"%{termo}%", f"%{termo}%")
                ).fetchall()
            if not clientes:
                UIBuilder.label(lista_frame, "Nenhum cliente encontrado.", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=4)
                return
            for cid, nome, cpf in clientes:
                txt = nome + (f" (CPF: {cpf})" if cpf else "")
                UIBuilder.button(lista_frame, txt, lambda c=cid, n=nome: selecionar(c, n), color=BG3, width=40).pack(fill="x", pady=2)

        busca_var.trace_add("write", buscar)

        UIBuilder.separator(win).pack(fill="x")
        brow = UIBuilder.frame(win, padx=24, pady=16)
        brow.pack(fill="x", side="bottom")

        def confirmar():
            if not self._cliente_sel:
                messagebox.showwarning("Atenção", "Selecione um cliente antes de confirmar.", parent=win)
                return
            cid, nome = self._cliente_sel
            if not messagebox.askyesno("Confirmar", f"Resgatar vale {self.codigo} de {brl(self.valor)} para {nome}?", parent=win):
                return

            loading_resgate = PopupLoadingOverlay(win, "Resgatando vale...")

            def _tarefa_resgatar():
                with get_conn() as conn:
                    cur = conn.execute(
                        "UPDATE vales SET cliente_id=%s, usado=1, usado_em=%s WHERE codigo=%s AND usado=0 AND cliente_id IS NULL",
                        (cid, agora(), self.codigo)
                    )
                    if cur.rowcount == 0:
                        conn.rollback()
                        return False
                    creditar_cliente(cid, self.valor, "vale", f"Resgate do vale {self.codigo}", conn=conn)
                    conn.commit()
                cache.invalidate_prefix("vales")
                cache.invalidate_prefix("dashboard")
                cache.invalidate_prefix("creditos")
                cache.invalidate_prefix("clientes")
                return True

            def _ao_resgatar_concluido(sucesso):
                loading_resgate.fechar()
                win.destroy()
                if not sucesso:
                    messagebox.showerror("Erro", "Esse vale não está mais disponível para resgate.")
                    return
                self.app.toast.show(f"Vale resgatado! {brl(self.valor)} creditado para {nome}.", "sucesso")
                if self.on_sucesso:
                    self.on_sucesso()

            self.app.executar_async(
                funcao_task=_tarefa_resgatar,
                callback_sucesso=_ao_resgatar_concluido,
                mensagem=None,
                show_global_loading=False
            )

        UIBuilder.button(brow, "✅ Confirmar", confirmar, color=SUCCESS, width=16).pack(side="left")
        UIBuilder.button(brow, "Cancelar", win.destroy, color=BG3, width=12).pack(side="left", padx=8)