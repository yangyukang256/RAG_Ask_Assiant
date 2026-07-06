"""内存缓存管理器（基于 cachetools，后续可替换为 Redis）"""
from functools import lru_cache
from typing import Any, Optional
import time
import json
import hashlib


class CacheManager:
    """简单内存缓存，支持 TTL"""

    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() < self._ttl.get(key, 0):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._ttl[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl_seconds

    def delete(self, key: str):
        self._cache.pop(key, None)
        self._ttl.pop(key, None)

    def clear(self):
        self._cache.clear()
        self._ttl.clear()

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """生成缓存键"""
        key_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# 全局缓存实例
cache = CacheManager()


def cached(ttl_seconds: int = 300):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = CacheManager.make_key(func.__name__, *args, **kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator