# steamgames_recommendation

## 简介（中文）
`steamgames_recommendation` 是一款基于用户 Steam 游玩数据的个性化游戏推荐工具。它并发抓取 Steam 与 SteamDB 元数据，统计用户“游玩时长 Top10”偏好（genre、category、多人/单人倾向、平均游玩时长），并将这些结构化概要与可选的“最近发布/更新”候选传入 DeepSeek 聊天模型，最终生成 5 条差异化且可直接用于购买的推荐。注重隐私与可复现性：模型输入会保存为 `deepseek_messages.jsonl`（不包含授权信息），并支持本地缓存与并发/重试策略以提高稳定性。

## Overview (English)
`steamgames_recommendation` is a personalized Steam game recommender that analyzes a user’s play history to produce high-quality suggestions. It concurrently fetches metadata from Steam and SteamDB, summarizes player preferences from the top-10 played titles, and supplies that structured context — plus optional recent-release candidates — to a DeepSeek chat model to generate 5 differentiated recommendations. Model inputs are logged to `deepseek_messages.jsonl` for debugging (no authorization saved).

## Features
- Analyze user play history (Top10 by playtime) and extract preference signals.
- Fetch game metadata from Steam store and SteamDB (genres, categories, release date, current players, score).
- Optional recent release / update candidate scraping.
- Prompt-engineered DeepSeek integration to produce structured 5-item recommendations.
- Local caching, retry/backoff, concurrency control, and debug logging.

## Requirements
- Python 3.10+
- Dependencies: `requests`, `python-dotenv`

Install dependencies:
```powershell
pip install requests python-dotenv
```

## Environment variables
- `DEEPSEEK_API_KEY` (required) — your DeepSeek API key. Prefer storing in `DEEPSEEK_API_KEY.env` at project root or set in environment.
- `DEBUG_DEEPSEEK_MESSAGES` (optional) — set to `1` to print and save model `messages` to `deepseek_messages.jsonl`.
- `INCLUDE_RECENT_RELEASES` (optional) — set to `1` to enable scraping recent-release candidates.
- `RECENT_RELEASES_DAYS` (optional) — days range for "recent" (default 180).
- `MAX_CONCURRENT_REQUESTS`, `TOP_N_STORE_DETAILS`, `MAX_RECOMMENDATION_TIME` — tuning parameters (see `OPERATION.md`).

Note: The script requires you to provide a Steam Web API Key at runtime (input). For security, do not commit API keys to version control.

## Quick start (PowerShell)
```powershell
#$env:STEAM_API_KEY='your_steam_api_key'   # optional env-read feature TODO
#$env:DEEPSEEK_API_KEY='your_deepseek_key'
#$env:DEBUG_DEEPSEEK_MESSAGES='1'   # optional
python .\py_ds_reco.py

# When prompted, enter:
# ID：<your 17-digit SteamID>，Key：<your Steam Web API Key>
```

## Output & logs
- `deepseek_messages.jsonl` — each line is a JSON record of the `messages` sent to DeepSeek (no Authorization header).
- `deepseek_error.log` — saved DeepSeek API error responses (no Authorization).
- `*.steamdb_cache.json`, `*.store_cache.json` — local caches for fetched metadata.

## Key files
- `py_ds_reco.py` — main script / entry point
- `OPERATION.md` — operation guide and environment variable explanations
- `RESUME_STEAM_RECO.md` — short project description for resume

## Notes & Next steps
- The scraping logic for recent releases relies on Steam store endpoints and HTML fragments; it may break if the store changes. If you plan public deployment, consider using official/contracted data sources or throttled proxy solutions.
- Consider adding automated tests (unit tests + mocked HTTP responses) and CI before publishing the repo publicly.

---

