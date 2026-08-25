"""
Popups relacionados a créditos.
"""

import tkinter as tk
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_H2, FONT_BODY, FONT_SMALL
from ui.components.base import UIBuilder
from core.database import get_conn
from core.cache import cache
from utils.helpers import brl, agora, txt_para_float
from utils.formatters import CurrencyFormatter


class PopupLancarCredito:
    """Popup para lançar crédito/débito."""
    
    def __init__(self, app, cid, callback):
        self.app = app
        self.cid = cid
        self.callback = callback
        self._build()
    
    def _build(self):
        with get_conn() as conn: 
            cli = conn.execute("SELECT nome, COALESCE(saldo,0) FROM clientes WHERE id=%s", (self.cid,)).fetchone()
        
        win = tk.Toplevel(self.app)
        win.title("Lançar Crédito")
        UIBuilder.centralizar_janela(win, 480, 480, parent=self.app)
        win.configure(bg=BG)
        win.grab_set()
        
        # 1. EMPACOTAR O RODAPÉ PRIMEIRO (Garante que o botão sempre fique visível)
        brow = UIBuilder.frame(win, bg=BG2, padx=36, pady=14)
        brow.pack(fill="x", side="bottom")

        # 2. EMPACOTAR O CARD CENTRAL (Ocupa o resto do espaço disponível)
        fm = UIBuilder.card(win, bg=BG2, px=36, py=24)
        fm.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        
        UIBuilder.label(fm, f"👤 {cli[0]}", font=FONT_H2, bg=BG2).pack(anchor="w")
        UIBuilder.label(fm, f"Saldo Atual: {brl(cli[1])}", font=FONT_BODY, bg=BG2, fg=SUCCESS).pack(anchor="w", pady=(0,15))
        
        tipo_var = tk.StringVar(value="entrada")
        r_tipo = UIBuilder.frame(fm, bg=BG2, pady=5)
        r_tipo.pack(fill="x")
        tk.Radiobutton(r_tipo, text="➕ Adicionar", variable=tipo_var, value="entrada", bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2).pack(side="left")
        tk.Radiobutton(r_tipo, text="➖ Deduzir", variable=tipo_var, value="saida", bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2).pack(side="left", padx=10)
        
        valor_var = tk.StringVar(value="0,00")
        motivo_var = tk.StringVar()
        UIBuilder.label(fm, "Valor (R$)*", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(10,0))
        
        e_val = UIBuilder.entry(fm, var=valor_var, width=20)
        e_val.pack(fill="x", ipady=6)
        e_val.bind("<KeyRelease>", lambda _: CurrencyFormatter.mascara_moeda_dinamica(e_val))
        
        UIBuilder.field(fm, "Motivo", motivo_var, bg=BG2)

        def salvar():
            val = txt_para_float(valor_var.get())
            if val <= 0: 
                self.app.toast.show("Valor inválido.", "erro")
                return
            tipo = tipo_var.get()
            if tipo == "saida" and val > cli[1]: 
                self.app.toast.show("Saldo insuficiente.", "erro")
                return
            motivo = motivo_var.get().strip() or "Ajuste manual"
            novo_saldo = cli[1] + val if tipo == "entrada" else cli[1] - val
            try:
                with get_conn() as conn:
                    conn.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (novo_saldo, self.cid))
                    conn.execute("""
                        INSERT INTO historico_credito (cliente_id,tipo,valor,motivo,criado) 
                        VALUES (%s,%s,%s,%s,%s)
                    """, (self.cid, tipo, val, motivo, agora()))
                    conn.commit()
                from core.cache import cache
                cache.invalidate_prefix("creditos")
                cache.invalidate_prefix("clientes")
                cache.invalidate_prefix("dashboard")
                win.destroy()
                self.callback()
                self.app.toast.show("Crédito atualizado!", "sucesso")
            except Exception as e:
                self.app.toast.show(f"Erro ao salvar: {e}", "erro")

        # Binds para poder pressionar Enter para salvar
        e_val.bind("<Return>", lambda _: salvar())
        
        # Barra de botões responsiva no rodapé
        UIBuilder.responsive_button_bar(
            brow,
            [
                ("Cancelar", win.destroy, BG3, TEXT),
                ("✅ Confirmar Lançamento", salvar, SUCCESS, "#000"),
            ],
            breakpoint=400,
            bg=BG2,
            py_btn=7
        ).pack(fill="x")


class PopupHistoricoCredito:
    """Popup de histórico de crédito."""
    
    def __init__(self, app, cid):
        self.app = app
        self.cid = cid
        self._build()
    
    def _build(self):
        with get_conn() as conn: 
            nome = conn.execute("SELECT nome FROM clientes WHERE id=%s", (self.cid,)).fetchone()[0]
        
        win = tk.Toplevel(self.app)
        win.title(f"Histórico — {nome}")
        UIBuilder.centralizar_janela(win, 660, 440, parent=self.app)
        win.configure(bg=BG)
        
        UIBuilder.label(win, f"📜 Histórico: {nome}", font=FONT_H2, padx=20, pady=12).pack(anchor="w")
        tf = UIBuilder.frame(win, padx=20, pady=8)
        tf.pack(fill="both", expand=True)
        tv = UIBuilder.make_tree(tf, ("Data","Tipo","Valor","Motivo"), [120,80,100,220], ["center","center","center","w"])
        tv.tag_configure("entrada", foreground=SUCCESS)
        tv.tag_configure("saida", foreground=DANGER)
        
        with get_conn() as conn: 
            hist = conn.execute("""
                SELECT criado,tipo,valor,motivo 
                FROM historico_credito 
                WHERE cliente_id=%s ORDER BY criado DESC
            """, (self.cid,)).fetchall()
        for r in hist: 
            tv.insert("","end", values=(r[0][:16], "Entrada" if r[1]=="entrada" else "Saída", brl(r[2]), r[3]), tags=(r[1],))


class PopupProdutosCliente:
    """Popup de produtos vinculados ao cliente."""
    
    def __init__(self, app, cid):
        self.app = app
        self.cid = cid
        self._build()
    
    def _build(self):
        with get_conn() as conn: 
            nome_cli = conn.execute("SELECT nome FROM clientes WHERE id=%s", (self.cid,)).fetchone()[0]
            produtos = conn.execute("""
                SELECT id, codigo_barras, nome, marca, tamanho, preco_outlet, estoque, status 
                FROM produtos_outlet WHERE cliente_id=%s ORDER BY id DESC
            """, (self.cid,)).fetchall()
        
        win = tk.Toplevel(self.app)
        win.title(f"Produtos de {nome_cli}")
        UIBuilder.centralizar_janela(win, 900, 480, parent=self.app)
        win.configure(bg=BG)
        
        UIBuilder.label(win, f"📦 Produtos Outlet — {nome_cli}", font=FONT_H2, padx=20, pady=12, fg=GOLD).pack(anchor="w")
        tf = UIBuilder.frame(win, padx=20, pady=8)
        tf.pack(fill="both", expand=True)
        tv = UIBuilder.make_tree(tf, ("ID","EAN","Descrição","Marca","Tam","Preço Outlet","Qtd","Status"), 
                                [50, 120, 240, 100, 50, 110, 60, 90], 
                                ["center","center","w","w","center","center","center","center"])
        for p in produtos: 
            tv.insert("","end", values=(p[0], p[1], p[2], p[3], p[4], brl(p[5]), p[6], p[7]))