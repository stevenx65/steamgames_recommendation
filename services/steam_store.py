"""Steam Store API 服务"""
import time
from typing import Dict, Any, Optional
import requests
from config import STEAM_STORE_HEADERS
from utils.cache import store_cache

def get_store_details(appid: int, session: requests.Session) -> Optional[Dict[str, Any]]:
    """从 Steam Store 获取游戏详情"""
    cached = store_cache.get(appid)
    if cached:
        return cached

    url = f"https://store.steampowered.com/api/appdetails"
    params = {"appids": appid, "cc": "us", "l": "schinese"}

    max_retries = 3
    backoff = 1

    for attempt in range(max_retries):
        try:
            response = session.get(
                url,
                params=params,
                headers=STEAM_STORE_HEADERS,
                timeout=20
            )
            response.raise_for_status()
            data = response.json()

            if str(appid) not in data or not data[str(appid)].get('success'):
                return None

            game_data = data[str(appid)]['data']

            result = {
                'name': game_data.get('name'),
                'metacritic_score': game_data.get('metacritic', {}).get('score'),
                'genres': [g.get('description') for g in game_data.get('genres', []) if g.get('description')],
                'categories': [c.get('description') for c in game_data.get('categories', []) if c.get('description')],
                'recommendations_total': game_data.get('recommendations', {}).get('total'),
                'release_date': game_data.get('release_date', {}).get('date'),
                'is_free': game_data.get('is_free', False),
            }

            store_cache.set(appid, result)
            time.sleep(0.06)
            return result

        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            continue
        except Exception:
            break

    return None
