@echo off
title lolAccessibility - Aceitar Termos de Servico
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0aceitar_termos_lol.ps1"
if %ERRORLEVEL% NEQ 0 (
    pause
)
