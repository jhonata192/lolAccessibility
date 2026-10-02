# -*- coding: utf-8 -*-
"""
Módulo de Aplicativo NVDA para a Janela da Partida 3D do League of Legends (League of Legends.exe).
Ativo EXCLUSIVAMENTE quando a janela do jogo 3D (RiotWindowClass) está em primeiro plano:
- H: Consulta Vida atual, Recursos (Mana/Energia) e Ouro.
- K: Consulta KDA (Abates/Mortes/Assistências) e Farm de tropas (CS).
- I: Consulta Itens comprados e Ouro atual.
- U: Consulta Nível e Tempo de Recarga de todas as Habilidades (Q, W, E, R).
- O: Consulta Inimigos Vivos e Mortos.
- T: Consulta Tempo de Jogo decorrido e modo de jogo.
- M: Executa a Varredura do Radar de Áudio Espacial 3D com bips estéreo.
- P: Abre a Loja Acessível com recomendações e árvore de compras.
- B: Inicia Retorno à Base (Recall) com áudio e monitoramento de interrupção por dano.
- Alt+1..4: Navegação tática no minimapa (Top, Mid, Bot, Base).
- Alt+Espaço: Centraliza a câmera e o cursor do mouse no Campeão.
- F6: Aceita partida encontrada ou pausa/retoma.
- Combinações Control+Shift correspondentes para cada função.

Isola completamente todas as teclas de letras simples dentro do League of Legends.exe,
garantindo ZERO atraso ou interferência na digitação em qualquer outro programa do Windows.
"""

import os
import sys
import ui
import tones
from scriptHandler import script, getLastScriptRepeatCount
from logHandler import log

from . import leagueclient

try:
    from lol_lib.riot_api_helper import (
        is_live_game_active,
        get_live_active_player,
        get_live_active_player_abilities,
        get_live_player_list,
        get_live_game_stats,
        get_live_enemy_lane_assignments,
        format_scoreboard_summary,
        format_champion_stats_summary,
        format_objectives_summary,
        format_enemies_summary
    )
except Exception:
    try:
        from riot_api_helper import (
            is_live_game_active,
            get_live_active_player,
            get_live_active_player_abilities,
            get_live_player_list,
            get_live_game_stats,
            get_live_enemy_lane_assignments,
            format_scoreboard_summary,
            format_champion_stats_summary,
            format_objectives_summary,
            format_enemies_summary
        )
    except Exception:
        is_live_game_active = lambda: False
        get_live_active_player = lambda: None
        get_live_active_player_abilities = lambda: None
        get_live_player_list = lambda: []
        get_live_game_stats = lambda: None
        get_live_enemy_lane_assignments = lambda: {}
        format_scoreboard_summary = lambda data=None: "Placar indisponível."
        format_champion_stats_summary = lambda data=None: "Estatísticas indisponíveis."
        format_objectives_summary = lambda data=None: "Objetivos indisponíveis."
        format_enemies_summary = lambda data=None: "Inimigos indisponíveis."


