# -*- coding: utf-8 -*-
"""
Script de instalação e atualização direta no NVDA local.
Copia os arquivos do add-on diretamente para a pasta de add-ons do usuário:
%APPDATA%\\nvda\\addons\\lolAccessibility
E emite o comando para recarregar ou reiniciar o NVDA.
"""

import os
import sys
import shutil
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_NAME = "lolAccessibility"

APPDATA = os.environ.get("APPDATA")
if not APPDATA:
    print("Erro: Variável APPDATA não encontrada.")
    sys.exit(1)

TARGET_DIR = os.path.join(APPDATA, "nvda", "addons", ADDON_NAME)

INCLUDED_ITEMS = [
    "manifest.ini",
    "appModules",
    "globalPlugins",
    "lol_lib",
    "lib",
    "scripts",
    "doc",
    "locale"
]

def clean_nvda_pending_state():
    """Remove o status pendingInstall de addonsState.json para o NVDA não dar erro de pasta inexistente."""
    state_file = os.path.join(APPDATA, "nvda", "addonsState.json")
    if os.path.exists(state_file):
        try:
            import json
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            pending_list = data.get("pendingInstallsSet", [])
            if "lolaccessibility" in [x.lower() for x in pending_list]:
                data["pendingInstallsSet"] = [x for x in pending_list if x.lower() != "lolaccessibility"]
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                print("addonsState.json limpo com sucesso (removido pendingInstalls).")
        except Exception as e:
            print(f"Aviso ao limpar addonsState.json: {e}")

def install():
    print(f"Instalando add-on '{ADDON_NAME}' em:\n{TARGET_DIR}\n")
    
    clean_nvda_pending_state()

    pending = os.path.join(APPDATA, "nvda", "addons", f"{ADDON_NAME}.pendingInstall")
    if os.path.exists(pending):
        shutil.rmtree(pending, ignore_errors=True)
        print("Removida pasta temporária pendingInstall residual.")

    # Limpar subpastas antigas se existirem
    old_gp_lib = os.path.join(TARGET_DIR, "globalPlugins", "lib")
    if os.path.exists(old_gp_lib):
        shutil.rmtree(old_gp_lib, ignore_errors=True)
        print("Removida subpasta antiga globalPlugins/lib para evitar erro de plugin.")

    os.makedirs(TARGET_DIR, exist_ok=True)
    
    for item in INCLUDED_ITEMS:
        src = os.path.join(ROOT_DIR, item)
        dst = os.path.join(TARGET_DIR, item)
        
        if not os.path.exists(src):
            continue
            
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Copiado: {item}")
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "__init__.py" if item in ("appModules", "globalPlugins") else ""))
            print(f"Copiado diretório: {item}")

    # Garantir que nunca existam __init__.py em appModules e globalPlugins
    for folder in ["appModules", "globalPlugins"]:
        init_file = os.path.join(TARGET_DIR, folder, "__init__.py")
        if os.path.isfile(init_file):
            os.remove(init_file)
            print(f"Removido {folder}/__init__.py para proteger namespace do NVDA.")

    print("\nInstalação dos arquivos concluída com sucesso no NVDA!")
    print("Para aplicar as alterações no NVDA:")
    print("  -> Pressione NVDA + Q e escolha Reiniciar (ou Enter)")
    print("  -> Ou pressione Control + NVDA + F3 para recarregar plugins.")

if __name__ == "__main__":
    install()
