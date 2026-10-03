# -*- coding: utf-8 -*-
"""
Script de compilação do pacote do Add-on do NVDA (.nvda-addon).
Gera um arquivo zip com a extensão .nvda-addon contendo todos os arquivos necessários.
"""

import os
import sys
import zipfile
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_NAME = "lolAccessibility"

def get_version():
    manifest_path = os.path.join(ROOT_DIR, "manifest.ini")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version"):
                    return line.split("=", 1)[1].strip()
    return "1.1.0"

VERSION = get_version()
OUTPUT_FILENAME = f"{ADDON_NAME}-{VERSION}.nvda-addon"
OUTPUT_PATH = os.path.join(ROOT_DIR, OUTPUT_FILENAME)

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

def build():
    print(f"Gerando pacote {OUTPUT_FILENAME}...")
    
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)

    with zipfile.ZipFile(OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for item in INCLUDED_ITEMS:
            src_path = os.path.join(ROOT_DIR, item)
            if os.path.isfile(src_path):
                z.write(src_path, item)
                print(f"Adicionado arquivo: {item}")
            elif os.path.isdir(src_path):
                for root, _, files in os.walk(src_path):
                    for file in files:
                        if file.endswith((".pyc", ".git", ".DS_Store")):
                            continue
                        if "__pycache__" in root:
                            continue
                        if file == "__init__.py" and item in ("appModules", "globalPlugins"):
                            continue
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, ROOT_DIR)
                        z.write(full_path, rel_path)
                        print(f"Adicionado: {rel_path}")

    print(f"\nSucesso! Pacote gerado com sucesso em:\n{OUTPUT_PATH}")
    return OUTPUT_PATH

if __name__ == "__main__":
    build()