class AppModule(leagueclient.AppModule):
    """Módulo NVDA ativo estritamente durante a partida 3D ao vivo do League of Legends."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.info("lolAccessibility: AppModule League of Legends (Partida 3D In-Game) inicializado com sucesso.")

    # ========================================================================
    # ATALHOS IN-GAME DE TECLA ÚNICA E COMBINAÇÕES TÁTICAS
    # ========================================================================

    @script(
        description="Consulta a Vida e Recursos atuais do jogador na partida (tecla H).",
        gestures=["kb:h", "kb:control+shift+h"]
    )
    def script_queryHealth(self, gesture):
        player = get_live_active_player()
        if not player:
            gesture.send()
            return
        stats = player.get("championStats") or player.get("champion_stats") or {}
        hp = int(stats.get("currentHealth") or stats.get("current_health") or 0)
        max_hp = int(stats.get("maxHealth") or stats.get("max_health") or 1)
        pct = int((hp / max_hp) * 100) if max_hp > 0 else 0
        res_type = (stats.get("resourceType") or stats.get("resource_type") or "MANA").capitalize()
        res_val = int(stats.get("resourceValue") or stats.get("resource_value") or 0)
        res_max = int(stats.get("resourceMax") or stats.get("resource_max") or 1)
        res_pct = int((res_val / res_max) * 100) if res_max > 0 else 0
        gold = int(player.get("currentGold") or player.get("current_gold") or 0)
        ui.message(f"Vida: {hp} de {max_hp} ({pct}%). {res_type}: {res_val} de {res_max} ({res_pct}%). Ouro: {gold}.")

    @script(
        description="Consulta o Placar e KDA do jogador na partida (tecla K).",
        gestures=["kb:k", "kb:control+shift+k"]
    )
    def script_queryKDA(self, gesture):
        player = get_live_active_player()
        if not player:
            gesture.send()
            return
        scores = player.get("scores") or {}
        k = scores.get("kills", 0)
        d = scores.get("deaths", 0)
        a = scores.get("assists", 0)
        cs = scores.get("creepScore") or scores.get("creep_score") or 0
        ui.message(f"KDA: {k} abates, {d} mortes, {a} assistências. Farm: {cs} tropas.")

    @script(
        description="Consulta os Itens comprados e Ouro atual (tecla I).",
        gestures=["kb:i", "kb:control+shift+i"]
    )
    def script_queryItems(self, gesture):
        player = get_live_active_player()
        if not player:
            gesture.send()
            return
        gold = int(player.get("currentGold") or player.get("current_gold") or 0)
        items = player.get("items", [])
        item_names = [it.get("displayName") or it.get("display_name") or "Item" for it in items if it.get("slot", 0) < 6 and (it.get("count", 0) > 0 or "count" not in it)]
        items_str = ", ".join(item_names) if item_names else "Nenhum item comprado"
        ui.message(f"Ouro: {gold}. Itens: {items_str}.")

    @script(
        description="Consulta o status, nível e tempo de recarga de todas as habilidades (tecla U).",
        gestures=["kb:u", "kb:control+shift+u"]
    )
    def script_queryAbilities(self, gesture):
        combat = getattr(self, "_combat_status", None)
        abilities = get_live_active_player_abilities()
        if combat and abilities:
            ui.message(combat.get_abilities_summary(abilities))
            return
        player = get_live_active_player()
        lvl = player.get("level", 1) if player else 1
        champ = player.get("championName") or player.get("champion_name") or "Campeão" if player else "Campeão"
        if not abilities:
            ui.message(f"{champ}, Nível {lvl}.")
            return
        details = []
        for key in ["Q", "W", "E", "R"]:
            ab = abilities.get(key, {})
            ab_lvl = ab.get("abilityLevel") or ab.get("ability_level") or 0
            details.append(f"{key}: nível {ab_lvl}")
        ui.message(f"{champ} nível {lvl}. Habilidades: " + ", ".join(details))

    @script(
        description="Anuncia quais inimigos estão vivos ou mortos (tecla O).",
        gestures=["kb:o", "kb:control+shift+o"]
    )
    def script_queryEnemies(self, gesture):
        players = get_live_player_list()
        active = get_live_active_player()
        if not players or not active:
            gesture.send()
            return
        my_team = active.get("team", "ORDER")
        enemies = [p for p in players if p.get("team") != my_team]
        dead = [p.get("championName") or p.get("champion_name") or "Inimigo" for p in enemies if p.get("isDead", False) or p.get("is_dead", False)]
        alive = [p.get("championName") or p.get("champion_name") or "Inimigo" for p in enemies if not (p.get("isDead", False) or p.get("is_dead", False))]
        if not dead:
            ui.message(f"Todos os {len(enemies)} inimigos estão vivos.")
        else:
            ui.message(f"Inimigos mortos: {', '.join(dead)}. Vivos: {', '.join(alive)}.")

    @script(
        description="Consulta o Tempo de Jogo da partida (tecla T).",
        gestures=["kb:t", "kb:control+shift+t"]
    )
    def script_queryGameTime(self, gesture):
        stats = get_live_game_stats()
        if not stats:
            ui.message("Tempo de jogo indisponível no momento.")
            return
        t = int(stats.get("gameTime") or stats.get("game_time") or 0)
        m = t // 60
        s = t % 60
        mode = stats.get("gameMode") or stats.get("game_mode") or "LoL"
        ui.message(f"Tempo de jogo: {m} minutos e {s} segundos ({mode}).")

    @script(
        description="Consulta as rotas dos inimigos deduzidas via heurística.",
        gestures=["kb:control+shift+e"]
    )
    def script_queryEnemyLanes(self, gesture):
        lane_info = get_live_enemy_lane_assignments()
        if not lane_info:
            ui.message("Rotas inimigas indisponíveis no momento.")
            return
        count = getLastScriptRepeatCount()
        if count >= 1:
            spells_txt = lane_info.get("spells_summary", "")
            if spells_txt:
                ui.message(spells_txt)
            else:
                ui.message("Feitiços inimigos indisponíveis.")
        else:
            txt = lane_info.get("text", "")
            if txt:
                ui.message(txt)
            else:
                ui.message("Rotas inimigas não identificadas.")

    @script(
        description="Consulta mensagens e pings recentes do chat da partida.",
        gestures=["kb:control+shift+m"]
    )
    def script_queryChatAndPings(self, gesture):
        reader = getattr(self, "_chat_reader", None)
        if not reader:
            ui.message("Leitor de chat indisponível.")
            return
        count = getLastScriptRepeatCount()
        if count >= 1:
            new_items = reader.scan_chat_sync()
            if new_items:
                msgs = [it.get("announcement", "") for it in new_items if it.get("announcement")]
                ui.message(". ".join(msgs))
            else:
                summary = reader.get_recent_summary(max_count=5)
                ui.message(f"Varredura concluída. {summary}")
        else:
            summary = reader.get_recent_summary(max_count=3)
            ui.message(summary)

    @script(
        description="Consulta o status tático do minimapa.",
        gestures=["kb:control+shift+n"]
    )
    def script_queryMinimap(self, gesture):
        scanner = getattr(self, "_minimap_scanner", None)
        if not scanner:
            ui.message("Scanner de minimapa indisponível.")
            return

        active = get_live_active_player() or {}
        players = get_live_player_list() or []
        my_team = "ORDER"
        summoner = active.get("summonerName", "")
        for p in players:
            if p.get("summonerName") == summoner:
                my_team = p.get("team", "ORDER")
                break

        live_data = {"allPlayers": players, "gameData": get_live_game_stats() or {}}
        count = getLastScriptRepeatCount()
        if count >= 1:
            msg = scanner.get_tactical_summary(live_data=live_data, my_team=my_team, detailed=True)
        else:
            msg = scanner.get_tactical_summary(live_data=live_data, my_team=my_team, detailed=False)
        ui.message(msg)

    @script(
        description="Executa a Varredura do Radar de Áudio Espacial 3D (tecla M).",
        gestures=["kb:m"]
    )
    def script_queryRadarSweep(self, gesture):
        scanner = getattr(self, "_minimap_scanner", None)
        if not scanner:
            ui.message("Scanner de radar indisponível.")
            return

        active = get_live_active_player() or {}
        players = get_live_player_list() or []
        my_team = "ORDER"
        summoner = active.get("summonerName", "")
        for p in players:
            if p.get("summonerName") == summoner:
                my_team = p.get("team", "ORDER")
                break

        lane_info = get_live_enemy_lane_assignments()
        my_lane = "BOTTOM"
        if lane_info and lane_info.get("my_assigned_lane"):
            my_lane = lane_info.get("my_assigned_lane")

        scan = scanner.scan_radar(player_lane=my_lane, my_team=my_team)
        if not scan:
            ui.message("Não foi possível capturar o radar no momento.")
            return

        player = getattr(self, "_spatial_player", None)
        if player:
            player.play_radar_sweep(scan.get("targets", []))

        ui.message(scan.get("text", "Radar executado."))

    @script(
        description="Alterna o Radar de Proximidade de Áudio Espacial 3D em tempo real.",
        gestures=["kb:control+shift+r"]
    )
    def script_toggleAudioRadar(self, gesture):
        self._spatial_radar_enabled = not getattr(self, "_spatial_radar_enabled", True)
        state = "ativado" if self._spatial_radar_enabled else "desativado"
        player = getattr(self, "_spatial_player", None)
        if player:
            if self._spatial_radar_enabled:
                player.play_spatial_tone(880, 80, -0.6, volume=0.6)
                player.play_spatial_tone(1175, 100, 0.6, volume=0.6)
            else:
                player.play_spatial_tone(880, 80, 0.6, volume=0.6)
                player.play_spatial_tone(440, 100, -0.6, volume=0.6)
        ui.message(f"Radar de áudio espacial 3D {state}.")

    @script(
        description="Alterna a leitura automática de pings e chat durante a partida.",
        gestures=["kb:control+shift+f7"]
    )
    def script_toggleAutoPings(self, gesture):
        self.auto_pings_enabled = not getattr(self, "auto_pings_enabled", True)
        state = "ativada" if self.auto_pings_enabled else "desativada"
        ui.message(f"Leitura automática de chat e pings {state}.")

    @script(
        description="Alterna o alerta automático de emboscadas e presença de inimigos (Alerta de Gank).",
        gestures=["kb:control+shift+f8"]
    )
    def script_toggleGankAlerts(self, gesture):
        self.auto_gank_alerts_enabled = not getattr(self, "auto_gank_alerts_enabled", True)
        state = "ativado" if self.auto_gank_alerts_enabled else "desativado"
        ui.message(f"Alerta sonoro de emboscadas {state}.")

    @script(
        description="Abre a Loja Acessível durante a partida (tecla P ou Control+Shift+P).",
        gestures=["kb:p", "kb:control+shift+p"]
    )
    def script_shopKey(self, gesture):
        self._open_in_game_shop()

    @script(
        description="Inicia o retorno à base (Recall / tecla B) com áudio e monitor de dano/interrupção.",
        gestures=["kb:b"]
    )
    def script_recallKey(self, gesture):
        active = get_live_active_player() or {}
        stats = active.get("championStats", {})
        cur_hp = stats.get("currentHealth", 1000.0)
        combat = getattr(self, "_combat_status", None)
        if combat:
            msg = combat.start_recall(cur_hp)
            ui.message(msg)
        gesture.send()

    @script(
        description="Move o campeão pelo minimapa para a Rota Superior (Top Lane).",
        gestures=["kb:alt+1"]
    )
    def script_navTop(self, gesture):
        nav = getattr(self, "_tactical_navigator", None)
        if nav:
            ok, msg = nav.navigate_to("TOP")
            ui.message(msg)
        else:
            ui.message("Navegador indisponível.")

    @script(
        description="Move o campeão pelo minimapa para a Rota do Meio (Mid Lane).",
        gestures=["kb:alt+2"]
    )
    def script_navMid(self, gesture):
        nav = getattr(self, "_tactical_navigator", None)
        if nav:
            ok, msg = nav.navigate_to("MID")
            ui.message(msg)
        else:
            ui.message("Navegador indisponível.")

    @script(
        description="Move o campeão pelo minimapa para a Rota Inferior (Bot Lane).",
        gestures=["kb:alt+3"]
    )
    def script_navBot(self, gesture):
        nav = getattr(self, "_tactical_navigator", None)
        if nav:
            ok, msg = nav.navigate_to("BOT")
            ui.message(msg)
        else:
            ui.message("Navegador indisponível.")

    @script(
        description="Move o campeão pelo minimapa de volta para a Base Aliada (Fonte Segura).",
        gestures=["kb:alt+4"]
    )
    def script_navBase(self, gesture):
        nav = getattr(self, "_tactical_navigator", None)
        if nav:
            ok, msg = nav.navigate_to("BASE")
            ui.message(msg)
        else:
            ui.message("Navegador indisponível.")

    @script(
        description="Centraliza a câmera e o cursor do mouse no Campeão.",
        gestures=["kb:alt+space"]
    )
    def script_centerChampion(self, gesture):
        nav = getattr(self, "_tactical_navigator", None)
        if nav:
            ok, msg = nav.center_camera_and_cursor()
            ui.message(msg)
        else:
            ui.message("Navegador indisponível.")

    @script(
        description="Abre o menu completo de navegação e waypoints de Summoner's Rift.",
        gestures=["kb:control+shift+w"]
    )
    def script_navMenu(self, gesture):
        nav = getattr(self, "_tactical_navigator", None)
        if not nav:
            ui.message("Navegador tático indisponível.")
            return
        team = nav.get_player_team()
        def _do_nav(target_key):
            ok, msg = nav.navigate_to(target_key, team=team)
            ui.message(msg)
        leagueclient.prompt_navigation_dialog(_do_nav, team=team)

    @script(
        description="Consulta o placar da partida: KDA do jogador, tropas (CS) e placar geral de abates.",
        gestures=["kb:control+shift+k"]
    )
    def script_queryScoreboard(self, gesture):
        ui.message(format_scoreboard_summary())

    @script(
        description="Consulta as estatísticas detalhadas do campeão (vida, mana/energia, atributos).",
        gestures=["kb:control+shift+s"]
    )
    def script_queryStats(self, gesture):
        ui.message(format_champion_stats_summary())

    @script(
        description="Consulta o tempo de jogo e status de objetivos globais (dragões, barões, torres).",
        gestures=["kb:control+shift+o"]
    )
    def script_queryObjectives(self, gesture):
        ui.message(format_objectives_summary())
