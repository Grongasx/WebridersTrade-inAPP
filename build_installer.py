"""
Script de automação de build e empacotamento do instalador do Vale Presente Manager.
Empacota o executável com PyInstaller, inclui com segurança o .env ativo e gera o instalador.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from config import APP_TITLE, APP_VERSION

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
APP_NAME = "ValePresenteManager"
OUTPUT_PACKAGE_DIR = os.path.join(DIST_DIR, APP_NAME)


def log(msg):
    print(f"[*] {msg}")


def verificar_prerequisitos():
    log("Verificando pré-requisitos...")
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        print("\n[!] AVISO CRÍTICO: Arquivo .env não foi encontrado na raiz do projeto!")
        print("    Crie o arquivo .env com a variável DATABASE antes de gerar o pacote.\n")
        return False
    return True


def limpar_diretorios():
    log("Limpando builds anteriores...")
    for pasta in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(pasta):
            try:
                shutil.rmtree(pasta)
            except Exception as e:
                print(f"[!] Aviso ao limpar {pasta}: {e}")

    spec_file = os.path.join(BASE_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
        except Exception:
            pass


def compilar_pyinstaller():
    log("Iniciando compilação do executável com PyInstaller...")

    hidden_imports = [
        "psycopg",
        "psycopg.pq",
        "psycopg.types",
        "psycopg.types.numeric",
        "psycopg.types.datetime",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "PIL.ImageWin",
        "win32print",
        "win32ui",
        "win32gui",
        "win32con",
        "dotenv",
        "barcode",
        "tkcalendar",
        "babel",
        "babel.numbers",
    ]

    icon_path = os.path.join(BASE_DIR, "assets", "ico", "tcv.ico")
    assets_dir = os.path.join(BASE_DIR, "assets")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name", APP_NAME,
        "--noconsole",
        "--windowed",
        "--onedir",
        "--clean",
        "--noconfirm",
        "--icon", icon_path,
        "--add-data", f"{assets_dir}{os.pathsep}assets",
        "--collect-all", "psycopg",
        "--collect-all", "barcode",
        "--collect-all", "tkcalendar",
        "--collect-all", "babel",
    ]

    for h in hidden_imports:
        cmd.extend(["--hidden-import", h])

    cmd.append(os.path.join(BASE_DIR, "main.py"))

    log(f"Comando de build: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode != 0:
        raise RuntimeError("Falha na compilação do PyInstaller.")
    log("Compilação concluída com sucesso!")


def empacotar_arquivos_distribuicao():
    log("Copiando arquivos de configuração (.env, config_local.json e assets) para o pacote...")

    if not os.path.exists(OUTPUT_PACKAGE_DIR):
        raise FileNotFoundError(f"Pasta do executável não encontrada em {OUTPUT_PACKAGE_DIR}")

    # Copia o .env ativo
    env_origem = os.path.join(BASE_DIR, ".env")
    env_destino = os.path.join(OUTPUT_PACKAGE_DIR, ".env")
    shutil.copy2(env_origem, env_destino)
    log(f"  [OK] .env copiado para {env_destino}")

    # Copia config_local.json se existir, senão gera padrão
    cfg_origem = os.path.join(BASE_DIR, "config_local.json")
    cfg_destino = os.path.join(OUTPUT_PACKAGE_DIR, "config_local.json")
    if os.path.exists(cfg_origem):
        shutil.copy2(cfg_origem, cfg_destino)
        log(f"  [OK] config_local.json copiado para {cfg_destino}")

    # Copia pasta assets
    assets_origem = os.path.join(BASE_DIR, "assets")
    assets_destino = os.path.join(OUTPUT_PACKAGE_DIR, "assets")
    if os.path.exists(assets_origem):
        if os.path.exists(assets_destino):
            shutil.rmtree(assets_destino)
        shutil.copytree(assets_origem, assets_destino)
        log(f"  [OK] assets copiados para {assets_destino}")

    # Cria arquivo de instruções para o usuário
    readme_path = os.path.join(OUTPUT_PACKAGE_DIR, "LEIAME_INSTALACAO.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""=====================================================
{APP_TITLE} - Versão {APP_VERSION}
=====================================================

COMO EXECUTAR:
1. Dê um duplo clique no arquivo "{APP_NAME}.exe".
2. O sistema iniciará conectado ao banco de dados com as credenciais pré-configuradas no arquivo .env.

CONFIGURAÇÕES:
- O arquivo .env contém a chave de conexão segura com o banco PostgreSQL (Neon).
- O arquivo config_local.json armazena as configurações da sua impressora térmica Zebra/Windows.
- Você pode criar um atalho na Área de Trabalho para o arquivo "{APP_NAME}.exe".

=====================================================
""")
    log(f"  [OK] Instruções criadas em {readme_path}")


