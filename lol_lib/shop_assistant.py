# -*- coding: utf-8 -*-
"""
Assistente Acessível de Loja e Receitas de Itens para League of Legends.
Permite que jogadores com deficiência visual consultem o catálogo de itens,
verifiquem receitas, saibam quanto ouro falta para fechar seus itens
e comprem itens de forma 100% segura através do teclado.
"""

import time
import unicodedata
import re
import ctypes
from ctypes import wintypes

try:
    from logHandler import log
except Exception:
    import logging
    log = logging.getLogger("lol_shop_assistant")

try:
    from lol_lib.riot_api_helper import get_league_client_lockfile, request_api
except Exception:
    try:
        from riot_api_helper import get_league_client_lockfile, request_api
    except Exception:
        get_league_client_lockfile = lambda: None
        request_api = lambda *a, **kw: None


# Apelidos e atalhos populares de itens da comunidade brasileira de LoL
ITEM_ALIASES = {
    "bork": "Espada do Rei Destruído",
    "rei": "Espada do Rei Destruído",
    "reidestruido": "Espada do Rei Destruído",
    "trindade": "Força da Trindade",
    "triforce": "Força da Trindade",
    "gume": "Gume do Infinito",
    "ie": "Gume do Infinito",
    "infinity": "Gume do Infinito",
    "zhonya": "Ampulheta de Zhonya",
    "ampulheta": "Ampulheta de Zhonya",
    "rabadon": "Capuz da Morte de Rabadon",
    "capuz": "Capuz da Morte de Rabadon",
    "cutelo": "Cutelo Negro",
    "blackcleaver": "Cutelo Negro",
    "dançarina": "Dançarina Fantasma",
    "dancarina": "Dançarina Fantasma",
    "coleta": "A Coletora",
    "coletora": "A Coletora",
    "lembrança": "Lembranças do Lorde Dominik",
    "dominik": "Lembranças do Lorde Dominik",
    "passos": "Passos de Mercúrio",
    "mercurio": "Passos de Mercúrio",
    "tabi": "Botas Galvanizadas de Aço",
    "aço": "Botas Galvanizadas de Aço",
    "galvanizada": "Botas Galvanizadas de Aço",
    "lucidez": "Botas Ionianas da Lucidez",
    "ioniana": "Botas Ionianas da Lucidez",
    "berserker": "Grevas do Berserker",
    "grevas": "Grevas do Berserker",
    "hextrapolação": "Hexdrinker",
    "hexdrinker": "Hexdrinker",
    "fauce": "Fauce de Malmortius",
    "malmortius": "Fauce de Malmortius",
    "coração": "Coração de Aço",
    "espinhos": "Armadura de Espinhos",
    "thornmail": "Armadura de Espinhos",
    "solari": "Medalhão dos Solari de Ferro",
    "locket": "Medalhão dos Solari de Ferro",
    "luden": "Companheiro de Luden",
    "liandry": "Tormento de Liandry",
    "abraço": "Abraço de Seraph",
    "seraph": "Abraço de Seraph",
    "manopla": "Manopla dos Glacinatas",
    "hidra": "Hidra Titânica",
    "hidrarav": "Hidra Raivosa",
    "sinal": "Sinal de Sterak",
    "sterak": "Sinal de Sterak",
    "warmog": "Armadura de Warmog",
    "anjo": "Anjo Guardião",
    "ga": "Anjo Guardião",
    "sedenta": "Sedenta por Sangue",
    "bt": "Sedenta por Sangue",
    "cajado": "Cajado do Vazio",
    "void": "Cajado do Vazio",
    "morello": "Morellonomicon",
    "pocao": "Poção de Vida",
    "refil": "Poção com Refil",
}

