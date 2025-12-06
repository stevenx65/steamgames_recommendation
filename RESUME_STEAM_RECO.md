项目名称：steamgames_recommendation（基于 DeepSeek 与 Steam 数据）

职责：独立设计并实现从 Steam 用户库抓取、并发获取商店与 SteamDB 详情、进行用户行为分析，并调用 DeepSeek 聊天模型生成结构化的个性化推荐。

技术栈：Python、requests、concurrent.futures、dotenv、Steam Web API、Steam store API、DeepSeek Chat API

成果与亮点：
- 实现端到端推荐流水线：基于用户“游玩时长 Top10”自动识别偏好（genres、categories、多人/单人倾向、平均游玩时长），并生成 5 条差异化、高质量推荐。
- 支持可选抓取“最近发布/更新”候选以优先推荐新作，并通过本地缓存和并发控制提升性能与稳定性。
- 完善的调试与可复现机制：将发送给模型的 messages 保存为 `deepseek_messages.jsonl` 以便复现与排查，记录 DeepSeek 错误响应（不包含授权信息）。
- 处理复杂环境问题：实现 API Key 的多路径加载、时区感知日志写入、对不一致的日期格式做容错解析、以及反爬与速率限制的退避策略。

（文件主脚本：`py_ds_reco.py`，项目名：`steamgames_recommendation`）
