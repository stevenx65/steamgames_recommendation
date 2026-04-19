"""DeepSeek API 服务"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL,
    DEBUG_DEEPSEEK_MESSAGES, TOP_N_STORE_DETAILS
)

PROMPT_TEMPLATE = """你是专业的Steam游戏推荐助手，需基于用户的Steam游戏数据，推荐5款游戏，严格遵循以下规则：

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
   ...
4. 补充要求：匹配点需具体，避免笼统描述；购买链接需替换为对应游戏的Steam商店页。
"""

def _log_error(error: Exception, status: Optional[int], body: Optional[str], messages: List[Dict]):
    """记录 DeepSeek 错误日志"""
    try:
        log_path = Path(__file__).parent.parent / 'deepseek_error.log'
        with log_path.open('a', encoding='utf-8') as f:
            f.write('---\n')
            f.write(f"time: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"status: {status}\n")
            f.write(f"model: {DEEPSEEK_MODEL}\n")
            f.write(f"error: {str(error)}\n")
            if body:
                f.write(f"body: {body}\n")
            f.write('---\n')
    except Exception:
        pass

def _save_messages(messages: List[Dict]):
    """保存消息到调试文件"""
    if not DEBUG_DEEPSEEK_MESSAGES:
        return

    try:
        msg_path = Path(__file__).parent.parent / 'deepseek_messages.jsonl'
        record = {
            'time': datetime.now(timezone.utc).isoformat(),
            'model': DEEPSEEK_MODEL,
            'messages': messages
        }
        with msg_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"[DEBUG] Messages saved to {msg_path}")
    except Exception:
        pass

def get_recommendations(
    user_games: List[Dict],
    game_details: List[Dict],
    user_style: Dict[str, Any],
    session: requests.Session
) -> str:
    """调用 DeepSeek API 生成推荐"""
    if not DEEPSEEK_API_KEY:
        return "❌ 未配置 DeepSeek API Key。请设置环境变量 DEEPSEEK_API_KEY"

    user_summary = {
        'games': user_games[:10],
        'details': game_details[:TOP_N_STORE_DETAILS],
        'style': user_style
    }

    messages = [
        {"role": "system", "content": PROMPT_TEMPLATE},
        {"role": "user", "content": json.dumps(user_summary, ensure_ascii=False)}
    ]

    _save_messages(messages)

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = session.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else None
        body = e.response.text if e.response else None
        _log_error(e, status, body, messages)

        if status == 401:
            return "❌ DeepSeek API Key 无效或未授权"
        elif status == 402:
            return "❌ DeepSeek 账户余额不足或需要付费"
        elif status == 429:
            return "❌ 请求过于频繁，请稍后重试"
        else:
            return f"❌ DeepSeek API 调用失败：{e}"

    except Exception as e:
        return f"❌ 生成推荐失败：{e}"