# Base de itens essenciais para fallback caso a API LCU esteja temporariamente indisponível
FALLBACK_ITEMS = [
    {"id": 1001, "name": "Botas", "priceTotal": 300, "from": [], "to": [3006, 3009, 3020, 3047, 3111, 3158]},
    {"id": 3006, "name": "Grevas do Berserker", "priceTotal": 1100, "from": [1001, 1042], "to": []},
    {"id": 3009, "name": "Botas da Rapidez", "priceTotal": 900, "from": [1001], "to": []},
    {"id": 3020, "name": "Sapatos do Feiticeiro", "priceTotal": 1100, "from": [1001], "to": []},
    {"id": 3047, "name": "Botas Galvanizadas de Aço", "priceTotal": 1200, "from": [1001, 1029], "to": []},
    {"id": 3111, "name": "Passos de Mercúrio", "priceTotal": 1200, "from": [1001, 1033], "to": []},
    {"id": 3158, "name": "Botas Ionianas da Lucidez", "priceTotal": 900, "from": [1001], "to": []},
    {"id": 1055, "name": "Lâmina de Doran", "priceTotal": 450, "from": [], "to": []},
    {"id": 1056, "name": "Anel de Doran", "priceTotal": 400, "from": [], "to": []},
    {"id": 1054, "name": "Escudo de Doran", "priceTotal": 450, "from": [], "to": []},
    {"id": 2003, "name": "Poção de Vida", "priceTotal": 50, "from": [], "to": []},
    {"id": 2031, "name": "Poção com Refil", "priceTotal": 150, "from": [], "to": []},
    {"id": 3078, "name": "Força da Trindade", "priceTotal": 3333, "from": [3057, 3044, 3067], "to": []},
    {"id": 3031, "name": "Gume do Infinito", "priceTotal": 3400, "from": [1038, 1037, 1018], "to": []},
    {"id": 3153, "name": "Espada do Rei Destruído", "priceTotal": 3200, "from": [1043, 1053, 1036], "to": []},
    {"id": 3071, "name": "Cutelo Negro", "priceTotal": 3000, "from": [3044, 3067], "to": []},
    {"id": 3157, "name": "Ampulheta de Zhonya", "priceTotal": 3250, "from": [3191, 1058, 2420], "to": []},
    {"id": 3089, "name": "Capuz da Morte de Rabadon", "priceTotal": 3600, "from": [1058, 1058], "to": []},
    {"id": 3026, "name": "Anjo Guardião", "priceTotal": 3200, "from": [1038, 1031], "to": []},
    {"id": 3075, "name": "Armadura de Espinhos", "priceTotal": 2700, "from": [3076, 1011], "to": []},
    {"id": 3065, "name": "Semblante Espiritual", "priceTotal": 2900, "from": [3211, 3067], "to": []},
    {"id": 3068, "name": "Égide de Fogo Solar", "priceTotal": 2700, "from": [3751, 1031], "to": []},
    {"id": 3142, "name": "Lâmina Fantasma de Youmuu", "priceTotal": 2700, "from": [3134, 3133], "to": []},
    {"id": 6676, "name": "A Coletora", "priceTotal": 3200, "from": [3134, 1037, 1018], "to": []},
]


def normalize_name(text):
    """Remove acentos, pontuações e converte para minúsculas."""
    if not text:
        return ""
    t = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-zA-Z0-9]', '', t.lower())


