"""
優化後的小提琴練習記錄系統視圖處理模組 - 完全兼容版本
保持所有原有API端點，只優化內部實現
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, Case, When, F, IntegerField
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from datetime import timedelta, date
from .models import PracticeLog
import logging
from functools import wraps
from typing import Dict, List, Optional, Tuple, Union
import json

logger = logging.getLogger(__name__)

# ============ 常量定義 ============
class Constants:
    DEFAULT_DAYS = 30
    MAX_DAYS = 365
    RECENT_DAYS = 7
    MIN_PRACTICE_MINUTES = 1
    MAX_PRACTICE_MINUTES = 600
    MIN_RATING = 1
    MAX_RATING = 10

# 練習重點選項
FOCUS_CHOICES = [
    ('intonation', '音準'),
    ('rhythm', '節奏'),
    ('tone', '音色'),
    ('technique', '技巧'),
    ('expression', '表現力'),
    ('sight_reading', '視奏'),
    ('memorization', '記譜'),
    ('other', '其他')
]

# ============ 自定義異常 ============
class APIException(Exception):
    def __init__(self, message="An error occurred", status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

# ============ 裝飾器 ============
def api_exception_handler(func):
    """API異常處理裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            return JsonResponse({
                'error': e.message,
                'error_code': e.error_code
            }, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return JsonResponse({
                'error': "An unexpected error occurred",
                'error_code': 'INTERNAL_ERROR'
            }, status=500)
    return wrapper

def page_exception_handler(func):
    """頁面異常處理裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            return render(args[0], 'practice_logs/error.html', {
                'error_title': '錯誤',
                'error_message': e.message,
                'error_code': e.error_code,
                'back_url': '/',
                'back_text': '返回首頁'
            })
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return render(args[0], 'practice_logs/error.html', {
                'error_title': '系統錯誤',
                'error_message': '發生未預期的錯誤',
                'back_url': '/',
                'back_text': '返回首頁'
            })
    return wrapper

# ============ 請求處理輔助類 ============
class RequestHelper:
    """請求處理輔助類"""
    
    @staticmethod
    def get_student_name(request) -> str:
        student_name = request.GET.get('student_name')
        return DataValidator.validate_student_name(student_name)
    
    @staticmethod
    def get_date_range(request) -> Tuple[date, date]:
        end_date = timezone.now().date()
        days = request.GET.get('days', Constants.DEFAULT_DAYS)
        try:
            days = int(days)
            if days < 1:
                days = Constants.DEFAULT_DAYS
            elif days > Constants.MAX_DAYS:
                days = Constants.MAX_DAYS
        except ValueError:
            days = Constants.DEFAULT_DAYS
        
        start_date = end_date - timedelta(days=days)
        return DataValidator.validate_date_range(start_date, end_date)

# ============ 數據驗證 ============
class DataValidator:
    """數據驗證類"""
    
    @staticmethod
    def validate_student_name(name: str) -> str:
        if not name or not name.strip():
            raise APIException('學生姓名不能為空')
        if len(name.strip()) > 50:
            raise APIException('學生姓名不能超過50個字符')
        return name.strip()
    
    @staticmethod
    def validate_practice_minutes(minutes: Union[str, int]) -> int:
        try:
            minutes = int(minutes)
            if minutes < Constants.MIN_PRACTICE_MINUTES:
                raise APIException(f'練習時間不能少於{Constants.MIN_PRACTICE_MINUTES}分鐘')
            if minutes > Constants.MAX_PRACTICE_MINUTES:
                raise APIException(f'練習時間不能超過{Constants.MAX_PRACTICE_MINUTES}分鐘')
            return minutes
        except (ValueError, TypeError):
            raise APIException('練習時間必須是有效數字')
    
    @staticmethod
    def validate_rating(rating: Union[str, int]) -> int:
        try:
            rating = int(rating)
            if not (Constants.MIN_RATING <= rating <= Constants.MAX_RATING):
                raise APIException(f'評分必須在{Constants.MIN_RATING}到{Constants.MAX_RATING}之間')
            return rating
        except (ValueError, TypeError):
            raise APIException('評分必須是有效數字')
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> Tuple[date, date]:
        if start_date > end_date:
            raise APIException('開始日期不能晚於結束日期')
        if (end_date - start_date).days > Constants.MAX_DAYS:
            raise APIException(f'日期範圍不能超過{Constants.MAX_DAYS}天')
        return start_date, end_date

# ============ 數據庫查詢服務 ============
class PracticeLogService:
    """練習記錄服務類"""
    
    @staticmethod
    def get_base_queryset(student_name: str, start_date: date, end_date: date):
        """獲取基礎查詢集"""
        return PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=start_date,
            date__lte=end_date
        )
    
    @staticmethod
    def get_student_stats(student_name: str) -> Dict:
        """獲取學生基本統計"""
        stats = PracticeLog.objects.filter(student_name=student_name).aggregate(
            total_practice_time=Sum('minutes'),
            total_sessions=Count('id'),
            avg_rating=Avg('rating'),
            avg_session_length=Avg('minutes')
        )
        
        return {
            'total_practice_time': stats['total_practice_time'] or 0,
            'total_sessions': stats['total_sessions'] or 0,
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'avg_session_length': round(stats['avg_session_length'] or 0, 2)
        }
    
    @staticmethod
    def get_recent_logs(student_name: str, limit: int = 5) -> List:
        """獲取最近的練習記錄"""
        return list(PracticeLog.objects
                   .filter(student_name=student_name)
                   .order_by('-date', '-id')[:limit])
    
    @staticmethod
    def create_practice_log(data: Dict) -> PracticeLog:
        """創建練習記錄"""
        # 只處理必要的字段
        validated_data = {
            'student_name': DataValidator.validate_student_name(data['student_name']),
            'piece': data['piece'].strip() if data.get('piece') else '',
            'minutes': DataValidator.validate_practice_minutes(data['minutes']),
            'rating': DataValidator.validate_rating(data['rating']),
            'date': data.get('date') or timezone.now().date(),
            'focus': data.get('focus', 'other'),  # 預設為"其他"
            'notes': data.get('notes', '').strip()  # 預設為空字串
        }
        
        if not validated_data['piece']:
            raise APIException('樂曲名稱不能為空')
            
        # 驗證練習重點是否有效
        if validated_data['focus'] not in dict(FOCUS_CHOICES):
            raise APIException('無效的練習重點選項')
            
        # 驗證筆記長度
        if len(validated_data['notes']) > 1000:
            raise APIException('練習筆記不能超過1000個字符')
            
        return PracticeLog.objects.create(**validated_data)

# ============ 頁面視圖 ============
@api_exception_handler
def index(request):
    """首頁視圖"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 驗證並創建練習記錄
            PracticeLogService.create_practice_log(data)
            return JsonResponse({'message': '練習記錄已保存'})
        except json.JSONDecodeError:
            raise APIException('無效的請求數據格式')
        except Exception as e:
            logger.error(f"Error creating practice log: {str(e)}")
            raise APIException('創建練習記錄失敗')

    # 獲取最後一個練習記錄的學生姓名
    last_practice = PracticeLog.objects.order_by('-date', '-id').first()
    current_student = last_practice.student_name if last_practice else None

    return render(request, 'practice_logs/index.html', {
        'current_student': current_student,
        'focus_choices': FOCUS_CHOICES
    })

@page_exception_handler
def analytics(request, student_name):
    """分析頁面視圖"""
    # 1. 驗證學生姓名
    validated_name = DataValidator.validate_student_name(student_name)
    
    # 2. 檢查學生是否存在
    if not PracticeLog.objects.filter(student_name=validated_name).exists():
        raise APIException(
            message=f'找不到學生 "{validated_name}" 的練習記錄',
            status_code=404,
            error_code='STUDENT_NOT_FOUND'
        )

    # 3. 獲取學生統計數據
    stats = PracticeLogService.get_student_stats(validated_name)
        
    # 4. 獲取最近的練習記錄
    recent_logs = PracticeLogService.get_recent_logs(validated_name, limit=3)

    # 5. 準備上下文數據
    context = {
        'student_name': validated_name,
        'stats': stats,
        'recent_logs': recent_logs,
        'has_data': bool(stats['total_sessions']),
        'last_practice': recent_logs[0].date if recent_logs else None
    }
    
    return render(request, 'practice_logs/analytics.html', context)

# ============ API 端點 - 保持原有函數名和響應格式 ============

@api_exception_handler
@require_http_methods(["GET"])
def chart_data(request):
    """獲取練習時間圖表數據的API端點"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    data = (PracticeLogService.get_base_queryset(student_name, start_date, end_date)
           .values('piece')
           .annotate(
               total_minutes=Sum('minutes'),
               avg_rating=Avg('rating')
           )
           .order_by('-total_minutes'))
    
    if not data.exists():
        raise APIException(
            message="找不到練習記錄",
            status_code=404,
            error_code='NO_PRACTICE_DATA'
        )
    
    return JsonResponse({
        'status': 'success',
        'data': list(data)
    })

@api_exception_handler
def get_weekly_practice_data(request):
    """獲取每週練習總時數的API端點 - 保持原格式"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    data = (PracticeLogService.get_base_queryset(student_name, start_date, end_date)
           .values('date')
           .annotate(
               total_minutes=Sum('minutes'),
               avg_rating=Avg('rating')
           )
           .order_by('date'))
    
    return JsonResponse(list(data), safe=False)

