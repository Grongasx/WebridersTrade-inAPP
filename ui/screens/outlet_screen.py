"""
Tela Outlet - Gerenciamento de produtos outlet.
"""

import tkinter as tk
from tkinter import messagebox
import time
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from core.cache import cache
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
        """Busca a lista de produtos outlet no banco em segundo plano com suporte a cache."""

        def _buscar_db():
            cached = cache.get("outlet:list")
            if cached is not None:
                return cached

            with get_conn() as conn:
                rows = conn.execute("""
                    SELECT p.id, 
                           COALESCE(p.codigo_barras, '') AS ean, 
                           COALESCE(p.sku, '') AS sku, 
                           COALESCE(p.tipo, 'Outros') AS tipo, 
                           CONCAT(COALESCE(p.marca, ''), ' ', COALESCE(p.modelo, p.nome)) AS produto,
                           CONCAT(COALESCE(p.grafico, '—'), ' / ', COALESCE(p.cor, '—')) AS grafico_cor,
                           COALESCE(p.numeracao, p.tamanho, '—') AS numeracao,
                           COALESCE(c.nome, '—') AS cliente_nome, 
                           COALESCE(p.preco_outlet, p.valor_sugerido, 0) AS preco, 
                           COALESCE(p.quantidade, p.estoque, 1) AS quantidade, 
                           p.status, 
                           c.id AS cliente_id
                    FROM produtos_outlet p 
                    LEFT JOIN clientes c ON p.cliente_id = c.id 
                    ORDER BY p.id DESC
                """).fetchall()
                cache.set("outlet:list", rows, ttl=60)
                return rows

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
        h = self.build_header("🏷️ Outlet — Produtos & SKU", fg=GOLD)
        
        fb = UIBuilder.frame(self.content, pady=10, padx=28)
        fb.pack(fill="x")
        UIBuilder.label(fb, "🔍 Buscar EAN, SKU, Produto, Marca ou Cliente:", bg=BG, fg=TEXT_DIM, font=FONT_SMALL).pack(side="left", padx=(0, 6))
        UIBuilder.entry(fb, var=self._busca_out, width=38).pack(side="left", ipady=5)
        
        # Filtra a treeview em memória sem nova requisição SQL
        self._busca_out.trace_add("write", lambda *_: self._popular_tree())

        brow = UIBuilder.frame(self.content, padx=28, pady=8)
        brow.pack(side="bottom", fill="x")
        UIBuilder.button(brow, "➕ Novo Produto / SKU", self._entrada, color=GOLD, fg="#000", width=20).pack(side="left", padx=4)
        UIBuilder.button(brow, "👁️ Detalhes", self._detalhes, color=BG3, width=14).pack(side="left", padx=4)
        UIBuilder.button(brow, "🖨️ Imprimir Etiqueta", self._imprimir_direto, color=ACCENT, width=20).pack(side="left", padx=4)
        UIBuilder.button(brow, "✅ Dar Baixa / Venda", self._baixa, color=SUCCESS, width=18).pack(side="left", padx=4)
        UIBuilder.button(brow, "🗑 Remover", self._excluir, color=DANGER, width=14).pack(side="left", padx=4)

        tf = UIBuilder.frame(self.content, padx=28, pady=4)
        tf.pack(fill="both", expand=True)
        cols = ("ID", "EAN-13", "SKU", "Tipo", "Marca / Modelo", "Gráfico / Cor", "Numeração", "Proprietário", "Preço Outlet", "Qtd", "Status")
        widths = [45, 115, 130, 70, 160, 120, 75, 130, 85, 40, 75]
        anchors = ["center", "center", "center", "center", "w", "w", "center", "w", "center", "center", "center"]
        self._tree_out = UIBuilder.make_tree(tf, cols, widths, anchors)
        self._tree_out.bind("<Double-1>", self._detalhes)

    def _popular_tree(self):
        """Preenche a Treeview com base no termo digitado na busca."""
        if not self._tree_out:
            return

        busca = self._busca_out.get().lower().strip()
        for r in self._tree_out.get_children(): 
            self._tree_out.delete(r)

        for r in self._todos_produtos:
            # r = (id, ean, sku, tipo, produto, grafico_cor, numeracao, cliente_nome, preco, quantidade, status, cliente_id)
            ean_str = (r[1] or "").lower()
            sku_str = (r[2] or "").lower()
            prod_str = (r[4] or "").lower()
            cli_str = (r[7] or "").lower()

            if busca and (busca not in ean_str and busca not in sku_str and busca not in prod_str and busca not in cli_str): 
                continue

            self._tree_out.insert(
                "", "end", iid=str(r[0]), 
                values=(r[0], r[1] or "—", r[2] or "—", r[3], r[4], r[5], r[6], r[7], brl(r[8]), r[9], r[10])
            )

    def _sel_id(self):
        sel = self._tree_out.selection()
        if not sel: 
            return None
        return int(sel[0])

    def _entrada(self):
        from ui.screens.popup_outlet import PopupProdutoEntrada
        PopupProdutoEntrada(self.app, self._carregar_outlet)

    def _detalhes(self, event=None):
        if event and self._tree_out.identify_region(event.x, event.y) != "cell":
            return
        pid = self._sel_id()
        if not pid:
            self.app.toast.show("Selecione um produto.", "aviso")
            return
        from ui.screens.popup_outlet import PopupProdutoDetalhes
        PopupProdutoDetalhes(self.app, pid, self._carregar_outlet)

    def _imprimir_direto(self):
        """Abre modal para imprimir etiqueta diretamente do banco com EAN-13."""
        sel = self._tree_out.selection()
        if not sel:
            self.app.toast.show("Selecione um produto para imprimir a etiqueta.", "aviso")
            return

        pid = int(sel[0])
        item_data = next((r for r in self._todos_produtos if r[0] == pid), None)
        if not item_data:
            return

        nome_prod = item_data[4]
        ean_cod = item_data[1] or f"200{pid:09d}"

        win = tk.Toplevel(self.app)
        win.title("Imprimir Etiqueta Direto do Banco")
        win.geometry("420x240")
        win.configure(bg=BG)
        win.grab_set()

        fm = UIBuilder.frame(win, bg=BG, padx=24, pady=18)
        fm.pack(fill="both", expand=True)

        UIBuilder.label(fm, "🖨️ Impressão Direta do Banco", font=FONT_H2, bg=BG, fg=GOLD).pack(anchor="w", pady=(0, 4))
        UIBuilder.label(fm, f"Produto: {nome_prod}", font=FONT_BODY, bg=BG, fg=TEXT).pack(anchor="w")
        UIBuilder.label(fm, f"Código EAN-13: {ean_cod}", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(0, 10))

        f_qtd = UIBuilder.frame(fm, bg=BG)
        f_qtd.pack(fill="x", pady=6)
        UIBuilder.label(f_qtd, "Cópias:", font=FONT_BODY, bg=BG, fg=TEXT).pack(side="left", padx=(0, 10))
        
        v_qtd = tk.StringVar(value="1")
        
        def dec():
            try:
                v = int(v_qtd.get())
                if v > 1:
                    v_qtd.set(str(v - 1))
            except ValueError:
                v_qtd.set("1")

        def inc():
            try:
                v = int(v_qtd.get())
                v_qtd.set(str(max(1, v + 1)))
            except ValueError:
                v_qtd.set("1")

        tk.Button(f_qtd, text="➖", command=dec, bg=BG3, fg=TEXT, font=("Segoe UI", 9, "bold"), relief="flat", padx=6, pady=2, cursor="hand2").pack(side="left", padx=(0, 2))
        from tkinter import ttk
        ttk.Spinbox(f_qtd, from_=1, to=999, textvariable=v_qtd, width=6, justify="center", font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
        tk.Button(f_qtd, text="➕", command=inc, bg=BG3, fg=TEXT, font=("Segoe UI", 9, "bold"), relief="flat", padx=6, pady=2, cursor="hand2").pack(side="left", padx=(2, 0))

        def disparar():
            try:
                qtd_val = max(1, int(v_qtd.get().strip()))
            except ValueError:
                qtd_val = 1
            win.destroy()

            from utils.printer import PDFPrinter
            printer = PDFPrinter()

            def _tarefa_imp():
                return printer.imprimir_produtos_direto([pid], {pid: qtd_val})

            def _ao_concluir_imp(res):
                sucesso, msg = res
                if sucesso:
                    self.app.toast.show(msg, "sucesso")
                else:
                    self.app.toast.show(msg, "erro")

            self.app.executar_async(
                funcao_task=_tarefa_imp,
                callback_sucesso=_ao_concluir_imp,
                mensagem=f"Imprimindo {qtd_val} etiqueta(s) EAN-13..."
            )

        UIBuilder.button(fm, "🖨️ Imprimir Agora", disparar, color=SUCCESS, fg="#000", width=24).pack(pady=14)

    def _baixa(self):
        pid = self._sel_id()
        if not pid: 
            self.app.toast.show("Selecione um produto para dar baixa.", "aviso")
            return
        from ui.screens.popup_outlet import PopupBaixaProduto
        PopupBaixaProduto(self.app, pid, self._carregar_outlet)

    def _excluir(self):
        sel = self._tree_out.selection()
        if not sel: 
            self.app.toast.show("Selecione um produto para remover.", "aviso")
            return

        pid = int(sel[0])
        if messagebox.askyesno("Excluir", "Remover produto permanentemente?"):
            def _tarefa_excluir():
                with get_conn() as conn:
                    conn.execute("DELETE FROM produtos_outlet WHERE id=%s", (pid,))
                    conn.commit()
                cache.invalidate_prefix("outlet")
                cache.invalidate_prefix("dashboard")

            def _ao_concluir_excluir(_):
                self.app.toast.show("Produto removido.", "aviso")
                self._carregar_outlet()

            self.app.executar_async(
                funcao_task=_tarefa_excluir,
                callback_sucesso=_ao_concluir_excluir,
                mensagem="Removendo produto..."
            )