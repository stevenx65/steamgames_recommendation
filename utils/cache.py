"""缓存管理"""
import json
from pathlib import Path
from typing import Any, Optional
from config import CACHE_DIR

class JsonCache:
    """JSON文件缓存"""

    def __init__(self, name: str):
        self.path = CACHE_DIR / f"{name}.json"
        self._data = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def _save(self):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def get(self, key: Any) -> Optional[Any]:
        return self._data.get(str(key))

    def set(self, key: Any, value: Any):
        self._data[str(key)] = value
        self._save()

store_cache = JsonCache('store')
steamdb_cache = JsonCache('steamdb')
