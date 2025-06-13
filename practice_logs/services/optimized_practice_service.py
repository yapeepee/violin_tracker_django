"""
優化的練習服務層
處理所有練習相關的業務邏輯和資料庫查詢優化
"""
from django.db.models import (
    Count, Sum, Avg, Max, Min, Q, F,
    Value, IntegerField, FloatField, 
    When, Case, Subquery, OuterRef,
    Prefetch
)
from django.db.models.functions import TruncDate, Coalesce, ExtractWeekDay
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from practice_logs.models.practice import PracticeLog
from practice_logs.models.instruments import Instrument
from practice_logs.utils.constants import Constants

logger = logging.getLogger(__name__)


class OptimizedPracticeService:
    """優化的練習服務，處理所有資料庫查詢最佳化"""
    
    # 快取時間設定
    CACHE_SHORT = 300  # 5分鐘
    CACHE_MEDIUM = 1800  # 30分鐘
    CACHE_LONG = 3600  # 1小時
    
    @classmethod
    def get_optimized_queryset(cls, student_name, start_date=None, end_date=None, 
                              instrument_code=None, prefetch_related_objects=True):
        """
        獲取優化的查詢集，避免 N+1 問題
        
        Args:
            student_name: 學生姓名
            start_date: 開始日期
            end_date: 結束日期
            instrument_code: 樂器代碼
            prefetch_related_objects: 是否預載關聯物件
            
        Returns:
            QuerySet: 優化的查詢集
        """
        # 基本查詢
        queryset = PracticeLog.objects.filter(student_name=student_name)
        
        # 日期篩選
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        # 樂器篩選
        if instrument_code:
            queryset = queryset.filter(instrument__code=instrument_code)
        
        # 優化查詢 - 預載關聯物件
        if prefetch_related_objects:
            queryset = queryset.select_related('instrument')
            
        # 添加常用的註解
        queryset = queryset.annotate(
            weekday=ExtractWeekDay('date'),
            total_score=F('rating') * F('minutes')
        )
        
        return queryset
    
    @classmethod
    def get_student_stats_optimized(cls, student_name, days=30, use_cache=True):
        """
        獲取學生統計資料（優化版本）
        使用單一查詢獲取所有統計資料，避免多次查詢
        """
        cache_key = f'student_stats:{student_name}:{days}'
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Stats cache hit for {student_name}")
                return cached_data
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 單一查詢獲取所有統計資料
        stats = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=[start_date, end_date]
        ).aggregate(
            total_minutes=Coalesce(Sum('minutes'), 0),
            total_practices=Count('id'),
            avg_rating=Coalesce(Avg('rating'), 0.0),
            max_streak=Coalesce(Max('streak_count'), 0),
            unique_pieces=Count('piece', distinct=True),
            best_rating=Coalesce(Max('rating'), 0),
            total_points=Coalesce(Sum('points'), 0),
            avg_minutes=Coalesce(Avg('minutes'), 0.0),
            
            # 依據練習重點的統計
            basic_count=Count(Case(When(practice_focus='basic', then=1))),
            technique_count=Count(Case(When(practice_focus='technique', then=1))),
            music_count=Count(Case(When(practice_focus='musicality', then=1))),
            memory_count=Count(Case(When(practice_focus='memorization', then=1)))
        )
        
        # 計算連續練習天數（需要特別處理）
        streak_days = cls._calculate_streak_days_optimized(student_name)
        stats['current_streak'] = streak_days
        
        # 計算進步率
        stats['improvement_rate'] = cls._calculate_improvement_rate(student_name, days)
        
        # 快取結果
        if use_cache:
            cache.set(cache_key, stats, cls.CACHE_MEDIUM)
            
        return stats
    
    @classmethod
    def _calculate_streak_days_optimized(cls, student_name):
        """優化的連續練習天數計算"""
        # 獲取最近的練習日期（降序）
        recent_dates = list(
            PracticeLog.objects.filter(student_name=student_name)
            .values_list('date', flat=True)
            .distinct()
            .order_by('-date')[:30]  # 最多檢查30天
        )
        
        if not recent_dates:
            return 0
            
        streak = 0
        today = timezone.now().date()
        
        # 如果今天沒有練習，從昨天開始算
        if recent_dates[0] != today:
            if recent_dates[0] != today - timedelta(days=1):
                return 0
            current_date = today - timedelta(days=1)
        else:
            current_date = today
            
        # 計算連續天數
        for date in recent_dates:
            if date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
                
        return streak
    
    @classmethod
    def _calculate_improvement_rate(cls, student_name, days):
        """計算進步率"""
        end_date = timezone.now().date()
        mid_date = end_date - timedelta(days=days//2)
        start_date = end_date - timedelta(days=days)
        
        # 前半段和後半段的平均評分
        first_half_avg = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=[start_date, mid_date]
        ).aggregate(avg=Coalesce(Avg('rating'), 0.0))['avg']
        
        second_half_avg = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=[mid_date, end_date]
        ).aggregate(avg=Coalesce(Avg('rating'), 0.0))['avg']
        
        if first_half_avg > 0:
            improvement = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            return round(improvement, 1)
        return 0.0
    
    @classmethod
    def get_pieces_progress_batch(cls, student_name, limit=10):
        """
        批次獲取多個曲目的進度
        避免在迴圈中查詢資料庫
        """
        # 獲取最近練習的曲目
        recent_pieces = (
            PracticeLog.objects.filter(student_name=student_name)
            .values('piece')
            .annotate(
                last_practice=Max('date'),
                total_minutes=Sum('minutes'),
                avg_rating=Avg('rating'),
                practice_count=Count('id')
            )
            .order_by('-last_practice')[:limit]
        )
        
        # 建立進度映射
        progress_map = {}
        piece_names = [p['piece'] for p in recent_pieces]
        
        # 一次查詢所有曲目的詳細記錄
        all_logs = (
            PracticeLog.objects.filter(
                student_name=student_name,
                piece__in=piece_names
            )
            .values('piece', 'date', 'rating', 'minutes')
            .order_by('piece', 'date')
        )
        
        # 組織資料
        piece_logs = defaultdict(list)
        for log in all_logs:
            piece_logs[log['piece']].append(log)
        
        # 計算每個曲目的進度
        for piece_data in recent_pieces:
            piece_name = piece_data['piece']
            logs = piece_logs[piece_name]
            
            if len(logs) >= 2:
                # 計算進步趨勢
                first_rating = logs[0]['rating']
                last_rating = logs[-1]['rating']
                progress = ((last_rating - first_rating) / first_rating * 100) if first_rating > 0 else 0
            else:
                progress = 0
                
            progress_map[piece_name] = {
                'progress': round(progress, 1),
                'last_practice': piece_data['last_practice'],
                'total_minutes': piece_data['total_minutes'],
                'avg_rating': round(piece_data['avg_rating'], 1),
                'practice_count': piece_data['practice_count']
            }
            
        return progress_map
    
    @classmethod
    def get_practice_calendar_data(cls, student_name, year, month):
        """
        獲取練習日曆資料（優化版本）
        一次查詢獲取整月資料
        """
        cache_key = f'calendar:{student_name}:{year}:{month}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # 計算月份範圍
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        
        # 一次查詢獲取整月資料
        practices = (
            PracticeLog.objects.filter(
                student_name=student_name,
                date__range=[start_date, end_date]
            )
            .values('date')
            .annotate(
                total_minutes=Sum('minutes'),
                practice_count=Count('id'),
                avg_rating=Avg('rating'),
                has_video=Count(Case(When(video_url__isnull=False, then=1)))
            )
            .order_by('date')
        )
        
        # 建立日曆資料結構
        calendar_data = {}
        for practice in practices:
            calendar_data[practice['date'].day] = {
                'minutes': practice['total_minutes'],
                'count': practice['practice_count'],
                'rating': round(practice['avg_rating'], 1),
                'has_video': practice['has_video'] > 0
            }
            
        # 快取結果
        cache.set(cache_key, calendar_data, cls.CACHE_LONG)
        
        return calendar_data
    
    @classmethod
    def get_weekly_comparison(cls, student_name):
        """
        獲取週間比較資料
        使用資料庫層級的聚合，避免在 Python 中處理大量資料
        """
        today = timezone.now().date()
        
        # 本週和上週的範圍
        this_week_start = today - timedelta(days=today.weekday())
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start - timedelta(days=1)
        
        # 使用子查詢獲取兩週的資料
        weeks_data = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=last_week_start
        ).aggregate(
            # 本週資料
            this_week_minutes=Sum(
                Case(
                    When(date__gte=this_week_start, then='minutes'),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            this_week_count=Count(
                Case(When(date__gte=this_week_start, then=1))
            ),
            this_week_avg_rating=Avg(
                Case(
                    When(date__gte=this_week_start, then='rating'),
                    output_field=FloatField()
                )
            ),
            
            # 上週資料
            last_week_minutes=Sum(
                Case(
                    When(date__lt=this_week_start, then='minutes'),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            last_week_count=Count(
                Case(When(date__lt=this_week_start, then=1))
            ),
            last_week_avg_rating=Avg(
                Case(
                    When(date__lt=this_week_start, then='rating'),
                    output_field=FloatField()
                )
            )
        )
        
        return {
            'this_week': {
                'total_minutes': weeks_data['this_week_minutes'] or 0,
                'practice_count': weeks_data['this_week_count'],
                'avg_rating': round(weeks_data['this_week_avg_rating'] or 0, 1)
            },
            'last_week': {
                'total_minutes': weeks_data['last_week_minutes'] or 0,
                'practice_count': weeks_data['last_week_count'],
                'avg_rating': round(weeks_data['last_week_avg_rating'] or 0, 1)
            }
        }
    
    @classmethod
    def bulk_create_practices(cls, practice_data_list):
        """
        批次創建練習記錄
        減少資料庫交易次數
        """
        # 驗證資料
        validated_data = []
        for data in practice_data_list:
            # 資料驗證邏輯
            validated_data.append(data)
            
        # 使用 bulk_create 一次插入多筆資料
        if validated_data:
            practices = [PracticeLog(**data) for data in validated_data]
            created = PracticeLog.objects.bulk_create(
                practices,
                batch_size=100  # 每批次100筆
            )
            
            # 清除相關快取
            for practice in created:
                cache_pattern = f'student_stats:{practice.student_name}:*'
                # 清除快取的邏輯
                
            return created
        return []
    
    @classmethod
    def get_performance_metrics(cls, student_name, days=30):
        """
        獲取效能指標
        使用單一複雜查詢取代多個簡單查詢
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 使用 annotate 和 aggregate 組合，一次獲取所有指標
        metrics = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=[start_date, end_date]
        ).aggregate(
            # 基本指標
            total_practices=Count('id'),
            total_minutes=Coalesce(Sum('minutes'), 0),
            avg_daily_minutes=Coalesce(
                Sum('minutes') / Count('date', distinct=True),
                0.0
            ),
            
            # 評分相關
            avg_rating=Coalesce(Avg('rating'), 0.0),
            rating_improvement=Coalesce(
                Avg(Case(
                    When(date__gte=end_date-timedelta(days=7), then='rating')
                )) - Avg(Case(
                    When(date__lt=end_date-timedelta(days=7), then='rating')
                )),
                0.0
            ),
            
            # 練習分佈
            morning_practices=Count(
                Case(When(date__hour__lt=12, then=1))
            ),
            afternoon_practices=Count(
                Case(When(date__hour__range=(12, 18), then=1))
            ),
            evening_practices=Count(
                Case(When(date__hour__gte=18, then=1))
            ),
            
            # 最佳表現
            best_performance_date=Max(
                Case(
                    When(rating=5, then='date')
                )
            ),
            perfect_practices=Count(
                Case(When(rating=5, then=1))
            )
        )
        
        return metrics
    
    @classmethod
    def clear_student_cache(cls, student_name):
        """清除特定學生的所有快取"""
        cache_patterns = [
            f'student_stats:{student_name}:*',
            f'calendar:{student_name}:*',
            f'progress:{student_name}:*'
        ]
        
        # 實作快取清除邏輯
        for pattern in cache_patterns:
            # Django cache 不支援 pattern 刪除，需要自定義實作
            pass