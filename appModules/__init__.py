# -*- coding: utf-8 -*-
try:
    import appModules
    if not hasattr(appModules, "EXECUTABLE_NAMES_TO_APP_MODS"):
        appModules.EXECUTABLE_NAMES_TO_APP_MODS = {}
    appModules.EXECUTABLE_NAMES_TO_APP_MODS.update({
        "league of legends": ("leagueoflegends", "leagueclient"),
        "league of legends.exe": ("leagueoflegends", "leagueclient"),
        "League of Legends": ("leagueoflegends", "leagueclient"),
        "League of Legends.exe": ("leagueoflegends", "leagueclient"),
        "leagueoflegends": ("leagueoflegends", "leagueclient"),
        "leagueoflegends.exe": ("leagueoflegends", "leagueclient"),
        "league_of_legends": ("leagueoflegends", "leagueclient"),
        "league_of_legends.exe": ("leagueoflegends", "leagueclient"),
        "LeagueClient": ("leagueclient",),
        "LeagueClient.exe": ("leagueclient",),
        "leagueclient": ("leagueclient",),
        "leagueclient.exe": ("leagueclient",),
        "leagueclientux": ("leagueclientux", "leagueclient"),
        "leagueclientux.exe": ("leagueclientux", "leagueclient"),
        "leagueclientuxrender": ("leagueclientuxrender", "leagueclient"),
        "leagueclientuxrender.exe": ("leagueclientuxrender", "leagueclient"),
        "riotclient": ("riotclient",),
        "riotclient.exe": ("riotclient",),
        "riot client": ("riotclient",),
        "riot client.exe": ("riotclient",),
        "riotclientux": ("riotclientux", "riotclient"),
        "riotclientux.exe": ("riotclientux", "riotclient"),
        "riotclientservices": ("riotclientservices", "riotclient"),
        "riotclientservices.exe": ("riotclientservices", "riotclient")
    })
except Exception:
    pass
