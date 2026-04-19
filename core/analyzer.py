"""用户游戏偏好分析"""
from collections import Counter
from typing import Dict, Any, List


def analyze_user_style(games_with_details: List[Dict]) -> Dict[str, Any]:
    """分析用户游戏偏好风格"""
    if not games_with_details:
        return {}

    genres_counter = Counter()
    categories_counter = Counter()
    multiplayer_count = 0
    total_playtime = 0

    for game in games_with_details:
        playtime = game.get('playtime', 0)
        total_playtime += playtime

        genres = game.get('genres', [])
        for g in genres:
            if g:
                genres_counter[g] += 1

        categories = game.get('categories', [])
        for c in categories:
            if c:
                categories_counter[c] += 1
                if 'multi' in c.lower() or '多人' in c:
                    multiplayer_count += 1

    game_count = len(games_with_details)
    avg_playtime = total_playtime // game_count if game_count > 0 else 0

    multiplayer_pref = multiplayer_count >= max(1, game_count // 2)

    return {
        'top_genres': [g for g, _ in genres_counter.most_common(5)],
        'top_categories': [c for c, _ in categories_counter.most_common(5)],
        'avg_playtime_minutes': avg_playtime,
        'multiplayer_pref': multiplayer_pref,
        'sample_games': [g.get('name') for g in games_with_details[:5]]
    }
