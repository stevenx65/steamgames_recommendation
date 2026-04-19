# Steam Games Recommendation

基于 Steam 游戏数据的个性化游戏推荐工具 / Personalized Steam game recommendation tool based on your gameplay data.

---

## 功能特性 | Features

- 分析 Steam 游戏库（游玩时长 Top 10）分析用户偏好
- 并发获取 Steam 商店与 SteamDB 元数据
- 调用 DeepSeek AI 模型生成 5 条差异化推荐
- 本地缓存减少重复请求
- 支持并发限速与超时保护

- Analyze Steam library (Top 10 by playtime) to extract user preferences
- Concurrently fetch metadata from Steam Store and SteamDB
- Generate 5 differentiated recommendations via DeepSeek AI
- Local caching to reduce API calls
- Concurrency limiting and timeout protection

---

## 目录结构 | Structure

```
.
├── config/           # 配置模块 / Configuration
├── core/             # 核心业务逻辑 / Core business logic
│   ├── analyzer.py   # 用户偏好分析 / User preference analysis
│   └── recommender.py # 推荐主流程 / Main recommendation flow
├── services/         # 外部 API 服务 / External API services
│   ├── steam_api.py    # Steam API
│   ├── steam_store.py  # Steam Store
│   ├── steamdb.py      # SteamDB
│   └── deepseek.py     # DeepSeek AI
├── utils/            # 工具函数 / Utilities
│   ├── cache.py      # JSON 缓存 / JSON caching
│   └── http.py       # HTTP 会话管理 / HTTP session
├── main.py           # CLI 入口 / CLI entry point
├── requirements.txt  # 依赖 / Dependencies
└── .env.example      # 环境变量示例 / Environment variables example
```

---

## 安装 | Installation

```bash
# 克隆仓库 / Clone repo
git clone https://github.com/stevenx65/steamgames_recommendation.git
cd steamgames_recommendation

# 创建虚拟环境（推荐）/ Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖 / Install dependencies
pip install -r requirements.txt
```

---

## 配置 | Configuration

复制示例环境文件并填入你的 API Key：

```bash
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY
```

| 变量 | 说明 | 必需 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 |
| `MAX_CONCURRENT_REQUESTS` | 最大并发请求数 | 否（默认 6）|
| `MAX_RECOMMENDATION_TIME` | 推荐超时时间（秒）| 否（默认 120）|
| `DEBUG_DEEPSEEK_MESSAGES` | 调试模式 | 否（默认 0）|

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | Yes |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent requests | No (default 6) |
| `MAX_RECOMMENDATION_TIME` | Timeout in seconds | No (default 120) |
| `DEBUG_DEEPSEEK_MESSAGES` | Debug mode | No (default 0) |

---

## 使用指南 | Usage

### 基本用法 | Basic Usage

```bash
python main.py <STEAM_ID> <STEAM_API_KEY>
```

示例 | Example:
```bash
python main.py 76561198012345678 YOUR_STEAM_API_KEY
```

### 获取 Steam API Key

访问 [Steam 开发者页面](https://steamcommunity.com/dev/apikey) 获取 API Key。

Visit [Steam Developer Page](https://steamcommunity.com/dev/apikey) to get your API key.

### 获取 Steam ID

方法 1：通过 [SteamID.io](https://steamid.io/) 查询你的 Steam ID（17位数字）

方法 2：在 Steam 客户端中查看个人资料 URL。

Method 1: Use [SteamID.io](https://steamid.io/) to find your Steam ID (17 digits)

Method 2: Check your profile URL in Steam client.

---

## 缓存 | Caching

缓存文件存储在用户目录：

```
~/.steam_recommendation/cache/
├── store.json      # Steam Store 缓存
└── steamdb.json    # SteamDB 缓存
```

Caches are stored in user home directory to avoid committing to git.

---

## 输出示例 | Sample Output

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

## 故障排查 | Troubleshooting

| 问题 | 解决 |
|------|------|
| 获取游戏库失败 | 检查 Steam ID 和 API Key 是否正确 |
| DeepSeek 401 错误 | 检查 DEEPSEEK_API_KEY 是否设置 |
| 请求超时 | 降低 MAX_CONCURRENT_REQUESTS 或增加 MAX_RECOMMENDATION_TIME |
| 缓存不更新 | 删除 `~/.steam_recommendation/cache/` 目录 |

| Issue | Solution |
|-------|----------|
| Failed to get library | Check Steam ID and API Key |
| DeepSeek 401 | Verify DEEPSEEK_API_KEY is set |
| Request timeout | Reduce MAX_CONCURRENT_REQUESTS or increase timeout |
| Stale cache | Delete `~/.steam_recommendation/cache/` |

---

## 依赖 | Dependencies

- Python 3.10+
- `requests` - HTTP 请求
- `python-dotenv` - 环境变量管理

---

## License

MIT
