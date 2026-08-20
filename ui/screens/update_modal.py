"""
Modal de Atualizacao do Sistema - Estilo Moderno Webriders / Discord.
Exibe informacoes da nova versao, changelog, barra de progresso e botao de instalacao.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk
from config import (
    BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER,
    FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, APP_VERSION
)
from ui.components.base import UIBuilder
from utils.updater import baixar_atualizacao, executar_instalador_e_sair


class UpdateModal(tk.Frame):
    """Modal overlay para download e instalacao de atualizacoes."""

    def __init__(self, root):
        super().__init__(root, bg="#070709")
        self.root = root
        self.update_info = None
        self.is_downloading = False
        self._build_ui()

    def _build_ui(self):
        # Card centralizado
        self.card = tk.Frame(
            self,
            bg=BG2,
            padx=32,
            pady=24,
            highlightbackground="#22C55E",
            highlightthickness=1
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=560)

        # Header com icone
        hdr = tk.Frame(self.card, bg=BG2)
        hdr.pack(fill="x", pady=(0, 10))

        icon_lbl = tk.Label(hdr, text="🚀", font=("Segoe UI", 24), bg=BG2)
        icon_lbl.pack(side="left", padx=(0, 12))

        titles_frame = tk.Frame(hdr, bg=BG2)
        titles_frame.pack(side="left", fill="x", expand=True)

        self.lbl_title = tk.Label(
            titles_frame,
            text="Nova Atualização Disponível!",
            font=("Segoe UI Black", 14, "bold"),
            bg=BG2,
            fg="#22C55E",
            anchor="w"
        )
        self.lbl_title.pack(fill="x")

        self.lbl_versions = tk.Label(
            titles_frame,
            text=f"Versão atual: v{APP_VERSION} → Nova versão: ...",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT_DIM,
            anchor="w"
        )
        self.lbl_versions.pack(fill="x")

        # Botao Fechar (X) no topo direito
        self.btn_close_top = tk.Button(
            hdr,
            text="✕",
            font=("Segoe UI", 12, "bold"),
            bg=BG2,
            fg=TEXT_DIM,
            activebackground=BG2,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.fechar
        )
        self.btn_close_top.pack(side="right", anchor="ne")

        UIBuilder.separator(self.card).pack(fill="x", pady=(4, 12))

        # Secao Notas de Versao / Changelog
        lbl_notes = tk.Label(
            self.card,
            text="O que há de novo nesta versão:",
            font=("Segoe UI", 10, "bold"),
            bg=BG2,
            fg=TEXT,
            anchor="w"
        )
        lbl_notes.pack(fill="x", pady=(0, 4))

        notes_container = tk.Frame(self.card, bg=BG3, padx=1, pady=1)
        notes_container.pack(fill="both", expand=True, pady=(0, 14))

        self.txt_notes = tk.Text(
            notes_container,
            bg=BG3,
            fg=TEXT,
            font=FONT_SMALL,
            height=6,
            relief="flat",
            bd=6,
            wrap="word"
        )
        self.txt_notes.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(notes_container, orient="vertical", command=self.txt_notes.yview)
        scroll.pack(side="right", fill="y")
        self.txt_notes.config(yscrollcommand=scroll.set)

        # Secao Progresso do Download
        self.progress_frame = tk.Frame(self.card, bg=BG2)
        self.progress_frame.pack(fill="x", pady=(0, 14))

        self.lbl_progress_status = tk.Label(
            self.progress_frame,
            text="Clique em 'Atualizar Agora' para baixar a nova versão.",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT_DIM,
            anchor="w"
        )
        self.lbl_progress_status.pack(fill="x", pady=(0, 4))

        # Canvas da barra de progresso personalizada
        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            height=12,
            bg=BG3,
            highlightthickness=0
        )
        self.progress_canvas.pack(fill="x")
        self.progress_bar_rect = None

        # Botoes de Acao
        self.btn_frame = tk.Frame(self.card, bg=BG2)
        self.btn_frame.pack(fill="x", pady=(8, 0))

        self.btn_cancelar = tk.Button(
            self.btn_frame,
            text="Lembrar Depois",
            font=("Segoe UI", 10, "bold"),
            bg=BG3,
            fg=TEXT_DIM,
            activebackground=BG,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
            command=self.fechar
        )
        self.btn_cancelar.pack(side="left", ipady=4)

        self.btn_atualizar = tk.Button(
            self.btn_frame,
            text="⚡ Baixar e Atualizar Agora",
            font=("Segoe UI", 10, "bold"),
            bg="#22C55E",
            fg="#FFFFFF",
            activebackground="#16A34A",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=22,
            pady=10,
            cursor="hand2",
            command=self._iniciar_download
        )
        self.btn_atualizar.pack(side="right", ipady=4)

    def abrir(self, update_info: dict):
        """Abre o modal preenchendo as informacoes da atualizacao."""
        self.update_info = update_info
        versao_nova = update_info.get("versao_str", update_info.get("tag", ""))
        self.lbl_title.config(text=f"Nova Versão {update_info.get('tag', '')} Disponível!")
        self.lbl_versions.config(text=f"Versão Instalada: v{APP_VERSION}  ➔  Nova: {update_info.get('tag', '')}")

        # Preenche notas de versao
        self.txt_notes.config(state="normal")
        self.txt_notes.delete("1.0", tk.END)
        self.txt_notes.insert(tk.END, update_info.get("notas", "Melhorias de desempenho e correções gerais."))
        self.txt_notes.config(state="disabled")

        # Reseta barra de progresso
        self._atualizar_barra_progresso(0)
        tamanho_mb = update_info.get("asset_size", 0) / (1024 * 1024)
        tamanho_str = f" (~{tamanho_mb:.1f} MB)" if tamanho_mb > 0 else ""
        self.lbl_progress_status.config(
            text=f"Pronto para baixar{tamanho_str}. O sistema será reiniciado automaticamente após o download.",
            fg=TEXT_DIM
        )

        self.btn_atualizar.config(state="normal", text="⚡ Baixar e Atualizar Agora", bg="#22C55E")
        self.btn_cancelar.config(state="normal")
        self.btn_close_top.config(state="normal")

        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

    def fechar(self):
        """Fecha o modal se nao estiver em meio a uma instalacao critica."""
        if self.is_downloading:
            # Notifica que esta baixando
            self.lbl_progress_status.config(text="Download em andamento. Aguarde a conclusão...", fg=WARNING)
            return
        self.place_forget()

    def _atualizar_barra_progresso(self, pct: float):
        """Redesenha a barra verde de progresso no canvas."""
        self.progress_canvas.delete("all")
        w = self.progress_canvas.winfo_width() or 490
        bar_w = int((pct / 100.0) * w)
        if bar_w > 0:
            self.progress_canvas.create_rectangle(0, 0, bar_w, 12, fill="#22C55E", outline="")

    def _iniciar_download(self):
        """Inicia o download do instalador em segundo plano."""
        if not self.update_info:
            return

        download_url = self.update_info.get("download_url")
        asset_name = self.update_info.get("asset_name") or f"Setup_v{self.update_info.get('versao_str')}.exe"

        if not download_url:
            self.lbl_progress_status.config(
                text="Erro: Link de download não encontrado no release do GitHub.",
                fg=DANGER
            )
            return

        self.is_downloading = True
        self.btn_atualizar.config(state="disabled", text="⏳ Baixando Atualização...", bg=BG3)
        self.btn_cancelar.config(state="disabled")
        self.btn_close_top.config(state="disabled")
        self.lbl_progress_status.config(text="Iniciando conexão e download...", fg="#22C55E")

        def callback_progresso(bytes_down, total_bytes, pct):
            def atualizar_ui():
                self._atualizar_barra_progresso(pct)
                mb_down = bytes_down / (1024 * 1024)
                mb_total = total_bytes / (1024 * 1024)
                self.lbl_progress_status.config(
                    text=f"Baixando: {pct:.1f}% ({mb_down:.1f} MB / {mb_total:.1f} MB)",
                    fg=TEXT
                )
            self.root.after(0, atualizar_ui)

        def worker():
            caminho_instalador = None
            erro = None
            try:
                caminho_instalador = baixar_atualizacao(
                    download_url,
                    asset_name,
                    progresso_callback=callback_progresso
                )
            except Exception as e:
                erro = e

            def finalizar():
                self.is_downloading = False
                if erro:
                    self.lbl_progress_status.config(text=f"Falha no download: {erro}", fg=DANGER)
                    self.btn_atualizar.config(state="normal", text="Tentar Novamente", bg=DANGER)
                    self.btn_cancelar.config(state="normal")
                    self.btn_close_top.config(state="normal")
                else:
                    self._atualizar_barra_progresso(100)
                    self.lbl_progress_status.config(
                        text="Download concluído! Aplicando atualização na build e reiniciando...",
                        fg=SUCCESS
                    )
                    # Aguarda 1 segundo e aplica a atualizacao in-place
                    self.root.after(1200, lambda: executar_instalador_e_sair(caminho_instalador))

            self.root.after(0, finalizar)

        threading.Thread(target=worker, daemon=True).start()
