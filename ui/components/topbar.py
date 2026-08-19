"""
Barra superior (TopBar) do sistema com indicador e botao de atualizacao estilo Discord.
"""

import tkinter as tk
from config import BG, BG2, BG3, TEXT, TEXT_DIM, SUCCESS, GOLD, FONT_SMALL


class TopBar(tk.Frame):
    """Barra superior com informacoes de contexto e botao de atualizacao estilo Discord."""

    def __init__(self, parent, on_click_update=None):
        super().__init__(parent, bg=BG2, height=42)
        self.parent = parent
        self.on_click_update = on_click_update
        self.update_info = None

        self.pack(side="top", fill="x")
        self.pack_propagate(False)

        self._build_ui()

    def _build_ui(self):
        # Lado esquerdo: Indicador discreto de status online / conexao
        left_frame = tk.Frame(self, bg=BG2)
        left_frame.pack(side="left", padx=(18, 0), fill="y")

        self.dot_status = tk.Label(left_frame, text="●", font=("Segoe UI", 8), bg=BG2, fg="#22C55E")
        self.dot_status.pack(side="left", padx=(0, 6))

        self.lbl_status = tk.Label(
            left_frame,
            text="Sistema Conectado",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT_DIM
        )
        self.lbl_status.pack(side="left")

        # Lado direito: Botão de atualização estilo Discord (verde vibrante)
        self.right_frame = tk.Frame(self, bg=BG2)
        self.right_frame.pack(side="right", padx=(0, 18), fill="y")

        # Botão de Atualização (inicialmente oculto)
        self.btn_update = tk.Button(
            self.right_frame,
            text="📥 Atualização Disponível",
            font=("Segoe UI", 9, "bold"),
            bg="#22C55E",
            fg="#FFFFFF",
            activebackground="#16A34A",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=3,
            cursor="hand2",
            command=self._ao_clicar
        )

        # Efeito hover no botao
        self.btn_update.bind("<Enter>", lambda e: self.btn_update.config(bg="#16A34A"))
        self.btn_update.bind("<Leave>", lambda e: self.btn_update.config(bg="#22C55E"))

    def mostrar_atualizacao(self, update_info: dict):
        """Exibe o botao verde de atualizacao no topo com a tag da versao."""
        self.update_info = update_info
        versao_tag = update_info.get("tag", "Nova Versão")
        self.btn_update.config(text=f"📥 Atualização {versao_tag}")
        self.btn_update.pack(side="right", pady=6)

    def ocultar_atualizacao(self):
        """Oculta o botao de atualizacao."""
        self.btn_update.pack_forget()

    def _ao_clicar(self):
        if self.on_click_update and self.update_info:
            self.on_click_update(self.update_info)
