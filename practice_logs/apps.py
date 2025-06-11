from django.apps import AppConfig
from django.db.backends.signals import connection_created


class PracticeLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'practice_logs'
    verbose_name = '練習記錄'

    def ready(self):
        # SQLite 優化設定
        def sqlite_optimize(sender, connection, **kwargs):
            """優化 SQLite 性能"""
            if connection.vendor == 'sqlite':
                cursor = connection.cursor()
                # 設定 SQLite 優化參數
                cursor.execute('PRAGMA journal_mode=WAL;')  # 寫前日誌模式
                cursor.execute('PRAGMA synchronous=NORMAL;')  # 同步模式
                cursor.execute('PRAGMA cache_size=-64000;')  # 64MB 快取
                cursor.execute('PRAGMA temp_store=MEMORY;')  # 記憶體臨時存儲
                cursor.execute('PRAGMA mmap_size=268435456;')  # 256MB 記憶體映射
        
        # 連接信號
        connection_created.connect(sqlite_optimize)
