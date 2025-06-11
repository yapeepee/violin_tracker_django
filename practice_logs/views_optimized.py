"""
優化後的小提琴練習記錄系統視圖處理模組
包含查詢優化、快取策略和性能改進
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, F, Prefetch, Case, When, IntegerField
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page, cache_control
from django.core.cache import cache
from django.db import transaction
from datetime import timedelta, date
from .models import PracticeLog, TeacherFeedback
import logging
from functools import wraps
from typing import Dict, List, Optional, Tuple, Union
import json

logger = logging.getLogger(__name__)

# ============ 快取裝飾器 ============
def smart_cache(cache_key_prefix: str, timeout: int = 300):
    """智能快取裝飾器，根據請求參數生成快取鍵"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # 生成快取鍵
            cache_key_parts = [cache_key_prefix]
            
            # 添加請求參數到快取鍵
            if request.method == 'GET':
                for key, value in sorted(request.GET.items()):
                    cache_key_parts.append(f"{key}:{value}")
            
            cache_key = ":".join(cache_key_parts)
            
            # 嘗試從快取獲取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 執行函數並快取結果
            result = func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator

# ============ 優化的查詢管理器 ============
class OptimizedPracticeLogManager:
    """優化的練習記錄查詢管理器"""
    
    @staticmethod
    def get_student_logs_optimized(student_name: str, start_date: date, end_date: date):
        """獲取學生練習記錄（優化版本）"""
        return PracticeLog.objects.filter(
            student_name=student_name,
            date__range=(start_date, end_date)
        ).select_related(
            'teacher_feedback'  # 如果有關聯的話
        ).only(
            # 只選擇需要的欄位
            'id', 'student_name', 'date', 'piece', 'minutes', 
            'rating', 'focus', 'mood', 'notes', 'created_at'
        ).order_by('-date')
    
    @staticmethod
    def get_practice_statistics(student_name: str, days: int = 30) -> Dict:
        """獲取練習統計數據（使用聚合優化）"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 使用單一查詢獲取所有統計
        stats = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=(start_date, end_date)
        ).aggregate(
            total_minutes=Sum('minutes'),
            total_sessions=Count('id'),
            avg_rating=Avg('rating'),
            avg_minutes=Avg('minutes'),
            unique_pieces=Count('piece', distinct=True),
            # 條件聚合
            excellent_sessions=Count(Case(
                When(rating__gte=4, then=1),
                output_field=IntegerField()
            )),
            long_sessions=Count(Case(
                When(minutes__gte=60, then=1),
                output_field=IntegerField()
            ))
        )
        
        # 添加默認值
        return {
            'total_minutes': stats['total_minutes'] or 0,
            'total_sessions': stats['total_sessions'] or 0,
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'avg_minutes': round(stats['avg_minutes'] or 0, 1),
            'unique_pieces': stats['unique_pieces'] or 0,
            'excellent_sessions': stats['excellent_sessions'] or 0,
            'long_sessions': stats['long_sessions'] or 0,
            'practice_days': days
        }
    
    @staticmethod
    def get_piece_progress_batch(student_name: str, pieces: List[str]) -> Dict[str, float]:
        """批量獲取多個曲目的進度"""
        progress_data = {}
        
        # 使用values和annotate進行批量查詢
        piece_stats = PracticeLog.objects.filter(
            student_name=student_name,
            piece__in=pieces
        ).values('piece').annotate(
            avg_rating=Avg('rating'),
            total_minutes=Sum('minutes'),
            session_count=Count('id'),
            latest_date=Max('date'),
            first_date=Min('date')
        )
        
        for stat in piece_stats:
            piece = stat['piece']
            # 計算進度分數
            progress_score = (
                (stat['avg_rating'] or 0) * 0.4 +  # 評分佔40%
                min(stat['total_minutes'] / 300, 1) * 0.3 +  # 練習時間佔30%
                min(stat['session_count'] / 10, 1) * 0.3  # 練習次數佔30%
            )
            progress_data[piece] = round(progress_score * 100, 1)
        
        return progress_data

# ============ 優化的視圖函數 ============
@cache_page(60 * 5)  # 快取5分鐘
def index(request):
    """優化的首頁視圖"""
    # 使用 select_related 和 prefetch_related 優化查詢
    recent_logs = PracticeLog.objects.select_related(
        'teacher_feedback'
    ).prefetch_related(
        Prefetch('student_achievements', 
                queryset=StudentAchievement.objects.select_related('achievement'))
    ).order_by('-created_at')[:10]
    
    # 批量獲取統計數據
    student_names = list(
        PracticeLog.objects.values_list('student_name', flat=True).distinct()[:20]
    )
    
    # 使用快取儲存學生列表
    cache.set('student_names_list', student_names, 600)  # 快取10分鐘
    
    context = {
        'recent_logs': recent_logs,
        'student_names': student_names,
        'total_students': len(student_names),
        'focus_choices': PracticeLog.FOCUS_CHOICES,
    }
    
    return render(request, 'practice_logs/index.html', context)

@smart_cache('analytics', timeout=300)
def analytics(request):
    """優化的分析頁面"""
    student_name = request.GET.get('student_name')
    if not student_name:
        return redirect('index')
    
    # 使用優化的查詢管理器
    manager = OptimizedPracticeLogManager()
    
    # 獲取統計數據
    stats = manager.get_practice_statistics(student_name, days=30)
    
    # 獲取練習記錄（只加載需要的欄位）
    recent_logs = manager.get_student_logs_optimized(
        student_name,
        timezone.now().date() - timedelta(days=30),
        timezone.now().date()
    )[:20]
    
    context = {
        'student_name': student_name,
        'stats': stats,
        'recent_logs': recent_logs,
    }
    
    return render(request, 'practice_logs/analytics.html', context)

@require_http_methods(["POST"])
@transaction.atomic
def add_log_optimized(request):
    """優化的新增練習記錄"""
    try:
        # 使用 transaction.atomic 確保數據一致性
        data = json.loads(request.body) if request.body else request.POST
        
        # 批量驗證數據
        validated_data = {
            'student_name': data.get('student_name', '').strip(),
            'piece': data.get('piece', '').strip(),
            'minutes': int(data.get('minutes', 0)),
            'rating': int(data.get('rating', 3)),
            'focus': data.get('focus', 'technique'),
            'mood': data.get('mood', 'focused'),
            'notes': data.get('notes', '').strip(),
            'date': timezone.now().date()
        }
        
        # 創建記錄
        log = PracticeLog.objects.create(**validated_data)
        
        # 清除相關快取
        cache_keys_to_delete = [
            f"analytics:student_name:{validated_data['student_name']}",
            f"student_stats:{validated_data['student_name']}",
            "recent_practice_logs"
        ]
        cache.delete_many(cache_keys_to_delete)
        
        return JsonResponse({
            'success': True,
            'log_id': log.id,
            'message': '練習記錄已成功添加'
        })
        
    except Exception as e:
        logger.error(f"Error adding practice log: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@cache_control(private=True, max_age=300)
def get_practice_data_api(request):
    """優化的API端點"""
    student_name = request.GET.get('student_name')
    days = int(request.GET.get('days', 30))
    
    if not student_name:
        return JsonResponse({'error': '需要提供學生姓名'}, status=400)
    
    # 使用快取
    cache_key = f"practice_data:{student_name}:{days}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
    
    # 獲取數據
    manager = OptimizedPracticeLogManager()
    stats = manager.get_practice_statistics(student_name, days)
    
    # 獲取每日練習數據
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    daily_data = PracticeLog.objects.filter(
        student_name=student_name,
        date__range=(start_date, end_date)
    ).values('date').annotate(
        total_minutes=Sum('minutes'),
        avg_rating=Avg('rating'),
        session_count=Count('id')
    ).order_by('date')
    
    # 構建響應數據
    response_data = {
        'stats': stats,
        'daily_data': list(daily_data),
        'student_name': student_name,
        'period_days': days
    }
    
    # 快取結果
    cache.set(cache_key, response_data, 300)  # 快取5分鐘
    
    return JsonResponse(response_data)

# ============ 批量操作優化 ============
@require_http_methods(["POST"])
@transaction.atomic
def bulk_add_logs(request):
    """批量添加練習記錄"""
    try:
        data = json.loads(request.body)
        logs_data = data.get('logs', [])
        
        if not logs_data:
            return JsonResponse({'error': '沒有提供練習記錄'}, status=400)
        
        # 批量創建
        logs = []
        for log_data in logs_data:
            logs.append(PracticeLog(
                student_name=log_data.get('student_name', '').strip(),
                piece=log_data.get('piece', '').strip(),
                minutes=int(log_data.get('minutes', 0)),
                rating=int(log_data.get('rating', 3)),
                focus=log_data.get('focus', 'technique'),
                mood=log_data.get('mood', 'focused'),
                notes=log_data.get('notes', '').strip(),
                date=log_data.get('date', timezone.now().date())
            ))
        
        # 使用 bulk_create 提升性能
        created_logs = PracticeLog.objects.bulk_create(logs, batch_size=100)
        
        # 清除快取
        student_names = list(set(log.student_name for log in created_logs))
        cache_keys = []
        for name in student_names:
            cache_keys.extend([
                f"analytics:student_name:{name}",
                f"student_stats:{name}",
                f"practice_data:{name}:*"
            ])
        cache.delete_many(cache_keys)
        
        return JsonResponse({
            'success': True,
            'created_count': len(created_logs)
        })
        
    except Exception as e:
        logger.error(f"Error in bulk add: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

# ============ 資料庫維護任務 ============
def optimize_database():
    """定期優化資料庫"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # SQLite優化命令
        cursor.execute("VACUUM;")
        cursor.execute("ANALYZE;")
        cursor.execute("REINDEX;")
    
    logger.info("Database optimization completed")

# ============ 性能監控 ============
class PerformanceMiddleware:
    """性能監控中間件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import time
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # 記錄慢查詢
        if duration > 1.0:  # 超過1秒
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
        
        # 添加性能標頭
        response['X-Response-Time'] = f"{duration:.3f}"
        
        return response