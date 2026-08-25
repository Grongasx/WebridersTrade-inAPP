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

from dotenv import load_dotenv
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuracoes
from config import BG, DB_PATH, APP_TITLE, APP_VERSION

# Core
from core.database import init_db, get_conn

# Utils
from utils.helpers import agora, brl, gerar_e_persistir_ean13

# UI Components
from ui.components.sidebar import Sidebar
from ui.components.topbar import TopBar
from ui.components.base import ToastNotification, UIBuilder, LoadingPopup

# Screens & Modals
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.clientes_screen import ClientesScreen
from ui.screens.novo_cliente_screen import NovoClienteScreen
from ui.screens.vales_screen import ValesScreen
from ui.screens.novo_vale_screen import NovoValeScreen
from ui.screens.confirmacao_screen import ConfirmacaoScreen
from ui.screens.creditos_screen import CreditosScreen
from ui.screens.outlet_screen import OutletScreen
from ui.screens.garantias_screen import GarantiasScreen
from ui.screens.configuracoes_screen import ConfiguracoesScreen
from ui.screens.update_modal import UpdateModal
from utils.updater import verificar_nova_versao
# from ui.screens.exportar_screen import ExportarScreen # Desabilitado temporariamente


class App(tk.Tk):
    """Aplicacao principal do Vale Presente Manager."""
    
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} — {APP_VERSION}")
        
        # Configuração de Tamanho e Centralização Responsiva para 1920x1080 e outros monitores
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        
        if sw >= 1920 and sh >= 1080:
            w, h = 1420, 860
        elif sw >= 1600:
            w, h = 1300, 800
        elif sw >= 1366:
            w, h = 1200, 720
        else:
            w = max(980, int(sw * 0.92))
            h = max(620, int(sh * 0.88))
            
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 25)
        
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1024, 640)
        self.configure(bg=BG)
        
        # Inicializacao
        init_db()
        
        # Definir icone da aplicacao
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        ico_file = os.path.join(base_dir, "assets", "ico", "tcv.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        UIBuilder.setup_tree_style(self)
        self.toast = ToastNotification(self)
        self.loading = LoadingPopup(self)
        self.modal_update = UpdateModal(self)
        
        # Screens registry
        self.screens = {}
        self._register_screens()
        
        # Layout
        self._build_layout()
        
        # Tela inicial
        self.show("dashboard")

        # Checagem de atualizacao em background
        self.after(2500, self.checar_atualizacoes_background)
        
    def executar_async(self, funcao_task, callback_sucesso=None, mensagem="Carregando...", show_global_loading=True):
        """Executa a função de banco em background. Se show_global_loading=True, exibe o popup escurecido na janela principal."""
        if show_global_loading:
            self.loading.start(mensagem)

        def worker():
            resultado = None
            erro = None
            try:
                resultado = funcao_task()
            except Exception as e:
                erro = e

            # Devolve o resultado para a Thread Principal do Tkinter
            self.after(0, lambda: self._finalizar_async(resultado, erro, callback_sucesso, show_global_loading))

        threading.Thread(target=worker, daemon=True).start()

    def _finalizar_async(self, resultado, erro, callback_sucesso, show_global_loading=True):
        if show_global_loading:
            self.loading.stop() # Fecha o popup e remove o escurecimento apenas se exibido
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
            "garantias": GarantiasScreen(self, None),
            "etiquetas": ConfiguracoesScreen(self, None),
            "configuracoes": ConfiguracoesScreen(self, None),
            # "exportar": ExportarScreen(self, None), # Desabilitado temporariamente
        }
    
    def _build_layout(self):
        """Constroi o layout principal da aplicacao."""
        # Sidebar
        self.sidebar = Sidebar(self, self.show, os.path.basename(DB_PATH))
        
        # Container principal (TopBar + Content)
        self.main_container = UIBuilder.frame(self, bg=BG)
        self.main_container.pack(side="left", fill="both", expand=True)

        # TopBar com indicador de status e botão estilo Discord
        self.topbar = TopBar(self.main_container, on_click_update=self.abrir_modal_atualizacao)

        # Content area (telas)
        self.content = UIBuilder.frame(self.main_container, bg=BG)
        self.content.pack(side="top", fill="both", expand=True)
        
        # Atualiza referencia de content em todas as screens
        for screen in self.screens.values():
            screen.content = self.content

    def checar_atualizacoes_background(self):
        """Verifica se ha nova versao disponivel no GitHub Releases de forma silenciosa."""
        def worker():
            info = verificar_nova_versao(APP_VERSION)
            if info:
                self.after(0, lambda: self.topbar.mostrar_atualizacao(info))
        threading.Thread(target=worker, daemon=True).start()

    def abrir_modal_atualizacao(self, info_update):
        """Abre o modal de atualizacao com notas de versao e barra de progresso."""
        self.modal_update.abrir(info_update)

    def checar_atualizacao_manual(self):
        """Dispara checagem manual com feedback visual via Toast/Modal."""
        self.toast.show("Verificando se há atualizações...", "aviso")

        def worker():
            info = verificar_nova_versao(APP_VERSION)
            def callback():
                if info:
                    self.topbar.mostrar_atualizacao(info)
                    self.abrir_modal_atualizacao(info)
                else:
                    self.toast.show(f"Você já está na versão mais recente (v{APP_VERSION})!", "sucesso")
            self.after(0, callback)

        threading.Thread(target=worker, daemon=True).start()
    
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
        """Adiciona produto a fila de impressao garantindo codigo de barras EAN-13 valido."""
        with get_conn() as conn:
            p = conn.execute("""
                SELECT p.nome, p.marca, p.tamanho, p.codigo_barras, p.preco_outlet, c.nome, p.sku
                FROM produtos_outlet p LEFT JOIN clientes c ON p.cliente_id=c.id
                WHERE p.id=%s
            """, (produto_id,)).fetchone()
            if not p:
                return

            ean_final = gerar_e_persistir_ean13(conn, produto_id, p[3])

            dados = {
                "id": produto_id,
                "id_banco": str(produto_id),
                "nome": p[0],
                "marca": p[1] or "",
                "tamanho": p[2] or "",
                "codigo": ean_final,
                "codigo_barras": ean_final,
                "sku": p[6] or ean_final,
                "preco": brl(p[4]),
                "dono": p[5] or ""
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