@api_exception_handler
def get_piece_practice_data(request):
    """獲取各樂曲練習總時間的API端點 - 包含多維度分析數據"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    base_queryset = PracticeLogService.get_base_queryset(student_name, start_date, end_date)
    
    # 獲取所有曲目的總練習時間
    total_practice_time = base_queryset.aggregate(
        total_minutes=Sum('minutes')
    )['total_minutes'] or 1  # 避免除以零
    
    # 獲取基本統計數據
    pieces_data = (base_queryset
           .values('piece')
           .annotate(
               total_minutes=Sum('minutes'),
               practice_count=Count('id'),
               avg_rating=Avg('rating'),
               avg_session_length=Avg('minutes'),
               # 按練習重點分類的時間統計
               technique_time=Sum(Case(
                   When(focus='technique', then=F('minutes')),
                   default=0,
                   output_field=IntegerField(),
               )),
               rhythm_time=Sum(Case(
                   When(focus='rhythm', then=F('minutes')),
                   default=0,
                   output_field=IntegerField(),
               )),
               intonation_time=Sum(Case(
                   When(focus='intonation', then=F('minutes')),
                   default=0,
                   output_field=IntegerField(),
               )),
               expression_time=Sum(Case(
                   When(focus='expression', then=F('minutes')),
                   default=0,
                   output_field=IntegerField(),
               ))
           )
           .order_by('-total_minutes'))
    
    # 轉換為列表以便添加進步和效率數據
    result_data = []
    for piece in pieces_data:
        # 計算投入時間比例
        time_ratio = (piece['total_minutes'] / total_practice_time) * 100
        
        # 獲取進步數據
        progress = PracticeLog.get_piece_progress(student_name, piece['piece'])
        
        # 計算各練習重點的時間比例
        total_piece_time = piece['total_minutes'] or 1  # 避免除以零
        focus_ratios = {
            'technique': (piece['technique_time'] / total_piece_time) * 100,
            'rhythm': (piece['rhythm_time'] / total_piece_time) * 100,
            'intonation': (piece['intonation_time'] / total_piece_time) * 100,
            'expression': (piece['expression_time'] / total_piece_time) * 100
        }
        
        # 計算技巧掌握度（基於評分和練習時間）
        mastery = min((piece['avg_rating'] * piece['total_minutes']) / 300, 100)  # 上限100%
        
        result_data.append({
            'piece': piece['piece'],
            'dimensions': {
                'time_investment': round(time_ratio, 1),  # 投入時間比例
                'score_progress': round(progress * 20, 1),  # 分數提升（轉換為百分比）
                'mastery': round(mastery, 1),  # 技巧掌握度
                'technique': round(focus_ratios['technique'], 1),
                'rhythm': round(focus_ratios['rhythm'], 1),
                'intonation': round(focus_ratios['intonation'], 1),
                'expression': round(focus_ratios['expression'], 1)
            },
            'practice_count': piece['practice_count'],
            'avg_rating': round(piece['avg_rating'], 1)
        })

    return JsonResponse(result_data, safe=False)

@api_exception_handler
def get_recent_trend_data(request):
    """獲取最近練習趨勢的API端點 - 保持原格式"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    data = (PracticeLogService.get_base_queryset(student_name, start_date, end_date)
           .values('date')
           .annotate(
               total_minutes=Sum('minutes'),
               pieces_practiced=Count('piece', distinct=True),
               avg_rating=Avg('rating')
           )
           .order_by('date'))

    return JsonResponse(list(data), safe=False)

