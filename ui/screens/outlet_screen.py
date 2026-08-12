"""
Tela Outlet - Gerenciamento de produtos outlet.
"""

import tkinter as tk
from tkinter import messagebox
import time
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import brl, agora, txt_para_float
from utils.formatters import CurrencyFormatter


class OutletScreen(BaseScreen):
    """Tela de produtos outlet."""
    
    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._busca_out = tk.StringVar()
        self._tree_out = None
        self._todos_produtos = []
    
    def show(self, **kwargs):
        # Dispara o carregamento assíncrono sem limpar a tela imediatamente
        self._carregar_outlet()

    def _carregar_outlet(self):
        """Busca a lista de produtos outlet no banco em segundo plano."""

        def _buscar_db():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT p.id, p.codigo_barras, p.nome, p.tamanho, c.nome, p.preco_outlet, p.estoque, p.status, c.id AS cliente_id
                    FROM produtos_outlet p 
                    JOIN clientes c ON p.cliente_id = c.id 
                    ORDER BY p.id DESC
                """).fetchall()

        def _ao_concluir(rows):
            self._todos_produtos = rows
            self.clear()
            self._build()
            self._popular_tree()

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem="Carregando produtos outlet..."
        )
    
    def _build(self):
        h = self.build_header("🏷️ Outlet — Produtos", fg=GOLD)
        
        fb = UIBuilder.frame(self.content, pady=10, padx=28)
        fb.pack(fill="x")
        UIBuilder.label(fb, "🔍 Buscar:", bg=BG, fg=TEXT_DIM, font=FONT_SMALL).pack(side="left", padx=(0, 6))
        UIBuilder.entry(fb, var=self._busca_out, width=35).pack(side="left", ipady=5)
        
        # Filtra a treeview em memória sem nova requisição SQL
        self._busca_out.trace_add("write", lambda *_: self._popular_tree())

        brow = UIBuilder.frame(self.content, padx=28, pady=8)
        brow.pack(side="bottom", fill="x")
        UIBuilder.button(brow, "➕ Dar Entrada", self._entrada, color=GOLD, fg="#000", width=18).pack(side="left", padx=4)
        UIBuilder.button(brow, "✅ Dar Baixa / Venda", self._baixa, color=SUCCESS, width=18).pack(side="left", padx=4)
        UIBuilder.button(brow, "🗑 Remover", self._excluir, color=DANGER, width=16).pack(side="left", padx=4)

        tf = UIBuilder.frame(self.content, padx=28, pady=4)
        tf.pack(fill="both", expand=True)
        cols = ("ID", "Cód. Barras", "Produto/Item", "Tamanho", "Dono (Cliente)", "Preço Outlet", "Qtd", "Status")
        widths = [45, 130, 200, 60, 180, 110, 50, 100]
        anchors = ["center", "w", "w", "center", "w", "center", "center", "center"]
        self._tree_out = UIBuilder.make_tree(tf, cols, widths, anchors)

    def _popular_tree(self):
        """Preenche a Treeview com base no termo digitado na busca."""
        if not self._tree_out:
            return

        busca = self._busca_out.get().lower().strip()
        for r in self._tree_out.get_children(): 
            self._tree_out.delete(r)

        for r in self._todos_produtos:
            # r = (id, codigo_barras, nome_prod, tamanho, nome_cli, preco_outlet, estoque, status, cliente_id)
            cod_barras = (r[1] or "").lower()
            nome_prod = (r[2] or "").lower()
            nome_cli = (r[4] or "").lower()

            if busca and (busca not in cod_barras and busca not in nome_prod and busca not in nome_cli): 
                continue

            self._tree_out.insert(
                "", "end", iid=str(r[0]), 
                values=(r[0], r[1] or "—", r[2], r[3] or "—", r[4], brl(r[5]), r[6], r[7])
            )

    def _sel_id(self):
        sel = self._tree_out.selection()
        if not sel: 
            return None
        return int(sel[0])

    def _entrada(self):
        from ui.screens.popup_outlet import PopupProdutoEntrada
        PopupProdutoEntrada(self.app, self._carregar_outlet)

    def _baixa(self):
        sel = self._tree_out.selection()
        if not sel: 
            self.toast.show("Selecione um produto.", "aviso")
            return

        pid = int(sel[0])
        item_data = next((r for r in self._todos_produtos if r[0] == pid), None)
        if not item_data: 
            return

        nome_prod = item_data[2]
        preco_outlet = float(item_data[5])
        cliente_id = item_data[8]

        win = tk.Toplevel(self.app)
        win.title("Baixa de Produto")
        win.geometry("460x300")
        win.configure(bg=BG)
        win.grab_set()

        fm = UIBuilder.frame(win, bg=BG, padx=28, pady=18)
        fm.pack(fill="both", expand=True)
        UIBuilder.label(fm, f"Venda do produto: {nome_prod}", font=FONT_BODY, bg=BG).pack()
        e_venda = UIBuilder.entry(fm, width=24)
        e_venda.pack(pady=10)
        e_venda.insert(0, f"{preco_outlet:.2f}".replace(".", ","))
        e_venda.bind("<KeyRelease>", lambda _: CurrencyFormatter.mascara_moeda_dinamica(e_venda))
        add_cred = tk.BooleanVar(value=True)
        tk.Checkbutton(fm, text="Converter em Crédito", variable=add_cred, bg=BG, fg=TEXT).pack()

        def confirmar():
            val = txt_para_float(e_venda.get())
            win.destroy()

            def _tarefa_baixa():
                with get_conn() as conn:
                    conn.execute("UPDATE produtos_outlet SET status='Baixado', estoque=0 WHERE id=%s", (pid,))
                    conn.execute("""
                        INSERT INTO vendas_outlet (cliente_id, produto_id, quantidade, preco_pago, criado) 
                        VALUES (%s,%s,%s,%s,%s)
                    """, (cliente_id, pid, 1, val, agora()))
                    if add_cred.get():
                        conn.execute("UPDATE clientes SET saldo = COALESCE(saldo,0) + %s WHERE id=%s", (val, cliente_id))
                        conn.execute("""
                            INSERT INTO historico_credito (cliente_id,tipo,valor,motivo,criado) 
                            VALUES (%s,%s,%s,%s,%s)
                        """, (cliente_id, "entrada", val, f"Venda outlet: {nome_prod}", agora()))
                    conn.commit()

            def _ao_concluir_baixa(_):
                self.toast.show("Baixa realizada com sucesso!", "sucesso")
                self._carregar_outlet()

            self.app.executar_async(
                funcao_task=_tarefa_baixa,
                callback_sucesso=_ao_concluir_baixa,
                mensagem="Registrando baixa e crédito..."
            )

        UIBuilder.button(fm, "Confirmar Baixa", confirmar, color=SUCCESS).pack(pady=10)

    def _excluir(self):
        sel = self._tree_out.selection()
        if not sel: 
            self.toast.show("Selecione um produto para remover.", "aviso")
            return

        pid = int(sel[0])
        if messagebox.askyesno("Excluir", "Remover produto permanentemente?"):
            def _tarefa_excluir():
                with get_conn() as conn:
                    conn.execute("DELETE FROM produtos_outlet WHERE id=%s", (pid,))
                    conn.commit()

            def _ao_concluir_excluir(_):
                self.toast.show("Produto removido.", "aviso")
                self._carregar_outlet()

            self.app.executar_async(
                funcao_task=_tarefa_excluir,
                callback_sucesso=_ao_concluir_excluir,
                mensagem="Removendo produto..."
            )