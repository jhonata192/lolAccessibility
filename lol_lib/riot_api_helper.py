# -*- coding: utf-8 -*-
"""
Helper para comunicação com as três camadas de API da Riot Games:
1. Live Client Data API (https://127.0.0.1:2999) - Dados em tempo real durante a partida (Oficial).
2. League Client API (LCU) - Interface pré e pós jogo via lockfile (Lobby, Fila, Champ Select).
3. Riot Client API - Launcher, downloads e autenticação via lockfile.
4. Riot Web API (RGAPI) - Dados remotos e histórico via Developer Portal (Opcional).

Totalmente compatível com o Riot Vanguard, sem injeção de memória, 100% seguro.
"""

import os
import ssl
import base64
import json
import urllib.request
import urllib.error
import time
import re
import unicodedata

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("lolAccessibility")

_ssl_context = None

def get_ssl_context():
    global _ssl_context
    if _ssl_context is None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        _ssl_context = ctx
    return _ssl_context


def is_pid_alive(pid):
    """Verifica se um processo com o PID fornecido está ativo no sistema."""
    if not pid or pid <= 0:
        return False
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        kernel32.CloseHandle(handle)
        return exit_code.value == 259
    except Exception:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def read_lockfile(path, check_alive=True):
    """Lê e analisa um arquivo de bloqueio da Riot no formato: nome:pid:porta:token:protocolo"""
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        parts = content.split(":")
        if len(parts) >= 5:
            pid = int(parts[1])
            if check_alive and not is_pid_alive(pid):
                log.debug(f"lolAccessibility: Lockfile {path} contém PID inativo ({pid}). Ignorando lockfile obsoleto.")
                try:
                    os.remove(path)
                except Exception:
                    pass
                return None
            return {
                "process": parts[0],
                "pid": pid,
                "port": int(parts[2]),
                "token": parts[3],
                "protocol": parts[4]
            }
    except Exception as e:
        log.debug(f"lolAccessibility: Erro ao ler lockfile {path}: {e}")
    return None


def get_riot_client_lockfile():
    """
    Localiza e lê dinamicamente o lockfile ativo do Riot Client em qualquer computador.
    Totalmente dinâmico, sem caminhos absolutos ou nomes de usuário fixos.
    """
    candidates = []
    
    # 1. Variáveis de ambiente do usuário atual (%LOCALAPPDATA% e %USERPROFILE%)
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.append(os.path.join(local_app_data, "Riot Games", "Riot Client", "Config", "lockfile"))
        
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        candidates.append(os.path.join(user_profile, "AppData", "Local", "Riot Games", "Riot Client", "Config", "lockfile"))
        
    # 2. Metadados globais da máquina (%PROGRAMDATA%)
    program_data = os.environ.get("PROGRAMDATA", "")
    if program_data:
        candidates.append(os.path.join(program_data, "Riot Games", "Metadata", "Riot Client", "lockfile"))
        
    # 3. Caso o NVDA execute em outra conta de serviço, vasculha as pastas de usuários de forma dinâmica
    system_drive = os.environ.get("SystemDrive", "C:")
    users_root = os.path.join(system_drive, os.sep, "Users")
    if os.path.isdir(users_root):
        try:
            for user_name in os.listdir(users_root):
                user_folder = os.path.join(users_root, user_name)
                if os.path.isdir(user_folder) and not user_name.lower().startswith(("public", "default", "all users")):
                    candidates.append(os.path.join(user_folder, "AppData", "Local", "Riot Games", "Riot Client", "Config", "lockfile"))
        except Exception:
            pass

    for c in candidates:
        if c and os.path.isfile(c):
            info = read_lockfile(c)
            if info:
                return info
    return None


