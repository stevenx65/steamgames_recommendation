操作指南 — steamgames_recommendation

概述
- 脚本：`py_ds_reco.py`
- 功能：基于 Steam 用户库（游玩时长 Top10）分析用户偏好并调用 DeepSeek 模型生成 5 条个性化推荐；可选抓取最近发布/更新候选；保存模型输入用于复现与调试。

运行前准备
1. Python 环境：建议 Python 3.10+
2. 依赖：`requests`, `python-dotenv`（可通过 `pip install requests python-dotenv` 安装）
3. DeepSeek API Key：必须提供。建议通过在项目根创建 `DEEPSEEK_API_KEY.env`（内容示例：`DEEPSEEK_API_KEY=你的_key`）或在运行前在 PowerShell 中设置环境变量。
4. Steam API Key：必须在运行时通过输入提供（见下面的使用说明）。请勿将密钥提交到版本控制。

可选环境变量
- `DEBUG_DEEPSEEK_MESSAGES=1`：将发送给 DeepSeek 的 `messages` 保存到 `deepseek_messages.jsonl` 并打印到控制台（便于调试）。
- `INCLUDE_RECENT_RELEASES=1`：启用抓取最近发布/更新候选以优先推荐新作。
- `RECENT_RELEASES_DAYS`：控制“最近”时间范围（默认 180 天）。
- `MAX_CONCURRENT_REQUESTS`：并发请求上限（默认 6）。
- `TOP_N_STORE_DETAILS`：传给模型的商店详情数量（默认 5）。
- `MAX_RECOMMENDATION_TIME`：整体推荐流程超时（秒，默认 120）。

运行示例（PowerShell）
```powershell
# 可选：开启 messages 调试打印
$env:DEBUG_DEEPSEEK_MESSAGES='1'
# 可选：启用最近发布抓取
$env:INCLUDE_RECENT_RELEASES='1'
$env:RECENT_RELEASES_DAYS='180'

python .\py_ds_reco.py
```

交互示例（脚本运行后输入）
- 正确输入格式：
  ID：7656119XXXXXXXXXX，Key：<你的Steam API Key>
- 退出：输入 `退出`
- 帮助：输入 `帮助`

输出与日志文件
- 推荐结果会在终端打印（包含“用户游戏风格摘要”与 DeepSeek 返回的 5 条推荐）。
- `deepseek_messages.jsonl`：每次调用时保存的模型输入（不包含 Authorization），用于复现与排查。
- `deepseek_error.log`：DeepSeek 错误响应记录（不包含 Authorization）。
- 缓存文件：`py_ds_reco.steamdb_cache.json` 与 `py_ds_reco.store_cache.json`（用于减少重复请求）。

注意事项
- 请勿在公开仓库或共享环境中写入真实 API Key。建议在本地以 `DEEPSEEK_API_KEY.env` 或临时环境变量方式提供。
- Steam store 的搜索接口与 HTML 结构可能随时间变化，若抓取失败请尝试关闭 `INCLUDE_RECENT_RELEASES` 或使用稳定的 Steam API 数据源。
- 若推荐生成缓慢或报错，可调整 `MAX_CONCURRENT_REQUESTS` 与 `MAX_RECOMMENDATION_TIME`。

故障排查
- 若出现 DeepSeek 授权错误（401），请确认 `DEEPSEEK_API_KEY` 有效且已设置。
- 若抓取商店详情失败或频繁超时，尝试降低 `MAX_CONCURRENT_REQUESTS` 并查看 `py_ds_reco.store_cache.json` 是否包含缓存数据。

关键文件
- `py_ds_reco.py`（主脚本）
- `RESUME_STEAM_RECO.md`（简历条目）
- `deepseek_messages.jsonl`（模型输入记录）
- `deepseek_error.log`（错误日志）