@api_exception_handler
def get_piece_switching_stats(request):
    """獲取樂曲切換頻率統計的API端點 - 保持原格式"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    data = (PracticeLogService.get_base_queryset(student_name, start_date, end_date)
           .values('date')
           .annotate(
               pieces_count=Count('piece', distinct=True),
               total_sessions=Count('id'),
               total_minutes=Sum('minutes'),
               avg_rating=Avg('rating')
           )
           .order_by('date'))

    return JsonResponse(list(data), safe=False)

@api_exception_handler
def get_rest_day_stats(request):
    """獲取休息日統計的API端點"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    # 獲取所有練習日期
    practice_dates = set(
        PracticeLogService.get_base_queryset(student_name, start_date, end_date)
        .values_list('date', flat=True)
    )
    
    if not practice_dates:
        raise APIException(
            message="找不到練習記錄",
            status_code=404,
            error_code='NO_PRACTICE_DATA'
        )
    
    # 計算練習日和休息日
    current_date = start_date
    practice_days = []
    rest_days = []
    
    while current_date <= end_date:
        if current_date in practice_dates:
            practice_days.append(current_date)
        else:
            rest_days.append(current_date)
        current_date += timedelta(days=1)
    
    # 計算統計數據
    total_days = (end_date - start_date).days + 1
    practice_count = len(practice_days)
    
    return JsonResponse({
        'total_days': total_days,
        'practice_days': practice_count,
        'rest_days': total_days - practice_count,
        'practice_dates': [d.strftime('%Y-%m-%d') for d in practice_days],
        'rest_dates': [d.strftime('%Y-%m-%d') for d in rest_days],
        'practice_ratio': practice_count / total_days if total_days > 0 else 0
    })

