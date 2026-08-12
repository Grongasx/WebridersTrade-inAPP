import tkinter as tk
from config import BG2, BG3, ACCENT, TEXT

class LoadingOverlay(tk.Frame):
    """Overlay semi-transparente ou bloco com indicador visual de carregamento WEBRIDERS CLUB."""
    def __init__(self, parent):
        super().__init__(parent, bg="#070709")
        self.is_running = False
        self._angle = 0
        
        # Container central
        self.box = tk.Frame(self, bg=BG2, padx=28, pady=22, highlightbackground=ACCENT, highlightthickness=1)
        self.box.place(relx=0.5, rely=0.5, anchor="center")
        
        # Emblem Webriders
        tk.Label(self.box, text="❖ WEBRIDERS", font=("Segoe UI Black", 10, "bold"), bg=BG2, fg=ACCENT).pack(pady=(0, 8))

        # Canvas para animação do spinner
        self.canvas = tk.Canvas(self.box, width=48, height=48, bg=BG2, highlightthickness=0)
        self.canvas.pack()
        
        # Mensagem de texto
        self.label = tk.Label(self.box, text="Carregando...", bg=BG2, fg=TEXT, font=("Segoe UI", 11, "bold"))
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
        # Trilho sutil
        self.canvas.create_oval(4, 4, 44, 44, outline=BG3, width=4)
        # Arco animado giratório
        self.canvas.create_arc(
            4, 4, 44, 44, 
            start=self._angle, 
            extent=110, 
            outline=ACCENT, 
            width=4, 
            style="arc"
        )
        self._angle = (self._angle + 14) % 360
        self.after(25, self._animate)