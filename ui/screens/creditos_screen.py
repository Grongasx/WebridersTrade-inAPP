"""
Tela de Créditos - Gestão de crédito de clientes.
"""

import tkinter as tk
from tkinter import messagebox
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import brl, agora
from utils.formatters import CurrencyFormatter


class CreditosScreen(BaseScreen):
    """Tela de gestão de crédito de clientes."""
    
    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._busca_cred = tk.StringVar()
        self._tree_cred = None
        self._todos_clientes = []
    
    def show(self, **kwargs):
        # Dispara o carregamento assíncrono sem limpar a tela imediatamente
        self._carregar_creditos()

    def _carregar_creditos(self):
        """Busca os saldos de clientes no banco de dados em segundo plano."""
        
        def _buscar_db():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT id, nome, cpf, COALESCE(saldo, 0) 
                    FROM clientes 
                    ORDER BY nome
                """).fetchall()

        def _ao_concluir(rows):
            self._todos_clientes = rows
            self.clear()
            self._build()
            self._popular_tree()

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem="Carregando saldos de crédito..."
        )
    
    def _build(self):
        h = self.build_header("💳 Gestão de Crédito", fg=SUCCESS)
        
        fb = UIBuilder.frame(self.content, pady=10, padx=28)
        fb.pack(fill="x")
        UIBuilder.label(fb, "🔍 Buscar Cliente:", bg=BG, fg=TEXT_DIM, font=FONT_SMALL).pack(side="left", padx=(0, 6))
        UIBuilder.entry(fb, var=self._busca_cred, width=32).pack(side="left", ipady=5)
        
        # Filtra a treeview em tempo real em memória sem fazer nova requisição SQL
        self._busca_cred.trace_add("write", lambda *_: self._popular_tree())

        brow = UIBuilder.frame(self.content, padx=28, pady=8)
        brow.pack(side="bottom", fill="x")
        UIBuilder.button(brow, "➕ Lançar Crédito/Débito", self._lancar, color=SUCCESS, width=22).pack(side="left", padx=4)
        UIBuilder.button(brow, "📜 Ver Histórico", self._historico, color=BG3, width=14).pack(side="left", padx=4)
        UIBuilder.button(brow, "📦 Produtos Vinculados", self._produtos, color=GOLD, fg="#000", width=20).pack(side="left", padx=4)

        tf = UIBuilder.frame(self.content, padx=28, pady=4)
        tf.pack(fill="both", expand=True)
        cols = ("ID", "Nome do Cliente", "CPF", "Saldo em Crédito")
        widths = [50, 300, 150, 150]
        anchors = ["center", "w", "center", "center"]
        self._tree_cred = UIBuilder.make_tree(tf, cols, widths, anchors)
        self._tree_cred.tag_configure("com_saldo", foreground=SUCCESS)

    def _popular_tree(self):
        """Preenche a Treeview com base no termo digitado na busca."""
        if not self._tree_cred:
            return

        busca = self._busca_cred.get().lower().strip()
        
        # Limpa itens atuais
        for item in self._tree_cred.get_children():
            self._tree_cred.delete(item)

        # Filtra e insere
        for r in self._todos_clientes:
            # r = (id, nome, cpf, saldo)
            nome = r[1] or ""
            cpf = r[2] or ""
            if busca and (busca not in nome.lower() and busca not in cpf.lower()):
                continue
            
            saldo_val = float(r[3])
            tag = ("com_saldo",) if saldo_val > 0 else ()
            
            self._tree_cred.insert(
                "", 
                "end", 
                iid=str(r[0]), 
                values=(r[0], r[1], r[2] or "—", brl(saldo_val)), 
                tags=tag
            )

    def _sel_id(self):
        sel = self._tree_cred.selection()
        if not sel: 
            self.toast.show("Selecione um cliente.", "aviso")
            return None
        return int(self._tree_cred.item(sel[0], "values")[0])

    def _lancar(self):
        cid = self._sel_id()
        if cid:
            from ui.screens.popup_credito import PopupLancarCredito
            PopupLancarCredito(self.app, cid, self._carregar_creditos)

    def _historico(self):
        cid = self._sel_id()
        if cid:
            from ui.screens.popup_credito import PopupHistoricoCredito
            PopupHistoricoCredito(self.app, cid)

    def _produtos(self):
        cid = self._sel_id()
        if cid:
            from ui.screens.popup_credito import PopupProdutosCliente
            PopupProdutosCliente(self.app, cid)