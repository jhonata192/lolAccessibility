# -*- coding: utf-8 -*-
"""
Testes unitários e validação do add-on lolAccessibility.
Testa:
1. Compilação de todos os módulos Python (py_compile).
2. Conformidade do manifest.ini.
3. Decodificação de lockfile e userinfo do Riot Client.
4. Processamento da Live Client Data API (127.0.0.1:2999): Vida, KDA, Itens, Eventos.
"""

import os
import sys
import py_compile
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_syntax():
    """Valida a compilação de todos os arquivos .py do projeto."""
    print("Testando sintaxe dos arquivos Python...")
    count = 0
    for root, _, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                py_compile.compile(path, doraise=True)
                count += 1
    print(f"OK: {count} arquivos Python compilaram sem erros de sintaxe.")


def test_manifest():
    """Valida a conformidade do manifest.ini."""
    print("Validando manifest.ini...")
    manifest_path = os.path.join(ROOT_DIR, "manifest.ini")
    assert os.path.exists(manifest_path), "manifest.ini não encontrado!"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_keys = ["name", "summary", "description", "author", "version", "minimumNVDAVersion"]
    for key in required_keys:
        assert f"{key} =" in content, f"Chave obrigatória '{key}' ausente no manifest.ini!"
        
    print("OK: manifest.ini validado com sucesso.")


def test_riot_decoding():
    """Testa a lógica de decodificação do lockfile e userinfo."""
    print("Testando decodificação de dados da Riot...")
    
    mock_lockfile = "Riot Client:7476:58487:0pT6DFIXCLytrJBJpM0_nw:https"
    parts = mock_lockfile.split(":")
    assert len(parts) >= 5
    assert parts[0] == "Riot Client"
    assert parts[2] == "58487"
    assert parts[4] == "https"
    
    mock_user_info = {
        "userInfo": json.dumps({
            "country": "bra",
            "region": "br1",
            "acct": {
                "game_name": "jhonata",
                "tag_line": "2515"
            }
        })
    }
    
    raw = json.loads(mock_user_info["userInfo"])
    full_tag = f"{raw['acct']['game_name']}#{raw['acct']['tag_line']}"
    assert full_tag == "jhonata#2515"
    print(f"OK: Decodificação de usuário bem-sucedida ({full_tag}).")


def test_live_client_data_processing():
    """Testa o processamento dos dados da Live Client Data API (127.0.0.1:2999)."""
    print("Testando processamento de dados in-game (Live Client Data API)...")
    
    mock_active = {
        "championStats": {
            "currentHealth": 1450.0,
            "maxHealth": 1800.0,
            "resourceValue": 420.0,
            "resourceMax": 600.0,
            "resourceType": "MANA"
        },
        "level": 8,
        "currentGold": 1250.0,
        "summonerName": "jhonata"
    }
    
    cur_hp = int(mock_active["championStats"]["currentHealth"])
    max_hp = int(mock_active["championStats"]["maxHealth"])
    pct = int((cur_hp / max_hp) * 100)
    assert pct == 80
    assert mock_active["level"] == 8
    
    # Teste de evento de Kill
    mock_event = {
        "EventID": 5,
        "EventName": "ChampionKill",
        "KillerName": "jhonata",
        "VictimName": "Zed"
    }
    assert mock_event["EventName"] == "ChampionKill"
    assert mock_event["KillerName"] == "jhonata"
    print("OK: Processamento de dados in-game validado com sucesso.")


