"""
Tela Dashboard - Visao geral do sistema.
"""

import tkinter as tk
from config import BG, BG2, BG3, GOLD, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import brl, hoje


class DashboardScreen(BaseScreen):
    """Tela principal com metricas e resumo do sistema."""
    
    def show(self, **kwargs):
        # Dispara o carregamento assincrono mantendo a tela atual sob o popup escurecido
        self._carregar_dashboard()
    
    def _carregar_dashboard(self):
        """Busca os dados no banco em background e atualiza a UI."""
        
        def _buscar_dados_db():
            data_hoje = hoje()
            with get_conn() as conn:
                # Total de clientes e total geral de vales
                total_cli   = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
                total_vales = conn.execute("SELECT COUNT(*) FROM vales").fetchone()[0]
                
                # Vales Usados (usado = 1)
                usados = conn.execute("SELECT COUNT(*) FROM vales WHERE usado = 1").fetchone()[0]
                
                # Vales Vencidos (usado = 0 e dentro do prazo ultrapassado)
                vencidos = conn.execute(
                    "SELECT COUNT(*) FROM vales WHERE usado = 0 AND validade IS NOT NULL AND validade < %s", 
                    (data_hoje,)
                ).fetchone()[0]
                
                # Vales Disponiveis (usado = 0 e dentro da validade)
                disponiveis = conn.execute(
                    "SELECT COUNT(*) FROM vales WHERE usado = 0 AND (validade IS NULL OR validade >= %s)", 
                    (data_hoje,)
                ).fetchone()[0]
                
                # Valores Financeiros
                soma_disponiveis = conn.execute(
                    "SELECT COALESCE(SUM(valor),0) FROM vales WHERE usado = 0 AND (validade IS NULL OR validade >= %s)", 
                    (data_hoje,)
                ).fetchone()[0]
                
                soma_usados = conn.execute(
                    "SELECT COALESCE(SUM(valor),0) FROM vales WHERE usado = 1"
                ).fetchone()[0]
                
                soma_total = conn.execute(
                    "SELECT COALESCE(SUM(valor),0) FROM vales"
                ).fetchone()[0]
                
                # Ultimos Vales Emitidos
                recentes = conn.execute("""
                    SELECT v.codigo, COALESCE(c.nome, 'Sem Cliente') as nome, v.valor, v.usado, v.criado, v.validade
                    FROM vales v 
                    LEFT JOIN clientes c ON c.id = v.cliente_id
                    ORDER BY v.criado DESC LIMIT 6
                """).fetchall()
                
                # Top Clientes
                top_cli = conn.execute("""
                    SELECT c.nome, COUNT(v.id) as qtd, COALESCE(SUM(v.valor),0) as total
                    FROM clientes c 
                    LEFT JOIN vales v ON v.cliente_id = c.id
                    GROUP BY c.id, c.nome 
                    ORDER BY qtd DESC, total DESC LIMIT 5
                """).fetchall()

            return {
                "total_cli": total_cli,
                "total_vales": total_vales,
                "disponiveis": disponiveis,
                "usados": usados,
                "vencidos": vencidos,
                "soma_disponiveis": soma_disponiveis,
                "soma_usados": soma_usados,
                "soma_total": soma_total,
                "recentes": recentes,
                "top_cli": top_cli
            }

        def _ao_concluir(dados):
            self.clear()          # Limpa a tela apenas quando os dados ja estao prontos
            self._build_ui(dados) # Desenha a UI atualizada

        # Dispara a busca executando o Popup Modal Escurecido
        self.app.executar_async(
            funcao_task=_buscar_dados_db,
            callback_sucesso=_ao_concluir,
            mensagem="Carregando informações do dashboard..."
        )

    def _build_ui(self, dados):
        """Monta a interface grafica com os dados atualizados."""
        c = self.content
        
        # Cabecalho
        h = UIBuilder.frame(c, pady=20, padx=28)
        h.pack(fill="x")
        UIBuilder.label(h, "Dashboard", font=FONT_TITLE).pack(side="left")
        UIBuilder.label(h, f"Hoje: {hoje()}", font=FONT_SMALL, fg=TEXT_DIM).pack(side="right", padx=4)
        UIBuilder.separator(c).pack(fill="x", padx=28, pady=2)

        wrap = UIBuilder.frame(c, padx=28, pady=12)
        wrap.pack(fill="both", expand=True)

        # Linha 1: Cards de Metricas
        row1 = UIBuilder.frame(wrap, bg=BG)
        row1.pack(fill="x", pady=(0, 14))

        self._metric_card(row1, "👤", dados["total_cli"],    "Clientes",              TEXT)
        self._metric_card(row1, "🎟️", dados["total_vales"],  "Total de Vales",        TEXT)
        self._metric_card(row1, "✅", dados["disponiveis"],  "Vales Disponíveis",     SUCCESS)
        self._metric_card(row1, "✔️", dados["usados"],       "Vales Usados",          TEXT_DIM)
        self._metric_card(row1, "⏰", dados["vencidos"],     "Vencidos",              DANGER)

        # Linha 2: Detalhes Financeiros e Top Clientes
        row2 = UIBuilder.frame(wrap, bg=BG)
        row2.pack(fill="both", expand=True)

        col_l = UIBuilder.frame(row2, bg=BG)
        col_l.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Card Financeiro
        fin = UIBuilder.card(col_l, bg=BG2)
        fin.pack(fill="x", pady=(0, 10))
        UIBuilder.label(fin, "💰 Valores em Circulação", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 10))
        row_fin = UIBuilder.frame(fin, bg=BG2)
        row_fin.pack(fill="x")
        
        for txt, val, cor in [
            ("Saldo Disponível",  brl(dados["soma_disponiveis"]), SUCCESS),
            ("Total Resgatado",   brl(dados["soma_usados"]),      TEXT_DIM),
            ("Total Emitido",     brl(dados["soma_total"]),       TEXT),
        ]:
            sf = UIBuilder.frame(row_fin, bg=BG3, padx=14, pady=10)
            sf.pack(side="left", padx=4, fill="x", expand=True)
            UIBuilder.label(sf, val, font=("Segoe UI", 15, "bold"), bg=BG3, fg=cor).pack(anchor="w")
            UIBuilder.label(sf, txt, font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")

        # Card de Ultimos Vales
        rec = UIBuilder.card(col_l, bg=BG2)
        rec.pack(fill="both", expand=True)
        UIBuilder.label(rec, "🕐 Últimos Vales Emitidos", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 8))
        
        data_hoje = hoje()
        for r in dados["recentes"]:
            # r = (codigo, nome, valor, usado, criado, validade)
            codigo, nome, valor, usado, criado, validade = r
            
            rf = UIBuilder.frame(rec, bg=BG3, pady=8, padx=12)
            rf.pack(fill="x", pady=2)
            
            # Identificacao de Status
            if usado:
                cor_status = TEXT_DIM
                st_txt = "Usado"
            elif validade and validade < data_hoje:
                cor_status = DANGER
                st_txt = "Vencido"
            else:
                cor_status = SUCCESS
                st_txt = "Disponível"

            UIBuilder.label(rf, codigo, font=FONT_MONO, bg=BG3, fg=GOLD).pack(side="left")
            UIBuilder.label(rf, nome[:25], font=FONT_SMALL, bg=BG3, fg=TEXT).pack(side="left", padx=10)
            
            # Badge com o Status
            UIBuilder.label(rf, f"({st_txt})", font=FONT_SMALL, bg=BG3, fg=cor_status).pack(side="right", padx=(8, 0))
            UIBuilder.label(rf, brl(valor), font=("Segoe UI", 10, "bold"), bg=BG3, fg=cor_status).pack(side="right")
            
        if not dados["recentes"]:
            UIBuilder.label(rec, "Nenhum vale emitido ainda.", bg=BG2, fg=TEXT_DIM).pack()

        # Coluna Direita: Top Clientes
        col_r = UIBuilder.frame(row2, bg=BG, width=280)
        col_r.pack(side="left", fill="y", padx=(8, 0))
        col_r.pack_propagate(False)

        tc = UIBuilder.card(col_r, bg=BG2)
        tc.pack(fill="both", expand=True)
        UIBuilder.label(tc, "🏆 Top Clientes", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 10))
        
        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        for i, r in enumerate(dados["top_cli"]):
            tf2 = UIBuilder.frame(tc, bg=BG3, pady=8, padx=12)
            tf2.pack(fill="x", pady=2)
            UIBuilder.label(tf2, medals[i], bg=BG3, font=("Segoe UI", 14)).pack(side="left")
            UIBuilder.label(tf2, r[0][:20], font=FONT_SMALL, bg=BG3, fg=TEXT).pack(side="left", padx=6)
            UIBuilder.label(tf2, f"{r[1]} vales", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(side="right")
            
        if not dados["top_cli"]:
            UIBuilder.label(tc, "Nenhum cliente ainda.", bg=BG2, fg=TEXT_DIM).pack()

        # Botoes de Acao
        brow = UIBuilder.frame(c, padx=28, pady=10)
        brow.pack(fill="x")
        UIBuilder.button(brow, "➕ Novo Cliente",   lambda: self.app.show("novo_cli"),  color=BG3, width=18).pack(side="left", padx=4)
        UIBuilder.button(brow, "✨ Emitir Vale",    lambda: self.app.show("novo_vale"), color=GOLD, fg="#000", width=18).pack(side="left", padx=4)
        UIBuilder.button(
            brow, 
            "🔍 Consultar Vale", 
            lambda: self.app.show("vales", focus_search=True), 
            color=BG3, 
            width=18
        ).pack(side="left", padx=4)

    def _metric_card(self, parent, icon, valor, titulo, cor=TEXT):
        mc = UIBuilder.card(parent, bg=BG2, px=22, py=18)
        mc.pack(side="left", padx=6, fill="x", expand=True)
        UIBuilder.label(mc, icon, font=("Segoe UI", 26), bg=BG2, fg=cor).pack(anchor="w")
        UIBuilder.label(mc, str(valor), font=("Segoe UI", 22, "bold"), bg=BG2, fg=cor).pack(anchor="w")
        UIBuilder.label(mc, titulo, font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")