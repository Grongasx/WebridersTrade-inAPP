@echo off
title Gerador de Instalador - Vale Presente Manager
color 0A

echo ========================================================
echo   GERADOR DE INSTALADOR - VALE PRESENTE MANAGER
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado no PATH do sistema.
    pause
    exit /b 1
)

python build_installer.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu uma falha durante o processo de build.
    pause
    exit /b %errorlevel%
)

echo.
echo Processo finalizado com sucesso!
echo Verifique a pasta 'dist' para obter o pacote com o .env incluso.
echo.
pause
