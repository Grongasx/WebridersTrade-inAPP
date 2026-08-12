"""
Popup de detalhes do vale.
"""

import tkinter as tk
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM
from config import FONT_H2, FONT_BODY
from ui.components.base import UIBuilder


class PopupValeDetalhe:
    """Popup de detalhes do vale."""
    
    def __init__(self, app, valores):
        self.app = app
        self.valores = valores
        self._build()
    
    def _build(self):
        win = tk.Toplevel(self.app)
        win.title("Detalhes do Vale")
        win.geometry("460x520")
        win.configure(bg=BG)
        win.transient(self.app)
        win.grab_set()
        
        h = UIBuilder.frame(win, pady=15)
        h.pack(fill="x")
        UIBuilder.label(h, "📋 DETALHES", font=FONT_H2, fg=GOLD).pack()
        UIBuilder.separator(win).pack(fill="x", padx=20)
        
        body = UIBuilder.frame(win, padx=20, pady=15, bg=BG2)
        body.pack(fill="both", expand=True, padx=20, pady=15)
        
        colunas = ("Código","Cliente","Valor","Status","Validade","Emitido","Usado em")
        for i, (col, val) in enumerate(zip(colunas, self.valores)):
            lbl_campo = UIBuilder.label(body, text=f"{col.upper()}:", font=("Segoe UI", 10, "bold"), fg=TEXT_DIM)
            lbl_campo.configure(bg=BG2)
            lbl_campo.grid(row=i, column=0, sticky="e", padx=10, pady=8)
            lbl_val = UIBuilder.label(body, text=str(val), font=FONT_BODY, fg=TEXT)
            lbl_val.configure(bg=BG2)
            lbl_val.grid(row=i, column=1, sticky="w", padx=10, pady=8)
        body.grid_columnconfigure(1, weight=1)