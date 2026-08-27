"""
Modulo de gerenciamento de atualizacoes automaticas via GitHub Releases.
Suporta atualizacao direta in-place da build em dist/ (hot update) preservando configs.
"""

import os
import sys
import json
import shutil
import zipfile
import urllib.request
import urllib.error
import subprocess
import tempfile
from typing import Optional, Dict, Any, Callable
from config import APP_VERSION

REPO_OWNER = "Grongasx"
REPO_NAME = "WebridersTrade-inAPP"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"


def parse_version(v_str: str) -> tuple:
    """Converte string de versao (ex: 'v1.8.0', '1.8.0', '1.9.1') em tupla de inteiros para comparacao."""
    v_clean = v_str.strip().lstrip("vV")
    partes = []
    for p in v_clean.split("."):
        num = "".join(filter(str.isdigit, p))
        if num:
            partes.append(int(num))
        else:
            partes.append(0)
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes[:3])


def verificar_nova_versao(versao_atual: str = APP_VERSION) -> Optional[Dict[str, Any]]:
    """
    Consulta o GitHub Releases para verificar se existe uma versao mais recente que a atual.
    Prioriza os pacotes de build (.zip) para atualizacao direta in-place na pasta dist.
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "User-Agent": "ValePresenteManager-Updater",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))

        tag_name = data.get("tag_name", "")
        versao_remota = parse_version(tag_name)
        versao_local = parse_version(versao_atual)

        if versao_remota > versao_local:
            assets = data.get("assets", [])
            asset_download_url = None
            asset_name = None
            asset_size = 0

            # 1. Prioridade Maxima: Pacote ZIP da build (*build*.zip)
            for asset in assets:
                nome = asset.get("name", "")
                if "build" in nome.lower() and nome.lower().endswith(".zip"):
                    asset_download_url = asset.get("browser_download_url")
                    asset_name = nome
                    asset_size = asset.get("size", 0)
                    break

            # 2. Segunda Prioridade: Qualquer pacote .zip de distribuicao
            if not asset_download_url:
                for asset in assets:
                    nome = asset.get("name", "")
                    if nome.lower().endswith(".zip"):
                        asset_download_url = asset.get("browser_download_url")
                        asset_name = nome
                        asset_size = asset.get("size", 0)
                        break

            # 3. Terceira Prioridade: Executavel direto .exe
            if not asset_download_url:
                for asset in assets:
                    nome = asset.get("name", "")
                    if nome.lower().endswith(".exe"):
                        asset_download_url = asset.get("browser_download_url")
                        asset_name = nome
                        asset_size = asset.get("size", 0)
                        break

            # 4. Quarta Prioridade (Direto do Repositório Git): Busca os ZIPs versionados em dist/
            if not asset_download_url:
                v_clean = tag_name.lstrip("vV")
                candidatos_repo = [
                    (f"https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/{tag_name}/dist/ValePresenteManager_v{v_clean}_build.zip", f"ValePresenteManager_v{v_clean}_build.zip"),
                    (f"https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/main/dist/ValePresenteManager_v{v_clean}_build.zip", f"ValePresenteManager_v{v_clean}_build.zip"),
                    (f"https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/{tag_name}/dist/ValePresenteManager_v{v_clean}_Instalador_Completo.zip", f"ValePresenteManager_v{v_clean}_Instalador_Completo.zip"),
                    (f"https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/main/dist/ValePresenteManager_v{v_clean}_Instalador_Completo.zip", f"ValePresenteManager_v{v_clean}_Instalador_Completo.zip"),
                ]
                for url_cand, nome_cand in candidatos_repo:
                    try:
                        req_test = urllib.request.Request(
                            url_cand,
                            headers={"User-Agent": "ValePresenteManager-Updater"}
                        )
                        with urllib.request.urlopen(req_test, timeout=5) as resp_test:
                            if resp_test.status in (200, 302):
                                asset_download_url = url_cand
                                asset_name = nome_cand
                                asset_size = int(resp_test.headers.get("content-length", 0))
                                break
                    except Exception:
                        continue

            # Se nenhum binário foi encontrado nos assets nem no repositório, aborta
            if not asset_download_url:
                print(f"[UPDATER] Release {tag_name} não possui pacote compilado (.zip/.exe) nos assets nem na pasta dist/ do repositório.")
                return None

            return {
                "tag": tag_name,
                "versao_str": tag_name.lstrip("vV"),
                "titulo": data.get("name") or tag_name,
                "notas": data.get("body") or "Atualização com melhorias gerais e correções de bugs.",
                "data_publicacao": data.get("published_at", ""),
                "html_url": data.get("html_url", ""),
                "download_url": asset_download_url,
                "asset_name": asset_name,
                "asset_size": asset_size,
            }

        return None
    except Exception as e:
        print(f"[UPDATER] Erro ao checar releases no GitHub: {e}")
        return None


def baixar_atualizacao(
    download_url: str,
    asset_name: str,
    progresso_callback: Optional[Callable[[int, int, float], None]] = None
) -> str:
    """
    Baixa o arquivo do release com relatorio de progresso.
    progresso_callback recebe: (bytes_baixados, total_bytes, porcentagem)
    Retorna o caminho local do arquivo baixado.
    """
    pasta_temp = tempfile.gettempdir()
    caminho_destino = os.path.join(pasta_temp, asset_name or "update_build.zip")

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "ValePresenteManager-Updater"}
    )

    with urllib.request.urlopen(req, timeout=45) as response:
        total_size = int(response.headers.get("content-length", 0))
        bytes_baixados = 0
        bloco = 1024 * 64  # 64 KB

        with open(caminho_destino, "wb") as out_file:
            while True:
                buffer = response.read(bloco)
                if not buffer:
                    break
                bytes_baixados += len(buffer)
                out_file.write(buffer)

                if progresso_callback and total_size > 0:
                    pct = (bytes_baixados / total_size) * 100.0
                    progresso_callback(bytes_baixados, total_size, pct)

    return caminho_destino


def obter_diretorio_aplicacao() -> str:
    """Retorna a pasta da build atual (dist/ValePresenteManager ou pasta do .exe)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    
    # Em desenvolvimento, verifica se existe pasta dist/ValePresenteManager
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_app = os.path.join(base_dir, "dist", "ValePresenteManager")
    if os.path.exists(dist_app):
        return dist_app
    return base_dir


