#!/usr/bin/env python3
"""Steam 游戏推荐工具 - 主入口"""
import sys
from config import DEEPSEEK_API_KEY
from core.recommender import generate_recommendation


def print_help():
    """打印帮助信息"""
    print("""
使用说明：
1. 设置环境变量 DEEPSEEK_API_KEY（必需）
2. 运行: python main.py <STEAM_ID> <STEAM_API_KEY>

环境变量:
- DEEPSEEK_API_KEY: DeepSeek API 密钥（必需）
- MAX_CONCURRENT_REQUESTS: 最大并发请求数（默认: 6）
- MAX_RECOMMENDATION_TIME: 推荐超时时间秒数（默认: 120）
- DEBUG_DEEPSEEK_MESSAGES: 设为 1 保存调试消息
""")


def main():
    """主函数"""
    if len(sys.argv) == 2 and sys.argv[1] in ('-h', '--help', '帮助'):
        print_help()
        sys.exit(0)

    if not DEEPSEEK_API_KEY:
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("   请在 .env 文件中设置：DEEPSEEK_API_KEY=your_key_here")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("用法: python main.py <STEAM_ID> <STEAM_API_KEY>")
        sys.exit(1)

    steam_id = sys.argv[1]
    steam_key = sys.argv[2]

    if len(steam_id) != 17 or not steam_id.isdigit():
        print("❌ Steam ID 应为 17 位数字")
        sys.exit(1)

    if len(steam_key) != 32:
        print("❌ Steam API Key 应为 32 位")
        sys.exit(1)

    result = generate_recommendation(steam_id, steam_key)
    print(f"\n🤖 {result}")


if __name__ == "__main__":
    main()
