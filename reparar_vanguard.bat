@echo off
title Reparador do Riot Vanguard - Correcao VAN 293
:: Batch para ativar e iniciar o servico do Riot Vanguard (vgc), corrigindo o erro VAN 293.
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Solicitando privilegios de Administrador para configurar o Vanguard...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~dpnx0\"\"' -Verb RunAs"
    exit /b
)

echo ========================================================
echo   Reparador do Riot Vanguard (Correcao do Erro VAN 293)
echo ========================================================
echo.
echo 1. Configurando o servico vgc para inicio Manual (Padrao Riot)...
sc.exe config vgc start= demand
if %ERRORLEVEL% NEQ 0 (
    echo Erro ao configurar o tipo de inicio do servico vgc.
) else (
    echo Servico vgc configurado com sucesso!
)

echo.
echo 2. Iniciando o servico vgc...
sc.exe start vgc
if %ERRORLEVEL% NEQ 0 (
    echo Nota: Se o servico nao puder ser iniciado imediatamente, reinicie o computador para carregar o driver vgk.sys.
) else (
    echo Servico vgc iniciado com sucesso!
)

echo.
echo Concluido! Pressione qualquer tecla para fechar.
pause
