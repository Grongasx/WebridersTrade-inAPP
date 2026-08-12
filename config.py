"""
Configuracoes globais do Vale Presente Manager.
"""

# Importacoes
import os

# ═══════════════════════════════════════════
# Paleta de cores – tema escuro com dourado
# ═══════════════════════════════════════════
BG       = "#1A1A2E"
BG2      = "#16213E"
BG3      = "#0F3460"
ACCENT   = "#E94560"
GOLD     = "#F5A623"
TEXT     = "#EAEAEA"
TEXT_DIM = "#8A8FA8"
SUCCESS  = "#4CAF50"
WARNING  = "#FF9800"
DANGER   = "#E94560"

# ═══════════════════════════════════════════
# Fontes
# ═══════════════════════════════════════════
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_H2    = ("Segoe UI", 14, "bold")
FONT_BODY  = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 11)
FONT_CODE  = ("Consolas", 14, "bold")

# ═══════════════════════════════════════════
# Caminho do banco de dados
# ═══════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vale_presente.db")