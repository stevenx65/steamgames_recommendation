import os
import json
import time
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import concurrent.futures
from pathlib import Path
# -------------------------- 配置区域 --------------------------
# 1. 加载环境变量（DeepSeek API Key）
load_dotenv()
# 尝试从标准 .env 加载；若未命中则尝试项目根目录下的 `DEEPSEEK_API_KEY.env`
# 这样方便用户将 API Key 放在单独文件而不污染通用 .env
DEEPSEEK_API_KEY = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
if not DEEPSEEK_API_KEY:
    alt_env = Path(__file__).with_name('DEEPSEEK_API_KEY.env')
    if alt_env.exists():
        load_dotenv(str(alt_env))
        DEEPSEEK_API_KEY = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
if not DEEPSEEK_API_KEY:
    print("⚠️ 未检测到 `DEEPSEEK_API_KEY` 环境变量；请在环境或 `DEEPSEEK_API_KEY.env` 文件中设置。示例：\nDEEPSEEK_API_KEY=your_api_key_here\n不要将密钥提交到版本控制。")
# 注意：不再在代码中提供默认的 Steam API Key，请在运行时通过输入或环境变量提供你的 Steam API Key。

# 本地缓存文件（用于缓存 SteamDB 请求结果，节省重复网络开销）
STEAMDB_CACHE_FILE = Path(__file__).with_suffix('.steamdb_cache.json')
# 新增：官方商店缓存文件
STORE_CACHE_FILE = Path(__file__).with_suffix('.store_cache.json')

# 2. SteamDB反爬请求头
STEAMDB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Referer": "https://steamdb.info/",
    "X-Requested-With": "XMLHttpRequest",
}
# 新增：官方商店请求头（模拟浏览器，减少被拒绝或限流的概率）
STEAM_STORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://store.steampowered.com/",
}

# 3. DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"  # 或 deepseek-coder-v2（适合专业领域）

# 4. 推荐逻辑Prompt
RECOMMEND_PROMPT = """
你是专业的Steam游戏推荐助手，需基于用户的Steam游戏数据，推荐5款游戏，严格遵循以下规则：

【核心规则】
1. 偏好分析：从用户游戏库中提取「游玩时长TOP10的游戏」和「高频标签TOP3」（如开放世界、RPG、多人联机）；
2. 推荐要求：
    - 排除用户已购/已游玩的游戏；
    - 选择SteamDB评分≥8.0、近30天在线峰值≥1万的游戏（如无则选择尽量匹配用户偏好的高质量作品）；
    - 5款游戏需差异化（例如：1款开放世界RPG、1款ARPG、1款多人派对、1款独立精品、1款策略或模拟）；
    - 优先推荐近6个月内更新或2024年后发布的新作；
3. 输出格式（固定，不可修改）：
    1. 《游戏名称》（英文原名）
        - 类型：XXX | SteamDB评分：XXX | 在线峰值：XXX
        - 匹配点：精准关联用户过往游戏（例如「你《艾尔登法环》游玩156分钟，偏好开放世界探索，本作的地图设计与剧情自由度高度契合」）
        - 购买链接：https://store.steampowered.com/app/游戏APPID/
    2. （同上格式）
    3. （同上格式）
    4. （同上格式）
    5. （同上格式）
4. 补充要求：匹配点需具体，避免笼统描述；购买链接需替换为对应游戏的Steam商店页。
"""
# -------------------------- 配置结束 --------------------------


# 并发与缓存调优配置（可通过环境变量调整）
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '6'))
TOP_N_STORE_DETAILS = int(os.getenv('TOP_N_STORE_DETAILS', '5'))
# 对整个推荐流程的超时保护（秒），防止无限挂起
MAX_RECOMMENDATION_TIME = int(os.getenv('MAX_RECOMMENDATION_TIME', '120'))
# 调试：是否保存/打印发送给 DeepSeek 的 messages（仅用于本地调试，不包含 Authorization）
DEBUG_DEEPSEEK_MESSAGES = os.getenv('DEBUG_DEEPSEEK_MESSAGES', '0').lower() in ('1', 'true', 'yes')
DEEPSEEK_MESSAGES_FILE = Path(__file__).with_name('deepseek_messages.jsonl')

