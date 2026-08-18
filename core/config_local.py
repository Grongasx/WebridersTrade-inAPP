import json
import os
import sys

# Determina o diretório base (pasta do .exe quando empacotado ou raiz do projeto)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "config_local.json")

CONFIG_PADRAO = {
    "nome_impressora": "",
    "etiq_largura_mm": "108.0",
    "etiq_altura_mm": "25.0",
    "etiq_por_linha": "3",
    "etiq_indiv_largura_mm": "36.0",
    "etiq_indiv_altura_mm": "22.0",
    "etiq_espaco_colunas_mm": "0.0",
    "etiq_margem_esq": "0.0",
    "etiq_margem_dir": "0.0",
    "etiq_margem_top": "0.5",
    "etiq_margem_baix": "0.5"
}

def carregar_config_local():
    """Lê o arquivo config_local.json. Se não existir, cria com os valores padrão."""
    if not os.path.exists(CONFIG_PATH):
        salvar_config_local(CONFIG_PADRAO)
        return CONFIG_PADRAO
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
            # Garante que chaves novas tenham fallback
            config_final = CONFIG_PADRAO.copy()
            config_final.update(dados)
            return config_final
    except Exception:
        return CONFIG_PADRAO

def salvar_config_local(novos_dados):
    """Salva ou atualiza chaves no arquivo config_local.json."""
    dados_atuais = carregar_config_local() if os.path.exists(CONFIG_PATH) else CONFIG_PADRAO.copy()
    dados_atuais.update(novos_dados)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(dados_atuais, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar arquivo de configuração local: {e}")
        return False