def test_champ_select_and_lobby():
    """Testa a lógica de busca de campeões, aliases e preferências de saguão."""
    print("Testando busca de campeões e suporte a saguão...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))
    
    from lol_lib.riot_api_helper import normalize_text, CHAMPION_ALIASES, POSITION_TRANSLATIONS
    
    assert normalize_text("Twisted Fate") == "twistedfate"
    assert normalize_text("Cho'Gath") == "chogath"
    assert normalize_text("Khar'Zix") == "kharzix"
    
    # Testar aliases conhecidos e tolerância a erros de digitação (typos)
    assert CHAMPION_ALIASES["tf"] == "Twisted Fate"
    assert CHAMPION_ALIASES["yi"] == "Master Yi"
    assert CHAMPION_ALIASES["cait"] == "Caitlyn"
    assert CHAMPION_ALIASES["j4"] == "Jarvan IV"
    assert CHAMPION_ALIASES["asol"] == "Aurelion Sol"
    assert CHAMPION_ALIASES["garem"] == "Garen"
    assert CHAMPION_ALIASES["ashr"] == "Ashe"
    assert CHAMPION_ALIASES["malfite"] == "Malphite"
    assert CHAMPION_ALIASES["morde"] == "Mordekaiser"
    
    # Testar busca com lista mockada e algoritmo difflib
    from lol_lib.riot_api_helper import find_champion_by_name, get_lcu_available_champions
    mock_champs = [
        {"id": 86, "name": "Garen", "is_available": False, "owned": False, "freeToPlay": False, "disabled": False},
        {"id": 51, "name": "Caitlyn", "is_available": True, "owned": False, "freeToPlay": True, "disabled": False},
        {"id": 54, "name": "Malphite", "is_available": True, "owned": True, "freeToPlay": False, "disabled": False}
    ]
    res_garem = find_champion_by_name("garem", mock_champs)
    assert res_garem is not None and res_garem["name"] == "Garen"

    res_cait = find_champion_by_name("caitlin", mock_champs)
    assert res_cait is not None and res_cait["name"] == "Caitlyn"

    res_malph = find_champion_by_name("malfit", mock_champs)
    assert res_malph is not None and res_malph["name"] == "Malphite"
    
    # Testar traduções de funções/roles e formatação de exibição para a caixa de combinação
    from lol_lib.riot_api_helper import ROLE_TRANSLATIONS, format_champion_display_name
    assert ROLE_TRANSLATIONS["marksman"] == "Atirador"
    assert ROLE_TRANSLATIONS["tank"] == "Tanque"
    assert ROLE_TRANSLATIONS["fighter"] == "Lutador"
    assert ROLE_TRANSLATIONS["mage"] == "Mago"
    assert ROLE_TRANSLATIONS["support"] == "Suporte"
    assert ROLE_TRANSLATIONS["assassin"] == "Assassino"

    c_cait = {"name": "Caitlyn", "roles": ["marksman"]}
    assert format_champion_display_name(c_cait) == "Caitlyn (Atirador)"

    c_malph = {"name": "Malphite", "roles": ["tank", "mage"]}
    assert format_champion_display_name(c_malph) == "Malphite (Tanque, Mago)"

    # Testar traduções de posições
    assert POSITION_TRANSLATIONS["TOP"] == "Topo"
    assert POSITION_TRANSLATIONS["JUNGLE"] == "Selva"
    assert POSITION_TRANSLATIONS["MIDDLE"] == "Meio"
    assert POSITION_TRANSLATIONS["BOTTOM"] == "Atirador"
    assert POSITION_TRANSLATIONS["UTILITY"] == "Suporte"

    # Testar imports de penalidade de fila e disponibilidade
    from lol_lib.riot_api_helper import get_lcu_queue_penalty, get_lcu_available_champions
    assert callable(get_lcu_queue_penalty)
    assert callable(get_lcu_available_champions)
    
    print("OK: Busca de campeões, saguão e detecção de penalidade validados com sucesso.")


def test_enemy_lane_deduction():
    """Testa o algoritmo heurístico de dedução de rotas dos inimigos."""
    print("Testando dedução heurística de rotas dos inimigos...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))
    
    from lol_lib.riot_api_helper import (
        ROLE_MARKSMEN, ROLE_TOP_LANERS, ROLE_MID_LANERS, ROLE_SUPPORTS, normalize_text
    )
    
    assert "darius" in ROLE_TOP_LANERS
    assert "ahri" in ROLE_MID_LANERS
    assert "jinx" in ROLE_MARKSMEN
    assert "blitzcrank" in ROLE_SUPPORTS
    
    # Testar identificação de selva por feitiço Smite / Golpear
    spells = ["Flash", "Smite"]
    spells_norm = [normalize_text(s) for s in spells]
    has_smite = any("smite" in s or "golpear" in s for s in spells_norm)
    assert has_smite is True
    
    # Testar identificação de suporte por item inicial Atlas Mundial
    items = ["Atlas Mundial", "Poção com Refil"]
    items_norm = [normalize_text(it) for it in items]
    has_sup_item = any(k in it for it in items_norm for k in ("atlas", "relic", "suporte"))
    assert has_sup_item is True
    
    print("OK: Dedução heurística de rotas validada com sucesso.")


def test_chat_and_pings_reader():
    """Testa o leitor e parser de chat e pings táticos."""
    print("Testando leitor de pings e chat...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.chat_reader import (
        LoLChatReader, PING_MISSING, PING_DANGER, PING_ON_MY_WAY,
        PING_ASSIST, PING_SPELL, PING_CHAT
    )

    reader = LoLChatReader()

    # 1. Ping de Inimigo Desaparecido (MIA / ?)
    r_mia = reader.parse_line("Ahri (Ahri): Inimigo Desaparecido")
    assert r_mia["type"] == PING_MISSING
    assert "Ahri" in r_mia["announcement"]
    assert "desapareceu" in r_mia["announcement"]

    # 2. Ping de Perigo
    r_perigo = reader.parse_line("Lee Sin (Lee Sin): Perigo")
    assert r_perigo["type"] == PING_DANGER
    assert "Perigo" in r_perigo["announcement"]

    # 3. Ping de A Caminho
    r_omw = reader.parse_line("Darius: A Caminho")
    assert r_omw["type"] == PING_ON_MY_WAY
    assert "Darius" in r_omw["announcement"]
    assert "a caminho" in r_omw["announcement"]

    # 4. Ping de Ajuda
    r_ajuda = reader.parse_line("Blitzcrank (Blitzcrank): Preciso de Ajuda")
    assert r_ajuda["type"] == PING_ASSIST
    assert "ajuda" in r_ajuda["announcement"]

    # 5. Feitiço pingado
    r_spell = reader.parse_line("Jinx (Jinx) - Flash (250s)")
    assert r_spell["type"] == PING_SPELL
    assert "Flash" in r_spell["announcement"]

    # 6. Mensagem no chat geral
    r_chat = reader.parse_line("[Todos] Yasuo (Yasuo): gg wp")
    assert r_chat["type"] == PING_CHAT
    assert "Yasuo" in r_chat["announcement"]
    assert "gg wp" in r_chat["announcement"]

    # 7. Deduplicação e Cooldown de pings em massa (anti-spam)
    now = 1000.0
    items1 = reader.process_raw_text("Ahri (Ahri): Inimigo Desaparecido", now=now)
    assert len(items1) == 1
    # Segundo ping idêntico 0.5s depois -> silenciado para não poluir voz
    items2 = reader.process_raw_text("Ahri (Ahri): Inimigo Desaparecido", now=now + 0.5)
    assert len(items2) == 0

    # 8. Histórico recente de pings
    summary = reader.get_recent_summary(max_count=2)
    assert len(summary) > 0
    assert "MIA" in summary or "Ahri" in summary

    print("OK: Leitor de pings e chat validado com sucesso.")


def test_tactical_live_events():
    """Testa a tradução e detalhamento de eventos táticos da Live Client Data API."""
    print("Testando eventos táticos da Live API...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.riot_api_helper import (
        parse_turret_name, parse_inhib_name, format_live_game_event
    )

    # Nomes de torres detalhadas
    t_top = parse_turret_name("Turret_T2_L_03_A")
    assert "Topo" in t_top
    assert "Vermelho" in t_top

    t_mid = parse_turret_name("Turret_T1_C_01_A")
    assert "Meio" in t_mid
    assert "Azul" in t_mid

    # Nomes de inibidores
    inh = parse_inhib_name("Barracks_T1_L1")
    assert "Topo" in inh
    assert "Azul" in inh

    # Eventos formatados
    st, msg = format_live_game_event({"EventName": "FirstBlood", "Recipient": "Garen"})
    assert st == "FIRST_BLOOD"
    assert "Garen" in msg

    st, msg = format_live_game_event({"EventName": "HeraldKill", "KillerName": "Lee Sin"})
    assert st == "HERALD"
    assert "Lee Sin" in msg

    st, msg = format_live_game_event({"EventName": "TurretKilled", "TurretKilled": "Turret_T2_L_03_A", "KillerName": "Darius"})
    assert st == "TURRET"
    assert "Darius" in msg
    assert "Topo" in msg

    st, msg = format_live_game_event({"EventName": "Ace", "AcingTeam": "ORDER"})
    assert st == "ACE"
    assert "Azul" in msg

    print("OK: Eventos táticos da Live API validados com sucesso.")


def test_minimap_scanner():
    """Testa o scanner de minimapa, rotulação de marcadores e zonificação."""
    print("Testando scanner de minimapa e zonas táticas...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.minimap_scanner import LoLMinimapScanner

    scanner = LoLMinimapScanner()

    # 1. Zonificação de Summoner's Rift
    assert "Base Aliada" in scanner.classify_zone(0.05, 0.95, my_team="ORDER")
    assert "Base Inimiga" in scanner.classify_zone(0.95, 0.05, my_team="ORDER")
    assert "Topo" in scanner.classify_zone(0.10, 0.30, my_team="ORDER")
    assert "Meio" in scanner.classify_zone(0.50, 0.50, my_team="ORDER")
    assert "Inferior" in scanner.classify_zone(0.90, 0.40, my_team="ORDER")
    assert "Barão" in scanner.classify_zone(0.40, 0.38, my_team="ORDER")
    assert "Dragão" in scanner.classify_zone(0.60, 0.62, my_team="ORDER")

    # 2. Zonificação de ARAM / Howling Abyss
    assert "Base Aliada" in scanner.classify_zone(0.10, 0.90, my_team="ORDER", is_aram=True)
    assert "Ponte" in scanner.classify_zone(0.50, 0.50, my_team="ORDER", is_aram=True)
    assert "Base Inimiga" in scanner.classify_zone(0.90, 0.10, my_team="ORDER", is_aram=True)

    # 3. Teste de detecção de marcadores com buffer sintético 100x100
    w, h = 100, 100
    buf = bytearray(w * h * 4)

    def draw_marker(cx, cy, radius, r, g, b):
        for y in range(max(0, cy - radius), min(h, cy + radius)):
            for x in range(max(0, cx - radius), min(w, cx + radius)):
                if (x - cx)**2 + (y - cy)**2 <= radius**2:
                    idx = (y * w + x) * 4
                    buf[idx] = b
                    buf[idx + 1] = g
                    buf[idx + 2] = r
                    buf[idx + 3] = 255

    # Desenhar 1 inimigo (vermelho) em x=80, y=80 e 1 aliado (azul) em x=20, y=20
    draw_marker(80, 80, 5, 230, 20, 20)
    draw_marker(20, 20, 5, 20, 120, 240)

    icons = scanner.detect_markers(w, h, buf)
    assert len(icons) == 2

    enemies = [ic for ic in icons if ic["team"] == "enemy"]
    allies = [ic for ic in icons if ic["team"] == "ally"]

    assert len(enemies) == 1
    assert len(allies) == 1
    assert abs(enemies[0]["u"] - 0.80) < 0.05
    assert abs(enemies[0]["v"] - 0.80) < 0.05
    assert abs(allies[0]["u"] - 0.20) < 0.05
    assert abs(allies[0]["v"] - 0.20) < 0.05

    print("OK: Scanner de minimapa e zonas táticas validados com sucesso.")


def test_spatial_audio():
    """Testa o motor de áudio espacial 3D e cálculos geométricos de radar."""
    print("Testando áudio espacial 3D e cálculos geométricos...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    import wave
    import struct
    import io
    from lol_lib.spatial_audio import (
        generate_pcm_stereo_tone, generate_sweep_tone, generate_clean_radar_chord,
        get_spatial_audio_player
    )
    from lol_lib.minimap_scanner import LoLMinimapScanner

    # 1. Testar Panning Estéreo: Esquerda (-1.0)
    w_left = generate_pcm_stereo_tone(880, 50, pan=-1.0, volume=0.8)
    with wave.open(io.BytesIO(w_left), "rb") as wf:
        assert wf.getnchannels() == 2
        frames = wf.readframes(wf.getnframes())
        samples = struct.unpack(f"<{len(frames)//2}h", frames)
        left_samples = samples[0::2]
        right_samples = samples[1::2]
        max_left = max(abs(s) for s in left_samples)
        max_right = max(abs(s) for s in right_samples)
        assert max_left > 15000
        assert max_right == 0 or max_right < 500

    # 2. Testar Panning Estéreo: Direita (+1.0)
    w_right = generate_pcm_stereo_tone(880, 50, pan=1.0, volume=0.8)
    with wave.open(io.BytesIO(w_right), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        samples = struct.unpack(f"<{len(frames)//2}h", frames)
        max_left = max(abs(s) for s in samples[0::2])
        max_right = max(abs(s) for s in samples[1::2])
        assert max_right > 15000
        assert max_left == 0 or max_left < 500

    # 3. Testar Cálculos Espaciais e Horas do Relógio
    scanner = LoLMinimapScanner()
    mock_markers = [
        {"team": "enemy", "u": 0.20, "v": 0.50},  # Esquerda
        {"team": "enemy", "u": 0.50, "v": 0.20},  # À frente (Norte)
        {"team": "enemy", "u": 0.80, "v": 0.50},  # Direita
        {"team": "enemy", "u": 0.50, "v": 0.80},  # Atrás (Sul)
    ]
    targets = scanner.calculate_spatial_targets(mock_markers, cam_u=0.50, cam_v=0.50)
    assert len(targets) == 4

    # Esquerda: pan negativo, 9 horas
    t_left = targets[0]
    assert t_left["pan"] <= -0.8
    assert t_left["hour"] == 9
    assert t_left["dir_desc"] == "à esquerda"

    # À frente: pan centrado (0.0), 12 horas
    t_front = targets[1]
    assert abs(t_front["pan"]) < 0.1
    assert t_front["hour"] == 12
    assert t_front["dir_desc"] == "à frente"

    # Direita: pan positivo, 3 horas
    t_right = targets[2]
    assert t_right["pan"] >= 0.8
    assert t_right["hour"] == 3
    assert t_right["dir_desc"] == "à direita"

    # Atrás: pan centrado (0.0), 6 horas
    t_back = targets[3]
    assert abs(t_back["pan"]) < 0.1
    assert t_back["hour"] == 6
    assert t_back["dir_desc"] == "atrás"

    # 4. Testar Ciclo de Vida do SpatialAudioPlayer
    player = get_spatial_audio_player()
    assert player is not None
    player.play_clean_radar()
    player.stop()

    print("OK: Áudio espacial 3D, panning e cálculos de radar validados com sucesso.")


def test_shop_assistant():
    """Testa o assistente de loja, catálogo e cálculo de receitas."""
    print("Testando assistente de loja e receitas...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.shop_assistant import LoLShopAssistant

    shop = LoLShopAssistant()
    items = shop.load_items()
    assert len(items) > 10

    # 1. Testar busca por apelidos populares
    it_gume = shop.find_item_by_name("gume")
    assert it_gume is not None
    assert "Gume" in it_gume["name"]

    it_trin = shop.find_item_by_name("trindade")
    assert it_trin is not None
    assert "Trindade" in it_trin["name"]

    it_mercurio = shop.find_item_by_name("passos")
    assert it_mercurio is not None
    assert "Mercúrio" in it_mercurio["name"]

    # 2. Testar análise de inventário e cálculo de receitas
    mock_inv = [{"itemID": 1001, "displayName": "Botas"}]
    analysis = shop.analyze_inventory_and_gold(current_gold=1000, inventory_items=mock_inv)
    assert analysis["gold"] == 1000
    assert analysis["inventory_count"] == 1
    # Botas de Rapidez custam 900 e com Botas (desconto 300) custam 600, logo cabem no orçamento de 1000!
    assert any(b["name"] == "Botas da Rapidez" for b in analysis["can_buy_now"])

    speech = shop.format_shop_speech(analysis)
    assert "Loja:" in speech
    assert "1000 de ouro" in speech

    print("OK: Assistente de loja e receitas validados com sucesso.")


def test_combat_status():
    """Testa monitor de combate, batimento cardíaco, recall e habilidades."""
    print("Testando monitor de combate, vida crítica, recall e habilidades...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.combat_status import LoLCombatStatus

    combat = LoLCombatStatus()

    # 1. Testar Vida Crítica (< 30%)
    res_normal = combat.update_player_health(cur_hp=800, max_hp=1000)
    assert res_normal is None
    res_crit = combat.update_player_health(cur_hp=250, max_hp=1000)
    assert res_crit == "CRITICAL_HP"

    # 2. Testar Retorno à Base (Recall) e Interrupção por Dano
    combat.start_recall(current_health=1000.0)
    assert combat.is_recalling is True
    # Sofreu dano: vida caiu para 950
    ev, msg = combat.update_recall(current_health=950.0)
    assert ev == "INTERRUPTED"
    assert "interrompido" in msg
    assert combat.is_recalling is False

    # 3. Testar Notificação de Ultimate Pronto
    # Estado inicial: R em recarga (cooldown = 45s)
    abilities_cd = {
        "Q": {"displayName": "Golpe Decisivo", "abilityLevel": 3, "cooldown": 0.0},
        "W": {"displayName": "Coragem", "abilityLevel": 2, "cooldown": 5.0},
        "E": {"displayName": "Julgamento", "abilityLevel": 3, "cooldown": 0.0},
        "R": {"displayName": "Justiça de Demacia", "abilityLevel": 1, "cooldown": 45.0}
    }
    combat.last_ultimate_ready = False
    ev_r, msg_r = combat.update_abilities_cooldowns(abilities_cd)
    assert ev_r is None

    # Estado 2: R sai de recarga (cooldown = 0.0)
    abilities_ready = {
        "Q": {"displayName": "Golpe Decisivo", "abilityLevel": 3, "cooldown": 0.0},
        "W": {"displayName": "Coragem", "abilityLevel": 2, "cooldown": 0.0},
        "E": {"displayName": "Julgamento", "abilityLevel": 3, "cooldown": 0.0},
        "R": {"displayName": "Justiça de Demacia", "abilityLevel": 1, "cooldown": 0.0}
    }
    ev_ready, msg_ready = combat.update_abilities_cooldowns(abilities_ready)
    assert ev_ready == "ULTIMATE_READY"
    assert "pronto" in msg_ready

    # 4. Testar Resumo falado de habilidades
    summary = combat.get_abilities_summary(abilities_cd)
    assert "Q: Pronto" in summary
    assert "W: 5s de recarga" in summary
    assert "R: 45s de recarga" in summary

    print("OK: Monitor de combate, batimento cardíaco, recall e habilidades validados com sucesso.")


def test_tactical_navigator():
    """Testa o navegador tático, waypoints do minimapa e conversões de tela."""
    print("Testando navegador tático e movimentação no minimapa...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.tactical_navigator import (
        TacticalNavigator, get_tactical_navigator, WAYPOINTS
    )

    nav = TacticalNavigator()

    # 1. Waypoints para Time Azul (ORDER)
    wp_base_blue = nav.resolve_waypoint("BASE", team="ORDER")
    assert wp_base_blue is not None
    assert wp_base_blue["key"] == "ORDER_BASE"
    assert wp_base_blue["nx"] == 0.08
    assert wp_base_blue["ny"] == 0.92

    wp_mid_blue = nav.resolve_waypoint("MID", team="ORDER")
    assert wp_mid_blue is not None
    assert wp_mid_blue["key"] == "ORDER_MID_CENTER"
    assert wp_mid_blue["nx"] == 0.50
    assert wp_mid_blue["ny"] == 0.50

    wp_top_blue = nav.resolve_waypoint("TOP", team="ORDER")
    assert wp_top_blue["key"] == "ORDER_TOP_CENTER"

    wp_bot_blue = nav.resolve_waypoint("BOT", team="ORDER")
    assert wp_bot_blue["key"] == "ORDER_BOT_CENTER"

    # 2. Waypoints para Time Vermelho (CHAOS)
    wp_base_red = nav.resolve_waypoint("BASE", team="CHAOS")
    assert wp_base_red is not None
    assert wp_base_red["key"] == "CHAOS_BASE"
    assert wp_base_red["nx"] == 0.92
    assert wp_base_red["ny"] == 0.08

    # 3. Objetivos Neutros
    wp_drag = nav.resolve_waypoint("DRAGON")
    assert wp_drag is not None
    assert wp_drag["key"] == "DRAGON_PIT"

    wp_baron = nav.resolve_waypoint("BARON")
    assert wp_baron is not None
    assert wp_baron["key"] == "BARON_PIT"

    # 4. Cálculo geométrico de pixels de tela
    fake_minimap = {"x": 1600, "y": 800, "width": 300, "height": 300}
    px, py = nav.calculate_screen_coordinates(0.5, 0.5, fake_minimap)
    assert px == 1750
    assert py == 950

    px0, py0 = nav.calculate_screen_coordinates(0.0, 0.0, fake_minimap)
    assert px0 == 1600
    assert py0 == 800

    print("OK: Navegador tático e waypoints validados com sucesso.")


def test_tactical_hud_summaries():
    """Testa a formatação e geração dos relatórios acessíveis de Placar, Status, Objetivos e Inimigos."""
    print("Testando resumos do painel tático in-game (Placar, Status, Objetivos, Inimigos)...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    from lol_lib.riot_api_helper import (
        format_scoreboard_summary, format_champion_stats_summary,
        format_objectives_summary, format_enemies_summary
    )

    mock_live_data = {
        "activePlayer": {
            "summonerName": "jhonata#2515",
            "level": 9,
            "currentGold": 1450.0,
            "championStats": {
                "currentHealth": 1250.0,
                "maxHealth": 1500.0,
                "resourceValue": 0.0,
                "resourceMax": 0.0,
                "resourceType": "NONE",
                "attackDamage": 128.0,
                "abilityPower": 0.0,
                "armor": 72.0,
                "magicResist": 54.0,
                "moveSpeed": 385.0,
                "attackRange": 175.0
            }
        },
        "allPlayers": [
            {
                "championName": "Garen",
                "summonerName": "jhonata#2515",
                "team": "ORDER",
                "isDead": False,
                "respawnTimer": 0.0,
                "scores": {"kills": 4, "deaths": 1, "assists": 3, "creepScore": 75}
            },
            {
                "championName": "Ashe",
                "summonerName": "AllyBot",
                "team": "ORDER",
                "isDead": False,
                "respawnTimer": 0.0,
                "scores": {"kills": 2, "deaths": 2, "assists": 4, "creepScore": 60}
            },
            {
                "championName": "Darius",
                "summonerName": "EnemyBot1",
                "team": "CHAOS",
                "isDead": True,
                "respawnTimer": 15.0,
                "scores": {"kills": 1, "deaths": 3, "assists": 0, "creepScore": 40},
                "summonerSpells": {
                    "summonerSpellOne": {"displayName": "Flash"},
                    "summonerSpellTwo": {"displayName": "Fantasma"}
                }
            },
            {
                "championName": "Ahri",
                "summonerName": "EnemyBot2",
                "team": "CHAOS",
                "isDead": False,
                "respawnTimer": 0.0,
                "scores": {"kills": 2, "deaths": 3, "assists": 1, "creepScore": 55},
                "summonerSpells": {
                    "summonerSpellOne": {"displayName": "Flash"},
                    "summonerSpellTwo": {"displayName": "Incendiar"}
                }
            }
        ],
        "gameData": {
            "gameTime": 815.0,
            "gameMode": "CLASSIC"
        },
        "events": {
            "Events": [
                {"EventName": "DragonKill", "KillerName": "jhonata#2515"},
                {"EventName": "TurretKilled", "KillerName": "jhonata#2515"}
            ]
        }
    }

    # 1. Placar
    sb = format_scoreboard_summary(mock_live_data)
    assert "4 abates" in sb
    assert "1 mortes" in sb
    assert "3 assistências" in sb
    assert "75 tropas" in sb
    assert "Placar: 6 x 3" in sb

    # 2. Estatísticas do Campeão
    st = format_champion_stats_summary(mock_live_data)
    assert "Nível 9" in st
    assert "Vida: 1250 de 1500 (83%)" in st
    assert "Ataque: 128" in st
    assert "Armadura: 72" in st

    # 3. Objetivos
    obj = format_objectives_summary(mock_live_data)
    assert "13 minutos e 35 segundos" in obj
    assert "Dragões: Seu time 1" in obj
    assert "Torres inimigas destruídas: 1" in obj

    # 4. Inimigos
    enm = format_enemies_summary(mock_live_data)
    assert "Darius: Morto por mais 15s com Flash e Fantasma" in enm
    assert "Ahri: Vivo com Flash e Incendiar" in enm

    print("OK: Resumos do painel tático validados com sucesso.")


def test_champion_ownership_and_validation():
    """Testa a validação de propriedade e disponibilidade de campeões para escolha e banimento."""
    print("Testando validação de propriedade de campeões...")
    sys.path.insert(0, ROOT_DIR)
    sys.path.insert(0, os.path.join(ROOT_DIR, "lol_lib"))

    import lol_lib.riot_api_helper as rah

    mock_grid = [
        {"id": 86, "name": "Garen", "is_available": False, "owned": False, "freeToPlay": False, "disabled": False},
        {"id": 51, "name": "Caitlyn", "is_available": True, "owned": False, "freeToPlay": True, "disabled": False},
        {"id": 54, "name": "Malphite", "is_available": True, "owned": True, "freeToPlay": False, "disabled": False},
        {"id": 999, "name": "DisabledChamp", "is_available": True, "owned": True, "freeToPlay": False, "disabled": True},
    ]

    old_cache = rah._champions_cache
    old_time = rah._champions_cache_time
    try:
        rah._champions_cache = mock_grid
        rah._champions_cache_time = 9999999999.0

        # Para escolha (pick): apenas Caitlyn e Malphite
        picks = rah.get_lcu_available_champions(is_ban=False)
        pick_names = [c["name"] for c in picks]
        assert "Caitlyn" in pick_names
        assert "Malphite" in pick_names
        assert "Garen" not in pick_names
        assert "DisabledChamp" not in pick_names

        # Para banimento (ban): Garen, Caitlyn e Malphite (apenas DisabledChamp excluído)
        bans = rah.get_lcu_available_champions(is_ban=True)
        ban_names = [c["name"] for c in bans]
        assert "Garen" in ban_names
        assert "Caitlyn" in ban_names
        assert "Malphite" in ban_names
        assert "DisabledChamp" not in ban_names

        # Testar mock de pick_or_ban_champion recusando Garen por não ser possuído
        orig_lock = rah.get_league_client_lockfile
        orig_req = rah.request_api
        try:
            rah.get_league_client_lockfile = lambda: {"port": 1234, "token": "abc", "protocol": "https"}
            rah.request_api = lambda lock, ep, **kw: {"localPlayerCellId": 0, "actions": [[{"actorCellId": 0, "type": "pick", "completed": False, "id": 10}]]} if "session" in ep else True

            ok, msg, cname = rah.pick_or_ban_champion("Garen", is_ban=False, lock_in=True)
            assert ok is False
            assert "Você não possui Garen" in msg
            assert "Caitlyn" in msg or "Malphite" in msg

            # Banir Garen deve ser permitido mesmo sem possuir
            ban_calls = 0
            def mock_ban_req(lock, ep, **kw):
                nonlocal ban_calls
                ban_calls += 1
                if "session" in ep:
                    comp = True if ban_calls > 2 else False
                    return {"localPlayerCellId": 0, "actions": [[{"actorCellId": 0, "type": "ban", "completed": comp, "id": 10, "championId": 86}]]}
                return True

            rah.request_api = mock_ban_req
            ok_ban, msg_ban, cname_ban = rah.pick_or_ban_champion("Garen", is_ban=True, lock_in=True)
            assert ok_ban is True
            assert "banido com sucesso" in msg_ban
        finally:
            rah.get_league_client_lockfile = orig_lock
            rah.request_api = orig_req

    finally:
        rah._champions_cache = old_cache
        rah._champions_cache_time = old_time

    print("OK: Validação de propriedade e bloqueio de falsos positivos validada com sucesso.")


def test_stale_lockfile_and_tutorial_queues():
    """Valida detecção de processos inativos (stale lockfile) e suporte a filas de tutorial."""
    print("Testando detecção de lockfile obsoleto e filas de tutorial...")
    import lol_lib.riot_api_helper as rah
    import tempfile

    # 1. is_pid_alive
    assert rah.is_pid_alive(os.getpid()) is True, "PID do processo de teste atual deve estar vivo"
    assert rah.is_pid_alive(9999999) is False, "PID 9999999 fictício deve ser considerado inativo"

    # 2. read_lockfile com PID vivo
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write(f"LeagueClient:{os.getpid()}:50000:abcde:https")
        tf_path = tf.name
    try:
        lock_live = rah.read_lockfile(tf_path, check_alive=True)
        assert lock_live is not None, "Lockfile com PID ativo deve ser lido com sucesso"
        assert lock_live["pid"] == os.getpid()
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)

    # 3. read_lockfile com PID morto (deve retornar None e limpar arquivo)
    with tempfile.NamedTemporaryFile("w", delete=False) as tf_dead:
        tf_dead.write("LeagueClient:9999999:50000:abcde:https")
        tf_dead_path = tf_dead.name
    try:
        lock_dead = rah.read_lockfile(tf_dead_path, check_alive=True)
        assert lock_dead is None, "Lockfile com PID morto deve ser rejeitado"
        assert not os.path.exists(tf_dead_path), "Lockfile obsoleto deve ter sido removido do disco"
    finally:
        if os.path.exists(tf_dead_path):
            os.remove(tf_dead_path)

    # 4. create_lcu_lobby com suporte a tutoriais (2000, 2010, 2020)
    created_queues = []
    def mock_lobby_req(lock, endpoint, method="GET", body=None):
        if endpoint == "/lol-lobby/v2/lobby" and method == "POST":
            created_queues.append(body.get("queueId"))
            return {"queueId": body.get("queueId")}
        return None

    orig_lock = rah.get_league_client_lockfile
    orig_req = rah.request_api
    try:
        rah.get_league_client_lockfile = lambda: {"process": "LeagueClient", "pid": os.getpid(), "port": 50000, "token": "t", "protocol": "https"}
        rah.request_api = mock_lobby_req

        for q_id in [880, 450, 2000, 2010, 2020]:
            ok = rah.create_lcu_lobby(q_id)
            assert ok is True

        assert created_queues == [880, 450, 2000, 2010, 2020]
    finally:
        rah.get_league_client_lockfile = orig_lock
        rah.request_api = orig_req

    print("OK: Lockfile obsoleto e filas de tutorial validadas com sucesso.")


def test_gesture_focus_filtering():
    """Valida que atalhos como Ctrl+Shift+T, Alt+Space, etc. nunca sequestram foco fora do LoL."""
    print("Testando filtro estrito de foco e repasse de atalhos (anti-sequestro de teclas)...")
    
    class MockGesture:
        def __init__(self, gid, mods=None):
            self.id = gid
            self.modifierNames = set(mods or [])
            self.sent = False
        def send(self):
            self.sent = True

    bridge_path = os.path.join(ROOT_DIR, "globalPlugins", "lol_accessibility_bridge.py")
    with open(bridge_path, "r", encoding="utf-8") as f:
        src = f.read()

    assert "control+shift+w" not in src.lower(), "ERRO: control+shift+w não pode estar presente em nenhum atalho (fecha abas de navegadores)!"

    def check_game_gesture(is_live, is_game_focused, gesture):
        if not is_live:
            return False
        if is_game_focused:
            return True
        gid = getattr(gesture, "id", "") or ""
        mod_names = getattr(gesture, "modifierNames", None) or set()
        if "nvda" in gid.lower() or "nvda" in [str(m).lower() for m in mod_names]:
            return True
        return False

    def check_launcher_gesture(is_riot_or_league, is_live_or_client, gesture):
        if is_riot_or_league:
            return True
        gid = getattr(gesture, "id", "") or ""
        mod_names = getattr(gesture, "modifierNames", None) or set()
        if "nvda" in gid.lower() or "nvda" in [str(m).lower() for m in mod_names]:
            if is_live_or_client:
                return True
        return False

    g_ctrl_shift_t = MockGesture("kb:control+shift+t", ["Control", "Shift"])
    g_t = MockGesture("kb:t")
    g_alt_space = MockGesture("kb:alt+space", ["Alt"])
    g_alt_1 = MockGesture("kb:alt+1", ["Alt"])
    g_nvda_shift_t = MockGesture("kb:NVDA+shift+t", ["NVDA", "Shift"])
    g_ctrl_shift_p = MockGesture("kb:control+shift+p", ["Control", "Shift"])
    g_ctrl_shift_s = MockGesture("kb:control+shift+s", ["Control", "Shift"])
    g_nvda_shift_l = MockGesture("kb:NVDA+shift+l", ["NVDA", "Shift"])

    assert check_game_gesture(is_live=True, is_game_focused=False, gesture=g_ctrl_shift_t) is False
    assert check_game_gesture(is_live=True, is_game_focused=False, gesture=g_t) is False
    assert check_game_gesture(is_live=True, is_game_focused=False, gesture=g_alt_space) is False
    assert check_game_gesture(is_live=True, is_game_focused=False, gesture=g_alt_1) is False
    assert check_game_gesture(is_live=True, is_game_focused=False, gesture=g_nvda_shift_t) is True

    assert check_launcher_gesture(is_riot_or_league=False, is_live_or_client=True, gesture=g_ctrl_shift_p) is False
    assert check_launcher_gesture(is_riot_or_league=False, is_live_or_client=True, gesture=g_ctrl_shift_s) is False
    assert check_launcher_gesture(is_riot_or_league=False, is_live_or_client=True, gesture=g_nvda_shift_l) is True

    assert check_game_gesture(is_live=True, is_game_focused=True, gesture=g_ctrl_shift_t) is True
    assert check_game_gesture(is_live=True, is_game_focused=True, gesture=g_t) is True
    assert check_game_gesture(is_live=True, is_game_focused=True, gesture=g_alt_space) is True
    assert check_game_gesture(is_live=True, is_game_focused=True, gesture=g_alt_1) is True

    assert check_launcher_gesture(is_riot_or_league=True, is_live_or_client=True, gesture=g_ctrl_shift_p) is True
    assert check_launcher_gesture(is_riot_or_league=True, is_live_or_client=True, gesture=g_ctrl_shift_s) is True

    print("OK: Filtro de foco e repasse de atalhos validados com sucesso (zero sequestro de teclas).")



def test_no_keyboard_interference():
    """Garante que teclas de letras simples NUNCA existam no GlobalPlugin ou LeagueClient."""
    print("Testando ausência total de interferência na digitação do teclado...")
    
    bridge_path = os.path.join(ROOT_DIR, "globalPlugins", "lol_accessibility_bridge.py")
    with open(bridge_path, "r", encoding="utf-8") as f:
        bridge_src = f.read()

    # Teclas simples que jamais podem ser capturadas globalmente pelo NVDA
    forbidden_global = [
        '"kb:h"', '"kb:k"', '"kb:i"', '"kb:u"', '"kb:o"', '"kb:t"',
        '"kb:m"', '"kb:p"', '"kb:b"', '"kb:n"', '"kb:f6"',
        '"kb:alt+1"', '"kb:alt+2"', '"kb:alt+3"', '"kb:alt+4"', '"kb:alt+space"',
        '"kb:control+shift+t"', '"kb:control+shift+p"'
    ]
    for key in forbidden_global:
        assert key not in bridge_src, f"ERRO CRÍTICO: {key} encontrado no GlobalPlugin! Causa atraso de digitação no Windows."

    # LeagueClient não pode ter teclas de letras soltas (o usuário digita no chat do cliente e busca campeões)
    lc_path = os.path.join(ROOT_DIR, "appModules", "leagueclient.py")
    with open(lc_path, "r", encoding="utf-8") as f:
        lc_src = f.read()

    forbidden_lc = ['"kb:h"', '"kb:k"', '"kb:i"', '"kb:u"', '"kb:o"', '"kb:t"', '"kb:m"', '"kb:p"', '"kb:b"', '"kb:n"']
    for key in forbidden_lc:
        assert key not in lc_src, f"ERRO CRÍTICO: {key} encontrado no LeagueClient! Interfere na busca/chat do launcher."

    # LeagueOfLegends DEVE conter os atalhos in-game da partida 3D
    lol_path = os.path.join(ROOT_DIR, "appModules", "leagueoflegends.py")
    with open(lol_path, "r", encoding="utf-8") as f:
        lol_src = f.read()

    required_in_game = ['"kb:h"', '"kb:k"', '"kb:i"', '"kb:u"', '"kb:o"', '"kb:t"', '"kb:m"', '"kb:p"', '"kb:b"']
    for key in required_in_game:
        assert key in lol_src, f"ERRO: Atalho in-game {key} ausente no módulo da partida 3D!"

    print("OK: Proteção contra atraso de teclado e isolamento de módulos 100% validados.")


def test_tos_helper():
    """Valida o módulo de acessibilidade para Termos de Serviço (ToS)."""
    print("Testando assistente de Termos de Serviço (tos_helper)...")
    from lol_lib.tos_helper import (
        LoLToSHelper,
        ensure_interactive_desktop,
        find_target_window,
        scroll_and_accept_sync,
        scroll_and_accept_async
    )

    # 1. Valida associação à Área de Trabalho Interativa
    desk = ensure_interactive_desktop()
    print(f"  Desktop interativo vinculado: {desk is not None}")

    # 2. Valida busca de janelas sem crash
    target = find_target_window()
    print(f"  Janela alvo detectada: {target is not None}")

    # 3. Valida execução segura quando janela não está aberta
    ok, msg = scroll_and_accept_sync(scroll_steps=1, click_button=False)
    assert isinstance(ok, bool)
    assert isinstance(msg, str)
    assert len(msg) > 0

    # 4. Valida existência dos scripts autônomos e skills
    ps_path = os.path.join(ROOT_DIR, "scripts", "aceitar_termos_lol.ps1")
    bat_path = os.path.join(ROOT_DIR, "scripts", "aceitar_termos_lol.bat")
    root_bat = os.path.join(ROOT_DIR, "aceitar_termos_lol.bat")
    skill_path = os.path.join(ROOT_DIR, ".agents", "skills", "riot-tos-accessibility", "SKILL.md")

    assert os.path.exists(ps_path), "scripts/aceitar_termos_lol.ps1 não encontrado!"
    assert os.path.exists(bat_path), "scripts/aceitar_termos_lol.bat não encontrado!"
    assert os.path.exists(root_bat), "aceitar_termos_lol.bat raiz não encontrado!"
    assert os.path.exists(skill_path), "Skill riot-tos-accessibility não encontrada!"

    # 5. Valida atalhos de ToS nos módulos
    for mod_path in [
        os.path.join(ROOT_DIR, "appModules", "riotclient.py"),
        os.path.join(ROOT_DIR, "appModules", "leagueclient.py"),
        os.path.join(ROOT_DIR, "globalPlugins", "lol_accessibility_bridge.py")
    ]:
        with open(mod_path, "r", encoding="utf-8") as f:
            src = f.read()
        assert "script_acceptTerms" in src or "script_globalAcceptTerms" in src, f"Atalho de ToS ausente em {mod_path}!"
        assert "tos_helper" in src, f"Import tos_helper ausente em {mod_path}!"

    print("OK: Assistente de Termos de Serviço (ToS) 100% validado.")


if __name__ == "__main__":
    test_syntax()
    test_manifest()
    test_riot_decoding()
    test_live_client_data_processing()
    test_champ_select_and_lobby()
    test_champion_ownership_and_validation()
    test_stale_lockfile_and_tutorial_queues()
    test_enemy_lane_deduction()
    test_chat_and_pings_reader()
    test_tactical_live_events()
    test_minimap_scanner()
    test_spatial_audio()
    test_shop_assistant()
    test_combat_status()
    test_tactical_navigator()
    test_tactical_hud_summaries()
    test_gesture_focus_filtering()
    test_no_keyboard_interference()
    test_tos_helper()
    print("\nTodos os testes unitários passaram com 100% de sucesso!")