# 初始化requests会话（重试机制+SSL跳过）
session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[403, 500, 502, 503, 504],
)
# 增加连接池，以提升高并发场景下的连接复用和速度
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 载入或初始化 steamdb 缓存
try:
    if STEAMDB_CACHE_FILE.exists():
        with STEAMDB_CACHE_FILE.open('r', encoding='utf-8') as f:
            STEAMDB_CACHE = json.load(f)
    else:
        STEAMDB_CACHE = {}
except Exception:
    STEAMDB_CACHE = {}

# 载入或初始化 store 缓存
try:
    if STORE_CACHE_FILE.exists():
        with STORE_CACHE_FILE.open('r', encoding='utf-8') as f:
            STORE_CACHE = json.load(f)
    else:
        STORE_CACHE = {}
except Exception:
    STORE_CACHE = {}

# 缓存脏标记：避免每次更新都做磁盘写入，改为批量保存以提升性能
STEAMDB_CACHE_DIRTY = False
STORE_CACHE_DIRTY = False

# 最近发布/更新列表缓存（减少对 Steam 商店的频繁抓取）
RECENT_RELEASES_CACHE = {
    'fetched_at': 0,
    'data': []
}
RECENT_RELEASES_TTL = int(os.getenv('RECENT_RELEASES_TTL', '3600'))  # 秒


def _save_steamdb_cache():
    try:
        with STEAMDB_CACHE_FILE.open('w', encoding='utf-8') as f:
            json.dump(STEAMDB_CACHE, f, ensure_ascii=False, indent=2)
        global STEAMDB_CACHE_DIRTY
        STEAMDB_CACHE_DIRTY = False
    except Exception:
        pass


def _save_store_cache():
    try:
        with STORE_CACHE_FILE.open('w', encoding='utf-8') as f:
            json.dump(STORE_CACHE, f, ensure_ascii=False, indent=2)
        global STORE_CACHE_DIRTY
        STORE_CACHE_DIRTY = False
    except Exception:
        pass


def save_all_caches():
    """批量保存两个缓存到磁盘（在批量请求结束后调用以减少 I/O 写操作）"""
    if STEAMDB_CACHE_DIRTY:
        _save_steamdb_cache()
    if STORE_CACHE_DIRTY:
        _save_store_cache()


