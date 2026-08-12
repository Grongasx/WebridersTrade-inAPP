"""
Classe base para todas as telas do sistema.
"""

from config import BG, TEXT, FONT_TITLE
from ui.components.base import UIBuilder


class BaseScreen:
    """Classe base que todas as telas (screens) devem herdar."""

    def __init__(self, app, content_frame):
        self.app = app
        self.content = content_frame
        # Reaproveita o toast global do app, se existir.
        self.toast = getattr(app, "toast", None)

    def clear(self):
        """Remove todos os widgets do conteudo atual da tela."""
        for widget in self.content.winfo_children():
            widget.destroy()

    def build_header(self, titulo, fg=TEXT):
        """Cria um cabecalho padrao com titulo + linha separadora.
        Retorna o frame do cabecalho, para a tela poder adicionar
        botoes extras (ex: .pack(side='right')).
        fg: cor opcional do texto do titulo."""
        h = UIBuilder.frame(self.content, pady=20, padx=28)
        h.pack(fill="x")
        UIBuilder.label(h, titulo, font=FONT_TITLE, fg=fg).pack(side="left")
        UIBuilder.separator(self.content).pack(fill="x", padx=28, pady=2)
        return h

    def show(self, **kwargs):
        """Deve ser sobrescrito por cada tela para desenhar seu conteudo."""
        raise NotImplementedError("As subclasses devem implementar o metodo show().")