def aplicar_atualizacao_e_reiniciar(caminho_arquivo: str):
    """
    Aplica a atualizacao da build no dist/pasta do app de forma in-place
    e reinicia a aplicacao automaticamente, preservando .env e config_local.json.
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    pasta_app = obter_diretorio_aplicacao()
    exe_name = "ValePresenteManager.exe"
    exe_path = os.path.join(pasta_app, exe_name)

    # Se for um arquivo ZIP (.zip)
    if caminho_arquivo.lower().endswith(".zip"):
        pasta_temp = tempfile.gettempdir()
        pasta_stage = os.path.join(pasta_temp, "vpm_build_update_stage")
        if os.path.exists(pasta_stage):
            try:
                shutil.rmtree(pasta_stage)
            except Exception:
                pass
        os.makedirs(pasta_stage, exist_ok=True)

        # Extrai o ZIP no stage
        with zipfile.ZipFile(caminho_arquivo, "r") as zip_ref:
            zip_ref.extractall(pasta_stage)

        # Verifica se o zip extraiu com pasta aninhada (ex: ValePresenteManager/...)
        origem_copia = pasta_stage
        subitens = [os.path.join(pasta_stage, x) for x in os.listdir(pasta_stage)]
        if len(subitens) == 1 and os.path.isdir(subitens[0]):
            origem_copia = subitens[0]

        # Script de aplicacao in-place com robocopy (preserva .env e config_local.json)
        bat_path = os.path.join(pasta_temp, "vpm_update_in_place.bat")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 /nobreak >nul
taskkill /f /im "{exe_name}" >nul 2>&1
robocopy "{origem_copia}" "{pasta_app}" /E /XF .env config_local.json /R:5 /W:1 >nul
if exist "{exe_path}" (
    start "" "{exe_path}"
)
del "{caminho_arquivo}" >nul 2>&1
rmdir /s /q "{pasta_stage}" >nul 2>&1
del "%~f0" >nul 2>&1
exit
""")
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=creationflags)
        sys.exit(0)

    # Se for um executavel direto (.exe)
    if caminho_arquivo.lower().endswith(".exe"):
        if "setup" in os.path.basename(caminho_arquivo).lower():
            subprocess.Popen([caminho_arquivo], shell=True)
            sys.exit(0)
        else:
            pasta_temp = tempfile.gettempdir()
            bat_path = os.path.join(pasta_temp, "vpm_update_in_place.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f"""@echo off
timeout /t 2 /nobreak >nul
taskkill /f /im "{exe_name}" >nul 2>&1
copy /y "{caminho_arquivo}" "{exe_path}" >nul
if exist "{exe_path}" (
    start "" "{exe_path}"
)
del "{caminho_arquivo}" >nul 2>&1
del "%~f0" >nul 2>&1
exit
""")
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=creationflags)
            sys.exit(0)

    # Fallback
    os.startfile(caminho_arquivo)
    sys.exit(0)


# Alias de retrocompatibilidade
executar_instalador_e_sair = aplicar_atualizacao_e_reiniciar