class LoLShopAssistant:
    """
    Gerencia consultas de preços, receitas de itens e automação
    de compras para jogadores com deficiência visual.
    """

    def __init__(self):
        self._items_cache = None
        self._items_map = {}
        self._last_load_time = 0

    def load_items(self, force=False):
        """Carrega e indexa a lista de itens da Riot via LCU ou fallback."""
        now = time.time()
        if not force and self._items_cache and (now - self._last_load_time < 300.0):
            return self._items_cache

        lock = get_league_client_lockfile()
        items_data = None
        if lock:
            raw = request_api(lock, "/lol-game-data/assets/v1/items.json")
            if raw and isinstance(raw, list):
                items_data = raw

        if not items_data:
            items_data = FALLBACK_ITEMS

        self._items_map = {}
        valid_items = []
        for it in items_data:
            iid = it.get("id", 0)
            name = (it.get("name") or "").strip()
            price = it.get("priceTotal", it.get("price", 0))
            if iid > 0 and name and price >= 0:
                item_obj = {
                    "id": iid,
                    "name": name,
                    "price": price,
                    "from": [int(x) for x in it.get("from", [])],
                    "to": [int(x) for x in it.get("to", [])],
                    "categories": it.get("categories", []),
                    "norm_name": normalize_name(name)
                }
                self._items_map[iid] = item_obj
                valid_items.append(item_obj)

        self._items_cache = valid_items
        self._last_load_time = now
        return self._items_cache

    def get_item_by_id(self, item_id):
        """Retorna os dados de um item pelo seu ID numérico."""
        if not self._items_map:
            self.load_items()
        return self._items_map.get(int(item_id))

    def find_item_by_name(self, query):
        """Localiza um item por nome exato, parcial ou apelido popular."""
        if not query:
            return None
        if not self._items_cache:
            self.load_items()

        qn = normalize_name(query)
        target_name = ITEM_ALIASES.get(qn, query)
        target_norm = normalize_name(target_name)

        # 1. Correspondência exata
        for it in self._items_cache:
            if it["norm_name"] == target_norm:
                return it

        # 2. Inicia com
        for it in self._items_cache:
            if it["norm_name"].startswith(target_norm):
                return it

        # 3. Contém substring
        for it in self._items_cache:
            if target_norm in it["norm_name"]:
                return it

        return None

    def analyze_inventory_and_gold(self, current_gold, inventory_items):
        """
        Analisa os itens atualmente no inventário e calcula:
        - Itens que o jogador pode fechar ou comprar imediatamente com o ouro atual.
        - Itens em progresso de construção e quanto ouro falta para completar cada um.
        """
        if not self._items_map:
            self.load_items()

        inv_ids = []
        inv_names = []
        for it in inventory_items or []:
            iid = it.get("itemID") or it.get("id") or 0
            if iid > 0:
                inv_ids.append(int(iid))
                inv_names.append(it.get("displayName") or it.get("name") or f"Item {iid}")

        # Identificar itens superiores que são construídos a partir dos componentes possuídos
        potential_upgrades = set()
        for iid in inv_ids:
            cur = self.get_item_by_id(iid)
            if cur and cur.get("to"):
                for up_id in cur["to"]:
                    potential_upgrades.add(up_id)

        in_progress = []
        can_buy_now = []

        for up_id in potential_upgrades:
            up_item = self.get_item_by_id(up_id)
            if not up_item:
                continue

            total_price = up_item["price"]
            # Calcular desconto dos componentes que o jogador já comprou
            components = list(up_item.get("from", []))
            owned_discount = 0
            for comp_id in components:
                if comp_id in inv_ids:
                    comp_item = self.get_item_by_id(comp_id)
                    if comp_item:
                        owned_discount += comp_item["price"]

            cost_to_finish = max(0, total_price - owned_discount)
            gold_needed = max(0, cost_to_finish - current_gold)

            info = {
                "id": up_id,
                "name": up_item["name"],
                "total_price": total_price,
                "cost_to_finish": cost_to_finish,
                "gold_needed": gold_needed,
                "can_buy": cost_to_finish <= current_gold
            }

            if info["can_buy"]:
                can_buy_now.append(info)
            else:
                in_progress.append(info)

        # Se não tiver botas no inventário, sugere Botas básicas se tiver ouro suficiente
        has_boots = any("bota" in normalize_name(name) or "grevas" in normalize_name(name) or "sapatos" in normalize_name(name) for name in inv_names)
        if not has_boots:
            boots_item = self.get_item_by_id(1001)
            if boots_item:
                b_info = {
                    "id": 1001,
                    "name": "Botas",
                    "total_price": 300,
                    "cost_to_finish": 300,
                    "gold_needed": max(0, 300 - current_gold),
                    "can_buy": current_gold >= 300
                }
                if b_info["can_buy"]:
                    can_buy_now.append(b_info)
                else:
                    in_progress.append(b_info)

        return {
            "gold": int(current_gold),
            "inventory_count": len(inv_ids),
            "can_buy_now": sorted(can_buy_now, key=lambda x: x["cost_to_finish"], reverse=True),
            "in_progress": sorted(in_progress, key=lambda x: x["gold_needed"])
        }

    def format_shop_speech(self, analysis):
        """Gera texto claro e conciso para ser anunciado pelo leitor de telas."""
        gold = analysis["gold"]
        can_buy = analysis["can_buy_now"]
        in_prog = analysis["in_progress"]

        parts = [f"Loja: você tem {gold} de ouro."]

        if can_buy:
            buy_names = [f"{b['name']} ({b['cost_to_finish']} ouro)" for b in can_buy[:3]]
            parts.append("Pronto para comprar: " + ", ".join(buy_names) + ".")
        else:
            parts.append("Nenhum item completo pronto para compra imediata.")

        if in_prog:
            prog_names = [f"{p['name']} (faltam {p['gold_needed']})" for p in in_prog[:2]]
            parts.append("Em construção: " + ", ".join(prog_names) + ".")

        parts.append("Pressione Control+Shift+P para abrir o diálogo de compras.")
        return " ".join(parts)

    @staticmethod
    def buy_item_via_keys(item_name):
        """
        Executa a sequência de compra dentro do League of Legends
        usando comandos de teclado 100% nativos e seguros (Vanguard safe):
        1. 'P' para abrir a loja
        2. 'Ctrl + L' para focar campo de busca
        3. Digita o nome do item
        4. 'Enter' para comprar
        5. 'Escape' para fechar a loja
        """
        if not item_name:
            return False

        user32 = ctypes.windll.user32
        VK_CONTROL = 0x11
        VK_RETURN = 0x0D
        VK_ESCAPE = 0x1B
        KEYEVENTF_KEYUP = 0x0002

        def press_key(vk):
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)

        def type_text(text):
            for char in text:
                # Envia tecla via caracter unicode
                user32.keybd_event(0, ord(char.upper()), 0, 0)
                time.sleep(0.015)
                user32.keybd_event(0, ord(char.upper()), KEYEVENTF_KEYUP, 0)
                time.sleep(0.015)

        try:
            # 1. Abrir loja (tecla P)
            press_key(ord('P'))
            time.sleep(0.20)

            # 2. Focar campo de busca da loja (Ctrl + L)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            press_key(ord('L'))
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.12)

            # 3. Digitar nome do item
            type_text(item_name)
            time.sleep(0.15)

            # 4. Confirmar e comprar (Enter duas vezes)
            press_key(VK_RETURN)
            time.sleep(0.08)
            press_key(VK_RETURN)
            time.sleep(0.15)

            # 5. Fechar loja (Escape)
            press_key(VK_ESCAPE)
            return True
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao comprar item via teclas: {e}")
            return False
