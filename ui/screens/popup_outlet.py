"""
Popup de entrada de produto outlet.
"""

import tkinter as tk
import time
from config import BG, BG2, GOLD, FONT_H2, FONT_SMALL
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import agora, txt_para_float
from utils.formatters import CurrencyFormatter


class PopupProdutoEntrada:
    """Popup para dar entrada de produto no outlet."""
    
    def __init__(self, app, callback):
        self.app = app
        self.callback = callback
        self._build()
    
    def _build(self):
        win = tk.Toplevel(self.app)
        win.title("Entrada de Produto")
        win.geometry("960x640")
        win.configure(bg=BG)
        win.grab_set()

        main_fm = UIBuilder.card(win, bg=BG2, px=24, py=20)
        main_fm.pack(fill="both", expand=True, padx=15, pady=15)
        split = UIBuilder.frame(main_fm, bg=BG2)
        split.pack(fill="both", expand=True)
        
        # Coluna Esquerda - Seleção de Cliente
        col_e = UIBuilder.frame(split, bg=BG2, width=420)
        col_e.pack(side="left", fill="both", expand=True, padx=(0,15))
        col_e.pack_propagate(False)
        UIBuilder.label(col_e, "1. Proprietário", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0,5))
        
        f_b = UIBuilder.frame(col_e, bg=BG2)
        f_b.pack(fill="x", pady=5)
        v_b = tk.StringVar()
        UIBuilder.entry(f_b, var=v_b, width=30).pack(side="left", fill="x", expand=True, ipady=3)
        
        tf_cli = UIBuilder.frame(col_e, bg=BG2)
        tf_cli.pack(fill="both", expand=True, pady=5)
        tv_cli = UIBuilder.make_tree(tf_cli, ("ID","Nome","CPF"), [50,230,120], ["center","w","center"])
        
        def filtrar(*_):
            t = v_b.get().strip().lower()
            for r in tv_cli.get_children(): 
                tv_cli.delete(r)
            with get_conn() as conn: 
                rows = conn.execute("SELECT id, nome, cpf FROM clientes ORDER BY nome").fetchall()
            for r in rows:
                if t and t not in r[1].lower(): 
                    continue
                tv_cli.insert("","end", iid=str(r[0]), values=(r[0], r[1], r[2]))
        v_b.trace_add("write", filtrar)
        filtrar()

        # Coluna Direita - Dados do Produto
        col_d = UIBuilder.frame(split, bg=BG2, width=460)
        col_d.pack(side="right", fill="both", expand=True, padx=(15,0))
        col_d.pack_propagate(False)
        UIBuilder.label(col_d, "2. Produto", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0,10))
        
        vs = {k: tk.StringVar() for k in ["ean","nome","marca","tamanho","estoque"]}
        UIBuilder.field(col_d, "EAN", vs["ean"], bg=BG2)
        UIBuilder.field(col_d, "Nome *", vs["nome"], bg=BG2)
        UIBuilder.field(col_d, "Marca", vs["marca"], bg=BG2)
        UIBuilder.field(col_d, "Tamanho", vs["tamanho"], bg=BG2)
        
        r3 = UIBuilder.frame(col_d, bg=BG2)
        r3.pack(fill="x", pady=6)
        fp = UIBuilder.frame(r3, bg=BG2)
        fp.pack(side="left", fill="x", expand=True)
        UIBuilder.label(fp, "Preço Outlet *", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        e_out = UIBuilder.entry(fp, width=15)
        e_out.pack(fill="x", ipady=4)
        e_out.insert(0,"0,00")
        e_out.bind("<KeyRelease>", lambda _: CurrencyFormatter.formatar_moeda_local(e_out))
        
        UIBuilder.field(col_d, "Quantidade *", vs["estoque"], bg=BG2)
        vs["estoque"].set("1")

        def salvar():
            sel = tv_cli.selection()
            if not sel: 
                self.app.toast.show("Selecione o Cliente", "erro")
                return
            nome = vs["nome"].get().strip()
            if not nome: 
                self.app.toast.show("Nome obrigatório", "erro")
                return
            p_out = txt_para_float(e_out.get())
            cod = vs["ean"].get().strip()
            if not cod:
                cod = f"OUT{int(time.time()*100) % 100000000:08d}"
            
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO produtos_outlet (cliente_id, codigo_barras, nome, marca, tamanho, preco_outlet, estoque, status, criado) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'Disponível',%s)
                    RETURNING id
                """, (int(sel[0]), cod, nome, vs["marca"].get(), vs["tamanho"].get(), p_out, int(vs["estoque"].get() or 1), agora()))
                
                pid = cur.fetchone()[0]
                conn.commit()
            
            if hasattr(self.app, "_adicionar_fila_impressao"):
                self.app._adicionar_fila_impressao(pid)
                
            win.destroy()
            self.callback()
            self.app.toast.show("Produto salvo e enviado para fila!", "sucesso")
        
        UIBuilder.button(main_fm, "Salvar e Enviar p/ Fila", salvar, color=GOLD, fg="#000", width=28).pack(pady=10)