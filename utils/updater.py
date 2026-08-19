"""
Modulo de gerenciamento de atualizacoes automaticas via GitHub Releases.
"""

import os
import sys
import json
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
    Retorna dict com detalhes da release se houver atualizacao, ou None se ja estiver na mais recente.
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

            # Preferencia para instalador .exe
            for asset in assets:
                nome = asset.get("name", "")
                if nome.lower().endswith(".exe"):
                    asset_download_url = asset.get("browser_download_url")
                    asset_name = nome
                    asset_size = asset.get("size", 0)
                    break

            # Fallback para .zip
            if not asset_download_url:
                for asset in assets:
                    nome = asset.get("name", "")
                    if nome.lower().endswith(".zip"):
                        asset_download_url = asset.get("browser_download_url")
                        asset_name = nome
                        asset_size = asset.get("size", 0)
                        break

            # Fallback para zipball do release
            if not asset_download_url:
                asset_download_url = data.get("zipball_url")
                asset_name = f"update_{tag_name}.zip"
                asset_size = 0

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
    caminho_destino = os.path.join(pasta_temp, asset_name or "update_setup.exe")

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "ValePresenteManager-Updater"}
    )

    with urllib.request.urlopen(req, timeout=30) as response:
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


def executar_instalador_e_sair(caminho_instalador: str):
    """
    Executa o instalador baixado e fecha o processo atual.
    """
    if not os.path.exists(caminho_instalador):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_instalador}")

    if caminho_instalador.lower().endswith(".exe"):
        subprocess.Popen([caminho_instalador], shell=True)
    else:
        os.startfile(caminho_instalador)

    sys.exit(0)