@api_exception_handler
def get_focus_stats(request):
    """獲取練習重點統計的API端點 - 保持原格式"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    # 獲取所有練習重點的統計數據
    focus_stats = (PracticeLogService.get_base_queryset(student_name, start_date, end_date)
                  .values('focus')
                  .annotate(
                      total_minutes=Sum('minutes'),
                      session_count=Count('id'),
                      avg_rating=Avg('rating')
                  )
                  .order_by('-total_minutes'))

    # 將統計數據轉換為字典形式，方便查找
    focus_data = {item['focus']: item for item in focus_stats}
    
    # 確保所有練習重點都有數據
    data = []
    for focus_code, focus_name in PracticeLog.FOCUS_CHOICES:
        if focus_code in focus_data:
            item = focus_data[focus_code]
        else:
            item = {
                'focus': focus_code,
                'total_minutes': 0,
                'session_count': 0,
                'avg_rating': 0
            }
        item['focus_display'] = focus_name
        data.append(item)

    return JsonResponse(data, safe=False)

# ============ 額外的優化功能（可選使用） ============

@api_exception_handler
def get_practice_summary(request):
    """新增：獲取練習總結數據（可選的新API）"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    queryset = PracticeLogService.get_base_queryset(student_name, start_date, end_date)
    
    # 綜合統計
    summary = queryset.aggregate(
        total_minutes=Sum('minutes'),
        total_sessions=Count('id'),
        avg_rating=Avg('rating'),
        unique_pieces=Count('piece', distinct=True)
    )
    
    # 每日數據
    daily_data = (queryset
                 .values('date')
                 .annotate(
                     daily_minutes=Sum('minutes'),
                     daily_sessions=Count('id')
                 )
                 .order_by('date'))
    
    return JsonResponse({
        'summary': summary,
        'daily_data': list(daily_data),
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
    })