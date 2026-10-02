# -*- coding: utf-8 -*-
"""
Leitor e Analisador Acessível de Minimapa do League of Legends.
Utiliza visão computacional ultrarrápida via GDI Windows (< 3ms) e
rotulação de componentes conectados para localizar campeões inimigos
e aliados no minimapa.
Classifica posições em zonas táticas semânticas (Topo, Meio, Bot,
Selva Superior/Barão, Selva Inferior/Dragão, Bases) e cruza com a
Live Client Data API para identificar inimigos desaparecidos (MIA)
e alertar contra emboscadas (ganks).
100% seguro contra o Riot Vanguard (zero injeção / zero leitura de memória).
"""

import os
import time
import math
import collections
import ctypes
from ctypes import wintypes

try:
    from logHandler import log
except Exception:
    import logging
    log = logging.getLogger("lol_minimap_scanner")


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]


class LoLMinimapScanner:
    """
    Controla a detecção de tela do minimapa, captura de imagem GDI,
    reconhecimento de marcadores de campeões e zoneamento tático.
    """

    def __init__(self):
        self.last_scan_time = 0
        self.last_enemy_count = 0
        self.last_zones_state = {}
        self.last_gank_alert_time = 0
        self.game_cfg_cache = None
        self.game_cfg_mtime = 0

    @staticmethod
    def find_league_game_window():
        """Retorna o HWND da janela 3D do League of Legends se ativa e visível."""
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("RiotWindowClass", None)
        if not hwnd:
            hwnd = user32.FindWindowW(None, "League of Legends (TM) Client")
        if not hwnd:
            try:
                hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
                if hdesk:
                    user32.SetThreadDesktop(hdesk)
                    hwnd = user32.FindWindowW("RiotWindowClass", None)
                    if not hwnd:
                        hwnd = user32.FindWindowW(None, "League of Legends (TM) Client")
            except Exception:
                pass
        if hwnd:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.05)
            if user32.IsWindowVisible(hwnd):
                return hwnd
        return None

    def _read_game_cfg(self):
        """Lê configurações de HUD e Minimapa do arquivo game.cfg se disponível."""
        cfg_paths = [
            r"C:\Riot Games\League of Legends\Config\game.cfg",
            r"D:\Riot Games\League of Legends\Config\game.cfg"
        ]
        cfg = {"flip_minimap": 0, "minimap_scale": 1.0}
        for path in cfg_paths:
            if os.path.exists(path):
                try:
                    mtime = os.path.getmtime(path)
                    if self.game_cfg_cache and mtime == self.game_cfg_mtime:
                        return self.game_cfg_cache
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("FlipMiniMap="):
                                cfg["flip_minimap"] = int(line.split("=")[1])
                            elif line.startswith("MinimapScale="):
                                cfg["minimap_scale"] = float(line.split("=")[1])
                    self.game_cfg_cache = cfg
                    self.game_cfg_mtime = mtime
                    return cfg
                except Exception as e:
                    log.debug(f"lolAccessibility: Erro ao ler game.cfg: {e}")
        return cfg

    def get_minimap_rect(self, hwnd):
        """
        Calcula as coordenadas de tela exatas do minimapa.
        Por padrão, localiza-se no canto inferior direito da janela.
        """
        user32 = ctypes.windll.user32
        rect = RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return None

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width < 640 or height < 480:
            return None

        pt = wintypes.POINT(rect.left, rect.top)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))

        cfg = self._read_game_cfg()
        flip = cfg.get("flip_minimap", 0)
        scale = cfg.get("minimap_scale", 1.0)
        scale = max(0.5, min(2.0, scale))

        # O minimapa clássico ocupa cerca de 26% da altura da tela na escala padrão (1.0)
        base_size = int(height * 0.26 * scale)
        base_size = max(180, min(500, base_size))

        if flip == 1:
            # Minimapa invertido no canto inferior esquerdo
            m_left = pt.x
            m_top = pt.y + height - base_size
        else:
            # Padrão: canto inferior direito
            m_left = pt.x + width - base_size
            m_top = pt.y + height - base_size

        return {
            "x": max(0, m_left),
            "y": max(0, m_top),
            "width": base_size,
            "height": base_size
        }

    @staticmethod
    def capture_minimap_pixels(m_rect):
        """
        Captura a região do minimapa via Win32 GDI BitBlt e retorna (width, height, bytes_bgra).
        Execução ultra-eficiente (< 3 ms).
        """
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        w = m_rect["width"]
        h = m_rect["height"]
        src_x = m_rect["x"]
        src_y = m_rect["y"]

        hdc_screen = user32.GetDC(0)
        if not hdc_screen:
            return None

        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        old_bm = gdi32.SelectObject(hdc_mem, hbm)

        SRCCOPY = 0x00CC0020
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, src_x, src_y, SRCCOPY)

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h  # top-down DIB
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0  # BI_RGB

        buf = (ctypes.c_ubyte * (w * h * 4))()
        gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(bmi), 0)

        # Limpeza
        gdi32.SelectObject(hdc_mem, old_bm)
        gdi32.DeleteObject(hbm)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        return w, h, buf

    @staticmethod
    def detect_markers(w, h, buf):
        """
        Executa rotulação de componentes conectados com passo 2 para localizar
        marcadores de campeões inimigos (vermelho) e aliados (azul) no buffer BGRA.
        Retorna lista de ícones detectados com coordenadas relativas (u, v) [0..1].
        """
        step = 2
        grid_w = w // step
        grid_h = h // step
        grid = bytearray(grid_w * grid_h)

        # Varredura rápida de pixels amostrados
        for gy in range(grid_h):
            y = gy * step
            row_idx = gy * grid_w
            pixel_row_offset = y * w * 4
            for gx in range(grid_w):
                x = gx * step
                offset = pixel_row_offset + (x * 4)
                b = buf[offset]
                g = buf[offset + 1]
                r = buf[offset + 2]

                # Marcador Inimigo: Vermelho dominante
                if r > 140 and r > (g * 1.55) and r > (b * 1.55) and (g + b) < 220:
                    grid[row_idx + gx] = 1
                # Marcador Aliado: Azul/Ciano dominante
                elif b > 140 and b > (r * 1.45) and g > 50 and (r + g) < 230:
                    grid[row_idx + gx] = 2

        # BFS para agrupar componentes conectados
        visited = bytearray(grid_w * grid_h)
        icons = []

        for gy in range(grid_h):
            row_idx = gy * grid_w
            for gx in range(grid_w):
                idx = row_idx + gx
                val = grid[idx]
                if val == 0 or visited[idx]:
                    continue

                queue = [(gx, gy)]
                visited[idx] = 1
                points = []

                while queue:
                    cx, cy = queue.pop()
                    points.append((cx, cy))
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < grid_w and 0 <= ny < grid_h:
                            nidx = ny * grid_w + nx
                            if not visited[nidx] and grid[nidx] == val:
                                visited[nidx] = 1
                                queue.append((nx, ny))

                # Amostras válidas para um ícone de campeão no minimapa
                if 5 <= len(points) <= 150:
                    avg_gx = sum(p[0] for p in points) / len(points)
                    avg_gy = sum(p[1] for p in points) / len(points)
                    u = (avg_gx * step) / w
                    v = (avg_gy * step) / h
                    icons.append({
                        "team": "enemy" if val == 1 else "ally",
                        "u": round(u, 3),
                        "v": round(v, 3),
                        "samples": len(points)
                    })

        return icons

    @staticmethod
    def detect_camera_viewport(w, h, buf):
        """
        Localiza o retângulo branco delimitador do viewport da câmera do jogador
        no minimapa. Retorna (cam_u, cam_v) correspondente ao centro do campo de visão.
        Caso não encontre retângulo nítido, retorna (0.5, 0.5).
        """
        step = 2
        min_x = w
        max_x = 0
        min_y = h
        max_y = 0
        found_pixels = 0

        # Amostragem rápida procurando borda branca do retângulo da câmera
        for y in range(0, h, step):
            row_offset = y * w * 4
            for x in range(0, w, step):
                offset = row_offset + (x * 4)
                b = buf[offset]
                g = buf[offset + 1]
                r = buf[offset + 2]
                # Linhas brancas/claras da caixa de câmera
                if r > 195 and g > 195 and b > 195 and abs(r - g) < 25 and abs(r - b) < 25:
                    found_pixels += 1
                    if x < min_x: min_x = x
                    if x > max_x: max_x = x
                    if y < min_y: min_y = y
                    if y > max_y: max_y = y

        box_w = max_x - min_x
        box_h = max_y - min_y

        # Valida se as dimensões correspondem a uma câmera de LoL (típico: 10% a 50% do minimapa)
        if found_pixels >= 15 and (0.10 * w) <= box_w <= (0.50 * w) and (0.08 * h) <= box_h <= (0.45 * h):
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
            return round(cx / float(w), 3), round(cy / float(h), 3)

        return 0.5, 0.5

    @staticmethod
    def calculate_spatial_targets(markers, cam_u=0.5, cam_v=0.5):
        """
        Calcula o vetor espacial relativo (dx, dy), panning estéreo (-1.0 a +1.0),
        distância euclidiana, frequência de pitch de áudio e direção de relógio (horas).
        """
        targets = []
        for m in markers:
            u = m.get("u", 0.5)
            v = m.get("v", 0.5)
            team = m.get("team", "enemy")

            dx = u - cam_u
            dy = v - cam_v

            # Panning estéreo: dx multiplicado por escala angular de percepção
            pan = max(-1.0, min(1.0, dx * 3.5))

            # Distância euclidiana normalizada no minimapa
            dist = math.sqrt(dx * dx + dy * dy)

            # Mapeamento de frequência por proximidade (mais próximo = mais agudo)
            if dist < 0.12:
                freq = 1350.0  # Muito perto / perigo iminente
                dist_desc = "muito perto"
            elif dist < 0.25:
                freq = 1000.0  # Próximo / na mesma rota ou rio adjacente
                dist_desc = "próximo"
            elif dist < 0.45:
                freq = 680.0   # Média distância
                dist_desc = "média distância"
            else:
                freq = 420.0   # Longe / outro lado do mapa
                dist_desc = "longe"

            # Direção polar em horas de relógio (12h à frente, 3h à direita, 6h atrás, 9h à esquerda)
            angle = math.atan2(dx, -dy)
            deg = (math.degrees(angle) + 360.0) % 360.0
            hour = int(round(deg / 30.0)) % 12
            hour = 12 if hour == 0 else hour

            # Descrição humana da direção
            if hour in (11, 12, 1):
                dir_desc = "à frente"
            elif hour in (2, 3, 4):
                dir_desc = "à direita"
            elif hour in (5, 6, 7):
                dir_desc = "atrás"
            else:
                dir_desc = "à esquerda"

            targets.append({
                "team": team,
                "u": u,
                "v": v,
                "dx": round(dx, 3),
                "dy": round(dy, 3),
                "pan": round(pan, 2),
                "dist": round(dist, 3),
                "freq": freq,
                "hour": hour,
                "dir_desc": dir_desc,
                "dist_desc": dist_desc
            })

        return targets

    @staticmethod
    def classify_zone(u, v, my_team="ORDER", is_aram=False):
        """
        Classifica as coordenadas relativas (u, v) [0..1] do minimapa em uma
        zona tática semântica do League of Legends.
        """
        # Se for modo ARAM / Howling Abyss
        if is_aram:
            if u <= 0.20 and v >= 0.80:
                return "Base Aliada" if my_team == "ORDER" else "Base Inimiga"
            elif u >= 0.80 and v <= 0.20:
                return "Base Inimiga" if my_team == "ORDER" else "Base Aliada"
            elif u <= 0.40 and v >= 0.60:
                return "Ponte (Recuado)"
            elif 0.40 <= u <= 0.60 and 0.40 <= v <= 0.60:
                return "Ponte (Centro)"
            else:
                return "Ponte (Avançado)"

        # Summoner's Rift
        # 1. Bases
        if u <= 0.22 and v >= 0.78:
            return "Base Aliada" if my_team == "ORDER" else "Base Inimiga"
        if u >= 0.78 and v <= 0.22:
            return "Base Inimiga" if my_team == "ORDER" else "Base Aliada"

        diag = u + v
        dist_from_diag = abs(diag - 1.0)

        # 2. Rota do Topo (borda superior-esquerda)
        if (u <= 0.20 and v < 0.78) or (v <= 0.20 and u < 0.78):
            if u <= 0.20 and v >= 0.48:
                return "Topo (Lado Azul)"
            elif v <= 0.20 and u >= 0.48:
                return "Topo (Lado Vermelho)"
            else:
                return "Topo (Extremo Superior)"

        # 3. Rota Inferior (borda inferior-direita)
        if (u >= 0.80 and v > 0.22) or (v >= 0.80 and u > 0.22):
            if v >= 0.80 and u <= 0.52:
                return "Rota Inferior (Lado Azul)"
            elif u >= 0.80 and v <= 0.52:
                return "Rota Inferior (Lado Vermelho)"
            else:
                return "Rota Inferior (Extremo Inferior)"

        # 4. Rota do Meio (diagonal)
        if dist_from_diag <= 0.16:
            if dist_from_diag <= 0.08 and 0.40 <= u <= 0.60:
                return "Meio (Rio / Centro)"
            elif diag < 1.0:
                return "Meio (Lado Azul)"
            else:
                return "Meio (Lado Vermelho)"

        # 5. Selvas e Rios
        if diag < 1.0:
            # Lado superior / Barão
            if 0.32 <= u <= 0.54 and 0.26 <= v <= 0.50:
                return "Rio Superior / Covil do Barão"
            elif u < 0.45:
                return "Selva Superior (Azul)"
            else:
                return "Selva Superior (Vermelha)"
        else:
            # Lado inferior / Dragão
            if 0.46 <= u <= 0.68 and 0.50 <= v <= 0.74:
                return "Rio Inferior / Covil do Dragão"
            elif v > 0.55:
                return "Selva Inferior (Azul)"
            else:
                return "Selva Inferior (Vermelha)"

    def scan_minimap(self, my_team="ORDER", is_aram=False):
        """
        Executa a captura da tela e classificação de marcadores no minimapa.
        Retorna dicionário estruturado com a contagem de inimigos e aliados por zona.
        """
        hwnd = self.find_league_game_window()
        if not hwnd:
            return None

        m_rect = self.get_minimap_rect(hwnd)
        if not m_rect:
            return None

        t0 = time.perf_counter()
        capture = self.capture_minimap_pixels(m_rect)
        if not capture:
            return None

        w, h, buf = capture
        icons = self.detect_markers(w, h, buf)
        elapsed = (time.perf_counter() - t0) * 1000.0

        # Mapeamento por zonas
        zones = collections.defaultdict(lambda: {"enemies": 0, "allies": 0})
        enemy_list = []
        ally_list = []

        for ic in icons:
            zone_name = self.classify_zone(ic["u"], ic["v"], my_team=my_team, is_aram=is_aram)
            ic["zone"] = zone_name
            if ic["team"] == "enemy":
                zones[zone_name]["enemies"] += 1
                enemy_list.append(ic)
            else:
                zones[zone_name]["allies"] += 1
                ally_list.append(ic)

        result = {
            "elapsed_ms": round(elapsed, 2),
            "total_enemies_spotted": len(enemy_list),
            "total_allies_spotted": len(ally_list),
            "zones": dict(zones),
            "enemies": enemy_list,
            "allies": ally_list,
            "timestamp": time.time()
        }
        return result

    def get_tactical_summary(self, live_data=None, my_team="ORDER", detailed=False):
        """
        Gera um relatório falado natural para o NVDA sobre a situação do minimapa.
        detailed=False: Resumo conciso de inimigos visíveis e desaparecidos.
        detailed=True: Detalhamento completo zona a zona.
        """
        # Checar se é ARAM
        is_aram = False
        if live_data:
            game_data = live_data.get("gameData", {})
            if "howling" in game_data.get("mapName", "").lower() or "aram" in game_data.get("gameMode", "").lower():
                is_aram = True

        scan = self.scan_minimap(my_team=my_team, is_aram=is_aram)
        if not scan:
            return "Minimapa não detectado na tela. Certifique-se de que a janela do jogo está visível."

        spotted_enemies = scan["total_enemies_spotted"]
        spotted_allies = scan["total_allies_spotted"]
        zones = scan["zones"]

        # Calcular inimigos vivos e MIA se live_data estiver disponível
        living_enemies = 5
        dead_enemies = 0
        if live_data:
            all_players = live_data.get("allPlayers", [])
            living_enemies = 0
            for p in all_players:
                p_team = p.get("team", "")
                if p_team != my_team:
                    if p.get("isDead", False):
                        dead_enemies += 1
                    else:
                        living_enemies += 1

        mia_count = max(0, living_enemies - spotted_enemies)

        # Construir agrupamentos principais
        # Agrupar zonas em 5 macro-regiões: Topo, Meio, Inferior, Selvas/Rios e Bases
        top_enemies = sum(z["enemies"] for name, z in zones.items() if "Topo" in name)
        mid_enemies = sum(z["enemies"] for name, z in zones.items() if "Meio" in name)
        bot_enemies = sum(z["enemies"] for name, z in zones.items() if "Inferior" in name)
        jungle_enemies = sum(z["enemies"] for name, z in zones.items() if "Selva" in name or "Rio" in name or "Barão" in name or "Dragão" in name)
        base_enemies = sum(z["enemies"] for name, z in zones.items() if "Base" in name)

        if not detailed:
            # Resumo rápido e direto para combate
            parts = []
            if is_aram:
                bridge_enemies = sum(z["enemies"] for name, z in zones.items() if "Ponte" in name)
                parts.append(f"{bridge_enemies} inimigos na ponte")
            else:
                if bot_enemies > 0:
                    parts.append(f"{bot_enemies} no Bot")
                if mid_enemies > 0:
                    parts.append(f"{mid_enemies} no Meio")
                if top_enemies > 0:
                    parts.append(f"{top_enemies} no Topo")
                if jungle_enemies > 0:
                    parts.append(f"{jungle_enemies} na Selva/Rio")
                if base_enemies > 0:
                    parts.append(f"{base_enemies} na Base")

            if parts:
                enemies_str = ", ".join(parts)
                summary = f"Minimapa: {spotted_enemies} inimigos visíveis: {enemies_str}."
            else:
                summary = "Minimapa: Nenhum inimigo avistado no momento."

            if mia_count > 0:
                summary += f" {mia_count} desaparecido{'s' if mia_count > 1 else ''} na névoa (MIA)."
            elif dead_enemies > 0:
                summary += f" {dead_enemies} morto{'s' if dead_enemies > 1 else ''}."

            return summary

        # Modo detalhado zona por zona
        detailed_parts = []
        if is_aram:
            for zone_key in ["Base Inimiga", "Ponte (Avançado)", "Ponte (Centro)", "Ponte (Recuado)", "Base Aliada"]:
                z = zones.get(zone_key, {"enemies": 0, "allies": 0})
                detailed_parts.append(f"{zone_key}: {z['enemies']} inimigos, {z['allies']} aliados")
        else:
            macro_sections = [
                ("Rota do Topo", top_enemies, sum(z["allies"] for name, z in zones.items() if "Topo" in name)),
                ("Selva e Barão", sum(z["enemies"] for name, z in zones.items() if "Barão" in name or "Superior" in name), sum(z["allies"] for name, z in zones.items() if "Barão" in name or "Superior" in name)),
                ("Rota do Meio", mid_enemies, sum(z["allies"] for name, z in zones.items() if "Meio" in name)),
                ("Selva e Dragão", sum(z["enemies"] for name, z in zones.items() if "Dragão" in name or "Inferior" in name and "Selva" in name), sum(z["allies"] for name, z in zones.items() if "Dragão" in name or "Inferior" in name and "Selva" in name)),
                ("Rota Inferior", bot_enemies, sum(z["allies"] for name, z in zones.items() if "Inferior" in name and "Rota" in name)),
            ]
            for name, e_cnt, a_cnt in macro_sections:
                if e_cnt == 0 and a_cnt == 0:
                    detailed_parts.append(f"{name}: Limpo")
                else:
                    detailed_parts.append(f"{name}: {e_cnt} inimigo{'s' if e_cnt != 1 else ''}, {a_cnt} aliado{'s' if a_cnt != 1 else ''}")

        detailed_str = ". ".join(detailed_parts)
        res = f"Análise detalhada do Minimapa: {detailed_str}."
        if mia_count > 0:
            res += f" {mia_count} inimigo{'s' if mia_count > 1 else ''} desaparecido{'s' if mia_count > 1 else ''} (MIA)."
        return res

    def check_gank_threat(self, player_lane="BOTTOM", live_data=None, my_team="ORDER"):
        """
        Verifica se há um aumento súbito ou presença de inimigos na rota do jogador
        ou nas selvas adjacentes (Alerta de Gank).
        Retorna mensagem de alerta se ameaça detectada, ou None.
        """
        now = time.time()
        if now - self.last_gank_alert_time < 8.0:
            # Intervalo mínimo de 8s entre alertas de gank para evitar repetição excessiva
            return None

        scan = self.scan_minimap(my_team=my_team)
        if not scan:
            return None

        zones = scan["zones"]
        player_lane_upper = (player_lane or "").upper()

        threat_count = 0
        threat_zone = ""

        if "BOT" in player_lane_upper:
            # Rota inferior ou Selva/Rio do Dragão
            threat_count = sum(z["enemies"] for name, z in zones.items() if "Inferior" in name or "Dragão" in name)
            threat_zone = "Rota Inferior"
            # Em bot normal já costuma ter 2 inimigos (ADC + Sup). Se tiver 3 ou mais, é gank iminente!
            if threat_count >= 3:
                self.last_gank_alert_time = now
                return f"Alerta de Gank! {threat_count} inimigos avistados na Rota Inferior!"
        elif "TOP" in player_lane_upper:
            # Rota do topo ou Selva/Rio do Barão
            threat_count = sum(z["enemies"] for name, z in zones.items() if "Topo" in name or "Barão" in name)
            threat_zone = "Rota do Topo"
            # No topo normal tem 1 inimigo. Se tiver 2 ou mais, é gank!
            if threat_count >= 2:
                self.last_gank_alert_time = now
                return f"Alerta de Gank! {threat_count} inimigos avistados no Topo!"
        elif "MID" in player_lane_upper or "MIDDLE" in player_lane_upper:
            # Meio normal tem 1 inimigo. Se tiver 2 ou mais, é gank!
            threat_count = sum(z["enemies"] for name, z in zones.items() if "Meio" in name)
            threat_zone = "Rota do Meio"
            if threat_count >= 2:
                self.last_gank_alert_time = now
                return f"Alerta de Gank! {threat_count} inimigos avistados no Meio!"

        return None

    def scan_radar(self, player_lane=None, my_team="ORDER", is_aram=False):
        """
        Executa uma varredura acústica completa do minimapa.
        Localiza os marcadores, detecta o viewport da câmera e calcula
        os alvos espaciais para o sintetizador estéreo.
        Retorna dicionário com alvos, contagem de ameaças e texto resumido.
        """
        hwnd = self.find_league_game_window()
        if not hwnd:
            return None

        rect = self.get_minimap_screen_rect(hwnd)
        if not rect:
            return None

        buf = self.capture_minimap_gdi(hwnd, rect)
        if not buf:
            return None

        w, h = rect["w"], rect["h"]
        markers = self.detect_markers(w, h, buf)
        cam_u, cam_v = self.detect_camera_viewport(w, h, buf)

        # Se o viewport da câmera não foi detectado (padrão 0.5, 0.5) e temos a rota do jogador,
        # posiciona uma estimativa da câmera próxima à rota
        if cam_u == 0.5 and cam_v == 0.5 and player_lane:
            pl_up = str(player_lane).upper()
            if "BOT" in pl_up:
                cam_u, cam_v = (0.75, 0.75) if my_team == "ORDER" else (0.85, 0.65)
            elif "TOP" in pl_up:
                cam_u, cam_v = (0.25, 0.25) if my_team == "ORDER" else (0.35, 0.15)
            elif "MID" in pl_up:
                cam_u, cam_v = (0.50, 0.50)

        targets = self.calculate_spatial_targets(markers, cam_u, cam_v)
        enemies = [t for t in targets if t["team"] == "enemy"]
        allies = [t for t in targets if t["team"] == "ally"]

        if not enemies:
            summary = "Radar limpo. Nenhum campeão inimigo visível no mapa."
        else:
            parts = []
            enemies_by_dist = sorted(enemies, key=lambda e: e["dist"])
            for e in enemies_by_dist:
                parts.append(f"Inimigo às {e['hour']} horas ({e['dir_desc']}), {e['dist_desc']}")
            summary = f"Radar: {len(enemies)} inimigo{'s' if len(enemies) > 1 else ''} visíveis. " + "; ".join(parts) + "."

        return {
            "cam_u": cam_u,
            "cam_v": cam_v,
            "targets": targets,
            "enemies": enemies,
            "allies": allies,
            "text": summary
        }
