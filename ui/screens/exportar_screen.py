"""
Tela Exportar - Exportação de dados.
"""

from config import BG
from config import FONT_TITLE
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder


class ExportarScreen(BaseScreen):
    """Tela de exportação de dados."""
    
    def show(self, **kwargs):
        self.clear()
        h = UIBuilder.frame(self.content, pady=20, padx=28)
        h.pack(fill="x")
        UIBuilder.label(h, "📤 Exportar", font=FONT_TITLE).pack()
        UIBuilder.label(self.content, "Em breve exportações unificadas aqui.", bg=BG).pack()