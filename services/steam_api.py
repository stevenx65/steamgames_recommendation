"""Steam API 服务"""
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

STEAM_API_BASE = "https://api.steampowered.com"

def get_owned_games(steam_id: str, api_key: str, session: requests.Session) -> List[Dict[str, Any]]:
    """获取用户 Steam 游戏库"""
    url = f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": api_key,
        "steamid": steam_id,
        "include_appinfo": 1,
        "include_played_free_games": 1,
        "format": "json"
    }

    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    games = []
    if "response" in data and "games" in data["response"]:
        for game in data["response"]["games"]:
            if game["playtime_forever"] > 0:
                games.append({
                    "appid": game["appid"],
                    "name": game["name"],
                    "playtime": game["playtime_forever"]
                })

    games.sort(key=lambda x: x["playtime"], reverse=True)
    return games


def get_current_players(appid: int, session: requests.Session) -> Optional[int]:
    """获取游戏当前在线人数"""
    url = f"{STEAM_API_BASE}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    params = {"appid": appid}

    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('response', {}).get('player_count')
    except Exception:
        return None
