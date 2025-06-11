"""
資料庫優化管理命令
執行各種資料庫優化操作
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.core.cache import cache
from django.db.models import Count, Sum, Avg, Q
from practice_logs.models import PracticeLog, TeacherFeedback
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '優化資料庫性能'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='執行 VACUUM 操作（僅 SQLite）',
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='執行 ANALYZE 操作',
        )
        parser.add_argument(
            '--rebuild-indexes',
            action='store_true',
            help='重建索引',
        )
        parser.add_argument(
            '--cache-warmup',
            action='store_true',
            help='預熱快取',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='清理舊數據',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='執行所有優化操作',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        if options['all']:
            options['vacuum'] = True
            options['analyze'] = True
            options['rebuild_indexes'] = True
            options['cache_warmup'] = True
            options['cleanup'] = True
        
        if options['vacuum']:
            self.vacuum_database()
        
        if options['analyze']:
            self.analyze_database()
        
        if options['rebuild_indexes']:
            self.rebuild_indexes()
        
        if options['cache_warmup']:
            self.warmup_cache()
        
        if options['cleanup']:
            self.cleanup_old_data()
        
        elapsed_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(f'資料庫優化完成，耗時 {elapsed_time:.2f} 秒')
        )

    def vacuum_database(self):
        """執行 VACUUM 操作（僅適用於 SQLite）"""
        self.stdout.write('執行 VACUUM 操作...')
        
        if connection.vendor == 'sqlite':
            with connection.cursor() as cursor:
                cursor.execute('VACUUM;')
            self.stdout.write(self.style.SUCCESS('✓ VACUUM 完成'))
        else:
            self.stdout.write(self.style.WARNING('跳過 VACUUM（僅支援 SQLite）'))

    def analyze_database(self):
        """執行 ANALYZE 操作"""
        self.stdout.write('執行 ANALYZE 操作...')
        
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute('ANALYZE;')
            elif connection.vendor == 'postgresql':
                cursor.execute('ANALYZE;')
            elif connection.vendor == 'mysql':
                # 獲取所有表名
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f'ANALYZE TABLE {table[0]};')
        
        self.stdout.write(self.style.SUCCESS('✓ ANALYZE 完成'))

    def rebuild_indexes(self):
        """重建資料庫索引"""
        self.stdout.write('重建索引...')
        
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute('REINDEX;')
            elif connection.vendor == 'postgresql':
                cursor.execute(
                    "SELECT schemaname, tablename FROM pg_tables "
                    "WHERE schemaname = 'public'"
                )
                tables = cursor.fetchall()
                for schema, table in tables:
                    cursor.execute(f'REINDEX TABLE {schema}.{table};')
            elif connection.vendor == 'mysql':
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f'OPTIMIZE TABLE {table[0]};')
        
        self.stdout.write(self.style.SUCCESS('✓ 索引重建完成'))

    def warmup_cache(self):
        """預熱快取"""
        self.stdout.write('預熱快取...')
        
        # 清除舊快取
        cache.clear()
        
        # 獲取活躍學生列表
        active_students = PracticeLog.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).values_list('student_name', flat=True).distinct()[:50]
        
        cached_count = 0
        
        # 為每個活躍學生預載入統計數據
        for student_name in active_students:
            # 快取學生統計
            stats = PracticeLog.objects.filter(
                student_name=student_name
            ).aggregate(
                total_minutes=Sum('minutes'),
                total_sessions=Count('id'),
                avg_rating=Avg('rating'),
                unique_pieces=Count('piece', distinct=True)
            )
            
            cache.set(f'student_stats:{student_name}', stats, 3600)
            cached_count += 1
            
            # 快取最近練習記錄
            recent_logs = list(
                PracticeLog.objects.filter(
                    student_name=student_name
                ).select_related('teacher_feedback').order_by('-date')[:10]
            )
            
            cache.set(f'recent_logs:{student_name}', recent_logs, 1800)
            cached_count += 1
        
        # 快取全局統計
        global_stats = PracticeLog.objects.aggregate(
            total_students=Count('student_name', distinct=True),
            total_sessions=Count('id'),
            total_minutes=Sum('minutes'),
            avg_rating=Avg('rating')
        )
        
        cache.set('global_stats', global_stats, 3600)
        cached_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ 預熱快取完成，共快取 {cached_count} 項')
        )

    def cleanup_old_data(self):
        """清理舊數據"""
        self.stdout.write('清理舊數據...')
        
        from datetime import timedelta
        from django.utils import timezone
        
        # 刪除超過一年的登入記錄
        if hasattr(PracticeLog, 'userloginlog'):
            old_login_logs = UserLoginLog.objects.filter(
                login_time__lt=timezone.now() - timedelta(days=365)
            )
            deleted_count = old_login_logs.count()
            old_login_logs.delete()
            self.stdout.write(f'  刪除 {deleted_count} 條舊登入記錄')
        
        # 壓縮舊的練習記錄（可選）
        # 這裡可以將超過6個月的詳細評分數據聚合成摘要
        
        self.stdout.write(self.style.SUCCESS('✓ 清理完成'))

    def get_database_size(self):
        """獲取資料庫大小"""
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                size = cursor.fetchone()[0]
                return size / 1024 / 1024  # 轉換為 MB
            elif connection.vendor == 'postgresql':
                cursor.execute("SELECT pg_database_size(current_database())")
                size = cursor.fetchone()[0]
                return size / 1024 / 1024  # 轉換為 MB
            elif connection.vendor == 'mysql':
                cursor.execute(
                    "SELECT SUM(data_length + index_length) "
                    "FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )
                size = cursor.fetchone()[0] or 0
                return size / 1024 / 1024  # 轉換為 MB
        return 0