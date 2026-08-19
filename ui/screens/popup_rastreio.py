"""
Popup de Rastreamento de Encomendas dos Correios com Linha do Tempo Visual.
"""

import threading
import tkinter as tk
from tkinter import ttk
from config import (
    BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER,
    FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE
)
from ui.components.base import UIBuilder
from utils.correios import consultar_rastreio_correios, abrir_site_correios, limpar_codigo_rastreio


class PopupRastreioCorreios:
    """Modal de exibição do status e linha do tempo de rastreamento dos Correios."""

    def __init__(self, app, codigo_rastreio):
        self.app = app
        self.codigo = limpar_codigo_rastreio(codigo_rastreio)
        self.win = None
        self._build_janela()
        self._consultar_em_background()

    def _build_janela(self):
        self.win = tk.Toplevel(self.app)
        self.win.title(f"Rastreamento Correios — {self.codigo}")
        self.win.geometry("640x620")
        self.win.minsize(580, 480)
        self.win.configure(bg=BG)
        self.win.grab_set()

        self.main_fm = UIBuilder.card(self.win, bg=BG2, px=20, py=16)
        self.main_fm.pack(fill="both", expand=True, padx=14, pady=14)

        # ═══════════════════════════════════════════
        # Header do Rastreamento
        # ═══════════════════════════════════════════
        hdr = UIBuilder.frame(self.main_fm, bg=BG2)
        hdr.pack(fill="x", pady=(0, 8))

        # Título e Código
        h_left = UIBuilder.frame(hdr, bg=BG2)
        h_left.pack(side="left", fill="x", expand=True)

        UIBuilder.label(h_left, "📦 Rastreamento de Encomenda", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w")

        f_code = UIBuilder.frame(h_left, bg=BG2)
        f_code.pack(anchor="w", pady=(2, 0))

        UIBuilder.label(f_code, self.codigo or "Sem Código", font=("Consolas", 13, "bold"), bg=BG2, fg=TEXT).pack(side="left")

        if self.codigo:
            btn_copy = tk.Button(
                f_code,
                text="📋 Copiar",
                font=("Segoe UI", 8),
                bg=BG3,
                fg=TEXT_DIM,
                activebackground=BG2,
                activeforeground=TEXT,
                relief="flat",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=lambda: self.app._copiar_codigo_clipboard(self.codigo)
            )
            btn_copy.pack(side="left", padx=8)

        # Botão Abrir no Site dos Correios
        btn_site = tk.Button(
            hdr,
            text="🌐 Abrir no Site",
            font=("Segoe UI", 9, "bold"),
            bg=BG3,
            fg=GOLD,
            activebackground=BG,
            activeforeground=GOLD,
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=lambda: abrir_site_correios(self.codigo)
        )
        btn_site.pack(side="right", anchor="ne")

        UIBuilder.separator(self.main_fm).pack(fill="x", pady=(8, 10))

        # ═══════════════════════════════════════════
        # Card de Status Geral / Resumo
        # ═══════════════════════════════════════════
        self.card_status = UIBuilder.card(self.main_fm, bg=BG3, px=16, py=12)
        self.card_status.pack(fill="x", pady=(0, 10))

        self.lbl_status_geral = UIBuilder.label(
            self.card_status,
            "Consultando informações nos Correios...",
            font=("Segoe UI", 11, "bold"),
            bg=BG3,
            fg=TEXT
        )
        self.lbl_status_geral.pack(anchor="w")

        self.lbl_detalhe_geral = UIBuilder.label(
            self.card_status,
            "Aguarde a resposta da API...",
            font=FONT_SMALL,
            bg=BG3,
            fg=TEXT_DIM
        )
        self.lbl_detalhe_geral.pack(anchor="w", pady=(2, 0))

        # ═══════════════════════════════════════════
        # Container com Linha do Tempo (Timeline)
        # ═══════════════════════════════════════════
        UIBuilder.label(self.main_fm, "📜 Histórico de Movimentações:", font=("Segoe UI", 9, "bold"), bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 4))

        timeline_outer = UIBuilder.frame(self.main_fm, bg=BG2)
        timeline_outer.pack(fill="both", expand=True)

        canvas, self.inner_timeline = UIBuilder.scrolled_canvas(timeline_outer)

        # ═══════════════════════════════════════════
        # Rodapé de Ações
        # ═══════════════════════════════════════════
        b_bar = UIBuilder.frame(self.main_fm, bg=BG2)
        b_bar.pack(fill="x", pady=(10, 0))

        self.btn_refresh = UIBuilder.button(
            b_bar,
            "🔄 Atualizar Status",
            self._consultar_em_background,
            color=BG3,
            width=18
        )
        self.btn_refresh.pack(side="left")

        UIBuilder.button(
            b_bar,
            "✕ Fechar",
            self.win.destroy,
            color=BG3,
            width=12
        ).pack(side="right")

    def _consultar_em_background(self):
        """Dispara a requisição assíncrona para não travar a interface gráfica."""
        self.lbl_status_geral.config(text="Consultando informações nos Correios...", fg=TEXT)
        self.lbl_detalhe_geral.config(text="Conectando à API...", fg=TEXT_DIM)
        self.btn_refresh.config(state="disabled", text="⏳ Buscando...")

        # Limpa linha do tempo
        for child in self.inner_timeline.winfo_children():
            child.destroy()

        def worker():
            resultado = consultar_rastreio_correios(self.codigo)

            def atualizar_ui():
                self.btn_refresh.config(state="normal", text="🔄 Atualizar Status")
                self._preencher_resultado(resultado)

            if self.win and self.win.winfo_exists():
                self.win.after(0, atualizar_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _preencher_resultado(self, res: dict):
        """Renderiza os eventos na interface."""
        if not self.win or not self.win.winfo_exists():
            return

        if not res.get("sucesso"):
            erro_msg = res.get("erro", "Abra a consulta oficial no portal dos Correios.")
            self.lbl_status_geral.config(text="🌐 Consulta Oficial dos Correios", fg=GOLD)
            self.lbl_detalhe_geral.config(
                text=f"Objeto: {self.codigo}\n{erro_msg}",
                fg=TEXT_DIM
            )

            # Botão de destaque para abrir portal oficial
            card_action = UIBuilder.card(self.inner_timeline, bg=BG3, px=20, py=20)
            card_action.pack(fill="x", pady=20, padx=10)

            UIBuilder.label(
                card_action,
                "📦 Rastreamento Direto no Portal Oficial",
                font=("Segoe UI", 12, "bold"),
                bg=BG3,
                fg=GOLD
            ).pack(pady=(0, 6))

            UIBuilder.label(
                card_action,
                "Os Correios protegem as consultas em tempo real. Clique no botão abaixo para visualizar o trajeto completo:",
                font=FONT_SMALL,
                bg=BG3,
                fg=TEXT,
                wraplength=460,
                justify="center"
            ).pack(pady=(0, 14))

            btn_open_big = tk.Button(
                card_action,
                text=f"🚀 Abrir no Portal dos Correios ({self.codigo})",
                font=("Segoe UI", 11, "bold"),
                bg=GOLD,
                fg="#000000",
                activebackground="#E5971A",
                activeforeground="#000000",
                relief="flat",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: abrir_site_correios(self.codigo)
            )
            btn_open_big.pack()
            return

        status_geral = res.get("status_geral", "Em Processamento")
        entregue = res.get("entregue", False)
        cor_status = SUCCESS if entregue else ("#3B82F6" if "postado" in status_geral.lower() else WARNING)
        icone_status = "✅" if entregue else ("📮" if "postado" in status_geral.lower() else "🚚")

        self.lbl_status_geral.config(text=f"{icone_status} {status_geral}", fg=cor_status)
        self.lbl_detalhe_geral.config(
            text=f"Última atualização: {res.get('ultima_data', '—')} • {res.get('ultimo_local', '—')}",
            fg=TEXT
        )

        eventos = res.get("eventos", [])
        if not eventos:
            lbl_vazio = tk.Label(
                self.inner_timeline,
                text="Nenhum evento registrado até o momento para este código.",
                font=FONT_BODY,
                bg=BG2,
                fg=TEXT_DIM
            )
            lbl_vazio.pack(pady=20)
            return

        # Constrói itens da Linha do Tempo
        for idx, ev in enumerate(eventos):
            ev_frame = tk.Frame(self.inner_timeline, bg=BG2)
            ev_frame.pack(fill="x", pady=4, padx=8)

            # Coluna Esquerda: Marcador Visual e Linha
            f_marker = tk.Frame(ev_frame, bg=BG2, width=28)
            f_marker.pack(side="left", fill="y", padx=(0, 8))

            dot_color = SUCCESS if idx == 0 and entregue else (GOLD if idx == 0 else TEXT_DIM)
            dot = tk.Label(f_marker, text="●", font=("Segoe UI", 12), bg=BG2, fg=dot_color)
            dot.pack(anchor="n")

            # Coluna Direita: Conteúdo do Evento
            f_content = tk.Frame(ev_frame, bg=BG3, padx=12, pady=8, highlightbackground="#2E2E38", highlightthickness=1)
            f_content.pack(side="left", fill="x", expand=True)

            # Data e Hora
            d_str = f"{ev.get('data', '')} às {ev.get('hora', '')}".strip(" às")
            tk.Label(f_content, text=d_str, font=("Segoe UI", 8, "bold"), bg=BG3, fg=GOLD).pack(anchor="w")

            # Status do Evento
            tk.Label(f_content, text=ev.get("status", ""), font=("Segoe UI", 10, "bold"), bg=BG3, fg=TEXT, wraplength=440, justify="left").pack(anchor="w", pady=(1, 2))

            # Localização / Trajeto
            if ev.get("local"):
                tk.Label(f_content, text=f"📍 {ev.get('local')}", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM, wraplength=440, justify="left").pack(anchor="w")

            # Detalhes complementares
            if ev.get("detalhes") and ev.get("detalhes") != ev.get("local"):
                tk.Label(f_content, text=ev.get("detalhes"), font=("Segoe UI", 8), bg=BG3, fg=TEXT_DIM, wraplength=440, justify="left").pack(anchor="w", pady=(2, 0))