def get_user_games(steam_id, steam_key):
    """获取用户Steam游戏库"""
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": steam_key,
        "steamid": steam_id,
        "include_appinfo": 1,
        "include_played_free_games": 1,
        "format": "json"
    }
    try:
        response = session.get(url, params=params, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()
        valid_games = []
        if "response" in data and "games" in data["response"]:
            for game in data["response"]["games"]:
                if game["playtime_forever"] > 0 and game["appid"] not in [221410, 107410]:  # 排除工具类游戏
                    valid_games.append({
                        "appid": game["appid"],
                        "name": game["name"],
                        "playtime": game["playtime_forever"]
                    })
        # 按游玩时长排序（降序）
        valid_games.sort(key=lambda x: x["playtime"], reverse=True)
        return valid_games
    except Exception as e:
        print(f"❌ 获取用户游戏库失败：{e}")
        return []


def get_steamdb_game_detail(appid):
    """获取SteamDB游戏详情（带本地缓存与反爬策略）"""
    appid_str = str(appid)
    # 优先使用缓存
    cached = STEAMDB_CACHE.get(appid_str)
    if cached:
        return cached

    url = f"https://steamdb.info/api/GetAppInfo/?appid={appid}"
    try:
        response = session.get(
            url,
            headers=STEAMDB_HEADERS,
            verify=False,
            timeout=12
        )
        response.raise_for_status()

        # 检查返回内容是否有效
        if not response.text.strip() or response.text.strip().startswith("<"):
            return {}

        # 解析JSON
        data = response.json()
        if appid_str not in data:
            return {}

        # 提取核心信息
        game_data = data[appid_str]
        detail = {
            "steamdb_score": game_data.get("score", 0),
            "tags": game_data.get("tags", []),
            "players_peak_24h": game_data.get("players_peak_24h", 0),
            "players_peak_alltime": game_data.get("players_peak_alltime", 0)
        }
        # 写入内存缓存并标记为脏（延迟写入，批量保存会更高效）
        STEAMDB_CACHE[appid_str] = detail
        global STEAMDB_CACHE_DIRTY
        STEAMDB_CACHE_DIRTY = True
        return detail
    except Exception:
        return {}
    finally:
        # 若存在缓存则不再强制 sleep，若非缓存新请求则短暂 sleep 以缓解反爬压力
        if not cached:
            time.sleep(0.08)


# 新增：使用官方 Steam 商店与 GetNumberOfCurrentPlayers 获取游戏详情并缓存
def get_store_game_detail(appid):
    """从官方 Steam 商店与 GetNumberOfCurrentPlayers 获取游戏详情并缓存。

    改进点：
    - 使用浏览器类请求头
    - 对两个请求分别做重试和指数退避
    - 超时设置更大（store 20s，players 10s）
    - 失败时优先返回本地缓存（若有）以保证可用性
    """
    appid_str = str(appid)
    cached = STORE_CACHE.get(appid_str)
    if cached:
        return cached

    detail = {}
    # 商店详情接口（重试+退避）
    store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=schinese"
    max_attempts = 3
    backoff = 1
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.get(store_url, headers=STEAM_STORE_HEADERS, timeout=20)
            r.raise_for_status()
            store_data = r.json()
            if str(appid) in store_data and store_data[str(appid)].get('success'):
                data = store_data[str(appid)]['data']
                # 提取可用字段
                metacritic = data.get('metacritic', {})
                genres = [g.get('description') for g in data.get('genres', []) if g.get('description')]
                categories = [c.get('description') for c in data.get('categories', []) if c.get('description')]
                recommendations = data.get('recommendations', {})
                release_date = data.get('release_date', {}).get('date')
                is_free = data.get('is_free', False)

                detail.update({
                    'metacritic_score': metacritic.get('score'),
                    'genres': genres,
                    'categories': categories,
                    'recommendations_total': recommendations.get('total'),
                    'release_date': release_date,
                    'is_free': is_free,
                })
            break
        except requests.exceptions.RequestException:
            # 若达到最大重试且有缓存，则返回缓存以避免超时失败
            if attempt == max_attempts and cached:
                return cached
            time.sleep(backoff)
            backoff *= 2
        except Exception:
            # 非网络错误直接跳出重试循环
            break

    # 获取当前在线人数（官方接口，重试+退避）
    players_url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    max_attempts = 3
    backoff = 1
    for attempt in range(1, max_attempts + 1):
        try:
            r2 = session.get(players_url, headers=STEAM_STORE_HEADERS, timeout=10)
            r2.raise_for_status()
            pdata = r2.json()
            player_count = pdata.get('response', {}).get('player_count')
            if player_count is not None:
                detail['current_players'] = player_count
            break
        except requests.exceptions.RequestException:
            if attempt == max_attempts and cached:
                return cached
            time.sleep(backoff)
            backoff *= 2
        except Exception:
            break

    # 若都为空则返回空
    if not detail:
        return {}

    # 缓存并返回（延迟写磁盘）
    STORE_CACHE[appid_str] = detail
    global STORE_CACHE_DIRTY
    STORE_CACHE_DIRTY = True
    # 对于新请求稍作等待以防速率被限流
    if not cached:
        time.sleep(0.06)
    return detail


def get_recent_releases(count=24, days=180):
    """抓取 Steam 商店按发布日期排序的最近发布/更新游戏。

    实现方式：使用 Steam 商店的搜索结果接口（返回 HTML 片段），解析 `data-ds-appid`。
    对每个 appid 调用 `get_store_game_detail` 与 `get_steamdb_game_detail` 获取详细信息，
    并按发布日期过滤（days 参数）。n
    返回格式：列表，每项包含 `appid`, `name`, `release_date`, `store_detail`, `steamdb_detail`。
    """
    import time as _time
    now = int(_time.time())
    # 缓存有效期内直接返回
    if RECENT_RELEASES_CACHE.get('fetched_at', 0) + RECENT_RELEASES_TTL > now and RECENT_RELEASES_CACHE.get('data'):
        return RECENT_RELEASES_CACHE['data']

    search_url = "https://store.steampowered.com/search/results/"
    params = {
        'query': '',
        'start': 0,
        'count': count,
        'sort_by': 'Released_DESC',
        'infinite': 1,
        'cc': 'US',
        'l': 'schinese'
    }
    try:
        r = session.get(search_url, params=params, headers=STEAM_STORE_HEADERS, timeout=15, verify=False)
        r.raise_for_status()
        j = r.json()
        html = j.get('results_html', '')
        # 提取 appid
        import re
        appids = re.findall(r'data-ds-appid="(\d+)"', html)
        seen = set()
        results = []
        for aid in appids:
            if aid in seen:
                continue
            seen.add(aid)
            try:
                store = get_store_game_detail(aid)
                steamdb = get_steamdb_game_detail(aid)
                name = store.get('name') if isinstance(store, dict) and 'name' in store else None
                # store detail may contain release_date
                release_date = None
                if isinstance(store, dict):
                    release_date = store.get('release_date') or store.get('release_date')
                # 尝试解析 release_date 字符串到 timestamp，若失败则保留 None
                ts = None
                if release_date:
                    from datetime import datetime
                    try:
                        # Steam 返回的日期格式各异，尽量宽容解析
                        ts = int(datetime.strptime(release_date, '%b %d, %Y').timestamp())
                    except Exception:
                        try:
                            ts = int(datetime.fromisoformat(release_date).timestamp())
                        except Exception:
                            ts = None

                # 如果有时间戳且在 days 范围内，加入候选
                include = True
                if ts is not None:
                    from datetime import datetime, timezone
                    cutoff = int((_time.time()) - days * 24 * 3600)
                    include = ts >= cutoff

                results.append({
                    'appid': int(aid),
                    'name': name or '',
                    'release_date': release_date,
                    'release_ts': ts,
                    'store_detail': store,
                    'steamdb_detail': steamdb
                })
            except Exception:
                continue

        # 按 release_ts 降序（没有 ts 的放后面）
        results.sort(key=lambda x: x.get('release_ts') or 0, reverse=True)
        # 过滤掉超出 days 的（如果解析到时间戳）
        filtered = []
        cutoff = int((_time.time()) - days * 24 * 3600)
        for rlt in results:
            if rlt.get('release_ts') and rlt['release_ts'] < cutoff:
                continue
            filtered.append(rlt)

        RECENT_RELEASES_CACHE['fetched_at'] = now
        RECENT_RELEASES_CACHE['data'] = filtered
        return filtered
    except Exception:
        return []


def call_deepseek(prompt, user_games, steamdb_details, recent_releases=None, user_style=None):
    """调用DeepSeek API生成推荐（使用复用的 session 提高性能）"""
    # 为了减少 API 调用成本和网络传输，payload 只包括用户游玩时间 Top3 与每个游戏的关键字段（最多 TOP_N_STORE_DETAILS）
    messages = [
        {"role": "system", "content": prompt},
    ]

    user_content = f"用户游戏库：{json.dumps(user_games[:10], ensure_ascii=False)}\n商店详情：{json.dumps(steamdb_details[:TOP_N_STORE_DETAILS], ensure_ascii=False)}"
    if user_style:
        # 将用户风格摘要以简短可读形式加入消息中，便于模型使用
        try:
            style_text = json.dumps(user_style, ensure_ascii=False)
        except Exception:
            style_text = str(user_style)
        user_content += f"\n用户游戏风格摘要：{style_text}"
    if recent_releases:
        # 只传递必要字段以减少 payload
        rr_trimmed = [{
            'appid': r.get('appid'),
            'name': r.get('name'),
            'release_date': r.get('release_date'),
            'steamdb_score': (r.get('steamdb_detail') or {}).get('score') if isinstance(r.get('steamdb_detail'), dict) else None,
            'current_players': (r.get('store_detail') or {}).get('current_players') if isinstance(r.get('store_detail'), dict) else None
        } for r in recent_releases[:TOP_N_STORE_DETAILS]]
        user_content += f"\n最近发布/更新候选：{json.dumps(rr_trimmed, ensure_ascii=False)}"

    messages.append({"role": "user", "content": user_content})

    # 若未配置 API Key，提前返回并给出用户可操作的提示（避免空 Bearer 导致 401）
    if not DEEPSEEK_API_KEY:
        return (
            "❌ 未配置 DeepSeek API Key（`DEEPSEEK_API_KEY`）。"
            " 请在环境变量或项目根目录创建 `DEEPSEEK_API_KEY.env`，内容示例：\n"
            "DEEPSEEK_API_KEY=your_api_key_here\n"
            "设置后重启程序。不要将密钥提交到版本控制。"
        )

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        # 保存要发送给 DeepSeek 的 messages（不包含 Authorization），便于调试与复现问题
        try:
            from datetime import datetime, timezone
            record = {
                'time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'model': DEEPSEEK_MODEL,
                'messages': messages
            }
            with DEEPSEEK_MESSAGES_FILE.open('a', encoding='utf-8') as mf:
                mf.write(json.dumps(record, ensure_ascii=False) + '\n')
            if DEBUG_DEEPSEEK_MESSAGES:
                print(f"[DEBUG] DeepSeek messages saved to {DEEPSEEK_MESSAGES_FILE}")
                try:
                    print(json.dumps(record, ensure_ascii=False, indent=2))
                except Exception:
                    print(str(record))
        except Exception:
            pass

        # 使用已创建的 session.post 以复用连接
        print("[INFO] call_deepseek: 发起 DeepSeek 请求，payload 大小：", len(json.dumps(messages, ensure_ascii=False)))
        response = session.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        # 提取响应状态与响应体，便于诊断（例如 402 Payment Required）
        resp = getattr(e, 'response', None)
        status = None
        body = None
        try:
            if resp is not None:
                status = resp.status_code
                # 尝试以文本形式读取响应体（可能是 JSON 或纯文本）
                body = resp.text
        except Exception:
            status = None
            body = None

        # 记录错误日志，便于提交给 DeepSeek 支持排查（注意：不记录 Authorization Key）
        try:
            from datetime import datetime, timezone
            log_path = Path(__file__).with_name('deepseek_error.log')
            safe_headers = {k: v for k, v in (headers or {}).items() if k.lower() != 'authorization'}
            with log_path.open('a', encoding='utf-8') as lf:
                lf.write('---\n')
                lf.write(f"time: {datetime.now(timezone.utc).isoformat().replace('+00:00','Z')}\n")
                lf.write(f'status: {status}\n')
                lf.write(f'endpoint: {DEEPSEEK_API_URL}\n')
                lf.write(f'model: {DEEPSEEK_MODEL}\n')
                lf.write(f'payload_size: {len(json.dumps(messages, ensure_ascii=False))}\n')
                lf.write(f'headers: {json.dumps(safe_headers, ensure_ascii=False)}\n')
                lf.write(f'body: {body}\n')
                lf.write('---\n')
        except Exception:
            # 日志写入失败不影响主流程
            pass

        if status == 401:
            return "❌ DeepSeek API Key 无效或未授权，请检查 `DEEPSEEK_API_KEY`。"
        elif status == 402:
            msg = "❌ DeepSeek 返回 402（Payment Required）：请检查账户计费状态、订阅额度与支付方式是否有效。"
            if body:
                msg += f" 服务器响应：{body}"
            msg += " 已将完整响应记录到 `deepseek_error.log`，可附上日志联系 DeepSeek 支持。"
            return msg
        elif status == 429:
            return "❌ 请求过于频繁（429），请稍后重试或降低调用频率。"
        else:
            details = f" 状态码：{status}" if status else ""
            if body:
                details += f"，响应体：{body}"
            return f"❌ DeepSeek API调用失败：{e}{details}（已记录到 deepseek_error.log）"
    except Exception as e:
        return f"❌ 生成推荐失败：{e}"


def _run_with_timeout(fn, timeout_seconds, *args, **kwargs):
    """Run fn with timeout using a short-lived ThreadPoolExecutor. Returns (ok, result_or_error).

    ok=True -> result contained; ok=False -> result is error message.
    """
    import concurrent.futures as _fut
    with _fut.ThreadPoolExecutor(max_workers=1) as exe:
        future = exe.submit(fn, *args, **kwargs)
        try:
            result = future.result(timeout=timeout_seconds)
            return True, result
        except _fut.TimeoutError:
            return False, f"❌ 推荐流程超时（超过 {timeout_seconds} 秒），请稍后再试或调整 MAX_RECOMMENDATION_TIME 环境变量。"
        except Exception as e:
            return False, f"❌ 推荐流程内部错误：{e}"


def generate_recommendation(steam_id, steam_key):
    """生成游戏推荐的完整流程（并发获取 SteamDB 详情）"""
    print("\n🔍 正在获取你的游戏库...")
    user_games = get_user_games(steam_id, steam_key)
    if not user_games:
        return "❌ 未获取到你的游戏库数据，请检查Steam ID和API Key是否正确。"

    print(f"✅ 已获取到{len(user_games)}款有效游戏，正在并发分析游玩时长前10的 Steam 商店详情...")
    steamdb_details = []
    # 并发获取游玩时长前10的 官方商店 详情（用于偏好分析）；并使用环境配置的并发数
    top_games = user_games[:10]
    max_workers = max(1, min(MAX_CONCURRENT_REQUESTS, len(top_games)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_store_game_detail, g['appid']): g for g in top_games}
        for future in concurrent.futures.as_completed(futures):
            game = futures[future]
            try:
                # 给每个 future 设置一个最大等待时间，避免单个请求无限挂起
                detail = future.result(timeout=30)
                if detail:
                    steamdb_details.append({
                        "name": game["name"],
                        "appid": game["appid"],
                        "playtime": game["playtime"],
                        "metacritic_score": detail.get("metacritic_score"),
                        "recommendations_total": detail.get("recommendations_total"),
                        "genres": detail.get("genres", []),
                        "categories": detail.get("categories", []),
                        "current_players": detail.get("current_players", 0),
                        "release_date": detail.get("release_date"),
                        "is_free": detail.get("is_free", False),
                    })
                    print(f"[INFO] 已获取商店详情：{game['name']} (appid={game['appid']})")
            except concurrent.futures.TimeoutError:
                print(f"⚠️ 请求超时：{game['name']} (appid={game['appid']})，已跳过。")
                continue
            except Exception:
                # 某些请求失败时忽略，继续处理其他项
                continue

    # 批量地把内存中被标记为脏的缓存写入磁盘（减少 I/O）
    save_all_caches()

    if not steamdb_details:
        return "❌ 获取SteamDB游戏详情失败，可能被反爬，请稍后重试。"

    print("\n🤖 正在生成推荐，请稍候...")
    # 在调用 DeepSeek 前，先生成并打印用户游戏风格摘要，供终端展示与模型使用
    user_style = {}
    try:
        from collections import Counter
        genres_ctr = Counter()
        categories_ctr = Counter()
        total_playtime = 0
        count = 0
        multiplayer_count = 0
        for d in steamdb_details:
            # playtime 存在时累加
            pt = d.get('playtime') or 0
            total_playtime += pt
            count += 1
            for g in d.get('genres', []):
                if g:
                    genres_ctr[g] += 1
            for c in d.get('categories', []):
                if c:
                    categories_ctr[c] += 1
                    # 简单判断是否为多人类别
                    lc = c.lower() if isinstance(c, str) else ''
                    if 'multi' in lc or '多人' in c:
                        multiplayer_count += 1

        top_genres = [g for g, _ in genres_ctr.most_common(5)]
        top_categories = [c for c, _ in categories_ctr.most_common(5)]
        avg_playtime = int(total_playtime / count) if count else 0
        multiplayer_pref = (multiplayer_count >= max(1, int(0.5 * count))) if count else False

        user_style = {
            'top_genres': top_genres,
            'top_categories': top_categories,
            'avg_playtime_minutes': avg_playtime,
            'top_games_sample': [d.get('name') for d in steamdb_details][:5],
            'multiplayer_pref': multiplayer_pref
        }
    except Exception:
        user_style = {}

    # 将用户风格在终端打印成简短摘要，便于用户查看
    try:
        print('\n🧭 用户游戏风格摘要：')
        print(json.dumps(user_style, ensure_ascii=False, indent=2))
    except Exception:
        print(f"🧭 用户游戏风格摘要：{user_style}")

    # 使用整体超时保护调用 DeepSeek（避免在 API 请求或解析上无限挂起）
    # 可选：包含最近发布/更新的候选（受环境变量控制），以便推荐更“新”的游戏
    include_recent = os.getenv('INCLUDE_RECENT_RELEASES', '0').lower() in ('1', 'true', 'yes')
    recent_releases = None
    if include_recent:
        days = int(os.getenv('RECENT_RELEASES_DAYS', '180'))
        print("[INFO] 正在抓取最近发布/更新的游戏候选...")
        try:
            recent_releases = get_recent_releases(count=TOP_N_STORE_DETAILS * 3, days=days)
            # 过滤掉用户已拥有或已游玩的游戏
            owned = {g['appid'] for g in user_games}
            recent_releases = [r for r in recent_releases if r.get('appid') not in owned]
            print(f"[INFO] 找到 {len(recent_releases)} 个最近发布/更新候选（去重后）。")
        except Exception:
            recent_releases = None

    ok, result = _run_with_timeout(call_deepseek, MAX_RECOMMENDATION_TIME, RECOMMEND_PROMPT, user_games, steamdb_details, recent_releases, user_style)
    if not ok:
        return result
    return result


def benchmark_fetch(steam_id, steam_key, top_n=TOP_N_STORE_DETAILS):
    """简单速度测量：分别测量获取用户库与并发获取商店详情的耗时。仅供调试/基准参考。"""
    import time as _time
    t0 = _time.perf_counter()
    user_games = get_user_games(steam_id, steam_key)
    t1 = _time.perf_counter()

    top_games = user_games[:top_n]
    max_workers = max(1, min(MAX_CONCURRENT_REQUESTS, len(top_games)))
    details = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_store_game_detail, g['appid']): g for g in top_games}
        for future in concurrent.futures.as_completed(futures):
            try:
                details.append(future.result(timeout=30))
            except Exception:
                continue

    t2 = _time.perf_counter()
    return {
        'user_games_count': len(user_games),
        'user_fetch_time': round(t1 - t0, 3),
        'store_fetch_time': round(t2 - t1, 3),
        'total_time': round(t2 - t0, 3),
        'fetched_details': len(details)
    }


