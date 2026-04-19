"""应用配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent

ENV_FILE = PROJECT_ROOT / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

DATA_DIR = Path.home() / '.steam_recommendation'
CACHE_DIR = DATA_DIR / 'cache'

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '').strip()
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '6'))
MAX_RECOMMENDATION_TIME = int(os.getenv('MAX_RECOMMENDATION_TIME', '120'))
DEBUG_DEEPSEEK_MESSAGES = os.getenv('DEBUG_DEEPSEEK_MESSAGES', '0').lower() in ('1', 'true', 'yes')

STEAMDB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Referer": "https://steamdb.info/",
    "X-Requested-With": "XMLHttpRequest",
}

STEAM_STORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://store.steampowered.com/",
}

TOP_N_STORE_DETAILS = int(os.getenv('TOP_N_STORE_DETAILS', '5'))
RECENT_RELEASES_DAYS = int(os.getenv('RECENT_RELEASES_DAYS', '180'))
