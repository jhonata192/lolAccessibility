# -*- coding: utf-8 -*-
"""
Módulo de Limpeza e Semântica de Texto para Riot Client e League of Legends.
Usado conjuntamente por:
- RiotChromeVBufTextInfo (Buffer Virtual / Modo de Navegação)
- filter_speechSequence (Filtro Global de Fala do NVDA)
- Smart Overlays (Navegação via Tab / Foco)
"""

import re

class RiotTextCleaner:
    """
    Limpa ruídos do Chromium / Electron / CEF para Riot Client e League of Legends
    sem interferir em textos legítimos do jogo.
    """

    def __init__(self):
        self.last_spoken = ""

    def reset_state(self):
        """Reinicia o estado contextual."""
        self.last_spoken = ""

    def clean_text_block(self, block):
        """
        Limpa blocos de texto do buffer virtual.
        Retorna string limpa, omitindo linhas descartadas.
        """
        if not block:
            return ""
        lines = block.split("\n")
        out_lines = []
        for line in lines:
            cleaned = self.clean_single_line(line)
            if cleaned:
                out_lines.append(cleaned)
        return "\n".join(out_lines)

    def clean_single_line(self, raw):
        """
        Processa e limpa uma linha individual de texto.
        Retorna o texto tratado, ou vazio se for ruído a descartar.
        """
        if not raw:
            return ""
        text = raw.strip()
        if not text:
            return ""
        text_lower = text.lower()

        # 1. Suprimir mensagens de aviso de acessibilidade do Chromium
        if "descrições ausentes" in text_lower or "missing image descriptions" in text_lower:
            return ""

        # 2. Suprimir ruídos de banners internos e identificadores técnicos do Chromium
        if "displayedbannerid=" in text_lower or text_lower.startswith("troves displayedbannerid"):
            return ""

        # 3. Silenciar elementos decorativos puros 'animation' ou 'lottie'
        if text_lower in ("animation", "lottie"):
            return ""

        # 4. Formatar métricas de download da Riot quando presentes
        m = re.match(r"^([\d\.]+)/([\d\.]+)\s*GB@([\d\.]+)\s*MB/S(?:(\d+)\s*MIN)?$", text, re.IGNORECASE)
        if m:
            cur, total, speed, mins = m.groups()
            res = f"Download: {cur} de {total} GB a {speed} MB/s"
            if mins:
                res += f", {mins} minutos restantes"
            self.last_spoken = res
            return res

        m_speed_only = re.match(r"^([\d\.]+)/([\d\.]+)\s*GB@([\d\.]+)\s*MB/S$", text, re.IGNORECASE)
        if m_speed_only:
            cur, total, speed = m_speed_only.groups()
            res = f"Download: {cur} de {total} GB a {speed} MB/s"
            self.last_spoken = res
            return res

        m_min = re.match(r"^(\d+)\s*MIN$", text, re.IGNORECASE)
        if m_min:
            mins = m_min.group(1)
            res = f"Tempo estimado: {mins} minutos"
            self.last_spoken = res
            return res

        # 5. Preservar todo o restante do texto natural (números, versões 26.19, títulos, etc.)
        self.last_spoken = text
        return text

# Instância compartilhada singleton
shared_cleaner = RiotTextCleaner()
