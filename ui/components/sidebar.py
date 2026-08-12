"""
Sidebar com navegacao do sistema.
"""

import tkinter as tk
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM
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
        UIBuilder.label(fl, "🎁", font=("Segoe UI", 34), bg=BG2, fg=GOLD).pack()
        UIBuilder.label(fl, "Vale Presente", font=("Segoe UI", 13, "bold"), bg=BG2).pack()
        UIBuilder.label(fl, "Manager v4.0", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack()
        UIBuilder.separator(self.frame).pack(fill="x", padx=14, pady=2)

        menus = [
            ("dashboard",     "📊Dashboard",          "dashboard"),
            ("clientes",      "👤Clientes",           "clientes"),
            ("creditos",      "💳Credito de Cliente", "creditos"),
            ("outlet",        "📦Produtos Outlet",    "outlet"),
            ("vales",         "🎟️Vale Presentes",     "vales"),
            ("exportar",      "📤Exportar Dados",     "exportar"),
            ("configuracoes", "⚙️Etiquetas",          "configuracoes"), 
        ]
        
        for key, txt, target in menus:
            b = tk.Button(self.frame, text=txt, command=lambda t=target: self.on_navigate(t), 
                          font=("Segoe UI", 11), bg=BG2, fg=TEXT_DIM, activebackground=BG3, 
                          activeforeground=TEXT, relief="flat", bd=0, anchor="w", padx=20, 
                          pady=10, cursor="hand2", width=22)
            b.pack(fill="x", pady=1)
            self.mbtn[key] = b

        UIBuilder.separator(self.frame).pack(fill="x", padx=14, pady=6)
        UIBuilder.label(self.frame, self.db_path, font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="bottom", pady=(0, 8))
        UIBuilder.label(self.frame, "made by GrongasDev", font=("Segoe UI", 9, "italic bold"), bg=BG2, fg=GOLD).pack(side="bottom", pady=2)
    
    def set_active(self, key):
        """Define o botao ativo na sidebar."""
        for k, b in self.mbtn.items():
            b.config(bg=BG3 if k == key else BG2, fg=TEXT if k == key else TEXT_DIM)