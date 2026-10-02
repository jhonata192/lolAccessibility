# -*- coding: utf-8 -*-
try:
    import appModules
    if hasattr(appModules, "EXECUTABLE_NAMES_TO_APP_MODS"):
        appModules.EXECUTABLE_NAMES_TO_APP_MODS.update({
            "league of legends": "leagueclient",
            "league of legends.exe": "leagueclient",
            "League of Legends": "leagueclient",
            "League of Legends.exe": "leagueclient",
            "leagueoflegends": "leagueclient",
            "leagueoflegends.exe": "leagueclient",
            "league_of_legends": "leagueclient",
            "league_of_legends.exe": "leagueclient",
            "LeagueClient": "leagueclient",
            "LeagueClient.exe": "leagueclient",
            "leagueclient": "leagueclient",
            "leagueclient.exe": "leagueclient",
            "leagueclientux": "leagueclient",
            "leagueclientux.exe": "leagueclient",
            "leagueclientuxrender": "leagueclient",
            "leagueclientuxrender.exe": "leagueclient",
            "riotclient": "riotclient",
            "riotclient.exe": "riotclient",
            "riot client": "riotclient",
            "riot client.exe": "riotclient",
            "riotclientux": "riotclient",
            "riotclientux.exe": "riotclient",
            "riotclientservices": "riotclient",
            "riotclientservices.exe": "riotclient"
        })
except Exception:
    pass