def main():
    """命令行对话主函数"""
    print("=" * 50)
    print("🎮 steamgames_recommendation（基于 DeepSeek 的 Steam 游戏推荐助手）")
    print("=" * 50)
    print("使用说明：")
    print("1. 请按格式输入：ID：你的Steam数字ID，Key：你的Steam API Key")
    print("   示例：ID：76561198012345678，Key：1234567890ABCDEF1234567890ABCDEF")
    print("2. 输入'退出'结束对话")
    print("3. 输入'帮助'查看使用说明")
    print("4. 注意：请在输入中提供 Steam API Key（格式：Key：<你的Steam API Key>）")
    print("=" * 50)
    
    while True:
        user_input = input("\n你：").strip()
        
        if user_input == "退出":
            print("👋 再见！")
            break
        elif user_input == "帮助":
            print("使用说明：")
            print("1. 请按格式输入：ID：你的Steam数字ID，Key：你的Steam API Key")
            print("2. 输入'退出'结束对话")
            print("3. 注意：请在输入中提供 Steam API Key（格式：Key：<你的Steam API Key>）")
            continue
        
        # 解析用户输入
        if "ID：" in user_input:
            try:
                steam_id = user_input.split("ID：")[1].split("，")[0].strip()
                # 如果用户提供了 Key，则使用之；否则提示必须提供 Key
                if "Key：" in user_input:
                    steam_key = user_input.split("Key：")[1].strip()
                else:
                    print("❌ 未提供 Steam API Key；请按格式输入：ID：你的Steam数字ID，Key：你的Steam API Key")
                    continue

                # 简单格式校验
                if len(steam_id) != 17 or not steam_id.isdigit():
                    print("❌ Steam ID格式错误，应为17位数字。")
                    continue
                if len(steam_key) != 32:
                    print("❌ Steam API Key格式错误，应为32位字母数字组合。若未提供，请直接按示例输入或检查默认Key。")
                    continue

                # 生成推荐（整体流程增加超时保护，避免无限挂起）
                ok, recommendation = _run_with_timeout(generate_recommendation, MAX_RECOMMENDATION_TIME, steam_id, steam_key)
                if not ok:
                    print(recommendation)
                else:
                    print(f"\n🤖 {recommendation}")
            except IndexError:
                print("❌ 格式有误，请正确输入 ID 或 ID：XXX，Key：XXX 。")
        else:
            print("❌ 格式有误，请严格按照「ID：XXX，Key：XXX」格式发送。")


if __name__ == "__main__":
    main()