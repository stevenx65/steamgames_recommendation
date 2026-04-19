"""推荐生成主逻辑"""
import concurrent.futures
from typing import List, Dict, Any, Tuple
import requests
from config import MAX_CONCURRENT_REQUESTS, TOP_N_STORE_DETAILS, MAX_RECOMMENDATION_TIME
from services import get_owned_games, get_store_details, get_recommendations
from core.analyzer import analyze_user_style
from utils.http import create_session


def fetch_game_details_concurrent(
    games: List[Dict],
    session: requests.Session
) -> List[Dict]:
    """并发获取游戏详情"""
    results = []
    max_workers = max(1, min(MAX_CONCURRENT_REQUESTS, len(games)))

    def fetch_one(game: Dict) -> Dict:
        try:
            detail = get_store_details(game['appid'], session)
            if detail:
                return {
                    **game,
                    'metacritic_score': detail.get('metacritic_score'),
                    'genres': detail.get('genres', []),
                    'categories': detail.get('categories', []),
                    'current_players': detail.get('current_players', 0),
                    'release_date': detail.get('release_date'),
                    'is_free': detail.get('is_free', False),
                }
        except Exception:
            pass
        return game

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_one, g): g for g in games}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    return results


def generate_recommendation(steam_id: str, steam_key: str) -> str:
    """生成游戏推荐的完整流程"""
    session = create_session()

    print("\n🔍 正在获取你的游戏库...")
    try:
        user_games = get_owned_games(steam_id, steam_key, session)
    except Exception as e:
        return f"❌ 获取游戏库失败：{e}"

    if not user_games:
        return "❌ 未获取到游戏数据，请检查 Steam ID 和 API Key"

    print(f"✅ 已获取 {len(user_games)} 款游戏，正在分析 Top 10...")

    top_games = user_games[:10]
    games_with_details = fetch_game_details_concurrent(top_games, session)

    if not games_with_details:
        return "❌ 获取游戏详情失败"

    user_style = analyze_user_style(games_with_details)
    print("\n🧭 用户游戏风格摘要：")
    import json
    print(json.dumps(user_style, ensure_ascii=False, indent=2))

    print("\n🤖 正在生成推荐...")
    try:
        recommendation = get_recommendations(
            user_games,
            games_with_details,
            user_style,
            session
        )
        return recommendation
    except Exception as e:
        return f"❌ 生成推荐失败：{e}"
    finally:
        session.close()
