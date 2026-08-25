"""
Tela Dashboard - Visão 360° e Inteligência Operacional do Vale Presente Manager.
Gráficos vetoriais, KPIs em tempo real, pipeline de garantias, ciclo de vida de vales e feed operacional.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
from config import (
    BG, BG2, BG3, GOLD, ACCENT, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER,
    FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE
)
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from core.cache import cache
from utils.helpers import brl, hoje, agora


class DashboardScreen(BaseScreen):
    """Tela principal do sistema com métricas executivas, gráficos interativos e visão operacional completa."""

    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._feed_ativo = "vales"  # "vales", "garantias", "outlet"
        self._dados = None

    def show(self, **kwargs):
        self._carregar_dashboard()

    def _carregar_dashboard(self, forcar_atualizacao=False):
        """Busca os dados agregados no banco em background com suporte a cache."""
        if forcar_atualizacao:
            cache.invalidate_prefix("dashboard")

        def _buscar_dados_db():
            cached = cache.get("dashboard:metrics_v4")
            if cached is not None and not forcar_atualizacao:
                return cached

            data_hoje = hoje()
            with get_conn() as conn:
                # 1. Clientes & Saldos
                total_cli = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
                soma_saldo_clientes = conn.execute("SELECT COALESCE(SUM(saldo), 0) FROM clientes").fetchone()[0]
                clientes_com_saldo = conn.execute("SELECT COUNT(*) FROM clientes WHERE saldo > 0").fetchone()[0]

                # 2. Vales Presente
                total_vales = conn.execute("SELECT COUNT(*) FROM vales").fetchone()[0]
                usados = conn.execute("SELECT COUNT(*) FROM vales WHERE usado = 1").fetchone()[0]
                vencidos = conn.execute(
                    "SELECT COUNT(*) FROM vales WHERE usado = 0 AND validade IS NOT NULL AND validade < %s",
                    (data_hoje,)
                ).fetchone()[0]
                disponiveis = conn.execute(
                    "SELECT COUNT(*) FROM vales WHERE usado = 0 AND (validade IS NULL OR validade >= %s)",
                    (data_hoje,)
                ).fetchone()[0]

                soma_disponiveis = conn.execute(
                    "SELECT COALESCE(SUM(valor), 0) FROM vales WHERE usado = 0 AND (validade IS NULL OR validade >= %s)",
                    (data_hoje,)
                ).fetchone()[0]
                soma_usados = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM vales WHERE usado = 1").fetchone()[0]
                soma_total_vales = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM vales").fetchone()[0]
                taxa_conversao = round((usados / total_vales * 100), 1) if total_vales > 0 else 0.0

                # Total de crédito em circulação (Saldos + Vales Ativos)
                credito_total_circulacao = float(soma_saldo_clientes) + float(soma_disponiveis)

                # 3. Outlet & Trade-in
                try:
                    total_outlet = conn.execute("SELECT COUNT(*) FROM produtos_outlet").fetchone()[0]
                    outlet_disp = conn.execute("SELECT COUNT(*) FROM produtos_outlet WHERE status = 'Disponível' OR (status IS NULL AND estoque > 0)").fetchone()[0]
                    outlet_baixados = conn.execute("SELECT COUNT(*) FROM produtos_outlet WHERE status = 'Baixado' OR estoque = 0").fetchone()[0]
                    valor_estoque_outlet = conn.execute("SELECT COALESCE(SUM(preco_outlet * GREATEST(COALESCE(estoque, 1), 1)), 0) FROM produtos_outlet WHERE status != 'Baixado' AND (estoque > 0 OR estoque IS NULL)").fetchone()[0]
                    valor_vendido_outlet = conn.execute("SELECT COALESCE(SUM(preco_outlet), 0) FROM produtos_outlet WHERE status = 'Baixado'").fetchone()[0]
                except Exception:
                    total_outlet = outlet_disp = outlet_baixados = 0
                    valor_estoque_outlet = valor_vendido_outlet = 0.0

                # 4. Garantias & RMA
                try:
                    garantias_ativas = conn.execute("SELECT COUNT(*) FROM garantias WHERE status NOT IN ('finalizada', 'cancelada', 'concluida')").fetchone()[0]
                    garantias_concluidas = conn.execute("SELECT COUNT(*) FROM garantias WHERE status IN ('finalizada', 'concluida')").fetchone()[0]
                    garantias_canceladas = conn.execute("SELECT COUNT(*) FROM garantias WHERE status = 'cancelada'").fetchone()[0]
                    
                    rows_etapas = conn.execute("""
                        SELECT status, COUNT(*) FROM garantias 
                        WHERE status NOT IN ('finalizada', 'cancelada', 'concluida')
                        GROUP BY status
                    """).fetchall()
                    etapas_counts = {st: cnt for st, cnt in rows_etapas}
                except Exception:
                    garantias_ativas = garantias_concluidas = garantias_canceladas = 0
                    etapas_counts = {}

                # 5. Listas de Atividades Recentes
                recentes_vales = conn.execute("""
                    SELECT v.codigo, COALESCE(c.nome, 'Sem Cliente') as nome, v.valor, v.usado, v.criado, v.validade
                    FROM vales v 
                    LEFT JOIN clientes c ON c.id = v.cliente_id
                    ORDER BY v.criado DESC LIMIT 5
                """).fetchall()

                try:
                    recentes_garantias = conn.execute("""
                        SELECT g.protocolo, COALESCE(c.nome, 'Sem Cliente') as cli_nome,
                               CONCAT(COALESCE(g.marca, ''), ' ', COALESCE(g.modelo, g.tipo_produto, '')) as prod,
                               g.status, g.criado
                        FROM garantias g
                        LEFT JOIN clientes c ON c.id = g.cliente_id
                        ORDER BY g.criado DESC LIMIT 5
                    """).fetchall()
                except Exception:
                    recentes_garantias = []

                try:
                    recentes_outlet = conn.execute("""
                        SELECT p.sku, p.nome, p.marca, p.preco_outlet, p.status, p.criado
                        FROM produtos_outlet p
                        ORDER BY p.id DESC LIMIT 5
                    """).fetchall()
                except Exception:
                    recentes_outlet = []

                # Top Clientes (Maior Saldo)
                top_cli = conn.execute("""
                    SELECT c.id, c.nome, COALESCE(c.saldo, 0) as saldo, COUNT(v.id) as qtd_vales
                    FROM clientes c 
                    LEFT JOIN vales v ON v.cliente_id = c.id
                    GROUP BY c.id, c.nome, c.saldo
                    ORDER BY c.saldo DESC, qtd_vales DESC LIMIT 5
                """).fetchall()

            res = {
                "total_cli": total_cli,
                "soma_saldo_clientes": soma_saldo_clientes,
                "clientes_com_saldo": clientes_com_saldo,
                "total_vales": total_vales,
                "disponiveis": disponiveis,
                "usados": usados,
                "vencidos": vencidos,
                "soma_disponiveis": soma_disponiveis,
                "soma_usados": soma_usados,
                "soma_total_vales": soma_total_vales,
                "taxa_conversao": taxa_conversao,
                "credito_total_circulacao": credito_total_circulacao,
                "total_outlet": total_outlet,
                "outlet_disp": outlet_disp,
                "outlet_baixados": outlet_baixados,
                "valor_estoque_outlet": valor_estoque_outlet,
                "valor_vendido_outlet": valor_vendido_outlet,
                "garantias_ativas": garantias_ativas,
                "garantias_concluidas": garantias_concluidas,
                "garantias_canceladas": garantias_canceladas,
                "etapas_counts": etapas_counts,
                "recentes_vales": recentes_vales,
                "recentes_garantias": recentes_garantias,
                "recentes_outlet": recentes_outlet,
                "top_cli": top_cli
            }
            cache.set("dashboard:metrics_v4", res, ttl=60)
            return res

        def _ao_concluir(dados):
            self._dados = dados
            self.clear()
            self._build_ui(dados)

        self.app.executar_async(
            funcao_task=_buscar_dados_db,
            callback_sucesso=_ao_concluir,
            mensagem="Atualizando inteligência do dashboard..."
        )

    def _build_ui(self, dados):
        """Monta a interface gráfica com os dados atualizados."""
        c = self.content

        # ═══════════════════════════════════════════
        # Cabeçalho Principal com Botão de Refresh
        # ═══════════════════════════════════════════
        h = UIBuilder.frame(c, pady=12, padx=24)
        h.pack(fill="x")

        h_left = UIBuilder.frame(h, bg=BG)
        h_left.pack(side="left")

        UIBuilder.label(h_left, "📊 Visão Geral & Inteligência Operacional", font=FONT_TITLE, fg=TEXT).pack(anchor="w")
        data_str = hoje().strftime("%d/%m/%Y") if hasattr(hoje(), "strftime") else str(hoje())
        UIBuilder.label(h_left, f"Painel em Tempo Real • Atualizado em {data_str}", font=FONT_SMALL, fg=TEXT_DIM).pack(anchor="w")

        h_right = UIBuilder.frame(h, bg=BG)
        h_right.pack(side="right")

        UIBuilder.button(
            h_right,
            "🔄 Atualizar Dados",
            lambda: self._carregar_dashboard(forcar_atualizacao=True),
            color=BG3,
            width=16,
            pady=6
        ).pack(side="right")

        UIBuilder.separator(c).pack(fill="x", padx=24, pady=(2, 8))

        # ═══════════════════════════════════════════
        # Container Rolável Fluido
        # ═══════════════════════════════════════════
        scroll_fm = UIBuilder.frame(c, bg=BG)
        scroll_fm.pack(fill="both", expand=True)
        _, inner = UIBuilder.scrolled_canvas(scroll_fm)

        wrap = UIBuilder.frame(inner, padx=20, pady=6)
        wrap.pack(fill="both", expand=True)

        # ═══════════════════════════════════════════
        # Linha 1: Hero KPI Cards (Grid Proporcional 4 Colunas)
        # ═══════════════════════════════════════════
        row_kpi = UIBuilder.frame(wrap, bg=BG)
        row_kpi.pack(fill="x", pady=(0, 14))

        for c_idx in range(4):
            row_kpi.grid_columnconfigure(c_idx, weight=1, uniform="kpi_col")

        kpi_list = [
            ("💰 CRÉDITO ATIVO", SUCCESS, brl(dados["credito_total_circulacao"]), "Crédito Total em Circulação", f"Saldos: {brl(dados['soma_saldo_clientes'])} • Vales: {brl(dados['soma_disponiveis'])}", "💳"),
            ("🎟️ VALES", GOLD, f"{dados['disponiveis']} Ativos", "Vales Disponíveis / Emitidos", f"{dados['usados']} resgatados ({dados['taxa_conversao']}%) • {dados['vencidos']} vencidos", "🎁"),
            ("📦 OUTLET", "#3B82F6", f"{dados['outlet_disp']} Peças", "Estoque Outlet Disponível", f"Avaliação: {brl(dados['valor_estoque_outlet'])} • {dados['outlet_baixados']} baixados", "🏷️"),
            ("🛡️ RMA", "#8B5CF6", f"{dados['garantias_ativas']} Chamados", "Garantias em Andamento", f"{dados['garantias_concluidas']} no histórico • {dados['garantias_canceladas']} canceladas", "⚡"),
        ]

        for col_idx, (badge, b_cor, val, tit, sub, ico) in enumerate(kpi_list):
            kc = self._hero_kpi_card(row_kpi, badge, b_cor, val, tit, sub, ico)
            kc.grid(row=0, column=col_idx, padx=4, sticky="nsew")

        # ═══════════════════════════════════════════
        # Linha 2: Seção Principal Dividida (Gráficos vs Feed / Rank)
        # ═══════════════════════════════════════════
        row_main = UIBuilder.frame(wrap, bg=BG)
        row_main.pack(fill="both", expand=True, pady=(0, 12))

        # Coluna Esquerda: Gráficos & Visualizações
        col_graficos = UIBuilder.frame(row_main, bg=BG)
        col_graficos.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # 1. Gráfico Donut de Vales & Resgate
        card_donut = UIBuilder.card(col_graficos, bg=BG2, px=18, py=14)
        card_donut.pack(fill="x", pady=(0, 10))
        UIBuilder.label(card_donut, "🎟️  Ciclo de Vida & Conversão dos Vales", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 6))
        self._draw_donut_chart(card_donut, dados["disponiveis"], dados["usados"], dados["vencidos"], dados["taxa_conversao"])

        # 2. Pipeline de Garantias & RMA (Funil de Etapas Kanban)
        card_pipe = UIBuilder.card(col_graficos, bg=BG2, px=18, py=14)
        card_pipe.pack(fill="x", pady=(0, 10))
        UIBuilder.label(card_pipe, "🛡️  Pipeline Operacional de Garantias (Kanban)", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 6))
        self._draw_garantias_pipeline(card_pipe, dados["etapas_counts"], dados["garantias_ativas"])

        # 3. Panorama Financeiro do Outlet
        card_out = UIBuilder.card(col_graficos, bg=BG2, px=18, py=14)
        card_out.pack(fill="x")
        UIBuilder.label(card_out, "🏷️  Panorama do Estoque Outlet & Trade-in", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 6))
        self._draw_outlet_overview(card_out, dados["outlet_disp"], dados["outlet_baixados"], dados["valor_estoque_outlet"], dados["valor_vendido_outlet"])

        # Coluna Direita: Atividades Recentes & Top Clientes
        col_feeds = UIBuilder.frame(row_main, bg=BG, width=420)
        col_feeds.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # Card de Atividades Recentes com Filtro Rápido
        card_feed = UIBuilder.card(col_feeds, bg=BG2, px=18, py=14)
        card_feed.pack(fill="x", pady=(0, 10))

        f_feed_hdr = UIBuilder.frame(card_feed, bg=BG2)
        f_feed_hdr.pack(fill="x", pady=(0, 8))
        UIBuilder.label(f_feed_hdr, "⚡ Atividades Recentes", font=FONT_H2, bg=BG2, fg=GOLD).pack(side="left")

        # Botões de Seleção de Feed
        btn_box = UIBuilder.frame(f_feed_hdr, bg=BG2)
        btn_box.pack(side="right")

        self.btn_f_vales = tk.Button(
            btn_box, text="Vales", font=("Segoe UI", 8, "bold"),
            bg=ACCENT if self._feed_ativo == "vales" else BG3, fg=TEXT, relief="flat", bd=0, cursor="hand2", padx=8, pady=3,
            command=lambda: self._trocar_feed("vales")
        )
        self.btn_f_vales.pack(side="left", padx=2)

        self.btn_f_rma = tk.Button(
            btn_box, text="Garantias", font=("Segoe UI", 8, "bold"),
            bg=ACCENT if self._feed_ativo == "garantias" else BG3, fg=TEXT, relief="flat", bd=0, cursor="hand2", padx=8, pady=3,
            command=lambda: self._trocar_feed("garantias")
        )
        self.btn_f_rma.pack(side="left", padx=2)

        self.btn_f_out = tk.Button(
            btn_box, text="Outlet", font=("Segoe UI", 8, "bold"),
            bg=ACCENT if self._feed_ativo == "outlet" else BG3, fg=TEXT, relief="flat", bd=0, cursor="hand2", padx=8, pady=3,
            command=lambda: self._trocar_feed("outlet")
        )
        self.btn_f_out.pack(side="left", padx=2)

        self.feed_container = UIBuilder.frame(card_feed, bg=BG2)
        self.feed_container.pack(fill="x")
        self._renderizar_feed_conteudo()

        # Card de Top Clientes
        card_top = UIBuilder.card(col_feeds, bg=BG2, px=18, py=14)
        card_top.pack(fill="x")

        UIBuilder.label(card_top, "🏆  Top Clientes (Maior Saldo & Fidelidade)", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 8))
        
        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        for i, r in enumerate(dados["top_cli"]):
            # r = (id, nome, saldo, qtd_vales)
            cid, nome_c, saldo_c, q_vales = r
            
            row_cli = UIBuilder.frame(card_top, bg=BG3, pady=6, padx=10)
            row_cli.pack(fill="x", pady=2)

            UIBuilder.label(row_cli, medals[i], bg=BG3, font=("Segoe UI", 12)).pack(side="left")
            UIBuilder.label(row_cli, nome_c[:22], font=("Segoe UI", 9, "bold"), bg=BG3, fg=TEXT).pack(side="left", padx=6)

            UIBuilder.label(row_cli, brl(saldo_c), font=("Segoe UI", 10, "bold"), bg=BG3, fg=SUCCESS if saldo_c > 0 else TEXT_DIM).pack(side="right")
            UIBuilder.label(row_cli, f"{q_vales} vale(s) • ", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(side="right")

        if not dados["top_cli"]:
            UIBuilder.label(card_top, "Nenhum cliente cadastrado.", bg=BG2, fg=TEXT_DIM).pack(pady=6)

        # ═══════════════════════════════════════════
        # Linha 3: Barra de Atalhos e Ações Rápidas (Grid 100% Responsivo)
        # ═══════════════════════════════════════════
        card_acoes = UIBuilder.card(wrap, bg=BG2, px=18, py=14)
        card_acoes.pack(fill="x", pady=(8, 12))

        UIBuilder.label(card_acoes, "⚡ Ações Rápidas", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 8))
        b_bar = UIBuilder.frame(card_acoes, bg=BG2)
        b_bar.pack(fill="x")

        botoes_acoes = [
            ("➕ Novo Cliente", lambda: self.app.show("novo_cli"), BG3, TEXT),
            ("✨ Emitir Vale", lambda: self.app.show("novo_vale"), GOLD, "#000"),
            ("📦 Entrada Outlet", self._abrir_entrada_outlet, BG3, TEXT),
            ("🛡️ Nova Garantia", self._abrir_nova_garantia, BG3, TEXT),
            ("📜 Histórico RMA", self._abrir_historico_garantias, BG3, TEXT),
            ("💳 Lançar Créditos", lambda: self.app.show("creditos"), SUCCESS, "#000"),
        ]

        self._btn_widgets = []
        for rotulo, cmd, cor_bg, cor_fg in botoes_acoes:
            btn = UIBuilder.button(b_bar, rotulo, cmd, color=cor_bg, fg=cor_fg, pady=8)
            self._btn_widgets.append(btn)

        def _reorganizar_acoes(event=None):
            w = event.width if event else b_bar.winfo_width()
            if w <= 1:
                w = 1000

            for btn in self._btn_widgets:
                btn.grid_forget()

            if w < 920:
                # 3 colunas x 2 linhas
                for c in range(3):
                    b_bar.grid_columnconfigure(c, weight=1, uniform="act_3")
                for c in range(3, 6):
                    b_bar.grid_columnconfigure(c, weight=0, uniform="")

                for idx, btn in enumerate(self._btn_widgets):
                    r = idx // 3
                    c = idx % 3
                    btn.grid(row=r, column=c, padx=3, pady=3, sticky="ew")
            else:
                # 6 colunas x 1 linha (distribuição perfeita)
                for c in range(6):
                    b_bar.grid_columnconfigure(c, weight=1, uniform="act_6")

                for idx, btn in enumerate(self._btn_widgets):
                    btn.grid(row=0, column=idx, padx=3, pady=2, sticky="ew")

        b_bar.bind("<Configure>", _reorganizar_acoes)
        _reorganizar_acoes()

    def _hero_kpi_card(self, parent, badge, badge_cor, valor, titulo, subinfo, icone):
        """Cria cartão métrico estilo KPI Executivo."""
        kc = UIBuilder.card(parent, bg=BG2, px=16, py=14)

        # Header do Card com Badge e Ícone
        hdr = UIBuilder.frame(kc, bg=BG2)
        hdr.pack(fill="x", pady=(0, 4))

        UIBuilder.label(hdr, badge, font=("Segoe UI", 8, "bold"), bg=BG3, fg=badge_cor, padx=6, pady=2).pack(side="left")
        UIBuilder.label(hdr, icone, font=("Segoe UI", 14), bg=BG2, fg=TEXT_DIM).pack(side="right")

        # Valor Principal
        UIBuilder.label(kc, valor, font=("Segoe UI Black", 16, "bold"), bg=BG2, fg=TEXT).pack(anchor="w", pady=(2, 0))

        # Título e Subinfo
        UIBuilder.label(kc, titulo, font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.label(kc, subinfo, font=("Segoe UI", 8), bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(2, 0))

        return kc

    def _draw_donut_chart(self, parent, disponiveis, usados, vencidos, taxa_conv):
        """Desenha gráfico Donut com renderização vetorial anti-aliasing via PIL e overlay de texto."""
        f_chart = UIBuilder.frame(parent, bg=BG2)
        f_chart.pack(fill="x", pady=4)

        canvas_w, canvas_h = 140, 140
        cv = tk.Canvas(f_chart, width=canvas_w, height=canvas_h, bg=BG2, highlightthickness=0)
        cv.pack(side="left", padx=(6, 14))

        total = disponiveis + usados + vencidos

        # Renderização do Donut via PIL com supersampling 3x para bordas perfeitamente lisas
        scale = 3
        dim = canvas_w * scale
        img = Image.new("RGBA", (dim, dim), (24, 24, 28, 255))  # Cor de fundo BG2
        draw = ImageDraw.Draw(img)

        pad = 8 * scale
        cx, cy = dim // 2, dim // 2
        r_out_box = [pad, pad, dim - pad, dim - pad]
        r_in = (dim // 2) - pad - (20 * scale)

        if total == 0:
            draw.ellipse(r_out_box, fill=(36, 36, 42, 255))  # BG3
            draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(24, 24, 28, 255))  # BG2
        else:
            slices = [
                (disponiveis, (34, 197, 94, 255)),   # Verde #22C55E
                (usados, (59, 130, 246, 255)),        # Azul #3B82F6
                (vencidos, (255, 30, 39, 255))        # Vermelho #FF1E27
            ]

            ativas = [(val, col) for val, col in slices if val > 0]
            if len(ativas) == 1:
                # 100% de uma única fatia
                draw.ellipse(r_out_box, fill=ativas[0][1])
            else:
                curr_angle = -90.0  # Início no topo (12 horas)
                for val, col in slices:
                    if val <= 0:
                        continue
                    angle_extent = (val / total) * 360.0
                    draw.pieslice(
                        r_out_box,
                        start=curr_angle,
                        end=curr_angle + angle_extent,
                        fill=col,
                        outline=(24, 24, 28, 255),
                        width=2 * scale
                    )
                    curr_angle += angle_extent

            # Centro oco do Donut
            draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(24, 24, 28, 255))

        # Redimensionamento suave via LANCZOS
        img_resized = img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        self._donut_img = ImageTk.PhotoImage(img_resized)

        # Desenha Donut na tela
        cv.create_image(canvas_w // 2, canvas_h // 2, image=self._donut_img)

        # Textos Centrais com fontes TrueType
        if total == 0:
            cv.create_text(canvas_w // 2, canvas_h // 2 - 6, text="0", fill=TEXT_DIM, font=("Segoe UI Black", 14, "bold"))
            cv.create_text(canvas_w // 2, canvas_h // 2 + 10, text="Sem vales", fill=TEXT_DIM, font=("Segoe UI", 7, "bold"))
        else:
            cv.create_text(canvas_w // 2, canvas_h // 2 - 6, text=f"{taxa_conv}%", fill=TEXT, font=("Segoe UI Black", 14, "bold"))
            cv.create_text(canvas_w // 2, canvas_h // 2 + 10, text="Resgatados", fill=TEXT_DIM, font=("Segoe UI", 7, "bold"))

        # Legenda lateral
        leg = UIBuilder.frame(f_chart, bg=BG2)
        leg.pack(side="left", fill="both", expand=True)

        itens_leg = [
            ("🟢 Disponíveis", disponiveis, "#22C55E", f"{round(disponiveis/total*100, 1) if total>0 else 0}%"),
            ("🔵 Resgatados",  usados,      "#3B82F6", f"{round(usados/total*100, 1) if total>0 else 0}%"),
            ("🔴 Vencidos",    vencidos,    "#FF1E27", f"{round(vencidos/total*100, 1) if total>0 else 0}%"),
        ]
        for lbl, qtd, cor, pct in itens_leg:
            row = UIBuilder.frame(leg, bg=BG2, pady=2)
            row.pack(fill="x")
            UIBuilder.label(row, lbl, font=("Segoe UI", 9, "bold"), bg=BG2, fg=TEXT).pack(side="left")
            UIBuilder.label(row, f"{qtd} ({pct})", font=FONT_SMALL, bg=BG2, fg=cor).pack(side="right")

    def _draw_garantias_pipeline(self, parent, etapas_counts, total_ativas):
        """Renderiza barras de progresso para as etapas ativas do Kanban de Garantias."""
        from ui.screens.popup_garantia import ETAPAS_GARANTIA

        f_pipe = UIBuilder.frame(parent, bg=BG2)
        f_pipe.pack(fill="x", pady=2)

        if total_ativas == 0:
            UIBuilder.label(f_pipe, "Nenhum chamado ativo no momento.", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(pady=8)
            return

        for key, nome, cor in ETAPAS_GARANTIA:
            qtd = etapas_counts.get(key, 0)
            pct = (qtd / total_ativas) if total_ativas > 0 else 0

            row = UIBuilder.frame(f_pipe, bg=BG2, pady=2)
            row.pack(fill="x")

            h_sub = UIBuilder.frame(row, bg=BG2)
            h_sub.pack(fill="x")
            UIBuilder.label(h_sub, nome, font=("Segoe UI", 8, "bold"), bg=BG2, fg=TEXT).pack(side="left")
            UIBuilder.label(h_sub, f"{qtd}", font=("Segoe UI", 8, "bold"), bg=BG2, fg=cor).pack(side="right")

            cv = tk.Canvas(row, height=8, bg=BG3, highlightthickness=0)
            cv.pack(fill="x", pady=(1, 3))
            
            def _desenhar_barra(event=None, c=cv, p=pct, col=cor):
                w_tot = event.width if event else c.winfo_width()
                if w_tot <= 1:
                    w_tot = 340
                w = max(4, int(w_tot * p)) if p > 0 else 0
                c.delete("all")
                c.create_rectangle(0, 0, w_tot, 8, fill=BG3, width=0)
                if w > 0:
                    c.create_rectangle(0, 0, w, 8, fill=col, width=0)

            cv.bind("<Configure>", _desenhar_barra)
            _desenhar_barra()

    def _draw_outlet_overview(self, parent, outlet_disp, outlet_baixados, val_estoque, val_vendido):
        """Renderiza cartões com avaliação e barra segmentada do Outlet."""
        f_out = UIBuilder.frame(parent, bg=BG2)
        f_out.pack(fill="x", pady=2)

        total = outlet_disp + outlet_baixados
        pct_disp = (outlet_disp / total) if total > 0 else 0

        row_metric = UIBuilder.frame(f_out, bg=BG2)
        row_metric.pack(fill="x", pady=(0, 4))

        m1 = UIBuilder.card(row_metric, bg=BG3, px=10, py=6)
        m1.pack(side="left", fill="x", expand=True, padx=(0, 4))
        UIBuilder.label(m1, "Em Estoque", font=("Segoe UI", 8), bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.label(m1, brl(val_estoque), font=("Segoe UI", 11, "bold"), bg=BG3, fg=GOLD).pack(anchor="w")
        UIBuilder.label(m1, f"{outlet_disp} peça(s) disponível(is)", font=("Segoe UI", 8), bg=BG3, fg=SUCCESS).pack(anchor="w")

        m2 = UIBuilder.card(row_metric, bg=BG3, px=10, py=6)
        m2.pack(side="left", fill="x", expand=True, padx=(4, 0))
        UIBuilder.label(m2, "Baixado / Vendido", font=("Segoe UI", 8), bg=BG3, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.label(m2, brl(val_vendido), font=("Segoe UI", 11, "bold"), bg=BG3, fg=TEXT).pack(anchor="w")
        UIBuilder.label(m2, f"{outlet_baixados} peça(s) comercializada(s)", font=("Segoe UI", 8), bg=BG3, fg=TEXT_DIM).pack(anchor="w")

        # Barra segmentada de proporção
        if total > 0:
            cv = tk.Canvas(f_out, height=8, bg=BG3, highlightthickness=0)
            cv.pack(fill="x", pady=(4, 0))
            def _desenhar_seg(event=None, c=cv, p=pct_disp):
                w_tot = event.width if event else c.winfo_width()
                if w_tot <= 1:
                    w_tot = 340
                w = int(w_tot * p)
                c.delete("all")
                c.create_rectangle(0, 0, w_tot, 8, fill=BG3, width=0)
                if w > 0:
                    c.create_rectangle(0, 0, w, 8, fill=SUCCESS, width=0)
            cv.bind("<Configure>", _desenhar_seg)
            _desenhar_seg()

    def _trocar_feed(self, tipo):
        self._feed_ativo = tipo
        self.btn_f_vales.config(bg=ACCENT if tipo == "vales" else BG3)
        self.btn_f_rma.config(bg=ACCENT if tipo == "garantias" else BG3)
        self.btn_f_out.config(bg=ACCENT if tipo == "outlet" else BG3)
        self._renderizar_feed_conteudo()

    def _renderizar_feed_conteudo(self):
        if not self.feed_container:
            return

        for child in self.feed_container.winfo_children():
            child.destroy()

        dados = self._dados
        if not dados:
            return

        data_hoje = hoje()

        if self._feed_ativo == "vales":
            for r in dados["recentes_vales"]:
                codigo, nome, valor, usado, criado, validade = r
                if usado:
                    st_cor, st_txt = TEXT_DIM, "Usado"
                elif validade and validade < data_hoje:
                    st_cor, st_txt = DANGER, "Vencido"
                else:
                    st_cor, st_txt = SUCCESS, "Disponível"

                rf = UIBuilder.frame(self.feed_container, bg=BG3, pady=6, padx=10)
                rf.pack(fill="x", pady=2)
                UIBuilder.label(rf, codigo, font=FONT_MONO, bg=BG3, fg=GOLD).pack(side="left")
                UIBuilder.label(rf, nome[:18], font=FONT_SMALL, bg=BG3, fg=TEXT).pack(side="left", padx=8)

                UIBuilder.label(rf, f"({st_txt})", font=FONT_SMALL, bg=BG3, fg=st_cor).pack(side="right", padx=(6, 0))
                UIBuilder.label(rf, brl(valor), font=("Segoe UI", 9, "bold"), bg=BG3, fg=st_cor).pack(side="right")

            if not dados["recentes_vales"]:
                UIBuilder.label(self.feed_container, "Nenhum vale recente.", bg=BG2, fg=TEXT_DIM).pack(pady=8)

        elif self._feed_ativo == "garantias":
            from ui.screens.popup_garantia import ETAPAS_GARANTIA
            mapa_nomes = {k: lbl for k, lbl, _ in ETAPAS_GARANTIA}

            for r in dados["recentes_garantias"]:
                proto, cli_n, prod_n, st, criado = r
                nome_etapa = mapa_nomes.get(st, st)

                rf = UIBuilder.frame(self.feed_container, bg=BG3, pady=6, padx=10)
                rf.pack(fill="x", pady=2)
                UIBuilder.label(rf, proto, font=FONT_MONO, bg=BG3, fg=GOLD).pack(side="left")
                UIBuilder.label(rf, f"{prod_n[:18]}", font=FONT_SMALL, bg=BG3, fg=TEXT).pack(side="left", padx=8)

                UIBuilder.label(rf, nome_etapa[:14], font=("Segoe UI", 8, "bold"), bg=BG3, fg=ACCENT).pack(side="right")

            if not dados["recentes_garantias"]:
                UIBuilder.label(self.feed_container, "Nenhuma garantia recente.", bg=BG2, fg=TEXT_DIM).pack(pady=8)

        elif self._feed_ativo == "outlet":
            for r in dados["recentes_outlet"]:
                sku, nome_p, marca, preco, st, criado = r
                st_txt = st or "Disponível"
                st_cor = SUCCESS if st_txt == "Disponível" else TEXT_DIM

                rf = UIBuilder.frame(self.feed_container, bg=BG3, pady=6, padx=10)
                rf.pack(fill="x", pady=2)
                UIBuilder.label(rf, sku or "—", font=FONT_MONO, bg=BG3, fg=GOLD).pack(side="left")
                UIBuilder.label(rf, f"{marca} {nome_p}"[:20], font=FONT_SMALL, bg=BG3, fg=TEXT).pack(side="left", padx=8)

                UIBuilder.label(rf, f"({st_txt})", font=FONT_SMALL, bg=BG3, fg=st_cor).pack(side="right", padx=(6, 0))
                UIBuilder.label(rf, brl(preco), font=("Segoe UI", 9, "bold"), bg=BG3, fg=TEXT).pack(side="right")

            if not dados["recentes_outlet"]:
                UIBuilder.label(self.feed_container, "Nenhum produto outlet recente.", bg=BG2, fg=TEXT_DIM).pack(pady=8)

    def _abrir_entrada_outlet(self):
        from ui.screens.popup_outlet import PopupProdutoEntrada
        PopupProdutoEntrada(self.app, callback=lambda: self._carregar_dashboard(forcar_atualizacao=True))

    def _abrir_nova_garantia(self):
        from ui.screens.popup_garantia import PopupNovaGarantia
        PopupNovaGarantia(self.app, callback_sucesso=lambda: self._carregar_dashboard(forcar_atualizacao=True))

    def _abrir_historico_garantias(self):
        from ui.screens.popup_garantia import PopupHistoricoGarantias
        PopupHistoricoGarantias(self.app, callback_atualizar_pai=lambda: self._carregar_dashboard(forcar_atualizacao=True))