def criar_zip_distribuicao():
    zip_nome = f"{APP_NAME}_v{APP_VERSION}_Instalador_Completo.zip"
    zip_path = os.path.join(DIST_DIR, zip_nome)
    log(f"Gerando pacote ZIP para distribuição: {zip_nome}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(OUTPUT_PACKAGE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, DIST_DIR)
                zipf.write(file_path, rel_path)

    log(f"[OK] Pacote ZIP gerado em: {zip_path}")
    return zip_path


def gerar_script_inno_setup():
    iss_path = os.path.join(DIST_DIR, "installer.iss")
    icon_path = os.path.join(BASE_DIR, "assets", "ico", "tcv.ico")
    log(f"Gerando script do Inno Setup em {iss_path}...")

    iss_content = f"""; Script de Instalação Inno Setup para {APP_TITLE}
[Setup]
AppName={APP_TITLE}
AppVersion={APP_VERSION}
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_TITLE}
SetupIconFile={icon_path}
UninstallDisplayIcon={{app}}\\{APP_NAME}.exe
Compression=lzma2
SolidCompression=yes
OutputDir={DIST_DIR}
OutputBaseFilename={APP_NAME}_v{APP_VERSION}_Setup
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "{OUTPUT_PACKAGE_DIR}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{autoprograms}}\\{APP_TITLE}"; Filename: "{{app}}\\{APP_NAME}.exe"; IconFilename: "{{app}}\\assets\\ico\\tcv.ico"
Name: "{{autodesktop}}\\{APP_TITLE}"; Filename: "{{app}}\\{APP_NAME}.exe"; Tasks: desktopicon; IconFilename: "{{app}}\\assets\\ico\\tcv.ico"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "Iniciar o {APP_TITLE}"; Flags: nowait postinstall skipifsilent
"""
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(iss_content)
    log(f"[OK] Script Inno Setup criado: {iss_path}")

    # Tenta compilar se o Inno Setup estiver instalado na máquina
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for iscc in iscc_paths:
        if os.path.exists(iscc):
            log(f"Compilando Instalador Setup.exe com Inno Setup ({iscc})...")
            try:
                subprocess.run([iscc, iss_path], check=True)
                log(f"[OK] Instalador Setup.exe compilado com sucesso em {DIST_DIR}!")
            except Exception as e:
                print(f"[!] Erro ao compilar com Inno Setup: {e}")
            break


def main():
    print("=" * 60)
    print(f" Gerador de Instalador & Pacote - {APP_TITLE} v{APP_VERSION}")
    print("=" * 60)

    if not verificar_prerequisitos():
        return

    limpar_diretorios()
    compilar_pyinstaller()
    empacotar_arquivos_distribuicao()
    zip_path = criar_zip_distribuicao()
    gerar_script_inno_setup()

    print("\n" + "=" * 60)
    print(" BUILD CONCLUÍDO COM SUCESSO!")
    print(f" Pasta de Distribuição : {OUTPUT_PACKAGE_DIR}")
    print(f" Pacote ZIP com .env   : {zip_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
