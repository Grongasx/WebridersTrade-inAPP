"""
Tela de Clientes - Gerenciamento de clientes.
"""

import tkinter as tk
from tkinter import messagebox
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import brl, agora, formatar_data

from ui.screens.popup_cliente import PopupClienteDetalhe, PopupClienteEditar


class ClientesScreen(BaseScreen):
    """Tela de gerenciamento de clientes."""
    
    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._busca_cli = tk.StringVar()
        self._tree_cli = None
        self._todos_clientes = []
    
    def show(self, **kwargs):
        # Dispara a busca assincrona sem limpar a tela imediatamente
        self._carregar_clientes()

    def _carregar_clientes(self):
        """Busca os clientes no banco de dados em segundo plano."""
        
        def _buscar_db():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT c.id, c.nome, c.email, c.telefone, COUNT(v.id), c.criado
                    FROM clientes c 
                    LEFT JOIN vales v ON v.cliente_id = c.id
                    GROUP BY c.id, c.nome, c.email, c.telefone, c.criado 
                    ORDER BY c.nome
                """).fetchall()

        def _ao_concluir(rows):
            self._todos_clientes = rows
            self.clear()
            self._build()
            self._popular_tree()

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem="Carregando lista de clientes..."
        )
    
    def _build(self):
        h = self.build_header("Clientes")
        UIBuilder.button(h, "➕ Novo", lambda: self.app.show("novo_cli"), width=12).pack(side="right")

        fb = UIBuilder.frame(self.content, pady=10, padx=28)
        fb.pack(fill="x")
        UIBuilder.label(fb, "🔍 Buscar:", bg=BG, fg=TEXT_DIM, font=FONT_SMALL).pack(side="left", padx=(0, 6))
        UIBuilder.entry(fb, var=self._busca_cli, width=32).pack(side="left", ipady=5)
        
        # Filtra a treeview em tempo real ao digitar sem refazer consulta ao banco
        self._busca_cli.trace_add("write", lambda *_: self._popular_tree())

        tf = UIBuilder.frame(self.content, padx=28, pady=4)
        tf.pack(fill="both", expand=True)
        cols    = ("ID", "Nome", "E-mail", "Telefone", "Vales", "Cadastrado")
        widths  = [50, 220, 220, 130, 60, 120]
        anchors = ["center", "w", "w", "w", "center", "center"]
        self._tree_cli = UIBuilder.make_tree(tf, cols, widths, anchors)
        
        self._tree_cli.bind("<Double-1>", self._detalhe)

        brow = UIBuilder.frame(self.content, padx=28, pady=8)
        brow.pack(fill="x")
        UIBuilder.button(brow, "✏️ Editar",     self._editar_sel,  color=BG3,   width=14).pack(side="left", padx=4)
        UIBuilder.button(brow, "🗑 Excluir",    self._excluir_sel, color=DANGER, width=14).pack(side="left", padx=4)

    def _popular_tree(self):
        """Preenche a Treeview com base no termo de busca digitado."""
        if not self._tree_cli:
            return

        busca = self._busca_cli.get().lower().strip()
        
        # Limpa as linhas atuais
        for item in self._tree_cli.get_children():
            self._tree_cli.delete(item)

        # Filtra e insere
        for i, r in enumerate(self._todos_clientes):
            nome = r[1] or ""
            email = r[2] or ""
            if busca and (busca not in nome.lower() and busca not in email.lower()):
                continue
            self._tree_cli.insert(
                "", 
                "end", 
                iid=str(r[0]), 
                values=(r[0], r[1], r[2] or "—", r[3] or "—", r[4], formatar_data(r[5]))
            )

    def _sel_id(self):
        sel = self._tree_cli.selection()
        if not sel:
            self.toast.show("Selecione um cliente primeiro.", "aviso")
            return None
        return int(sel[0])

    def _detalhe(self, event=None):
        if event and self._tree_cli.identify_region(event.x, event.y) != "cell":
            return
            
        cid = self._sel_id()
        if cid:
            PopupClienteDetalhe(self.app, cid)

    def _editar_sel(self):
        cid = self._sel_id()
        if cid:
            PopupClienteEditar(self.app, cid, self._carregar_clientes)

    def _excluir_sel(self):
        cid = self._sel_id()
        if not cid: 
            return
            
        with get_conn() as conn:
            nome = conn.execute("SELECT nome FROM clientes WHERE id=%s", (cid,)).fetchone()[0]
            qtd  = conn.execute("SELECT COUNT(*) FROM vales WHERE cliente_id=%s", (cid,)).fetchone()[0]
            
        msg = f"Excluir '{nome}'?"
        if qtd:
            msg += f"\n\n⚠ Este cliente possui {qtd} vale(s) que também serão excluídos!"
            
        if not messagebox.askyesno("Confirmar exclusão", msg):
            return

        def _tarefa_excluir():
            with get_conn() as conn:
                conn.execute("DELETE FROM vales WHERE cliente_id=%s", (cid,))
                conn.execute("DELETE FROM clientes WHERE id=%s", (cid,))
                conn.commit()

        def _ao_excluir_sucesso(_):
            self.toast.show(f"Cliente '{nome}' excluído.", "aviso")
            self._carregar_clientes()

        self.app.executar_async(
            funcao_task=_tarefa_excluir,
            callback_sucesso=_ao_excluir_sucesso,
            mensagem="Excluindo cliente..."
        )