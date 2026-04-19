"""SteamDB 服务"""
import time
from typing import Dict, Any, Optional
import requests
from config import STEAMDB_HEADERS
from utils.cache import steamdb_cache

def get_steamdb_details(appid: int, session: requests.Session) -> Optional[Dict[str, Any]]:
    """获取 SteamDB 游戏详情"""
    cached = steamdb_cache.get(appid)
    if cached:
        return cached

    url = f"https://steamdb.info/api/GetAppInfo/?appid={appid}"

    try:
        response = session.get(
            url,
            headers=STEAMDB_HEADERS,
            timeout=12
        )
        response.raise_for_status()

        text = response.text.strip()
        if not text or text.startswith("<"):
            return None

        data = response.json()
        if str(appid) not in data:
            return None

        game_data = data[str(appid)]
        result = {
            "steamdb_score": game_data.get("score", 0),
            "tags": game_data.get("tags", []),
            "players_peak_24h": game_data.get("players_peak_24h", 0),
            "players_peak_alltime": game_data.get("players_peak_alltime", 0)
        }

        steamdb_cache.set(appid, result)
        time.sleep(0.08)
        return result

    except Exception:
        return None
