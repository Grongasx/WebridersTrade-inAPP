"""
Configuracoes globais do Vale Presente Manager.
"""

# Importacoes
import os

# ═══════════════════════════════════════════
# Paleta de cores – WEBRIDERS CLUB (Off-Black e Vermelho Elétrico)
# ═══════════════════════════════════════════
BG       = "#0D0D10"
BG2      = "#18181C"
BG3      = "#24242A"
ACCENT   = "#FF1E27"
GOLD     = "#FF1E27"
TEXT     = "#FFFFFF"
TEXT_DIM = "#9E9EA7"
SUCCESS  = "#22C55E"
WARNING  = "#F59E0B"
DANGER   = "#FF1E27"

# ═══════════════════════════════════════════
# Fontes
# ═══════════════════════════════════════════
FONT_TITLE = ("Segoe UI Black", 22, "bold")
FONT_H2    = ("Segoe UI", 14, "bold")
FONT_BODY  = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 11)
FONT_CODE  = ("Consolas", 14, "bold")

# ═══════════════════════════════════════════
# Nome e Versão da Aplicação
# ═══════════════════════════════════════════
APP_TITLE   = "WebRiders TCV"
APP_VERSION = "v1.3.6"

# ═══════════════════════════════════════════
# Caminho do banco de dados
# ═══════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vale_presente.db")