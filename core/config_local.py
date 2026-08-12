import json
import os

# O arquivo será salvo na pasta do projeto
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_local.json")

CONFIG_PADRAO = {
    "nome_impressora": "",
    "etiq_largura_mm": "108",
    "etiq_altura_mm": "25",
    "etiq_por_linha": "3",
    "etiq_indiv_largura_mm": "34",
    "etiq_espaco_colunas_mm": "2",
    "etiq_margem_esq": "2",
    "etiq_margem_dir": "2",
    "etiq_margem_top": "2",
    "etiq_margem_baix": "2"
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