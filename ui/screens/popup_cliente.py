"""
Popups relacionados a clientes.
"""

import tkinter as tk
from tkinter import messagebox
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE
from ui.components.base import UIBuilder, ScrollableFrame
from core.database import get_conn
from utils.helpers import brl, agora, vencido, creditar_cliente, formatar_data


class PopupLoadingOverlay:
    """Camada de fundo esmaecido e mensagem de carregamento restrita ao Popup."""

    def __init__(self, parent_win, mensagem="Carregando..."):
        self.parent = parent_win
        self.overlay = tk.Frame(self.parent, bg="#111622")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = UIBuilder.frame(self.overlay, bg=BG2, padx=24, pady=18)
        card.place(relx=0.5, rely=0.5, anchor="center")

        UIBuilder.label(card, "⏳", font=("Segoe UI", 20), bg=BG2, fg=GOLD).pack()
        UIBuilder.label(card, mensagem, font=FONT_BODY, bg=BG2, fg=TEXT).pack(pady=(6, 0))

    def fechar(self):
        try:
            self.overlay.destroy()
        except Exception:
            pass


class PopupClienteDetalhe:
    """Popup de detalhes do cliente."""
    
    def __init__(self, app, cid, callback_atualizar_pai=None):
        self.app = app
        self.cid = cid
        self.callback_atualizar_pai = callback_atualizar_pai
        self.win = None
        self._build_container()
        self._carregar_dados()

    def _build_container(self):
        self.win = tk.Toplevel(self.app)
        self.win.title("Detalhes do Cliente")
        self.win.geometry("680x560")
        self.win.configure(bg=BG)
        self.win.grab_set()

    def _carregar_dados(self):
        """Busca os dados e recarrega o conteúdo na MESMA janela sem recriá-la."""
        loading = PopupLoadingOverlay(self.win, "Atualizando dados...")

        def _buscar_db():
            with get_conn() as conn:
                cli = conn.execute("""
                    SELECT id, nome, email, telefone, cpf, criado, saldo 
                    FROM clientes WHERE id=%s
                """, (self.cid,)).fetchone()
                
                vales = conn.execute("""
                    SELECT codigo, valor, usado, validade, criado, observacao, usado_em 
                    FROM vales WHERE cliente_id=%s ORDER BY criado DESC
                """, (self.cid,)).fetchall()
                return cli, vales

        def _ao_concluir(resultado):
            loading.fechar()
            cli, vales = resultado
            if not cli:
                messagebox.showerror("Erro", "Cliente não encontrado.", parent=self.win)
                self.win.destroy()
                return
            self._render_conteudo(cli, vales)

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem=None
        )
    
    def _render_conteudo(self, cli, vales):
        # Limpa os elementos atuais para redesenhar na mesma janela
        for child in self.win.winfo_children():
            child.destroy()

        self.win.title(f"Cliente: {cli[1]}")

        h = UIBuilder.frame(self.win, bg=BG2, padx=24, pady=16)
        h.pack(fill="x")
        UIBuilder.label(h, f"👤 {cli[1]}", font=FONT_H2, bg=BG2).pack(anchor="w")
        UIBuilder.label(h, f"📧 {cli[2] or '—'}   📞 {cli[3] or '—'}   🪪 {cli[4] or '—'}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=2)
        
        UIBuilder.label(h, f"Cadastrado em {formatar_data(cli[5])}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.label(h, f"💰 Saldo de crédito: {brl(cli[6] or 0)}", font=("Segoe UI", 13, "bold"), bg=BG2, fg=SUCCESS).pack(anchor="w", pady=(6, 0))

        row_btns = UIBuilder.frame(h, bg=BG2)
        row_btns.pack(anchor="e")
        UIBuilder.button(row_btns, "✏️ Editar", self._editar, color=BG3, width=12).pack(side="left", padx=4)
        UIBuilder.button(row_btns, "🎁 Resgatar Vale", self._abrir_resgate_vale, color=GOLD, fg="#000", width=14).pack(side="left", padx=4)

        UIBuilder.separator(self.win).pack(fill="x")
        UIBuilder.label(self.win, f"🎟️  Vales Resgatados ({len(vales)})", font=FONT_H2, padx=24, pady=8).pack(anchor="w")

        sf = UIBuilder.frame(self.win, padx=24, pady=4)
        sf.pack(fill="both", expand=True)
        _, inner = UIBuilder.scrolled_canvas(sf)

        if vales:
            sm = UIBuilder.frame(inner, bg=BG3, padx=14, pady=8)
            sm.pack(fill="x", pady=(0, 8))
            UIBuilder.label(sm, f"{len(vales)} vale(s) já resgatado(s) por este cliente", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(side="left")

        for v in vales:
            _vencido   = vencido(v[3]) and not v[2]
            cor        = DANGER if _vencido else (TEXT_DIM if v[2] else SUCCESS)
            status_txt = "Vencido" if _vencido else ("✓ Usado" if v[2] else "● Ativo")

            vf  = UIBuilder.frame(inner, bg=BG2, pady=10, padx=14)
            vf.pack(fill="x", pady=3)

            top = UIBuilder.frame(vf, bg=BG2)
            top.pack(fill="x")
            UIBuilder.label(top, v[0], font=FONT_CODE, bg=BG2, fg=GOLD if not v[2] else TEXT_DIM).pack(side="left")
            UIBuilder.label(top, brl(v[1]), font=("Segoe UI", 12, "bold"), bg=BG2, fg=cor).pack(side="left", padx=(10, 0))
            UIBuilder.button(top, "📋 Copiar", lambda cod=v[0]: self.app._copiar_codigo_clipboard(cod), color=BG3, width=8, pady=2, padx=5).pack(side="left", padx=10)
            UIBuilder.label(top, status_txt, font=FONT_SMALL, bg=BG2, fg=cor).pack(side="right")

            bot = UIBuilder.frame(vf, bg=BG2)
            bot.pack(fill="x")
            if v[3]: UIBuilder.label(bot, f"válido até {v[3]}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")
            if v[6]: UIBuilder.label(bot, f"  usado em {formatar_data(v[6])}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")
            if v[5]: UIBuilder.label(vf,  f"📝 {v[5]}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

            if not v[2]:
                def dar_baixa(com_cod=v[0]):
                    if messagebox.askyesno("Confirmar", f"Dar baixa no vale {com_cod}?", parent=self.win):
                        loading_baixa = PopupLoadingOverlay(self.win, "Dando baixa no vale...")

                        def _tarefa_baixa():
                            with get_conn() as conn:
                                conn.execute("UPDATE vales SET usado=1, usado_em=%s WHERE codigo=%s", (agora(), com_cod))
                                conn.commit()

                        def _ao_concluir_baixa(_):
                            loading_baixa.fechar()
                            self._carregar_dados() # Recarrega inline sem recriar janela

                        self.app.executar_async(
                            funcao_task=_tarefa_baixa,
                            callback_sucesso=_ao_concluir_baixa,
                            mensagem=None
                        )

                UIBuilder.button(vf, "✅ Dar Baixa", dar_baixa, color=BG3, width=14).pack(anchor="e", pady=(4, 0))

            self._bind_dblclick(vf, lambda e, vale=v: self._abrir_detalhe_vale(vale))

        if not vales:
            UIBuilder.label(inner, "Nenhum vale cadastrado.", fg=TEXT_DIM).pack(pady=20)

    def _bind_dblclick(self, widget, handler):
        widget.bind("<Double-1>", handler)
        for child in widget.winfo_children():
            self._bind_dblclick(child, handler)

    def _abrir_detalhe_vale(self, v):
        win2 = tk.Toplevel(self.app)
        win2.title(f"Vale {v[0]}")
        win2.geometry("420x420")
        win2.configure(bg=BG)
        win2.grab_set()

        _vencido   = vencido(v[3]) and not v[2]
        cor        = DANGER if _vencido else (TEXT_DIM if v[2] else SUCCESS)
        status_txt = "Vencido" if _vencido else ("✓ Usado" if v[2] else "● Ativo")

        h = UIBuilder.frame(win2, bg=BG2, padx=24, pady=16)
        h.pack(fill="x")
        UIBuilder.label(h, f"🎟️ {v[0]}", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w")
        UIBuilder.label(h, status_txt, font=FONT_SMALL, bg=BG2, fg=cor).pack(anchor="w", pady=(2, 0))
        UIBuilder.separator(win2).pack(fill="x")

        body = UIBuilder.frame(win2, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        UIBuilder.label(body, f"Valor: {brl(v[1])}", font=("Segoe UI", 15, "bold"), fg=cor).pack(anchor="w", pady=5)
        if v[3]: UIBuilder.label(body, f"Válido até: {v[3]}", font=FONT_BODY, fg=TEXT_DIM).pack(anchor="w", pady=5)
        UIBuilder.label(body, f"Criado em: {formatar_data(v[4])}", font=FONT_BODY, fg=TEXT_DIM).pack(anchor="w", pady=5)
        if v[6]: UIBuilder.label(body, f"Usado em: {formatar_data(v[6])}", font=FONT_BODY, fg=TEXT_DIM).pack(anchor="w", pady=5)
        if v[5]: UIBuilder.label(body, f"Observação: {v[5]}", font=FONT_BODY, fg=TEXT_DIM, wraplength=350, justify="left").pack(anchor="w", pady=5)

        UIBuilder.separator(win2).pack(fill="x")
        brow = UIBuilder.frame(win2, padx=24, pady=16)
        brow.pack(fill="x", side="bottom")
        UIBuilder.button(brow, "📋 Copiar Código", lambda: self.app._copiar_codigo_clipboard(v[0]), color=BG3, width=16).pack(side="left")

        if not v[2]:
            def dar_baixa():
                if messagebox.askyesno("Confirmar", f"Dar baixa no vale {v[0]}?", parent=win2):
                    loading_baixa = PopupLoadingOverlay(win2, "Dando baixa...")

                    def _tarefa_baixa():
                        with get_conn() as conn:
                            conn.execute("UPDATE vales SET usado=1, usado_em=%s WHERE codigo=%s", (agora(), v[0]))
                            conn.commit()

                    def _ao_concluir_baixa(_):
                        loading_baixa.fechar()
                        win2.destroy()
                        self._carregar_dados() # Atualiza janela pai inline

                    self.app.executar_async(
                        funcao_task=_tarefa_baixa,
                        callback_sucesso=_ao_concluir_baixa,
                        mensagem=None
                    )

            UIBuilder.button(brow, "✅ Dar Baixa", dar_baixa, color=SUCCESS, width=14).pack(side="left", padx=8)

        UIBuilder.button(brow, "Fechar", win2.destroy, color=BG3, width=10).pack(side="right")

    def _editar(self):
        PopupClienteEditar(self.app, self.cid, callback=self._carregar_dados)

    def _abrir_resgate_vale(self):
        with get_conn() as conn:
            nome = conn.execute("SELECT nome FROM clientes WHERE id=%s", (self.cid,)).fetchone()
            nome_cli = nome[0] if nome else ""
        PopupResgatarVale(self.app, self.cid, nome_cli, callback=self._carregar_dados)


class PopupClienteEditar:
    """Popup de edição de cliente."""
    
    def __init__(self, app, cid, callback=None):
        self.app = app
        self.cid = cid
        self.callback = callback
        self.win = None
        self._build()
    
    def _build(self):
        self.win = tk.Toplevel(self.app)
        self.win.title("Editar Cliente")
        self.win.geometry("500x480")
        self.win.configure(bg=BG)
        self.win.grab_set()

        loading = PopupLoadingOverlay(self.win, "Buscando dados...")

        def _buscar_db():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT id, nome, email, telefone, cpf 
                    FROM clientes WHERE id=%s
                """, (self.cid,)).fetchone()

        def _ao_concluir(cli):
            loading.fechar()
            if not cli:
                messagebox.showerror("Erro", "Cliente não encontrado.", parent=self.win)
                self.win.destroy()
                return
            self._render_form(cli)

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem=None
        )

    def _render_form(self, cli):
        h = UIBuilder.frame(self.win, bg=BG2, padx=28, pady=16)
        h.pack(fill="x")
        UIBuilder.label(h, "✏️ Editar Cliente", font=FONT_H2, bg=BG2).pack(anchor="w")
        UIBuilder.separator(self.win).pack(fill="x")

        fm = UIBuilder.frame(self.win, bg=BG2, padx=36)
        fm.pack(fill="both", expand=True, pady=12)
        vs = {k: tk.StringVar(value=v or "") for k, v in zip(["nome","email","tel","cpf"], [cli[1],cli[2],cli[3],cli[4]])}

        UIBuilder.field(fm, "Nome completo *", vs["nome"], bg=BG2)
        UIBuilder.field(fm, "E-mail",          vs["email"], bg=BG2)
        UIBuilder.field(fm, "Telefone",        vs["tel"],   bg=BG2)
        UIBuilder.field(fm, "CPF",             vs["cpf"],   bg=BG2)

        msg_v = tk.StringVar()
        UIBuilder.label(fm, textvariable=msg_v, font=FONT_SMALL, bg=BG2, fg=DANGER).pack(pady=(6, 0), anchor="w")

        UIBuilder.separator(self.win).pack(fill="x")
        brow = UIBuilder.frame(self.win, bg=BG2, padx=36, pady=16)
        brow.pack(fill="x", side="bottom")

        def salvar():
            nome  = vs["nome"].get().strip()
            email = vs["email"].get().strip() or None
            tel   = vs["tel"].get().strip() or None
            cpf   = vs["cpf"].get().strip() or None
            if not nome:
                msg_v.set("⚠ Nome é obrigatório.")
                return

            loading_salvar = PopupLoadingOverlay(self.win, "Salvando cliente...")

            def _tarefa_salvar():
                with get_conn() as conn:
                    conn.execute("UPDATE clientes SET nome=%s,email=%s,telefone=%s,cpf=%s WHERE id=%s", (nome, email, tel, cpf, self.cid))
                    conn.commit()

            def _ao_concluir_salvar(_):
                loading_salvar.fechar()
                self.app.toast.show(f"Cliente '{nome}' atualizado!", "sucesso")
                self.win.destroy()
                if self.callback: 
                    self.callback()

            def _ao_erro(e):
                loading_salvar.fechar()
                msg_v.set(f"⚠ {'E-mail' if 'email' in str(e) else 'CPF'} já cadastrado.")

            self.app.executar_async(
                funcao_task=_tarefa_salvar,
                callback_sucesso=_ao_concluir_salvar,
                callback_erro=_ao_erro,
                mensagem=None
            )

        self.win.bind("<Return>", lambda _: salvar())
        UIBuilder.button(brow, "✅ Salvar", salvar, width=14).pack(side="left")
        UIBuilder.button(brow, "Cancelar", self.win.destroy, color=BG3, width=12).pack(side="left", padx=8)


class PopupResgatarVale:
    """Popup para resgatar um vale presente."""

    def __init__(self, app, cid, nome_cliente, callback=None):
        self.app = app
        self.cid = cid
        self.nome_cliente = nome_cliente
        self.callback = callback
        self._vale_encontrado = None
        self.win = None
        self._build()

    def _build(self):
        self.win = tk.Toplevel(self.app)
        self.win.title("Resgatar Vale Presente")
        self.win.geometry("440x420")
        self.win.configure(bg=BG)
        self.win.grab_set()

        h = UIBuilder.frame(self.win, bg=BG2, padx=24, pady=16)
        h.pack(fill="x")
        UIBuilder.label(h, "🎁 Resgatar Vale Presente", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w")
        UIBuilder.label(h, f"Crédito será associado a: {self.nome_cliente}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(2, 0))
        UIBuilder.separator(self.win).pack(fill="x")

        body = UIBuilder.frame(self.win, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        UIBuilder.label(body, "Código do Vale", font=FONT_SMALL, fg=TEXT_DIM).pack(anchor="w")
        cod_var = tk.StringVar()
        e_cod = UIBuilder.entry(body, var=cod_var, width=28)
        e_cod.pack(fill="x", ipady=7, pady=(0, 10))
        e_cod.focus_set()

        resultado_frame = UIBuilder.frame(body, bg=BG)
        resultado_frame.pack(fill="x", pady=6)

        msg_v = tk.StringVar()
        UIBuilder.label(body, textvariable=msg_v, font=FONT_SMALL, fg=DANGER, wraplength=360, justify="left").pack(anchor="w")

        def buscar(_e=None):
            for w in resultado_frame.winfo_children():
                w.destroy()
            self._vale_encontrado = None
            msg_v.set("")
            codigo = cod_var.get().strip().upper()
            if not codigo:
                msg_v.set("⚠ Informe um código.")
                return

            loading_busca = PopupLoadingOverlay(self.win, "Buscando vale...")

            def _tarefa_buscar():
                with get_conn() as conn:
                    return conn.execute(
                        "SELECT codigo, valor, usado, validade, cliente_id FROM vales WHERE codigo=%s",
                        (codigo,)
                    ).fetchone()

            def _ao_concluir_busca(v):
                loading_busca.fechar()
                if not v:
                    msg_v.set("⚠ Vale não encontrado.")
                    return
                if v[2]:
                    msg_v.set("⚠ Este vale já foi usado.")
                    return
                if vencido(v[3]):
                    msg_v.set("⚠ Este vale está vencido.")
                    return
                if v[4] is not None:
                    msg_v.set("⚠ Este vale já está associado a outro cliente.")
                    return

                self._vale_encontrado = v
                card = UIBuilder.frame(resultado_frame, bg=BG3, padx=14, pady=10)
                card.pack(fill="x")
                UIBuilder.label(card, f"🎟️ {v[0]}", font=FONT_CODE, bg=BG3, fg=GOLD).pack(anchor="w")
                UIBuilder.label(card, f"Valor: {brl(v[1])}", font=("Segoe UI", 13, "bold"), bg=BG3, fg=SUCCESS).pack(anchor="w", pady=(4, 0))
                if v[3]:
                    UIBuilder.label(card, f"Válido até {v[3]}", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")

            self.app.executar_async(
                funcao_task=_tarefa_buscar,
                callback_sucesso=_ao_concluir_busca,
                mensagem=None
            )

        UIBuilder.button(body, "🔍 Buscar", buscar, color=BG3, width=14).pack(anchor="w")
        e_cod.bind("<Return>", buscar)

        UIBuilder.separator(self.win).pack(fill="x")
        brow = UIBuilder.frame(self.win, padx=24, pady=16)
        brow.pack(fill="x", side="bottom")

        def confirmar():
            v = self._vale_encontrado
            if not v:
                msg_v.set("⚠ Busque um vale válido antes de resgatar.")
                return
            codigo, valor = v[0], v[1]
            if not messagebox.askyesno("Confirmar", f"Resgatar vale {codigo} de {brl(valor)} para {self.nome_cliente}?", parent=self.win):
                return

            loading_resgate = PopupLoadingOverlay(self.win, "Resgatando vale...")

            def _tarefa_resgatar():
                with get_conn() as conn:
                    cur = conn.execute(
                        "UPDATE vales SET cliente_id=%s, usado=1, usado_em=%s WHERE codigo=%s AND usado=0 AND cliente_id IS NULL",
                        (self.cid, agora(), codigo)
                    )
                    if cur.rowcount == 0:
                        conn.rollback()
                        return False
                    creditar_cliente(self.cid, valor, "vale", f"Resgate do vale {codigo}", conn=conn)
                    conn.commit()
                    return True

            def _ao_concluir_resgate(sucesso):
                loading_resgate.fechar()
                if not sucesso:
                    self.app.toast.show("⚠ Esse vale não está mais disponível para resgate.", "erro")
                    self.win.destroy()
                    return
                self.app.toast.show(f"Vale resgatado! {brl(valor)} creditado para {self.nome_cliente}.", "sucesso")
                self.win.destroy()
                if self.callback:
                    self.callback()

            self.app.executar_async(
                funcao_task=_tarefa_resgatar,
                callback_sucesso=_ao_concluir_resgate,
                mensagem=None
            )

        UIBuilder.button(brow, "✅ Confirmar Resgate", confirmar, color=SUCCESS, width=18).pack(side="left")
        UIBuilder.button(brow, "Cancelar", self.win.destroy, color=BG3, width=12).pack(side="left", padx=8)