def get_league_client_lockfile():
    """
    Localiza e lê dinamicamente o lockfile ativo do League of Legends em qualquer computador.
    Verifica metadados de instalação da Riot, Registro do Windows e unidades disponíveis.
    Zero dependência de caminhos ou pastas fixas.
    """
    candidates = []
    
    # 1. Localizar pasta de instalação real através dos metadados da Riot (%PROGRAMDATA%)
    program_data = os.environ.get("PROGRAMDATA", "")
    if program_data:
        yaml_path = os.path.join(program_data, "Riot Games", "Metadata", "league_of_legends.live", "league_of_legends.live.product_settings.yaml")
        if os.path.isfile(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "product_install_full_path" in line:
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                install_dir = parts[1].strip().strip('"').strip("'")
                                if install_dir:
                                    candidates.append(os.path.join(install_dir, "lockfile"))
            except Exception:
                pass

    # 2. Consultar o Registro do Windows onde o LoL foi instalado
    try:
        import winreg
        for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for sub_key in (
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall\League of Legends",
                r"Software\Riot Games\League of Legends",
            ):
                try:
                    with winreg.OpenKey(root_key, sub_key) as k:
                        val, _ = winreg.QueryValueEx(k, "InstallLocation")
                        if val:
                            candidates.append(os.path.join(val, "lockfile"))
                except Exception:
                    pass
    except Exception:
        pass

    # 3. Varrer automaticamente as unidades ativas da máquina (C:, D:, E:...)
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            candidates.append(os.path.join(drive, "Riot Games", "League of Legends", "lockfile"))
            candidates.append(os.path.join(drive, "Games", "League of Legends", "lockfile"))
            candidates.append(os.path.join(drive, "Program Files", "Riot Games", "League of Legends", "lockfile"))

    for c in candidates:
        if c and os.path.isfile(c):
            info = read_lockfile(c)
            if info:
                return info
    return None


def request_api(lockfile_info, endpoint, method="GET", body=None, timeout=1.5):
    """Executa uma requisição HTTP autenticada contra a API local (LCU ou Riot Client)."""
    if not lockfile_info:
        return None
    
    port = lockfile_info["port"]
    token = lockfile_info["token"]
    protocol = lockfile_info.get("protocol", "https")
    
    url = f"{protocol}://127.0.0.1:{port}{endpoint}"
    auth = base64.b64encode(f"riot:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = get_ssl_context()
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            if content:
                try:
                    return json.loads(content)
                except Exception:
                    return content
            return True
    except urllib.error.HTTPError as e:
        log.debug(f"lolAccessibility: HTTP {e.code} para {endpoint}")
        return None
    except Exception as e:
        log.debug(f"lolAccessibility: Erro na requisição para {endpoint}: {e}")
        return None


# ============================================================================
# CAMADA 1: LIVE CLIENT DATA API (DURANTE A PARTIDA - 127.0.0.1:2999)
# ============================================================================

LIVE_API_BASE = "https://127.0.0.1:2999/liveclientdata"

def request_live_api(endpoint, timeout=0.6):
    """Faz requisição rápida para a Live Client Data API (porta 2999)."""
    url = f"{LIVE_API_BASE}{endpoint}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            if content:
                return json.loads(content)
            return None
    except Exception:
        return None


def is_live_game_active():
    """Retorna True se uma partida estiver em andamento no cliente 3D."""
    stats = request_live_api("/gamestats", timeout=0.3)
    return stats is not None and isinstance(stats, dict) and "gameTime" in stats


def get_live_allgamedata():
    """Retorna todos os dados da partida em andamento (jogadores, eventos, stats)."""
    return request_live_api("/allgamedata")


def get_live_active_player():
    """Retorna dados completos do jogador local (vida, mana, stats, nível, ouro, campeão, time, scores, itens)."""
    data = request_live_api("/activeplayer")
    if not data or not isinstance(data, dict):
        return data
    try:
        players = request_live_api("/playerlist")
        if players and isinstance(players, list):
            my_summoner = (data.get("summonerName") or data.get("riotId") or "").lower()
            my_game_name = (data.get("riotIdGameName") or "").lower()
            for p in players:
                p_sum = (p.get("summonerName") or p.get("riotId") or "").lower()
                p_gn = (p.get("riotIdGameName") or "").lower()
                if (my_summoner and (p_sum == my_summoner or my_summoner in p_sum or p_sum in my_summoner)) or \
                   (my_game_name and (p_gn == my_game_name or my_game_name in p_gn)):
                    for k in ("championName", "team", "scores", "items", "summonerSpells", "isDead", "respawnTimer"):
                        if k in p and k not in data:
                            data[k] = p[k]
                    break
    except Exception:
        pass
    return data


def get_live_active_player_abilities():
    """Retorna habilidades (Q, W, E, R, Passiva), níveis e recargas."""
    return request_live_api("/activeplayerabilities")


def get_live_player_list():
    """Retorna lista de todos os 10 jogadores (campeão, time, vivo/morto, itens, feitiços)."""
    return request_live_api("/playerlist")


def get_live_event_data():
    """Retorna histórico de eventos da partida (abates, dragões, barão, torres, ace)."""
    return request_live_api("/eventdata")


def get_live_game_stats():
    """Retorna estatísticas da partida (tempo de jogo, modo, mapa)."""
    return request_live_api("/gamestats")


# ============================================================================
# ARQUÉTIPOS E DEDUÇÃO INTELIGENTE DE ROTAS DOS INIMIGOS
# ============================================================================

ROLE_MARKSMEN = {
    'ashe', 'caitlyn', 'jinx', 'ezreal', 'kaisa', 'vayne', 'jhin', 'lucian',
    'missfortune', 'samira', 'sivir', 'tristana', 'varus', 'xayah', 'aphelios',
    'draven', 'twitch', 'kogmaw', 'kalista', 'zeri', 'nilah', 'smolder'
}

ROLE_TOP_LANERS = {
    'aatrox', 'camille', 'chogath', 'darius', 'drmundo', 'fiora', 'gangplank',
    'garen', 'gnar', 'gwen', 'illaoi', 'irelia', 'jax', 'jayce', 'kayle',
    'kennen', 'kled', 'ksante', 'malphite', 'mordekaiser', 'nasus', 'olaf',
    'ornn', 'poppy', 'quinn', 'renekton', 'riven', 'rumble', 'sett', 'shen',
    'singed', 'sion', 'tahmkench', 'teemo', 'trundle', 'urgot', 'volibear', 'warwick', 'yorick'
}

ROLE_MID_LANERS = {
    'ahri', 'akali', 'anivia', 'annie', 'aurelionsol', 'azir', 'cassiopeia',
    'corki', 'fizz', 'galio', 'hwei', 'kassadin', 'katarina', 'leblanc',
    'lissandra', 'lux', 'malzahar', 'naafiri', 'neeko', 'orianna', 'qiyana',
    'ryze', 'swain', 'sylas', 'syndra', 'taliyah', 'talon', 'twistedfate',
    'veigar', 'vex', 'viktor', 'vladimir', 'yasuo', 'yone', 'zed', 'zoe'
}

ROLE_SUPPORTS = {
    'blitzcrank', 'nautilus', 'thresh', 'leona', 'braum', 'alistar', 'taric',
    'rell', 'pyke', 'lulu', 'nami', 'janna', 'sona', 'soraka', 'yuumi',
    'milio', 'rakan', 'bard', 'renataglasc', 'senna', 'zyra', 'brand',
    'xerath', 'velkoz', 'morgana', 'karma', 'zilean'
}


def get_live_enemy_lane_assignments():
    """
    Deduz de forma inteligente a distribuição de rotas dos inimigos (Top, Jungle, Mid, Bot e Sup).
    Analisa feitiços de invocador (Smite/Golpear), itens iniciais (Atlas de Suporte, Doran, Pet da Selva)
    e arquétipos dos campeões oficiais.
    """
    if not is_live_game_active():
        return None

    stats = get_live_game_stats() or {}
    game_mode = (stats.get("gameMode") or "").upper()
    map_id = stats.get("mapId", 0)

    players = get_live_player_list()
    active_player = get_live_active_player()
    if not players or not isinstance(players, list) or not active_player:
        return None

    active_name = active_player.get("summonerName", "")
    my_team = None
    for p in players:
        if p.get("summonerName") == active_name:
            my_team = p.get("team")
            break
    if not my_team:
        my_team = active_player.get("team", "ORDER")

    enemies = [p for p in players if p.get("team") != my_team]
    if not enemies:
        return None

    # Se for ARAM ou Howling Abyss, rota única
    if game_mode in ("ARAM", "HOWLING_ABYSS") or map_id == 12:
        c_names = [e.get("championName", "Inimigo") for e in enemies]
        spells_list = []
        for p in enemies:
            cn = p.get("championName", "Inimigo")
            sp = p.get("summonerSpells", {})
            s1 = sp.get("summonerSpellOne", {}).get("displayName", "Feitiço 1")
            s2 = sp.get("summonerSpellTwo", {}).get("displayName", "Feitiço 2")
            spells_list.append(f"{cn} ({s1} e {s2})")
        return {
            "mode": "ARAM",
            "is_single_lane": True,
            "text": f"Modo ARAM: Rota única. Inimigos: {', '.join(c_names)}.",
            "enemies": c_names,
            "spells_summary": "Feitiços dos inimigos: " + ", ".join(spells_list) + "."
        }


    # Summoner's Rift (5v5 Clássico)
    assigned = {
        "TOP": None,
        "JUNGLE": None,
        "MIDDLE": None,
        "BOTTOM": None,
        "UTILITY": None
    }
    enemy_spells_summary = []
    unassigned = list(enemies)

    # 1. Caçador (Jungle): Smite / Golpear ou item de selva
    for p in list(unassigned):
        cname = p.get("championName", "")
        sp_data = p.get("summonerSpells", {})
        s1 = sp_data.get("summonerSpellOne", {}).get("displayName", "")
        s2 = sp_data.get("summonerSpellTwo", {}).get("displayName", "")
        spells_norm = [normalize_text(s1), normalize_text(s2)]
        items = [normalize_text(it.get("displayName", "")) for it in p.get("items", [])]
        
        has_smite = any("smite" in s or "golpear" in s for s in spells_norm)
        has_jungle_item = any(k in it for it in items for k in ("brotinho", "jungle", "hatchling", "seedling", "pup"))
        if has_smite or has_jungle_item:
            assigned["JUNGLE"] = cname
            unassigned.remove(p)
            break

    # 2. Suporte (Support): Item inicial de suporte
    for p in list(unassigned):
        cname = p.get("championName", "")
        items = [normalize_text(it.get("displayName", "")) for it in p.get("items", [])]
        has_sup_item = any(k in it for it in items for k in (
            "atlas", "relic", "spellthief", "shoulderguards", "sickle",
            "suporte", "relicario", "foz", "gume", "solsticio", "cancao",
            "criassolhos", "sonho", "compass"
        ))
        if has_sup_item:
            assigned["UTILITY"] = cname
            unassigned.remove(p)
            break

    # Se suporte ainda não foi achado por item, procurar por campeão clássico de suporte
    if not assigned["UTILITY"]:
        for p in list(unassigned):
            cn = normalize_text(p.get("championName", ""))
            if cn in ROLE_SUPPORTS:
                assigned["UTILITY"] = p.get("championName", "")
                unassigned.remove(p)
                break

    # 3. Atirador (ADC / Bot)
    for p in list(unassigned):
        cn = normalize_text(p.get("championName", ""))
        if cn in ROLE_MARKSMEN:
            assigned["BOTTOM"] = p.get("championName", "")
            unassigned.remove(p)
            break

    # 4. Topo (Top)
    for p in list(unassigned):
        cn = normalize_text(p.get("championName", ""))
        if cn in ROLE_TOP_LANERS:
            assigned["TOP"] = p.get("championName", "")
            unassigned.remove(p)
            break

    # 5. Meio (Mid)
    for p in list(unassigned):
        cn = normalize_text(p.get("championName", ""))
        if cn in ROLE_MID_LANERS:
            assigned["MIDDLE"] = p.get("championName", "")
            unassigned.remove(p)
            break

    # 6. Preencher vagas restantes com jogadores que sobraram (flex picks)
    empty_slots = [k for k, v in assigned.items() if v is None]
    for slot in empty_slots:
        if unassigned:
            p = unassigned.pop(0)
            assigned[slot] = p.get("championName", "")

    # Montar resumo de feitiços de cada inimigo
    for p in enemies:
        cname = p.get("championName", "Inimigo")
        sp_data = p.get("summonerSpells", {})
        s1 = sp_data.get("summonerSpellOne", {}).get("displayName", "Feitiço 1")
        s2 = sp_data.get("summonerSpellTwo", {}).get("displayName", "Feitiço 2")
        enemy_spells_summary.append(f"{cname} ({s1} e {s2})")

    top_c = assigned.get("TOP") or "Desconhecido"
    jg_c = assigned.get("JUNGLE") or "Desconhecido"
    mid_c = assigned.get("MIDDLE") or "Desconhecido"
    adc_c = assigned.get("BOTTOM") or "Desconhecido"
    sup_c = assigned.get("UTILITY") or "Desconhecido"

    text = f"Inimigos por rota: Topo: {top_c}. Selva: {jg_c} (Caçador). Meio: {mid_c}. Rota Inferior: {adc_c} e {sup_c} (Suporte)."

    return {
        "mode": "CLASSIC",
        "is_single_lane": False,
        "assigned": assigned,
        "text": text,
        "spells_summary": "Feitiços dos inimigos: " + ", ".join(enemy_spells_summary) + "."
    }


def parse_turret_name(raw_name):
    """
    Traduz identificadores de torres (ex: Turret_T1_L_03_A, Turret_T2_C_02_A) para nomes acessíveis em português.
    """
    if not raw_name or not isinstance(raw_name, str):
        return "Torre"
    name = raw_name.upper()
    lane = ""
    if "_L_" in name or "TOP" in name:
        lane = "do Topo"
    elif "_C_" in name or "MID" in name:
        lane = "do Meio"
    elif "_R_" in name or "BOT" in name:
        lane = "da Rota Inferior"

    tier = ""
    if "_03_" in name:
        tier = "Externa"
    elif "_02_" in name:
        tier = "Interna"
    elif "_01_" in name:
        tier = "do Inibidor"
    elif "NEXUS" in name:
        tier = "do Nexus"

    team = ""
    if "T1" in name or "ORDER" in name or "BLUE" in name:
        team = "(Time Azul)"
    elif "T2" in name or "CHAOS" in name or "RED" in name:
        team = "(Time Vermelho)"

    parts = [p for p in ["Torre", tier, lane, team] if p]
    res = " ".join(parts).strip()
    return res if res != "Torre" else "Torre"


def parse_inhib_name(raw_name):
    """
    Traduz identificadores de inibidores (ex: Barracks_T1_L1) para nomes em português.
    """
    if not raw_name or not isinstance(raw_name, str):
        return "Inibidor"
    name = raw_name.upper()
    lane = ""
    if "_L" in name or "TOP" in name:
        lane = "do Topo"
    elif "_C" in name or "MID" in name:
        lane = "do Meio"
    elif "_R" in name or "BOT" in name:
        lane = "da Rota Inferior"

    team = ""
    if "T1" in name or "ORDER" in name:
        team = "(Time Azul)"
    elif "T2" in name or "CHAOS" in name:
        team = "(Time Vermelho)"

    parts = [p for p in ["Inibidor", lane, team] if p]
    res = " ".join(parts).strip()
    return res if res != "Inibidor" else "Inibidor"


def format_live_game_event(ev, my_team=None):
    """
    Traduz eventos da Live Client Data API para anúncios sonoros e por voz acessíveis.
    Retorna uma tupla (sound_type, announcement_text).
    """
    if not ev or not isinstance(ev, dict):
        return None, ""

    ename = ev.get("EventName", "")

    if ename == "ChampionKill":
        killer = ev.get("KillerName", "Alguém")
        victim = ev.get("VictimName", "Inimigo")
        assisters = ev.get("Assisters", [])
        asst_txt = f" com assistência de {', '.join(assisters)}" if assisters else ""
        return "KILL", f"Abate: {killer} eliminou {victim}{asst_txt}!"

    elif ename == "Multikill":
        streak = ev.get("KillStreak", 2)
        killer = ev.get("KillerName", "Jogador")
        names = {2: "Double Kill!", 3: "Triple Kill!", 4: "Quadra Kill!", 5: "Penta Kill!"}
        kname = names.get(streak, f"Sequência de {streak} abates!")
        return "MULTIKILL", f"{killer} fez {kname}"

    elif ename == "FirstBlood":
        rec = ev.get("Recipient", "Alguém")
        return "FIRST_BLOOD", f"Primeiro Abate da partida para {rec}!"

    elif ename == "FirstBrick":
        killer = ev.get("KillerName", "Alguém")
        return "FIRST_BRICK", f"Primeira Torre da partida destruída por {killer}!"

    elif ename == "HeraldKill":
        killer = ev.get("KillerName", "Alguém")
        return "HERALD", f"Arauto do Vale abatido por {killer}!"

    elif ename == "DragonKill":
        dragon = ev.get("DragonType", "")
        killer = ev.get("KillerName", "Alguém")
        dname = f"Dragão {dragon}" if dragon else "Dragão"
        return "DRAGON", f"{dname} abatido por {killer}!"

    elif ename == "BaronKill":
        killer = ev.get("KillerName", "Alguém")
        return "BARON", f"Barão Na'Shor abatido por {killer}!"

    elif ename == "TurretKilled":
        raw_turret = ev.get("TurretKilled", "")
        killer = ev.get("KillerName", "Alguém")
        turret_desc = parse_turret_name(raw_turret)
        return "TURRET", f"{turret_desc} destruída por {killer}!"

    elif ename == "InhibKilled":
        raw_inhib = ev.get("InhibKilled", "")
        killer = ev.get("KillerName", "Alguém")
        inhib_desc = parse_inhib_name(raw_inhib)
        return "INHIB", f"{inhib_desc} destruído por {killer}!"

    elif ename == "Ace":
        acing = ev.get("AcingTeam", "")
        if acing:
            acing_pt = "Time Azul" if "ORDER" in acing.upper() else "Time Vermelho"
            return "ACE", f"Ás! O {acing_pt} eliminou todos os inimigos!"
        return "ACE", "Ás! Time adversário eliminado!"

    elif ename == "MinionsSpawning":
        return "MINIONS", "Tropas liberadas da base!"

    return None, ""


# ============================================================================
# CAMADA 2: LEAGUE CLIENT API (LCU - PRÉ/PÓS JOGO)
# ============================================================================


def get_lcu_gameflow_phase():
    """Retorna a fase do fluxo do LoL (Lobby, Matchmaking, ReadyCheck, ChampSelect, InProgress)."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    phase = request_api(lock, "/lol-gameflow/v1/gameflow-phase")
    return phase if isinstance(phase, str) else None


def get_lcu_ready_check():
    """Verifica se há um Ready Check (partida encontrada) ativo."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    return request_api(lock, "/lol-matchmaking/v1/ready-check")


def accept_lcu_match():
    """Aceita a partida encontrada (Ready Check) via API oficial LCU."""
    lock = get_league_client_lockfile()
    if not lock:
        return False
    res = request_api(lock, "/lol-matchmaking/v1/ready-check/accept", method="POST")
    return res is not None


def get_lcu_champ_select():
    """Retorna os dados detalhados da sessão de seleção de campeões."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    return request_api(lock, "/lol-champ-select/v1/session")


# ============================================================================
# TABELAS E MAPEAMENTOS DE CAMPEÕES, FEITIÇOS, RUNAS E SAGUÃO
# ============================================================================

SUMMONER_SPELL_NAMES = {
    1: "Purificar",
    3: "Exaustão",
    4: "Flash",
    6: "Fantasma",
    7: "Curar",
    11: "Golpear",
    12: "Teleporte",
    13: "Clareza",
    14: "Incendiar",
    21: "Barreira",
    32: "Marca",
    39: "Marca",
}

PERK_STYLE_NAMES = {
    8000: "Precisão",
    8100: "Dominação",
    8200: "Feitiçaria",
    8300: "Inspiração",
    8400: "Determinação",
}

POSITION_TRANSLATIONS = {
    "TOP": "Topo",
    "JUNGLE": "Selva",
    "MIDDLE": "Meio",
    "BOTTOM": "Atirador",
    "UTILITY": "Suporte",
    "FILL": "Preencher",
    "UNSELECTED": "Não selecionado",
}

ROLE_TRANSLATIONS = {
    "marksman": "Atirador",
    "fighter": "Lutador",
    "tank": "Tanque",
    "mage": "Mago",
    "assassin": "Assassino",
    "support": "Suporte",
}

def format_champion_display_name(champion_dict):
    """Retorna o nome do campeão formatado com suas classes em português (ex: Malphite (Tanque, Mago))."""
    if not champion_dict or not isinstance(champion_dict, dict):
        return ""
    name = champion_dict.get("name", "")
    roles = champion_dict.get("roles", [])
    if roles:
        roles_pt = [ROLE_TRANSLATIONS.get(r.lower(), r) for r in roles]
        return f"{name} ({', '.join(roles_pt)})"
    return name

CHAMPION_ALIASES = {
    "tf": "Twisted Fate",
    "mf": "Miss Fortune",
    "asol": "Aurelion Sol",
    "yi": "Master Yi",
    "mundo": "Dr. Mundo",
    "drmundo": "Dr. Mundo",
    "nunu": "Nunu e Willump",
    "willump": "Nunu e Willump",
    "jarvan": "Jarvan IV",
    "j4": "Jarvan IV",
    "renata": "Renata Glasc",
    "cait": "Caitlyn",
    "caitlyn": "Caitlyn",
    "kha": "Kha'Zix",
    "khazix": "Kha'Zix",
    "kog": "Kog'Maw",
    "kogmaw": "Kog'Maw",
    "kata": "Katarina",
    "cassio": "Cassiopeia",
    "noc": "Nocturne",
    "fiddle": "Fiddlesticks",
    "tahm": "Tahm Kench",
    "kench": "Tahm Kench",
    "chogath": "Cho'Gath",
    "cho": "Cho'Gath",
    "velkoz": "Vel'Koz",
    "vel": "Vel'Koz",
    "kaisa": "Kai'Sa",
    "reksai": "Rek'Sai",
    "belveth": "Bel'Veth",
    "ksante": "K'Sante",
    "wukong": "Wukong",
    "monkeyking": "Wukong",
    "blitz": "Blitzcrank",
    "morg": "Morgana",
    "trist": "Tristana",
    "trynd": "Tryndamere",
    "vlad": "Vladimir",
    "xin": "Xin Zhao",
    "gp": "Gangplank",
    "heimer": "Heimerdinger",
    "malph": "Malphite",
    "mali": "Malphite",
    "malfite": "Malphite",
    "garem": "Garen",
    "gar": "Garen",
    "ashr": "Ashe",
    "ash": "Ashe",
    "timo": "Teemo",
    "temo": "Teemo",
    "morde": "Mordekaiser",
    "caitlin": "Caitlyn",
    "tris": "Tristana",
    "panth": "Pantheon",
    "panteon": "Pantheon",
    "ramus": "Rammus",
    "eve": "Evelynn",
    "ez": "Ezreal",
}

_champions_cache = None
_champions_cache_time = 0

def normalize_text(text):
    """Remove acentos, caracteres especiais e converte para minúsculas."""
    if not text:
        return ""
    t = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-zA-Z0-9]', '', t.lower())


def get_lcu_all_champions():
    """Retorna lista de todos os campeões com ID, nome oficial, funções e disponibilidade."""
    global _champions_cache, _champions_cache_time
    now = time.time()
    if _champions_cache and (now - _champions_cache_time) < 60.0:
        return _champions_cache
    
    lock = get_league_client_lockfile()
    if not lock:
        return _champions_cache or []
        
    raw = request_api(lock, "/lol-champ-select/v1/all-grid-champions")
    if not raw or not isinstance(raw, list):
        raw = request_api(lock, "/lol-game-data/assets/v1/champions.json")
        
    if raw and isinstance(raw, list):
        champs = []
        for c in raw:
            cid = c.get("id", -1)
            name = (c.get("name") or "").strip()
            if cid > 0 and name and name.lower() != "nenhum":
                owned = bool(c.get("owned", False))
                ftp = bool(c.get("freeToPlay", False) or c.get("freeToPlayForQueue", False))
                rented = bool(c.get("rented", False))
                loyalty = bool(c.get("loyaltyReward", False))
                is_available = owned or ftp or rented or loyalty
                champs.append({
                    "id": cid,
                    "name": name,
                    "roles": c.get("roles", []),
                    "disabled": bool(c.get("disabled", False)),
                    "owned": owned,
                    "freeToPlay": ftp,
                    "rented": rented,
                    "is_available": is_available,
                    "selectionStatus": c.get("selectionStatus", {})
                })
        if champs:
            _champions_cache = champs
            _champions_cache_time = now
            return champs
            
    return _champions_cache or []


def get_lcu_available_champions(is_ban=False):
    """Retorna apenas os campeões disponíveis para escolha (ou todos válidos para banimento)."""
    champs = get_lcu_all_champions()
    if not champs:
        return []
    if is_ban:
        return [c for c in champs if not c.get("disabled")]
    return [c for c in champs if not c.get("disabled") and c.get("is_available")]


def find_champion_by_name(query, champs_list=None):
    """Localiza o melhor campeão correspondente à busca do usuário, com suporte a sinônimos e correção de digitação."""
    if not query:
        return None
    champs = champs_list if champs_list is not None else get_lcu_all_champions()
    if not champs:
        return None
        
    qn = normalize_text(query)
    target = CHAMPION_ALIASES.get(qn, qn)
    target_norm = normalize_text(target)
    
    # 1. Correspondência exata
    for c in champs:
        if normalize_text(c["name"]) == target_norm:
            return c
            
    # 2. Prefixo (começa com)
    for c in champs:
        if normalize_text(c["name"]).startswith(target_norm):
            return c
            
    # 3. Substring (contém)
    for c in champs:
        if target_norm in normalize_text(c["name"]):
            return c

    # 4. Busca aproximada por similaridade (correção de digitação como 'garem' -> 'garen')
    import difflib
    names_map = {normalize_text(c["name"]): c for c in champs}
    close = difflib.get_close_matches(target_norm, names_map.keys(), n=1, cutoff=0.55)
    if close:
        return names_map[close[0]]
            
    return None


def get_lcu_champ_select_detailed():
    """Retorna dados detalhados e estruturados da sessão de seleção de campeões."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
        
    session = request_api(lock, "/lol-champ-select/v1/session")
    if not session or not isinstance(session, dict):
        return None
        
    champs_map = {c["id"]: c["name"] for c in get_lcu_all_champions()}
    local_cell = session.get("localPlayerCellId", -1)
    
    # Identificar timer
    timer_data = session.get("timer", {})
    phase = timer_data.get("phase", "BAN_PICK")
    time_left_ms = timer_data.get("adjustedTimeLeftInPhase", 0)
    time_left_sec = max(0, int(time_left_ms / 1000))
    
    # Identificar ações
    actions = session.get("actions", [])
    local_action = None
    all_actions = []
    for group in actions:
        if isinstance(group, list):
            for act in group:
                all_actions.append(act)
                if act.get("actorCellId") == local_cell and not act.get("completed"):
                    if local_action is None or act.get("isActorActive") or act.get("isInProgress"):
                        local_action = act

    # Identificar time aliado
    my_team = []
    my_info = {}
    for m in session.get("myTeam", []):
        cell_id = m.get("cellId")
        cid = m.get("championId", 0)
        cname = champs_map.get(cid, "Não selecionado" if cid == 0 else f"Campeão {cid}")
        pos = (m.get("assignedPosition") or "").upper()
        pos_pt = POSITION_TRANSLATIONS.get(pos, pos)
        spells = [SUMMONER_SPELL_NAMES.get(m.get("spell1Id"), "Feitiço 1"), SUMMONER_SPELL_NAMES.get(m.get("spell2Id"), "Feitiço 2")]
        entry = {
            "cell_id": cell_id,
            "champion_id": cid,
            "champion_name": cname,
            "position": pos,
            "position_pt": pos_pt,
            "spells": spells,
            "is_me": (cell_id == local_cell)
        }
        my_team.append(entry)
        if cell_id == local_cell:
            my_info = entry

    # Identificar banco de reservas do ARAM
    bench = []
    for b in session.get("benchChampions", []):
        cid = b.get("championId")
        if cid:
            bench.append({"id": cid, "name": champs_map.get(cid, f"Campeão {cid}")})

    return {
        "raw_session": session,
        "phase": phase,
        "time_left_sec": time_left_sec,
        "local_cell": local_cell,
        "local_action": local_action,
        "my_info": my_info,
        "my_team": my_team,
        "bench": bench,
        "bench_enabled": session.get("benchEnabled", False),
        "rerolls_remaining": session.get("rerollsRemaining", 0),
    }


def pick_or_ban_champion(champ_name_or_id, is_ban=False, lock_in=True):
    """
    Executa a escolha (pick) ou banimento (ban) do campeão e trava (lock-in).
    Ao travar um pick, importa automaticamente runas e feitiços recomendados.
    """
    lock = get_league_client_lockfile()
    if not lock:
        return False, "Cliente do League of Legends não detectado.", ""
        
    session = request_api(lock, "/lol-champ-select/v1/session")
    if not session or not isinstance(session, dict):
        return False, "Seleção de campeões não está ativa.", ""

    champ_info = None
    if isinstance(champ_name_or_id, int):
        for c in get_lcu_all_champions():
            if c["id"] == champ_name_or_id:
                champ_info = c
                break
    else:
        champ_info = find_champion_by_name(champ_name_or_id)

    if not champ_info:
        return False, f"Campeão '{champ_name_or_id}' não encontrado.", ""

    champ_id = champ_info["id"]
    champ_name = champ_info["name"]

    # Validação de disponibilidade real na conta (se for escolha/pick)
    if not is_ban:
        is_avail = champ_info.get("is_available") or champ_info.get("owned") or champ_info.get("freeToPlay") or champ_info.get("rented")
        if not is_avail:
            avail_champs = get_lcu_available_champions(is_ban=False)
            avail_names = [c["name"] for c in avail_champs[:6]]
            sample_str = ", ".join(avail_names) if avail_names else "Nenhum detectado"
            return False, f"Você não possui {champ_name} habilitado nesta conta. Campeões gratuitos disponíveis agora: {sample_str}.", champ_name

    local_cell = session.get("localPlayerCellId", -1)
    
    target_type = "ban" if is_ban else "pick"
    target_action = None
    
    actions = session.get("actions", [])
    for group in actions:
        if isinstance(group, list):
            for act in group:
                if act.get("actorCellId") == local_cell and act.get("type") == target_type and not act.get("completed"):
                    target_action = act
                    break
            if target_action:
                break

    if not target_action:
        for group in actions:
            if isinstance(group, list):
                for act in group:
                    if act.get("actorCellId") == local_cell and not act.get("completed"):
                        target_action = act
                        break
                if target_action:
                    break

    if not target_action:
        action_name = "banir" if is_ban else "escolher"
        return False, f"Não é sua vez de {action_name} no momento.", champ_name

    act_id = target_action.get("id")
    body = {"championId": champ_id, "completed": lock_in}
    res = request_api(lock, f"/lol-champ-select/v1/session/actions/{act_id}", method="PATCH", body=body)
    if res is None:
        return False, f"Não foi possível selecionar {champ_name}. O cliente rejeitou a ação.", champ_name
    
    if lock_in:
        res_lock = request_api(lock, f"/lol-champ-select/v1/session/actions/{act_id}/complete", method="POST")
        # Verificar confirmação no cliente
        time.sleep(0.15)
        fresh_session = request_api(lock, "/lol-champ-select/v1/session")
        if fresh_session and isinstance(fresh_session, dict):
            completed = False
            for grp in fresh_session.get("actions", []):
                if isinstance(grp, list):
                    for a in grp:
                        if a.get("id") == act_id and (a.get("completed") or a.get("championId") == champ_id):
                            completed = True
                            break
            if not completed and res_lock is None:
                return False, f"Falha ao travar {champ_name}. O cliente rejeitou o bloqueio.", champ_name

    runes_msg = ""
    if not is_ban and lock_in:
        try:
            ok, r_msg = import_recommended_runes_and_spells(champ_id)
            if ok:
                runes_msg = f" {r_msg}"
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao auto-importar runas: {e}")

    verb = "banido" if is_ban else ("travado" if lock_in else "selecionado")
    msg = f"{champ_name} {verb} com sucesso!{runes_msg}"
    return True, msg, champ_name


def get_lcu_aram_bench():
    """Retorna os campeões disponíveis no banco de reservas do ARAM."""
    detailed = get_lcu_champ_select_detailed()
    if detailed:
        return detailed.get("bench", [])
    return []


def swap_lcu_aram_bench(champ_name_or_id):
    """Troca de campeão com o banco de reservas no ARAM."""
    lock = get_league_client_lockfile()
    if not lock:
        return False, "Cliente do League of Legends não detectado."
        
    bench = get_lcu_aram_bench()
    if not bench:
        return False, "Banco de reservas vazio ou indisponível nesta fila."

    target_id = None
    target_name = ""
    if isinstance(champ_name_or_id, int):
        target_id = champ_name_or_id
        for b in bench:
            if b["id"] == target_id:
                target_name = b["name"]
                break
    else:
        qn = normalize_text(champ_name_or_id)
        for b in bench:
            if qn in normalize_text(b["name"]):
                target_id = b["id"]
                target_name = b["name"]
                break

    if not target_id:
        return False, f"Campeão '{champ_name_or_id}' não está no banco de reservas."

    res = request_api(lock, f"/lol-champ-select/v1/session/bench/swap/{target_id}", method="POST")
    if res is not None:
        try:
            import_recommended_runes_and_spells(target_id)
        except Exception:
            pass
        return True, f"Trocado com sucesso para {target_name}!"
    return False, f"Não foi possível trocar para {target_name}."


def reroll_lcu_aram():
    """Rola o dado de campeão no ARAM."""
    lock = get_league_client_lockfile()
    if not lock:
        return False, "Cliente não detectado.", 0
        
    res = request_api(lock, "/lol-champ-select/v1/session/my-selection/reroll", method="POST")
    if res is not None:
        time.sleep(0.4)
        detailed = get_lcu_champ_select_detailed()
        dice = detailed.get("rerolls_remaining", 0) if detailed else 0
        my_info = detailed.get("my_info", {}) if detailed else {}
        cname = my_info.get("champion_name", "Novo campeão")
        cid = my_info.get("champion_id")
        if cid:
            try:
                import_recommended_runes_and_spells(cid)
            except Exception:
                pass
        return True, f"Dado rolado! Seu campeão agora é {cname}. Restam {dice} dado(s).", dice
    return False, "Não foi possível rolar o dado (sem dados suficientes ou bloqueado).", 0


def import_recommended_runes_and_spells(champion_id=None, position=None):
    """
    Importa a melhor página de runas oficial recomendada pela Riot e configura os feitiços de invocador.
    """
    lock = get_league_client_lockfile()
    if not lock:
        return False, "Cliente não detectado."

    detailed = get_lcu_champ_select_detailed()
    map_id = 11
    if detailed and detailed.get("bench_enabled"):
        map_id = 12

    if champion_id is None:
        if detailed and detailed.get("my_info"):
            champion_id = detailed["my_info"].get("champion_id")
        if not champion_id:
            cur = request_api(lock, "/lol-champ-select/v1/current-champion")
            if isinstance(cur, int) and cur > 0:
                champion_id = cur

    if not champion_id or champion_id <= 0:
        return False, "Nenhum campeão selecionado para importar runas."

    champs_map = {c["id"]: c["name"] for c in get_lcu_all_champions()}
    champ_name = champs_map.get(champion_id, f"Campeão {champion_id}")

    if not position:
        if detailed and detailed.get("my_info"):
            position = detailed["my_info"].get("position")
        if not position or position == "UNSELECTED":
            pos_data = request_api(lock, "/lol-perks/v1/recommended-champion-positions")
            if pos_data and isinstance(pos_data, dict):
                champ_pos = pos_data.get(str(champion_id), {}).get("recommendedPositions", [])
                if champ_pos:
                    position = champ_pos[0]
        if not position:
            position = "TOP"

    # Buscar páginas recomendadas
    recs = request_api(lock, f"/lol-perks/v1/recommended-pages/champion/{champion_id}/position/{position}/map/{map_id}")
    if not recs or not isinstance(recs, list) or len(recs) == 0:
        recs = request_api(lock, f"/lol-perks/v1/recommended-pages/champion/{champion_id}/position/{position}/map/11")
    if not recs or not isinstance(recs, list) or len(recs) == 0:
        return False, f"Nenhuma recomendação de runas encontrada para {champ_name}."

    rec = recs[0]
    p_style = rec.get("primaryPerkStyleId")
    s_style = rec.get("secondaryPerkStyleId")
    perks = [x["id"] for x in rec.get("perks", [])]
    spells = rec.get("summonerSpellIds", [])

    p_style_name = PERK_STYLE_NAMES.get(p_style, "Primária")
    s_style_name = PERK_STYLE_NAMES.get(s_style, "Secundária")

    page_body = {
        "name": f"LoL Acc: {champ_name}",
        "primaryStyleId": p_style,
        "subStyleId": s_style,
        "selectedPerkIds": perks,
        "current": True
    }

    pages = request_api(lock, "/lol-perks/v1/pages") or []
    target_page = None
    for pg in pages:
        if pg.get("isDeletable") or pg.get("isEditable"):
            target_page = pg
            break

    page_id = None
    if target_page:
        pid = target_page["id"]
        res_page = request_api(lock, f"/lol-perks/v1/pages/{pid}", method="PUT", body=page_body)
        page_id = pid
    else:
        res_page = request_api(lock, "/lol-perks/v1/pages", method="POST", body=page_body)
        if res_page and isinstance(res_page, dict):
            page_id = res_page.get("id")

    if page_id:
        request_api(lock, "/lol-perks/v1/currentpage", method="PUT", body=page_id)

    # Configurar Feitiços de Invocador se estiver na seleção de campeões
    spells_str = ""
    if spells and len(spells) >= 2:
        s1_name = SUMMONER_SPELL_NAMES.get(spells[0], f"Feitiço {spells[0]}")
        s2_name = SUMMONER_SPELL_NAMES.get(spells[1], f"Feitiço {spells[1]}")
        spells_str = f" Feitiços: {s1_name} e {s2_name}."
        if detailed:
            request_api(lock, "/lol-champ-select/v1/session/my-selection", method="PATCH", body={"spell1Id": spells[0], "spell2Id": spells[1]})

    return True, f"Runas de {p_style_name} e {s_style_name} importadas para {champ_name}!{spells_str}"


def set_lcu_lobby_positions(first_pos, second_pos="UNSELECTED"):
    """Define as posições/rotas no saguão (Top, Jungle, Mid, Bot, Support, Fill)."""
    lock = get_league_client_lockfile()
    if not lock:
        return False, "Cliente não detectado."
    first_pos = first_pos.upper()
    second_pos = second_pos.upper()
    body = {"firstPreference": first_pos, "secondPreference": second_pos}
    res = request_api(lock, "/lol-lobby/v2/lobby/members/localMember/position-preferences", method="PUT", body=body)
    if res is not None:
        p1 = POSITION_TRANSLATIONS.get(first_pos, first_pos)
        p2 = POSITION_TRANSLATIONS.get(second_pos, second_pos)
        return True, f"Rotas do saguão definidas: Primária {p1}, Secundária {p2}."
    return False, "Não foi possível definir rotas (você está em um saguão com seleção de rotas?)."


def get_lcu_chat_messages(conversation_id=None):
    """Retorna as mensagens recentes do chat do saguão/time."""
    lock = get_league_client_lockfile()
    if not lock:
        return []
    
    if not conversation_id:
        convs = request_api(lock, "/lol-chat/v1/conversations")
        if convs and isinstance(convs, list) and len(convs) > 0:
            conversation_id = convs[0].get("id")
            
    if conversation_id:
        msgs = request_api(lock, f"/lol-chat/v1/conversations/{conversation_id}/messages")
        if msgs and isinstance(msgs, list):
            return msgs
    return []


def get_lcu_summoner_info():
    """Retorna dados do invocador atual no League of Legends."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    data = request_api(lock, "/lol-summoner/v1/current-summoner")
    if data and isinstance(data, dict) and "gameName" in data:
        game_name = data.get("gameName") or "Invocador"
        tag_line = data.get("tagLine") or ""
        full_tag = f"{game_name}#{tag_line}" if tag_line else game_name
        lvl = data.get("summonerLevel", 1)
        xp_cur = data.get("xpSinceLastLevel", 0)
        xp_need = data.get("xpUntilNextLevel", 0)
        xp_pct = data.get("percentCompleteForNextLevel", 0)
        return {
            "name": game_name,
            "tag": tag_line,
            "full_tag": full_tag,
            "level": lvl,
            "xp_current": xp_cur,
            "xp_needed": xp_need,
            "xp_percent": xp_pct,
        }
    return None


def get_lcu_ranked_stats():
    """Retorna a classificação ranqueada atual do invocador."""
    lock = get_league_client_lockfile()
    if not lock:
        return "Sem dados ranqueados"
    data = request_api(lock, "/lol-ranked/v1/current-ranked-stats")
    if data and isinstance(data, dict):
        queues = data.get("queues", [])
        for q in queues:
            if q.get("queueType") == "RANKED_SOLO_5x5":
                tier = (q.get("tier") or "").strip()
                div = q.get("division", "")
                lp = q.get("leaguePoints", 0)
                wins = q.get("wins", 0)
                if not tier or tier.upper() in ("NONE", "UNRANKED", ""):
                    rem = q.get("provisionalGamesRemaining", 0)
                    if rem > 0:
                        return f"Sem classificação ({rem} partidas provisórias restantes)"
                    return "Sem classificação"
                div_str = f" {div}" if div and div != "NA" else ""
                return f"{tier.capitalize()}{div_str}, {lp} PDL ({wins} vitórias)"
    return "Sem classificação"


def get_lcu_lobby_info():
    """Retorna informações sobre o saguão atual."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    data = request_api(lock, "/lol-lobby/v2/lobby")
    if data and isinstance(data, dict):
        cfg = data.get("gameConfig", {})
        members = data.get("members", [])
        local_member = data.get("localMember", {})
        return {
            "queue_id": cfg.get("queueId"),
            "game_mode": cfg.get("gameMode", "LoL"),
            "is_leader": local_member.get("isLeader", False),
            "members_count": len(members),
            "can_start": data.get("canStartActivity", False)
        }
    return None


def get_lcu_search_state():
    """Retorna o status da busca por partida (tempo na fila, estimado)."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    data = request_api(lock, "/lol-lobby/v2/lobby/matchmaking/search-state")
    if data and isinstance(data, dict):
        state = data.get("searchState", "Invalid")
        time_in_q = int(data.get("timeInQueue", 0))
        est_time = int(data.get("estimatedQueueTime", 0))
        return {
            "is_searching": state == "Searching",
            "state": state,
            "time_in_queue": time_in_q,
            "estimated_time": est_time
        }
    return None


def create_lcu_lobby(queue_id):
    """Cria um saguão para a fila especificada."""
    lock = get_league_client_lockfile()
    if not lock:
        return False
    res = request_api(lock, "/lol-lobby/v2/lobby", method="POST", body={"queueId": queue_id})
    return res is not None


def start_lcu_matchmaking():
    """Inicia a busca por partida no saguão atual."""
    lock = get_league_client_lockfile()
    if not lock:
        return False
    res = request_api(lock, "/lol-lobby/v2/lobby/matchmaking/search", method="POST")
    return res is not None


def cancel_lcu_matchmaking():
    """Cancela a busca por partida atual."""
    lock = get_league_client_lockfile()
    if not lock:
        return False
    res = request_api(lock, "/lol-lobby/v2/lobby/matchmaking/search", method="DELETE")
    return res is not None


def get_lcu_queue_penalty():
    """Consulta se há penalidade temporária de espera ou bloqueio de fila ativo (ex: QUEUE_DODGER)."""
    lock = get_league_client_lockfile()
    if not lock:
        return None
    search = request_api(lock, "/lol-matchmaking/v1/search")
    if search and isinstance(search, dict) and search.get("errors"):
        for err in search["errors"]:
            etype = err.get("errorType") or err.get("message") or ""
            trem = float(err.get("penaltyTimeRemaining", 0))
            if trem > 0:
                mins = int(trem // 60)
                secs = int(trem % 60)
                time_str = f"{mins} minuto{'s' if mins != 1 else ''}" if mins > 0 else ""
                if secs > 0:
                    time_str += f" e {secs} segundo{'s' if secs != 1 else ''}" if time_str else f"{secs} segundo{'s' if secs != 1 else ''}"
                
                type_desc = "bloqueio por abandono de seleção" if "DODGE" in etype else "penalidade de fila de baixa prioridade"
                text = f"Fila temporariamente bloqueada ({type_desc}). Tempo de espera restante: {time_str}."
                return {
                    "has_penalty": True,
                    "type": etype,
                    "seconds_remaining": trem,
                    "time_str": time_str,
                    "text": text
                }
    return None


def dismiss_lcu_notifications():
    """Descarta e aceita notificações e diálogos modais pendentes do cliente."""
    lock = get_league_client_lockfile()
    if not lock:
        return 0
    count = 0
    # 1. Pacto da comunidade (Code of Conduct): verifica se a notificação existe antes de contar
    coc = request_api(lock, "/lol-player-behavior/v1/code-of-conduct-notification")
    if coc:
        request_api(lock, "/lol-player-behavior/v1/code-of-conduct-notification", method="DELETE")
        count += 1
    # Garante que o pacto fique registrado como aceito nas preferências da conta
    request_api(lock, "/lol-settings/v2/account/LCUPreferences/lol-player-behavior", method="PATCH", body={"data": {"codeOfConductAccepted": True}})

    # 2. Notificações do jogador (Temporada / Splits / Recompensas)
    notifs = request_api(lock, "/player-notifications/v1/notifications")
    if notifs and isinstance(notifs, list) and len(notifs) > 0:
        for n in notifs:
            nid = n.get("id")
            if nid is not None:
                request_api(lock, f"/player-notifications/v1/notifications/{nid}", method="DELETE")
                count += 1

    # 3. Mensagens de diálogos simples
    dialogs = request_api(lock, "/lol-simple-dialog-messages/v1/messages")
    if dialogs and isinstance(dialogs, list) and len(dialogs) > 0:
        for d in dialogs:
            mid = d.get("messageId")
            if mid:
                request_api(lock, f"/lol-simple-dialog-messages/v1/messages/{mid}", method="DELETE")
                count += 1
    return count

# CAMADA 3: RIOT CLIENT API (LAUNCHER E DOWNLOADS)
# ============================================================================

def get_riot_user_info():
    """Retorna dados do usuário atualmente autenticado no Riot Client."""
    lock = get_riot_client_lockfile()
    if not lock:
        return None
    
    data = request_api(lock, "/rso-auth/v1/authorization/userinfo")
    if data and isinstance(data, dict) and "userInfo" in data:
        try:
            raw_info = json.loads(data["userInfo"])
            acct = raw_info.get("acct", {})
            game_name = acct.get("game_name") or raw_info.get("preferred_username") or "Invocador"
            tag_line = acct.get("tag_line", "")
            full_tag = f"{game_name}#{tag_line}" if tag_line else game_name
            region = raw_info.get("region", "")
            if not region:
                loc_data = request_api(lock, "/riotclient/region-locale")
                if loc_data and isinstance(loc_data, dict):
                    region = loc_data.get("region", "")
            return {
                "name": game_name,
                "tag": tag_line,
                "full_tag": full_tag,
                "country": raw_info.get("country", "").upper(),
                "region": region,
            }
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao decodificar userinfo: {e}")
    return None


def get_riot_install_status():
    """Retorna o status de instalação/download de produtos gerenciados pela Riot."""
    lock = get_riot_client_lockfile()
    if not lock:
        return None
    
    installs = request_api(lock, "/patch/v1/installs")
    if not installs or not isinstance(installs, list):
        return None
    
    results = {}
    for inst_id in installs:
        status = request_api(lock, f"/patch/v1/installs/{inst_id}/status")
        if status and isinstance(status, dict):
            results[inst_id] = status
    return results


# ============================================================================
# CAMADA 4: RIOT WEB API (RGAPI - OPCIONAL / CONFIGURÁVEL)
# ============================================================================

def request_riot_web_api(region_routing, endpoint, api_key):
    """
    Executa consulta na Riot Web API remota usando a chave do Developer Portal.
    """
    if not api_key:
        return None
    url = f"https://{region_routing}.api.riotgames.com{endpoint}"
    headers = {
        "X-Riot-Token": api_key,
        "Accept": "application/json"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            content = resp.read().decode("utf-8")
            if content:
                return json.loads(content)
            return None
    except Exception as e:
        log.debug(f"lolAccessibility: Erro na Riot Web API ({endpoint}): {e}")
        return None


# ============================================================================
# FORMATAÇÃO DO PAINEL TÁTICO IN-GAME (PLACAR, STATUS, OBJETIVOS, INIMIGOS)
# ============================================================================

def format_scoreboard_summary(live_data=None):
    """Formata resumo falado do placar da partida: KDA do jogador, CS e placar geral de abates."""
    if not live_data:
        live_data = get_live_allgamedata()
    if not live_data or not isinstance(live_data, dict):
        return "Informações do placar indisponíveis no momento. Partida em andamento não detectada."

    active = live_data.get("activePlayer", {})
    my_name = active.get("summonerName", "")
    all_players = live_data.get("allPlayers", [])

    my_player = None
    my_team = "ORDER"
    order_kills = 0
    chaos_kills = 0

    for p in all_players:
        p_team = p.get("team", "ORDER")
        scores = p.get("scores", {})
        kills = scores.get("kills", 0)
        if p_team == "ORDER":
            order_kills += kills
        else:
            chaos_kills += kills

        if p.get("summonerName") == my_name or not my_player:
            my_player = p
            my_team = p_team

    if not my_player and all_players:
        my_player = all_players[0]
        my_team = my_player.get("team", "ORDER")

    scores = my_player.get("scores", {}) if my_player else {}
    k = scores.get("kills", 0)
    d = scores.get("deaths", 0)
    a = scores.get("assists", 0)
    cs = scores.get("creepScore", 0)

    my_team_kills = order_kills if my_team == "ORDER" else chaos_kills
    enemy_team_kills = chaos_kills if my_team == "ORDER" else order_kills

    diff = my_team_kills - enemy_team_kills
    if diff > 0:
        advantage = f"Seu time está na frente por {diff} abates."
    elif diff < 0:
        advantage = f"Inimigos lideram por {-diff} abates."
    else:
        advantage = "Partida empatada em abates."

    return (
        f"Seu KDA: {k} abates, {d} mortes, {a} assistências. {cs} tropas. "
        f"Placar: {my_team_kills} x {enemy_team_kills}. {advantage}"
    )


def format_champion_stats_summary(live_data=None):
    """Formata resumo falado das estatísticas completas do campeão (vida, mana, atributos)."""
    if not live_data:
        live_data = get_live_allgamedata()
    if not live_data or not isinstance(live_data, dict):
        return "Informações do campeão indisponíveis no momento."

    active = live_data.get("activePlayer", {})
    stats = active.get("championStats", {})
    level = active.get("level", 1)

    cur_hp = int(stats.get("currentHealth", 0))
    max_hp = int(stats.get("maxHealth", 1))
    hp_pct = int((cur_hp / max(1, max_hp)) * 100)

    res_val = int(stats.get("resourceValue", 0))
    res_max = int(stats.get("resourceMax", 0))
    res_type = stats.get("resourceType", "MANA")

    ad = int(round(stats.get("attackDamage", 0)))
    ap = int(round(stats.get("abilityPower", 0)))
    armor = int(round(stats.get("armor", 0)))
    mr = int(round(stats.get("magicResist", 0)))
    ms = int(round(stats.get("moveSpeed", 0)))
    range_val = int(round(stats.get("attackRange", 0)))

    parts = [f"Nível {level}", f"Vida: {cur_hp} de {max_hp} ({hp_pct}%)"]

    if res_max > 0 and res_type != "NONE":
        res_name = "Mana" if res_type == "MANA" else "Energia"
        res_pct = int((res_val / max(1, res_max)) * 100)
        parts.append(f"{res_name}: {res_val} de {res_max} ({res_pct}%)")

    parts.append(f"Ataque: {ad}")
    if ap > 0:
        parts.append(f"Poder Mágico: {ap}")
    parts.append(f"Armadura: {armor}")
    parts.append(f"Resistência Mágica: {mr}")
    parts.append(f"Velocidade: {ms}")
    parts.append(f"Alcance: {range_val}")

    return "Status: " + ", ".join(parts) + "."


def format_objectives_summary(live_data=None):
    """Formata resumo falado do tempo de jogo, dragões, barões e torres caídas."""
    if not live_data:
        live_data = get_live_allgamedata()
    if not live_data or not isinstance(live_data, dict):
        return "Informações de objetivos indisponíveis no momento."

    gdata = live_data.get("gameData", {})
    gtime = float(gdata.get("gameTime", 0.0))
    mins = int(gtime // 60)
    secs = int(gtime % 60)
    time_str = f"{mins} minutos e {secs} segundos"

    events = live_data.get("events", {}).get("Events", [])
    active = live_data.get("activePlayer", {})
    my_name = active.get("summonerName", "")
    all_players = live_data.get("allPlayers", [])

    my_team = "ORDER"
    for p in all_players:
        if p.get("summonerName") == my_name:
            my_team = p.get("team", "ORDER")
            break

    my_dragons = 0
    enemy_dragons = 0
    my_barons = 0
    enemy_barons = 0
    enemy_turrets_destroyed = 0

    player_teams = {p.get("summonerName"): p.get("team") for p in all_players}

    for ev in events:
        ename = ev.get("EventName")
        killer = ev.get("KillerName")
        k_team = player_teams.get(killer)

        if ename == "DragonKill":
            if k_team == my_team:
                my_dragons += 1
            elif k_team:
                enemy_dragons += 1
        elif ename == "BaronKill":
            if k_team == my_team:
                my_barons += 1
            elif k_team:
                enemy_barons += 1
        elif ename == "TurretKilled":
            if k_team == my_team:
                enemy_turrets_destroyed += 1

    return (
        f"Tempo: {time_str}. "
        f"Dragões: Seu time {my_dragons}, Inimigos {enemy_dragons}. "
        f"Barões: Seu time {my_barons}, Inimigos {enemy_barons}. "
        f"Torres inimigas destruídas: {enemy_turrets_destroyed}."
    )


def format_enemies_summary(live_data=None):
    """Formata resumo de inimigos vivos/mortos, rotas deduzidas e feitiços."""
    if not live_data:
        live_data = get_live_allgamedata()
    if not live_data or not isinstance(live_data, dict):
        return "Informações dos inimigos indisponíveis no momento."

    active = live_data.get("activePlayer", {})
    my_name = active.get("summonerName", "")
    all_players = live_data.get("allPlayers", [])

    my_team = "ORDER"
    for p in all_players:
        if p.get("summonerName") == my_name:
            my_team = p.get("team", "ORDER")
            break

    enemies = [p for p in all_players if p.get("team") != my_team]
    if not enemies:
        return "Nenhum campeão inimigo detectado na partida."

    items_desc = []
    for p in enemies:
        cname = p.get("championName", "Inimigo")
        is_dead = p.get("isDead", False)
        respawn = int(round(p.get("respawnTimer", 0.0)))
        status_txt = f"Morto por mais {respawn}s" if (is_dead and respawn > 0) else "Vivo"

        spells = p.get("summonerSpells", {})
        s1 = spells.get("summonerSpellOne", {}).get("displayName", "")
        s2 = spells.get("summonerSpellTwo", {}).get("displayName", "")
        sp_txt = f" com {s1} e {s2}" if (s1 and s2) else ""

        items_desc.append(f"{cname}: {status_txt}{sp_txt}")

    return "Inimigos: " + "; ".join(items_desc) + "."

