"""
Sidebar com navegacao do sistema.
"""

import tkinter as tk
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM, APP_TITLE, APP_VERSION
from config import FONT_SMALL
from ui.components.base import UIBuilder


class Sidebar:
    """Barra lateral de navegacao."""
    
    def __init__(self, parent, on_navigate, db_path):
        self.parent = parent
        self.on_navigate = on_navigate
        self.db_path = db_path
        self.mbtn = {}
        self._build()
    
    def _build(self):
        self.frame = UIBuilder.frame(self.parent, bg=BG2, width=215)
        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)
        
        fl = UIBuilder.frame(self.frame, bg=BG2, pady=22)
        fl.pack(fill="x")
        UIBuilder.label(fl, "❖", font=("Segoe UI Black", 32), bg=BG2, fg=GOLD).pack()
        UIBuilder.label(fl, APP_TITLE, font=("Segoe UI Black", 14, "bold"), bg=BG2, fg=TEXT).pack()
        UIBuilder.label(fl, f"Versão {APP_VERSION}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack()
        UIBuilder.separator(self.frame).pack(fill="x", padx=14, pady=2)

        menus = [
            ("dashboard", "⊞  Dashboard",            "dashboard"),
            ("clientes",  "👥  Clientes",             "clientes"),
            ("creditos",  "💳  Créditos & Saldos",    "creditos"),
            ("outlet",    "🏷  Produtos Outlet",      "outlet"),
            ("vales",     "🎁  Vales Presentes",       "vales"),
            ("exportar",  "⤓  Exportar Dados",       "exportar"),
            ("etiquetas", "🖨  Etiquetas & Impressão", "etiquetas"), 
        ]
        
        for key, txt, target in menus:
            b = tk.Button(self.frame, text=txt, command=lambda t=target: self.on_navigate(t), 
                          font=("Segoe UI", 11, "bold"), bg=BG2, fg=TEXT_DIM, activebackground=BG3, 
                          activeforeground=GOLD, relief="flat", bd=0, anchor="w", padx=20, 
                          pady=10, cursor="hand2", width=22)
            b.pack(fill="x", pady=1)
            self.mbtn[key] = b

        UIBuilder.separator(self.frame).pack(fill="x", padx=14, pady=6)
        UIBuilder.label(self.frame, self.db_path, font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="bottom", pady=(0, 8))
        UIBuilder.label(self.frame, APP_TITLE, font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD).pack(side="bottom", pady=2)
    
    def set_active(self, key):
        """Define o botao ativo na sidebar."""
        for k, b in self.mbtn.items():
            b.config(bg=BG3 if k == key else BG2, fg=GOLD if k == key else TEXT_DIM)