import tkinter as tk
from config import BG2, ACCENT, TEXT, FONT_BODY

class LoadingOverlay(tk.Frame):
    """Overlay semi-transparente ou bloco com indicador visual de carregamento."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG2)
        self.is_running = False
        self._angle = 0
        
        # Container central
        self.box = tk.Frame(self, bg=BG2, padx=20, pady=20)
        self.box.place(relx=0.5, rely=0.5, anchor="center")
        
        # Canvas para animação do spinner
        self.canvas = tk.Canvas(self.box, width=50, height=50, bg=BG2, highlightthickness=0)
        self.canvas.pack()
        
        # Mensagem de texto
        self.label = tk.Label(self.box, text="Carregando...", bg=BG2, fg=TEXT, font=FONT_BODY)
        self.label.pack(pady=(10, 0))

    def start(self, mensagem="Processando..."):
        """Exibe o loading e inicia a animação."""
        self.label.config(text=mensagem)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift() # Traz para a frente de todos os elementos
        self.is_running = True
        self._animate()

    def stop(self):
        """Oculta o loading e para a animação."""
        self.is_running = False
        self.place_forget()

    def _animate(self):
        """Faz a animação da linha girando no Canvas."""
        if not self.is_running:
            return
            
        self.canvas.delete("all")
        # Desenha o arco giratório
        self.canvas.create_arc(
            5, 5, 45, 45, 
            start=self._angle, 
            extent=100, 
            outline=ACCENT, 
            width=4, 
            style="arc"
        )
        self._angle = (self._angle + 15) % 360
        # Agenda o próximo frame em 30ms (~30 FPS)
        self.after(30, self._animate)