"""
Vale Presente Manager v4.0 (PDF Edition)
Sistema local de cadastro de clientes, vales e outlet
Com etiquetas dinamicas em PDF
"""

import tkinter as tk
from tkinter import ttk
import os
import sys
import subprocess
import threading
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuracoes
from config import BG, DB_PATH, APP_TITLE, APP_VERSION

# Core
from core.database import init_db, get_conn

# Utils
from utils.helpers import agora, brl

# UI Components
from ui.components.sidebar import Sidebar
from ui.components.base import ToastNotification, UIBuilder, LoadingPopup

# Screens
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.clientes_screen import ClientesScreen
from ui.screens.novo_cliente_screen import NovoClienteScreen
from ui.screens.vales_screen import ValesScreen
from ui.screens.novo_vale_screen import NovoValeScreen
from ui.screens.confirmacao_screen import ConfirmacaoScreen
from ui.screens.creditos_screen import CreditosScreen
from ui.screens.outlet_screen import OutletScreen
from ui.screens.configuracoes_screen import ConfiguracoesScreen
from ui.screens.exportar_screen import ExportarScreen


class App(tk.Tk):
    """Aplicacao principal do Vale Presente Manager."""
    
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} — {APP_VERSION}")
        self.geometry("1200x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        
        # Inicializacao
        init_db()
        UIBuilder.setup_tree_style()
        self.toast = ToastNotification(self)
        self.loading = LoadingPopup(self)
        
        # Screens registry
        self.screens = {}
        self._register_screens()
        
        # Layout
        self._build_layout()
        
        # Tela inicial
        self.show("dashboard")
        
    def executar_async(self, funcao_task, callback_sucesso=None, mensagem="Carregando..."):
        """Executa a função de banco em background enquanto exibe o popup escurecido."""
        self.loading.start(mensagem)

        def worker():
            resultado = None
            erro = None
            try:
                resultado = funcao_task()
            except Exception as e:
                erro = e

            # Devolve o resultado para a Thread Principal do Tkinter
            self.after(0, lambda: self._finalizar_async(resultado, erro, callback_sucesso))

        threading.Thread(target=worker, daemon=True).start()

    def _finalizar_async(self, resultado, erro, callback_sucesso):
        self.loading.stop() # Fecha o popup e remove o escurecimento
        if erro:
            print(f"[ERRO ASYNC]: {erro}")
            self.toast.show(f"Erro ao carregar dados: {erro}", "erro")
        elif callback_sucesso:
            callback_sucesso(resultado)
            
    def _register_screens(self):
        """Registra todas as telas do sistema."""
        self.screens = {
            "dashboard": DashboardScreen(self, None),
            "clientes": ClientesScreen(self, None),
            "novo_cli": NovoClienteScreen(self, None),
            "vales": ValesScreen(self, None),
            "novo_vale": NovoValeScreen(self, None),
            "confirmacao": ConfirmacaoScreen(self, None),
            "creditos": CreditosScreen(self, None),
            "outlet": OutletScreen(self, None),
            "etiquetas": ConfiguracoesScreen(self, None),
            "configuracoes": ConfiguracoesScreen(self, None),
            "exportar": ExportarScreen(self, None),
        }
    
    def _build_layout(self):
        """Constroi o layout principal da aplicacao."""
        # Sidebar
        self.sidebar = Sidebar(self, self.show, os.path.basename(DB_PATH))
        
        # Content area
        self.content = UIBuilder.frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        
        # Atualiza referencia de content em todas as screens
        for screen in self.screens.values():
            screen.content = self.content
    
    def show(self, tela, **kwargs):
        """Navega para uma tela especifica."""
        self.sidebar.set_active(tela)
        
        if tela in self.screens:
            self.screens[tela].show(**kwargs)
        else:
            print(f"Tela '{tela}' nao encontrada!")
    
    def _copiar_codigo_clipboard(self, codigo):
        """Copia codigo para a area de transferencia."""
        self.clipboard_clear()
        self.clipboard_append(codigo)
        self.update()
        self.toast.show(f"Codigo {codigo} copiado!", "sucesso")
    
    def _obter_impressoras_windows(self):
        """Obtem lista de impressoras disponiveis no Windows."""
        try:
            import win32print
            printers = [p[2] for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            if printers:
                return printers
        except Exception:
            pass
        try:
            cmd = 'powershell -Command "Get-Printer | Select-Object -ExpandProperty Name"'
            out = subprocess.check_output(cmd, shell=True, text=True)
            printers = [line.strip() for line in out.strip().split('\n') if line.strip()]
            if printers:
                return printers
        except Exception:
            pass
        return ["Zebra"]
    
    def _adicionar_fila_impressao(self, produto_id):
        """Adiciona produto a fila de impressao."""
        with get_conn() as conn:
            p = conn.execute("""
                SELECT p.nome, p.marca, p.tamanho, p.codigo_barras, p.preco_outlet, c.nome
                FROM produtos_outlet p JOIN clientes c ON p.cliente_id=c.id
                WHERE p.id=%s
            """, (produto_id,)).fetchone()
            if not p:
                return

            dados = {
                "id": produto_id,
                "nome": p[0],
                "marca": p[1] or "",
                "tamanho": p[2] or "",
                "codigo": p[3],
                "preco": brl(p[4]),
                "dono": p[5]
            }

            conn.execute("""
                INSERT INTO fila_impressao (produto_id, texto_etiqueta, status, criado, quantidade)
                VALUES (%s, %s, 'Pendente', %s, 1)
            """, (produto_id, json.dumps(dados), agora()))
            conn.commit()


# ═══════════════════════════════════════════
# Execucao
# ═══════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()