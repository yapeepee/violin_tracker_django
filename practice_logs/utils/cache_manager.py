"""
快取管理器
統一管理應用程式的快取策略
"""
from django.core.cache import cache
from django.conf import settings
import hashlib
import json
import logging
from functools import wraps
from typing import Any, Optional, Callable

logger = logging.getLogger(__name__)


class CacheManager:
    """快取管理器，提供統一的快取介面"""
    
    # 快取時間常數（秒）
    CACHE_MINUTE = 60
    CACHE_SHORT = 300       # 5分鐘
    CACHE_MEDIUM = 1800     # 30分鐘
    CACHE_LONG = 3600       # 1小時
    CACHE_DAY = 86400       # 1天
    
    # 快取鍵前綴
    PREFIX_STUDENT = 'student'
    PREFIX_PRACTICE = 'practice'
    PREFIX_STATS = 'stats'
    PREFIX_CALENDAR = 'calendar'
    PREFIX_ACHIEVEMENT = 'achievement'
    PREFIX_API = 'api'
    
    @classmethod
    def make_key(cls, prefix: str, *args, **kwargs) -> str:
        """
        生成快取鍵
        
        Args:
            prefix: 快取鍵前綴
            *args: 位置參數
            **kwargs: 關鍵字參數
            
        Returns:
            str: 快取鍵
        """
        # 建立基本鍵
        key_parts = [settings.CACHE_KEY_PREFIX, prefix]
        
        # 添加位置參數
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
                
        # 添加關鍵字參數（排序以確保一致性）
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if v is not None:
                    key_parts.append(f"{k}:{v}")
                    
        # 組合鍵
        key = ':'.join(key_parts)
        
        # 如果鍵太長，使用雜湊
        if len(key) > 250:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{settings.CACHE_KEY_PREFIX}:{prefix}:hash:{key_hash}"
            
        return key
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        獲取快取值
        
        Args:
            key: 快取鍵
            default: 預設值
            
        Returns:
            快取值或預設值
        """
        try:
            value = cache.get(key, default)
            if value is not None and value != default:
                logger.debug(f"Cache hit: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    @classmethod
    def set(cls, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        設定快取值
        
        Args:
            key: 快取鍵
            value: 快取值
            timeout: 過期時間（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            if timeout is None:
                timeout = cls.CACHE_MEDIUM
            cache.set(key, value, timeout)
            logger.debug(f"Cache set: {key} (timeout: {timeout}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        刪除快取
        
        Args:
            key: 快取鍵
            
        Returns:
            bool: 是否成功
        """
        try:
            cache.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    @classmethod
    def delete_pattern(cls, pattern: str) -> int:
        """
        刪除符合模式的快取（需要 Redis 後端）
        
        Args:
            pattern: 快取鍵模式（支援 * 萬用字元）
            
        Returns:
            int: 刪除的鍵數量
        """
        try:
            # 如果使用 Redis 快取後端
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'delete_pattern'):
                return cache._cache.delete_pattern(f"{settings.CACHE_KEY_PREFIX}:{pattern}")
            else:
                logger.warning("Cache backend doesn't support pattern deletion")
                return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    @classmethod
    def clear_student_cache(cls, student_name: str) -> None:
        """
        清除特定學生的所有快取
        
        Args:
            student_name: 學生姓名
        """
        patterns = [
            f"{cls.PREFIX_STUDENT}:{student_name}:*",
            f"{cls.PREFIX_PRACTICE}:{student_name}:*",
            f"{cls.PREFIX_STATS}:{student_name}:*",
            f"{cls.PREFIX_CALENDAR}:{student_name}:*",
            f"{cls.PREFIX_ACHIEVEMENT}:{student_name}:*"
        ]
        
        for pattern in patterns:
            deleted = cls.delete_pattern(pattern)
            if deleted:
                logger.info(f"Cleared {deleted} cache keys for pattern: {pattern}")
    
    @classmethod
    def get_or_set(cls, key: str, callable: Callable, timeout: Optional[int] = None) -> Any:
        """
        獲取快取，如果不存在則執行函數並快取結果
        
        Args:
            key: 快取鍵
            callable: 可呼叫物件
            timeout: 過期時間
            
        Returns:
            快取值或函數執行結果
        """
        value = cls.get(key)
        if value is None:
            value = callable()
            if value is not None:
                cls.set(key, value, timeout)
        return value


def cache_result(prefix: str, timeout: Optional[int] = None, 
                key_func: Optional[Callable] = None):
    """
    快取裝飾器
    
    Args:
        prefix: 快取鍵前綴
        timeout: 過期時間
        key_func: 自定義鍵生成函數
        
    使用範例:
        @cache_result('student_stats', timeout=CacheManager.CACHE_MEDIUM)
        def get_student_stats(student_name, days=30):
            # 函數實作
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成快取鍵
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 預設使用函數名和參數生成鍵
                cache_key = CacheManager.make_key(
                    prefix,
                    func.__name__,
                    *args,
                    **kwargs
                )
            
            # 嘗試從快取獲取
            result = CacheManager.get(cache_key)
            if result is not None:
                return result
            
            # 執行函數
            result = func(*args, **kwargs)
            
            # 快取結果
            if result is not None:
                CacheManager.set(cache_key, result, timeout)
                
            return result
            
        # 添加清除快取的方法
        def clear_cache(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = CacheManager.make_key(
                    prefix,
                    func.__name__,
                    *args,
                    **kwargs
                )
            CacheManager.delete(cache_key)
            
        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator


def invalidate_cache(patterns: list):
    """
    失效快取裝飾器
    在函數執行後清除指定模式的快取
    
    Args:
        patterns: 要清除的快取鍵模式列表
        
    使用範例:
        @invalidate_cache(['student:*', 'stats:*'])
        def update_practice_log(student_name, data):
            # 更新邏輯
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 執行函數
            result = func(*args, **kwargs)
            
            # 清除快取
            for pattern in patterns:
                # 可以在模式中使用參數
                if '{' in pattern:
                    # 簡單的模板替換
                    func_args = func.__code__.co_varnames[:func.__code__.co_argcount]
                    arg_dict = dict(zip(func_args, args))
                    arg_dict.update(kwargs)
                    
                    try:
                        pattern = pattern.format(**arg_dict)
                    except KeyError:
                        logger.warning(f"Cannot format cache pattern: {pattern}")
                        continue
                        
                CacheManager.delete_pattern(pattern)
                
            return result
        return wrapper
    return decorator


# 快取鍵生成函數範例
def student_cache_key(student_name: str, **kwargs) -> str:
    """生成學生相關的快取鍵"""
    return CacheManager.make_key(CacheManager.PREFIX_STUDENT, student_name, **kwargs)


def practice_cache_key(student_name: str, date: str = None, **kwargs) -> str:
    """生成練習相關的快取鍵"""
    return CacheManager.make_key(CacheManager.PREFIX_PRACTICE, student_name, date, **kwargs)


def stats_cache_key(student_name: str, period: str = None, **kwargs) -> str:
    """生成統計相關的快取鍵"""
    return CacheManager.make_key(CacheManager.PREFIX_STATS, student_name, period, **kwargs)