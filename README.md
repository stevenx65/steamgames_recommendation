[Chinese version](./README.zh.md)

# Steam Games Recommendation

Personalized Steam game recommendation tool based on your gameplay data.

---

## Features

- Analyze Steam library (Top 10 by playtime) to extract user preferences
- Concurrently fetch metadata from Steam Store and SteamDB
- Generate 5 differentiated recommendations via DeepSeek AI
- Local caching to reduce API calls
- Concurrency limiting and timeout protection

---

## Structure

```
.
├── config/           # Configuration
├── core/             # Core business logic
│   ├── analyzer.py   # User preference analysis
│   └── recommender.py # Main recommendation flow
├── services/         # External API services
│   ├── steam_api.py    # Steam API
│   ├── steam_store.py  # Steam Store
│   ├── steamdb.py      # SteamDB
│   └── deepseek.py     # DeepSeek AI
├── utils/            # Utilities
│   ├── cache.py      # JSON caching
│   └── http.py       # HTTP session
├── main.py           # CLI entry point
├── requirements.txt  # Dependencies
└── .env.example      # Environment variables example
```

---

## Installation

```bash
# Clone repo
git clone https://github.com/stevenx65/steamgames_recommendation.git
cd steamgames_recommendation

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy the example environment file and fill in your API Key:

```bash
cp .env.example .env
# Edit .env and set DEEPSEEK_API_KEY
```

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | Yes |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent requests | No (default 6) |
| `MAX_RECOMMENDATION_TIME` | Timeout in seconds | No (default 120) |
| `DEBUG_DEEPSEEK_MESSAGES` | Debug mode | No (default 0) |

---

## Usage

### Basic Usage

```bash
python main.py <STEAM_ID> <STEAM_API_KEY>
```

Example:
```bash
python main.py 76561198012345678 YOUR_STEAM_API_KEY
```

### Get a Steam API Key

Visit [Steam Developer Page](https://steamcommunity.com/dev/apikey) to get your API key.

### Get a Steam ID

Method 1: Use [SteamID.io](https://steamid.io/) to find your Steam ID (17 digits)

Method 2: Check your profile URL in Steam client.

---

## Caching

```
~/.steam_recommendation/cache/
├── store.json      # Steam Store cache
└── steamdb.json    # SteamDB cache
```

Caches are stored in user home directory to avoid committing to git.

---

## Sample Output

```
🔍 正在获取你的游戏库...
✅ 已获取 152 款游戏，正在分析 Top 10...

🧭 用户游戏风格摘要：
{
  "top_genres": ["RPG", "Open World", "Action"],
  "top_categories": ["Single-player", "Steam Achievements"],
  "avg_playtime_minutes": 2847,
  "multiplayer_pref": false,
  "sample_games": ["Elden Ring", "The Witcher 3", "Baldur's Gate 3"]
}

🤖 正在生成推荐...

1. 《Hades II》
   - 类型：Roguelike, Action | 评分：9.2
   - 匹配点：基于你对《Elden Ring》的高游玩时长，推荐这款高难度动作游戏
   - 链接：https://store.steampowered.com/app/1145350/
...
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Failed to get library | Check Steam ID and API Key |
| DeepSeek 401 | Verify DEEPSEEK_API_KEY is set |
| Request timeout | Reduce MAX_CONCURRENT_REQUESTS or increase timeout |
| Stale cache | Delete `~/.steam_recommendation/cache/` |

---

## Dependencies

- Python 3.10+
- `requests`
- `python-dotenv`

---

## License

MIT
