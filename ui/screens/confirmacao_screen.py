"""
Tela de Confirmação - Exibe código do vale emitido.
"""

from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM
from config import FONT_TITLE, FONT_H2
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from utils.helpers import brl


class ConfirmacaoScreen(BaseScreen):
    """Tela de confirmação após emitir vale."""
    
    def show(self, codigo, nome_cli, valor, validade, **kwargs):
        self.clear()
        self._build(codigo, nome_cli, valor, validade)
    
    def _build(self, codigo, nome_cli, valor, validade):
        wrap = UIBuilder.frame(self.content)
        wrap.pack(expand=True)
        box = UIBuilder.card(wrap, bg=BG2, px=64, py=48)
        box.pack(padx=100, pady=40)
        UIBuilder.label(box, "🎉", font=("Segoe UI",52), bg=BG2).pack()
        UIBuilder.label(box, "Vale emitido!", font=FONT_TITLE, bg=BG2, fg=GOLD).pack(pady=(4,2))
        UIBuilder.label(box, f"Para: {nome_cli}", font=FONT_H2, bg=BG2, fg=TEXT_DIM).pack()
        UIBuilder.separator(box).pack(fill="x", pady=18)
        cf = UIBuilder.frame(box, bg=BG3)
        cf.pack(ipadx=40, ipady=18, pady=4)
        UIBuilder.label(cf, codigo, font=("Consolas",24,"bold"), bg=BG3, fg=GOLD).pack(pady=4)
        UIBuilder.button(cf, "📋 Copiar", lambda: self.app._copiar_codigo_clipboard(codigo), color=BG2, width=16).pack(pady=4)
        brow = UIBuilder.frame(box, bg=BG2, pady=20)
        brow.pack()
        UIBuilder.button(brow, "Dashboard", lambda: self.app.show("dashboard"), color=BG3, width=14).pack(side="left", padx=6)