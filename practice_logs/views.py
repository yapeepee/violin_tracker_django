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
# 遊戲化功能已暫時移除
# from .services import GamificationService, AchievementService, ChallengeService
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
    MAX_RATING = 5

# 練習重點選項 - 与模型保持一致
FOCUS_CHOICES = [
    ('technique', '技巧練習'),
    ('expression', '表現力'),
    ('rhythm', '節奏'),
    ('sight_reading', '視奏'),
    ('memorization', '記譜'),
    ('ensemble', '重奏'),
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
    
    @staticmethod
    def get_days_filter(request) -> int:
        """獲取天數過濾器"""
        days = request.GET.get('days', Constants.DEFAULT_DAYS)
        try:
            days = int(days)
            if days < 1:
                days = Constants.DEFAULT_DAYS
            elif days > Constants.MAX_DAYS:
                days = Constants.MAX_DAYS
        except ValueError:
            days = Constants.DEFAULT_DAYS
        return days

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
        from django.utils import timezone
        from datetime import timedelta
        
        # 獲取基本統計
        stats = PracticeLog.objects.filter(student_name=student_name).aggregate(
            total_practice_time=Sum('minutes'),
            total_sessions=Count('id'),
            avg_rating=Avg('rating'),
            avg_session_length=Avg('minutes')
        )
        
        # 獲取本週練習數據
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        recent_sessions = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=week_start
        ).count()
        
        return {
            'total_practice_time': stats['total_practice_time'] or 0,
            'total_minutes': stats['total_practice_time'] or 0,  # 添加這個別名供模板使用
            'total_sessions': stats['total_sessions'] or 0,
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'average_rating': round(stats['avg_rating'] or 0, 2),  # 添加這個別名供模板使用
            'avg_session_length': round(stats['avg_session_length'] or 0, 2),
            'recent_sessions': recent_sessions
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
    """首頁視圖 - 整合遊戲化功能"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 驗證並創建練習記錄
            practice_log = PracticeLogService.create_practice_log(data)
            
            # 遊戲化邏輯已暫時移除
            # gamification_result = GamificationService.process_practice_log_creation(practice_log)
            
            response_data = {
                'message': '練習記錄已保存',
                # 遊戲化相關數據已移除
                # 'newly_earned_achievements': [
                #     {
                #         'name': achievement.name,
                #         'icon': achievement.icon,
                #         'description': achievement.description,
                #         'points': achievement.points
                #     } for achievement in gamification_result['newly_earned_achievements']
                # ],
                # 'level_info': gamification_result['level_info']
            }
            
            return JsonResponse(response_data)
            
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

@api_exception_handler
def add_log(request):
    """新增練習記錄頁面"""
    if request.method == 'POST':
        try:
            data = {
                'student_name': request.POST.get('student_name'),
                'date': request.POST.get('date'),
                'piece': request.POST.get('piece'),
                'minutes': request.POST.get('minutes'),
                'focus': request.POST.get('focus'),
                'rating': request.POST.get('rating'),
                'notes': request.POST.get('notes', '')
            }
            
            # 驗證並創建練習記錄
            practice_log = PracticeLogService.create_practice_log(data)
            
            from django.contrib import messages
            messages.success(request, '練習記錄已成功保存！')
            return redirect('practice_logs:index')
            
        except Exception as e:
            logger.error(f"Error creating practice log: {str(e)}")
            from django.contrib import messages
            messages.error(request, f'保存失敗：{str(e)}')
    
    # 獲取當前用戶的姓名
    current_student = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        current_student = request.user.profile.display_name
    
    # 如果沒有認證用戶，獲取最後一個練習記錄的學生姓名
    if not current_student:
        last_practice = PracticeLog.objects.order_by('-date', '-id').first()
        current_student = last_practice.student_name if last_practice else None
    
    return render(request, 'practice_logs/add_log.html', {
        'current_student': current_student,
        'focus_choices': FOCUS_CHOICES
    })

@api_exception_handler
def my_practices(request):
    """我的練習記錄頁面"""
    if not request.user.is_authenticated:
        return redirect('practice_logs:login')
    
    current_student = None
    if hasattr(request.user, 'profile'):
        current_student = request.user.profile.display_name
    
    if not current_student:
        from django.contrib import messages
        messages.error(request, '無法獲取用戶信息')
        return redirect('practice_logs:index')
    
    # 獲取練習記錄，支持分頁
    from django.core.paginator import Paginator
    practices = PracticeLog.objects.filter(
        student_name=current_student
    ).order_by('-date', '-id')
    
    paginator = Paginator(practices, 10)  # 每頁10條記錄
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 獲取統計數據
    stats = PracticeLogService.get_student_stats(current_student)
    
    return render(request, 'practice_logs/my_practices.html', {
        'page_obj': page_obj,
        'current_student': current_student,
        'stats': stats,
        'total_practices': practices.count()
    })

@api_exception_handler
def achievements_page(request):
    """成就頁面視圖"""
    # 獲取當前用戶
    current_student = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        current_student = request.user.profile.display_name
    
    # 如果沒有認證用戶，返回提示頁面
    if not current_student:
        return render(request, 'practice_logs/achievements.html', {
            'achievements': [],
            'current_student': None,
            'total_points': 0,
            'level_info': {'level': 1, 'name': '初學者', 'progress': 0}
        })
    
    # 獲取用戶的成就數據（暫時使用模擬數據）
    from .models import Achievement, StudentAchievement
    try:
        user_achievements = StudentAchievement.objects.filter(
            student=request.user
        ).select_related('achievement')
        
        total_points = sum(sa.achievement.points for sa in user_achievements)
        
        # 簡單的等級計算
        level = min(10, max(1, total_points // 100 + 1))
        level_names = {
            1: '初學者', 2: '練習生', 3: '進步中', 4: '熟練者', 5: '優秀者',
            6: '專家', 7: '大師', 8: '宗師', 9: '傳奇', 10: '完美者'
        }
        
        level_info = {
            'level': level,
            'name': level_names.get(level, '初學者'),
            'progress': (total_points % 100) if level < 10 else 100
        }
        
    except Exception as e:
        logger.error(f"Error getting achievements: {str(e)}")
        user_achievements = []
        total_points = 0
        level_info = {'level': 1, 'name': '初學者', 'progress': 0}
    
    return render(request, 'practice_logs/achievements.html', {
        'achievements': user_achievements,
        'current_student': current_student,
        'total_points': total_points,
        'level_info': level_info
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
    """獲取練習重點統計的API端點 - 支持按曲目篩選"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    piece = request.GET.get('piece', None)  # 新增：獲取曲目參數
    
    # 基礎查詢
    base_query = PracticeLogService.get_base_queryset(student_name, start_date, end_date)
    
    # 如果指定了曲目，添加曲目過濾
    if piece:
        base_query = base_query.filter(piece=piece)
    
    # 獲取所有練習重點的統計數據
    focus_stats = (base_query
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

    # 添加額外的統計信息
    total_minutes = sum(item['total_minutes'] for item in data)
    total_sessions = sum(item['session_count'] for item in data)
    avg_rating = sum(item['avg_rating'] * item['session_count'] for item in data if item['avg_rating']) / total_sessions if total_sessions > 0 else 0
    
    for item in data:
        item['percentage'] = round((item['total_minutes'] / total_minutes * 100) if total_minutes > 0 else 0, 1)

    return JsonResponse({
        'piece': piece or '整體分析',
        'data': data,
        'total_minutes': total_minutes,
        'total_sessions': total_sessions,
        'avg_rating': avg_rating
    }, safe=False)

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

@api_exception_handler
def get_period_stats(request):
    """獲取指定時間段的統計數據"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    # 獲取指定時間段的統計
    base_query = PracticeLogService.get_base_queryset(student_name, start_date, end_date)
    
    stats = base_query.aggregate(
        total_practice_time=Sum('minutes'),
        total_sessions=Count('id'),
        avg_rating=Avg('rating'),
        avg_session_length=Avg('minutes')
    )
    
    return JsonResponse({
        'total_practice_time': stats['total_practice_time'] or 0,
        'total_sessions': stats['total_sessions'] or 0,
        'avg_rating': round(stats['avg_rating'] or 0, 2),
        'avg_session_length': round(stats['avg_session_length'] or 0, 2),
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
    })

@api_exception_handler
def get_student_pieces(request):
    """獲取學生練習過的所有曲目列表"""
    student_name = RequestHelper.get_student_name(request)
    start_date, end_date = RequestHelper.get_date_range(request)
    
    # 獲取基礎查詢集
    base_query = PracticeLogService.get_base_queryset(student_name, start_date, end_date)
    
    # 獲取所有曲目及其基本統計
    pieces_data = (base_query
                  .values('piece')
                  .annotate(
                      total_minutes=Sum('minutes'),
                      practice_count=Count('id'),
                      avg_rating=Avg('rating')
                  )
                  .order_by('-total_minutes'))
    
    # 計算總練習時間
    total_practice_time = sum(piece['total_minutes'] for piece in pieces_data)
    
    # 格式化數據
    result = []
    for piece in pieces_data:
        result.append({
            'piece': piece['piece'],
            'total_minutes': piece['total_minutes'],
            'practice_count': piece['practice_count'],
            'avg_rating': round(piece['avg_rating'], 1),
            'percentage': round((piece['total_minutes'] / total_practice_time * 100) if total_practice_time > 0 else 0, 1)
        })
    
    return JsonResponse(result, safe=False)


# ============ 新增：練習記錄上傳相關視圖 ============

def practice_upload_page(request):
    """練習記錄上傳頁面 - 古典樂風格"""
    return render(request, 'practice_logs/practice_upload.html')

def test_rating_page(request):
    """動態評分系統測試頁面"""
    return render(request, 'practice_logs/test_rating.html')


@api_exception_handler
@require_http_methods(["POST"])
def upload_practice_record(request):
    """處理練習記錄上傳 (包含影片)"""
    try:
        # 提取基本表單數據
        form_data = {
            'student_name': request.POST.get('student_name'),
            'date': request.POST.get('date'),
            'piece': request.POST.get('piece'),
            'minutes': int(request.POST.get('minutes', 0)),
            'focus': request.POST.get('focus', 'technique'),
            'mood': request.POST.get('mood', 'focused'),
            'notes': request.POST.get('notes', ''),
            'student_notes_to_teacher': request.POST.get('student_notes_to_teacher', ''),
        }
        
        # 提取動態評分數據
        focus_specific_ratings = []
        all_rating_fields = [
            'technique_bow_control', 'technique_finger_position', 'technique_intonation',
            'expression_dynamics', 'expression_phrasing', 'expression_emotion',
            'rhythm_tempo_stability', 'rhythm_pattern_accuracy',
            'sight_reading_fluency', 'sight_reading_accuracy',
            'memorization_stability', 'memorization_confidence',
            'ensemble_listening', 'ensemble_timing'
        ]
        
        for field in all_rating_fields:
            value = request.POST.get(field)
            if value:
                try:
                    form_data[field] = int(value)
                    focus_specific_ratings.append(int(value))
                except ValueError:
                    pass
        
        # 計算整體評分 (基於實際填寫的評分平均)
        if focus_specific_ratings:
            overall_rating = round(sum(focus_specific_ratings) / len(focus_specific_ratings))
        else:
            overall_rating = 3  # 預設值
        form_data['rating'] = overall_rating
        
        # 處理影片文件
        video_file = request.FILES.get('video_file')
        thumbnail_file = request.FILES.get('thumbnail')
        
        if video_file:
            # 驗證影片文件
            if not _validate_video_file(video_file):
                raise APIException(
                    message="不支援的影片格式或文件過大",
                    status_code=400,
                    error_code='INVALID_VIDEO_FILE'
                )
            
            form_data['video_file'] = video_file
            
            # 處理縮圖
            if thumbnail_file:
                form_data['video_thumbnail'] = thumbnail_file
            
            # 獲取影片資訊
            video_info = _extract_video_metadata(video_file)
            form_data.update(video_info)
        
        # 創建練習記錄
        practice_log = PracticeLog.objects.create(**form_data)
        
        # 生成回應數據
        response_data = {
            'success': True,
            'practice_log_id': practice_log.id,
            'message': '練習記錄上傳成功！',
            'data': {
                'student_name': practice_log.student_name,
                'piece': practice_log.piece,
                'date': practice_log.date.strftime('%Y-%m-%d'),
                'overall_rating': practice_log.get_overall_performance_score(),
                'mood_display': practice_log.get_mood_display_emoji(),
                'has_video': practice_log.has_video,
                'thumbnail_url': practice_log.video_thumbnail.url if practice_log.video_thumbnail else None,
            }
        }
        
        logger.info(f"Practice record uploaded successfully for {practice_log.student_name}")
        return JsonResponse(response_data)
        
    except ValueError as e:
        raise APIException(
            message=f"數據格式錯誤: {str(e)}",
            status_code=400,
            error_code='INVALID_DATA_FORMAT'
        )
    except Exception as e:
        logger.error(f"Error uploading practice record: {str(e)}")
        raise APIException(
            message="練習記錄上傳失敗",
            status_code=500,
            error_code='UPLOAD_FAILED'
        )


def _validate_video_file(video_file):
    """驗證影片文件"""
    # 檢查文件大小 (100MB)
    max_size = 100 * 1024 * 1024
    if video_file.size > max_size:
        return False
    
    # 檢查文件類型
    allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/webm']
    if video_file.content_type not in allowed_types:
        return False
    
    return True


def _extract_video_metadata(video_file):
    """提取影片元資料"""
    try:
        # 這裡可以使用 ffmpeg-python 或其他庫來提取詳細資訊
        # 目前先返回基本資訊
        file_size_mb = round(video_file.size / (1024 * 1024), 2)
        
        return {
            'file_size': file_size_mb,
            # 'video_duration': None,  # 需要 ffmpeg 或類似工具
        }
    except Exception as e:
        logger.warning(f"Could not extract video metadata: {str(e)}")
        return {
            'file_size': round(video_file.size / (1024 * 1024), 2),
        }


@api_exception_handler
@require_http_methods(["GET"])
def get_focus_skill_analysis(request):
    """獲取練習重點技能分析數據 - 用於圖表展示"""
    student_name = RequestHelper.get_student_name(request)
    focus_type = request.GET.get('focus_type', 'technique')
    days = RequestHelper.get_days_filter(request)
    
    try:
        # 獲取指定時間範圍內的練習記錄
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        practice_logs = PracticeLog.objects.filter(
            student_name=student_name,
            focus=focus_type,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        if not practice_logs.exists():
            return JsonResponse({
                'focus_type': focus_type,
                'focus_name': dict(PracticeLog.FOCUS_CHOICES).get(focus_type, '未知'),
                'skill_trends': [],
                'average_scores': {},
                'improvement_rate': 0,
                'total_sessions': 0
            })
        
        # 獲取技能評分配置
        if focus_type not in PracticeLog.FOCUS_RATING_CONFIG:
            raise APIException(
                message=f"不支援的練習重點: {focus_type}",
                status_code=400,
                error_code='INVALID_FOCUS_TYPE'
            )
        
        config = PracticeLog.FOCUS_RATING_CONFIG[focus_type]
        skill_fields = [rating[0] for rating in config['ratings']]
        
        # 構建技能趨勢數據
        skill_trends = {}
        for field_name, display_name, description in config['ratings']:
            skill_trends[field_name] = {
                'name': display_name,
                'description': description,
                'data_points': []
            }
        
        # 收集每日數據
        for log in practice_logs:
            date_str = log.date.strftime('%Y-%m-%d')
            
            for field_name in skill_fields:
                value = getattr(log, field_name, None)
                if value is not None:
                    skill_trends[field_name]['data_points'].append({
                        'date': date_str,
                        'value': value,
                        'piece': log.piece,
                        'minutes': log.minutes
                    })
        
        # 計算平均分數和改善率
        average_scores = {}
        improvement_rates = {}
        
        for field_name, trend_data in skill_trends.items():
            if trend_data['data_points']:
                values = [point['value'] for point in trend_data['data_points']]
                average_scores[field_name] = round(sum(values) / len(values), 1)
                
                # 計算改善率 (比較前後25%的數據)
                if len(values) >= 4:
                    quarter = max(1, len(values) // 4)
                    early_avg = sum(values[:quarter]) / quarter
                    recent_avg = sum(values[-quarter:]) / quarter
                    improvement_rates[field_name] = round(((recent_avg - early_avg) / early_avg) * 100, 1)
                else:
                    improvement_rates[field_name] = 0
        
        # 計算整體改善率
        overall_improvement = round(sum(improvement_rates.values()) / len(improvement_rates), 1) if improvement_rates else 0
        
        response_data = {
            'focus_type': focus_type,
            'focus_name': config['name'],
            'skill_trends': skill_trends,
            'average_scores': average_scores,
            'improvement_rates': improvement_rates,
            'overall_improvement': overall_improvement,
            'total_sessions': practice_logs.count(),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error getting focus skill analysis for {student_name}: {str(e)}")
        raise APIException(
            message="無法獲取技能分析數據",
            status_code=500,
            error_code='SKILL_ANALYSIS_ERROR'
        )


@api_exception_handler  
@require_http_methods(["GET"])
def get_skill_comparison_chart(request):
    """獲取不同練習重點的技能比較數據"""
    student_name = RequestHelper.get_student_name(request)
    days = RequestHelper.get_days_filter(request)
    
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 獲取所有練習記錄
        practice_logs = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        if not practice_logs.exists():
            return JsonResponse({
                'skill_comparison': {},
                'focus_distribution': {},
                'overall_progress': {}
            })
        
        # 按練習重點分組統計
        focus_stats = {}
        skill_aggregation = {}
        
        for log in practice_logs:
            focus = log.focus
            if focus not in focus_stats:
                focus_stats[focus] = {
                    'sessions': 0,
                    'total_minutes': 0,
                    'skill_scores': {}
                }
            
            focus_stats[focus]['sessions'] += 1
            focus_stats[focus]['total_minutes'] += log.minutes
            
            # 收集技能評分
            if focus in PracticeLog.FOCUS_RATING_CONFIG:
                config = PracticeLog.FOCUS_RATING_CONFIG[focus]
                for field_name, display_name, description in config['ratings']:
                    value = getattr(log, field_name, None)
                    if value is not None:
                        if field_name not in focus_stats[focus]['skill_scores']:
                            focus_stats[focus]['skill_scores'][field_name] = []
                        focus_stats[focus]['skill_scores'][field_name].append(value)
                        
                        # 全局技能統計
                        if field_name not in skill_aggregation:
                            skill_aggregation[field_name] = []
                        skill_aggregation[field_name].append(value)
        
        # 計算平均分數
        for focus, stats in focus_stats.items():
            for skill, scores in stats['skill_scores'].items():
                stats['skill_scores'][skill] = round(sum(scores) / len(scores), 1)
        
        # 生成技能比較數據
        skill_comparison = {}
        for skill, all_scores in skill_aggregation.items():
            skill_comparison[skill] = {
                'overall_avg': round(sum(all_scores) / len(all_scores), 1),
                'focus_breakdown': {}
            }
            
            for focus, stats in focus_stats.items():
                if skill in stats['skill_scores']:
                    skill_comparison[skill]['focus_breakdown'][focus] = stats['skill_scores'][skill]
        
        # 練習重點分布
        focus_distribution = {}
        total_sessions = sum(stats['sessions'] for stats in focus_stats.values())
        
        for focus, stats in focus_stats.items():
            focus_name = dict(PracticeLog.FOCUS_CHOICES).get(focus, focus)
            focus_distribution[focus] = {
                'name': focus_name,
                'sessions': stats['sessions'],
                'percentage': round((stats['sessions'] / total_sessions) * 100, 1),
                'total_minutes': stats['total_minutes']
            }
        
        response_data = {
            'skill_comparison': skill_comparison,
            'focus_distribution': focus_distribution,
            'overall_progress': {
                'total_sessions': total_sessions,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                }
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error getting skill comparison for {student_name}: {str(e)}")
        raise APIException(
            message="無法獲取技能比較數據",
            status_code=500,
            error_code='SKILL_COMPARISON_ERROR'
        )

# ============ 影片管理系統 ============

@page_exception_handler
def video_upload_view(request):
    """影片上傳頁面"""
    from .models.recordings import PracticeRecording
    
    if request.method == 'POST':
        try:
            # 處理影片上傳
            student_name = request.POST.get('student_name')
            piece = request.POST.get('piece')
            recording_date = request.POST.get('recording_date')
            privacy_setting = request.POST.get('privacy_setting')
            notes = request.POST.get('notes', '')
            self_rating = request.POST.get('self_rating')
            recording_file = request.FILES.get('recording_file')
            
            if not all([student_name, piece, recording_date, privacy_setting, self_rating, recording_file]):
                raise APIException("請填寫所有必要欄位並上傳影片檔案")
            
            # 檢查檔案類型
            allowed_extensions = ['mp4', 'avi', 'mov', 'webm']
            file_extension = recording_file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise APIException("不支持的檔案格式，請上傳 MP4、AVI、MOV 或 WEBM 格式的影片")
            
            from datetime import datetime
            
            # 創建錄音記錄
            recording = PracticeRecording.objects.create(
                student_name=student_name,
                piece=piece,
                recording_type='video',
                file_path=recording_file,
                recording_date=datetime.strptime(recording_date, '%Y-%m-%d').date(),
                privacy_level=privacy_setting,
                notes=notes,
                self_rating=int(self_rating),
                file_size=recording_file.size,
                status='processing'
            )
            
            # 處理教師通知 (如果是teacher_only或public)
            if privacy_setting in ['teacher_only', 'public']:
                # 獲取當前用戶（應該已經是認證過的）
                if request.user.is_authenticated:
                    _create_teacher_notifications(request.user, recording)
                else:
                    # 如果是未認證用戶，嘗試通過student_name查找用戶
                    try:
                        from django.contrib.auth.models import User
                        student_user = User.objects.get(
                            Q(profile__display_name=student_name) | Q(username=student_name)
                        )
                        _create_teacher_notifications(student_user, recording)
                    except User.DoesNotExist:
                        logger.warning(f"Cannot find user for student name: {student_name}")
            
            # 如果是 AJAX 請求，返回 JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '影片上傳成功！',
                    'recording_id': recording.id
                })
            
            return redirect('practice_logs:video_library')
            
        except APIException as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': e.message})
            raise e
        except Exception as e:
            logger.error(f"Video upload error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': '上傳失敗，請稍後再試'})
            raise APIException("上傳失敗，請稍後再試")
    
    # 獲取學生練習的曲目列表
    student_name = request.GET.get('student_name', '')
    pieces = []
    
    if student_name:
        pieces = list(PracticeLog.objects
                     .filter(student_name=student_name)
                     .values_list('piece', flat=True)
                     .distinct()
                     .order_by('piece'))
    
    context = {
        'title': '上傳練習影片',
        'student_name': student_name,
        'pieces': pieces,
        'focus_choices': FOCUS_CHOICES,
    }
    
    return render(request, 'practice_logs/video_upload.html', context)


@page_exception_handler
def video_library_view(request):
    """影片庫頁面"""
    from .models.recordings import PracticeRecording
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # 獲取過濾參數
    student_name = request.GET.get('student_name', '')
    piece = request.GET.get('piece', '')
    week = request.GET.get('week', '')
    privacy_filter = request.GET.get('privacy', '')
    
    # 基礎查詢 - 考慮隱私設定
    try:
        # 首先獲取基本錄影記錄
        recordings = PracticeRecording.objects.filter(
            recording_type='video',
            status='ready'
        )
        
        # 根據用戶身分過濾
        if request.user.is_authenticated:
            try:
                # 檢查用戶是否有 profile
                user_profile = getattr(request.user, 'profile', None)
                
                if user_profile:
                    user_name = user_profile.display_name
                    is_teacher = user_profile.is_teacher
                else:
                    user_name = request.user.username
                    is_teacher = False
                
                if is_teacher:
                    # 教師可以看到公開、僅教師可見的影片，以及學生的私人影片
                    try:
                        from .models.user_profile import StudentTeacherRelation
                        student_relations = StudentTeacherRelation.objects.filter(
                            teacher=request.user,
                            is_active=True
                        ).select_related('student')
                        
                        student_names = []
                        for relation in student_relations:
                            if hasattr(relation.student, 'profile') and relation.student.profile:
                                student_names.append(relation.student.profile.display_name)
                            else:
                                student_names.append(relation.student.username)
                        
                        # 教師可以看到的影片
                        recordings = recordings.filter(
                            Q(privacy_level='public') |
                            Q(privacy_level='teacher_only') |
                            Q(student_name__in=student_names)
                        )
                    except Exception as teacher_e:
                        logger.error(f"Error getting teacher student relationships: {str(teacher_e)}")
                        # 如果師生關係查詢失敗，教師只能看到公開和教師可見的影片
                        recordings = recordings.filter(
                            Q(privacy_level='public') |
                            Q(privacy_level='teacher_only')
                        )
                else:
                    # 一般用戶只能看到公開的影片和自己的影片
                    recordings = recordings.filter(
                        Q(privacy_level='public') |
                        Q(student_name=user_name)
                    )
            except Exception as auth_e:
                logger.error(f"Error processing authenticated user: {str(auth_e)}")
                # 如果處理認證用戶失敗，只顯示公開影片
                recordings = recordings.filter(privacy_level='public')
        else:
            # 未登入用戶只能看到公開的影片
            recordings = recordings.filter(privacy_level='public')
        
        # 按上傳日期排序
        recordings = recordings.order_by('-upload_date')
        
    except Exception as e:
        logger.error(f"Error in video library base query: {str(e)}")
        # 如果基本查詢出錯，回退到最安全的查詢
        recordings = PracticeRecording.objects.filter(
            recording_type='video',
            status='ready',
            privacy_level='public'
        ).order_by('-upload_date')
    
    # 應用過濾器
    try:
        if student_name:
            recordings = recordings.filter(student_name__icontains=student_name)
        
        if piece:
            recordings = recordings.filter(piece__icontains=piece)
        
        if week:
            try:
                week_int = int(week)
                recordings = recordings.filter(week_number=week_int)
            except (ValueError, TypeError):
                pass  # 忽略無效的週數
        
        if privacy_filter:
            if privacy_filter == 'public':
                recordings = recordings.filter(privacy_level='public')
            elif privacy_filter == 'teacher':
                recordings = recordings.filter(privacy_level='teacher_only')
            elif privacy_filter == 'private':
                recordings = recordings.filter(privacy_level='private')
    except Exception as filter_e:
        logger.error(f"Error applying filters: {str(filter_e)}")
        # 如果過濾失敗，記錄錯誤但繼續處理
    
    # 分頁
    try:
        paginator = Paginator(recordings, 12)  # 每頁12個影片
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # 獲取統計數據
        total_videos = recordings.count()
        total_students = recordings.values('student_name').distinct().count()
        total_pieces = recordings.values('piece').distinct().count()
        
        # 獲取所有學生和曲目用於篩選
        all_students = list(recordings.values_list('student_name', flat=True).distinct().order_by('student_name'))
        all_pieces = list(recordings.values_list('piece', flat=True).distinct().order_by('piece'))
        
        # 獲取週數列表（處理可能的 None 值）
        week_numbers = recordings.values_list('week_number', flat=True).distinct()
        all_weeks = [w for w in week_numbers if w is not None]
        all_weeks.sort()
        
    except Exception as stats_e:
        logger.error(f"Error getting statistics: {str(stats_e)}")
        # 如果統計出錯，使用默認值
        page_obj = Paginator([], 12).get_page(1)
        total_videos = 0
        total_students = 0
        total_pieces = 0
        all_students = []
        all_pieces = []
        all_weeks = []
    
    context = {
        'title': '影片庫',
        'page_obj': page_obj,
        'total_videos': total_videos,
        'total_students': total_students,
        'total_pieces': total_pieces,
        'all_students': all_students,
        'all_pieces': all_pieces,
        'all_weeks': all_weeks,
        'current_filters': {
            'student_name': student_name,
            'piece': piece,
            'week': week,
            'privacy': privacy_filter,
        }
    }
    
    return render(request, 'practice_logs/video_library.html', context)


@page_exception_handler
def video_player_view(request, recording_id):
    """影片播放頁面"""
    from .models.recordings import PracticeRecording, RecordingComment
    from django.shortcuts import get_object_or_404
    
    recording = get_object_or_404(PracticeRecording, id=recording_id, recording_type='video')
    
    # 增加觀看次數
    recording.increment_view_count()
    
    # 獲取評論（置頂的優先顯示）
    comments = RecordingComment.objects.filter(
        recording=recording
    ).order_by('-is_pinned', '-timestamp')
    
    # 獲取相關影片（同學生的其他影片）
    related_videos = PracticeRecording.objects.filter(
        student_name=recording.student_name,
        recording_type='video',
        status='ready'
    ).exclude(id=recording_id).order_by('-upload_date')[:6]
    
    context = {
        'title': f'觀看影片 - {recording.piece}',
        'recording': recording,
        'comments': comments,
        'related_videos': related_videos,
        'can_comment': True,  # 根據實際權限邏輯調整
    }
    
    return render(request, 'practice_logs/video_player.html', context)


@api_exception_handler
@require_http_methods(["POST"])
def add_video_comment(request, recording_id):
    """添加影片評論"""
    from .models.recordings import PracticeRecording, RecordingComment
    from django.shortcuts import get_object_or_404
    
    recording = get_object_or_404(PracticeRecording, id=recording_id)
    
    try:
        comment_text = request.POST.get('comment', '').strip()
        rating = request.POST.get('rating')
        commenter_name = request.POST.get('commenter_name', '').strip()
        commenter_type = request.POST.get('commenter_type', 'self')
        timestamp_seconds = request.POST.get('timestamp')  # 影片時間戳
        
        if not comment_text or not commenter_name:
            raise APIException("評論內容和姓名不能為空")
        
        # 創建評論
        comment_data = {
            'recording': recording,
            'commenter_name': commenter_name,
            'commenter_type': commenter_type,
            'comment': comment_text,
        }
        
        if rating:
            comment_data['rating'] = int(rating)
        
        comment = RecordingComment.objects.create(**comment_data)
        
        # 如果有時間戳，可以記錄到評論內容中
        if timestamp_seconds:
            timestamp_text = f"[{int(float(timestamp_seconds))//60:02d}:{int(float(timestamp_seconds))%60:02d}] "
            comment.comment = timestamp_text + comment.comment
            comment.save()
        
        return JsonResponse({
            'success': True,
            'message': '評論已添加',
            'comment': {
                'id': comment.id,
                'commenter_display_name': comment.commenter_display_name,
                'comment': comment.comment,
                'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M'),
                'rating': comment.rating,
                'is_recent': comment.is_recent,
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding video comment: {str(e)}")
        raise APIException("添加評論失敗，請稍後再試")


@api_exception_handler
def video_progress_api(request):
    """影片進步追蹤API"""
    from .models.recordings import RecordingProgress, PracticeRecording
    
    student_name = request.GET.get('student_name')
    piece = request.GET.get('piece')
    
    if not student_name:
        raise APIException("請提供學生姓名")
    
    # 獲取進步追蹤數據
    progress_data = []
    
    if piece:
        # 特定曲目的進步
        try:
            progress = RecordingProgress.objects.get(
                student_name=student_name,
                piece=piece
            )
            progress.calculate_improvement()  # 重新計算
            
            progress_data.append({
                'piece': progress.piece,
                'improvement_score': progress.improvement_score,
                'improvement_percentage': progress.improvement_percentage,
                'total_recordings': progress.total_recordings,
                'weeks_span': progress.weeks_span,
                'first_recording': {
                    'id': progress.first_recording.id,
                    'week_number': progress.first_recording.week_number,
                    'average_rating': progress.first_recording.average_rating,
                },
                'latest_recording': {
                    'id': progress.latest_recording.id,
                    'week_number': progress.latest_recording.week_number,
                    'average_rating': progress.latest_recording.average_rating,
                }
            })
        except RecordingProgress.DoesNotExist:
            pass
    else:
        # 所有曲目的進步
        all_progress = RecordingProgress.objects.filter(
            student_name=student_name
        ).order_by('-improvement_score')
        
        for progress in all_progress:
            progress.calculate_improvement()  # 重新計算
            progress_data.append({
                'piece': progress.piece,
                'improvement_score': progress.improvement_score,
                'improvement_percentage': progress.improvement_percentage,
                'total_recordings': progress.total_recordings,
                'weeks_span': progress.weeks_span,
            })
    
    return JsonResponse({
        'progress_data': progress_data,
        'student_name': student_name,
        'piece': piece
    })


# ============ 師生關係管理系統 ============

@page_exception_handler
def teacher_selection_view(request):
    """學生選擇教師頁面"""
    if not request.user.is_authenticated:
        return redirect('practice_logs:login')
    
    try:
        # 確認用戶有profile
        if not (hasattr(request.user, 'profile') and request.user.profile):
            from django.contrib import messages
            messages.error(request, '請先完善個人資料')
            return redirect('practice_logs:profile')
        
        from .models.user_profile import StudentTeacherRelation, UserProfile
        from django.contrib.auth.models import User
        
        # 獲取當前用戶的教師關係
        current_teachers = StudentTeacherRelation.objects.filter(
            student=request.user,
            is_active=True
        ).select_related('teacher', 'teacher__profile')
        
        # 獲取所有可選擇的教師（排除已選擇的）
        current_teacher_ids = [rel.teacher.id for rel in current_teachers]
        
        # 安全地獲取教師列表
        try:
            available_teachers = User.objects.filter(
                profile__role='teacher',
                is_active=True
            ).exclude(
                id__in=current_teacher_ids
            ).select_related('profile')
        except Exception as e:
            logger.error(f"Error getting available teachers: {str(e)}")
            available_teachers = User.objects.none()
        
        # 為每個教師添加學生數統計
        for teacher in available_teachers:
            try:
                teacher.students_count = StudentTeacherRelation.objects.filter(
                    teacher=teacher,
                    is_active=True
                ).count()
            except Exception as e:
                logger.error(f"Error getting student count for teacher {teacher.id}: {str(e)}")
                teacher.students_count = 0
        
        context = {
            'title': '選擇我的教師',
            'current_teachers': current_teachers,
            'available_teachers': available_teachers,
        }
        
        return render(request, 'practice_logs/teacher_selection.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in teacher_selection_view: {str(e)}")
        return render(request, 'practice_logs/error.html', {
            'error_title': '頁面載入錯誤',
            'error_message': '教師選擇頁面載入時發生錯誤，請稍後再試。',
            'back_url': '/',
            'back_text': '返回首頁'
        })


@api_exception_handler
@require_http_methods(["POST"])
def select_teacher_api(request):
    """學生選擇教師API"""
    if not request.user.is_authenticated:
        raise APIException("請先登入", status_code=401)
    
    try:
        import json
        data = json.loads(request.body)
        teacher_id = data.get('teacher_id')
        
        if not teacher_id:
            raise APIException("請提供教師ID")
        
        from django.contrib.auth.models import User
        from .models.user_profile import StudentTeacherRelation
        
        # 檢查教師是否存在且是教師身份
        try:
            teacher = User.objects.get(
                id=teacher_id,
                profile__role='teacher',
                is_active=True
            )
        except User.DoesNotExist:
            raise APIException("指定的教師不存在或無效")
        
        # 檢查是否已經存在關係
        existing_relation = StudentTeacherRelation.objects.filter(
            student=request.user,
            teacher=teacher,
            is_active=True
        ).first()
        
        if existing_relation:
            raise APIException("您已經選擇了這位教師")
        
        # 創建師生關係
        relation = StudentTeacherRelation.objects.create(
            student=request.user,
            teacher=teacher,
            is_active=True
        )
        
        # 創建通知給教師
        try:
            from .models.recordings import TeacherNotification
            TeacherNotification.objects.create(
                teacher=teacher,
                student=request.user,
                notification_type='system',
                title=f'新學生加入',
                message=f'學生 {request.user.profile.display_name or request.user.username} 選擇了您作為指導教師。'
            )
        except Exception as e:
            logger.warning(f"Failed to create teacher notification: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'成功選擇 {teacher.profile.display_name or teacher.username} 為您的教師'
        })
        
    except json.JSONDecodeError:
        raise APIException("請求數據格式錯誤")
    except Exception as e:
        logger.error(f"Error selecting teacher: {str(e)}")
        raise APIException("選擇教師失敗，請稍後再試")


@api_exception_handler
@require_http_methods(["POST"])
def remove_teacher_api(request, relation_id):
    """移除教師關係API"""
    if not request.user.is_authenticated:
        raise APIException("請先登入", status_code=401)
    
    try:
        from .models.user_profile import StudentTeacherRelation
        
        # 檢查關係是否存在且屬於當前用戶
        try:
            relation = StudentTeacherRelation.objects.get(
                id=relation_id,
                student=request.user,
                is_active=True
            )
        except StudentTeacherRelation.DoesNotExist:
            raise APIException("指定的師生關係不存在")
        
        # 軟刪除關係（設為不活躍）
        relation.is_active = False
        relation.save()
        
        return JsonResponse({
            'success': True,
            'message': '成功移除教師關係'
        })
        
    except Exception as e:
        logger.error(f"Error removing teacher relationship: {str(e)}")
        raise APIException("移除教師關係失敗，請稍後再試")


# ============ 教師通知系統 ============

def _create_teacher_notifications(student_user, recording):
    """為學生的指定教師創建通知"""
    try:
        from .models.user_profile import StudentTeacherRelation
        from .models.recordings import TeacherNotification
        
        # 找到該學生的所有活躍教師關係
        teacher_relations = StudentTeacherRelation.objects.filter(
            student=student_user,
            is_active=True
        ).select_related('teacher')
        
        student_name = student_user.profile.display_name if student_user.profile else student_user.username
        
        for relation in teacher_relations:
            teacher = relation.teacher
            
            # 創建通知
            TeacherNotification.objects.create(
                teacher=teacher,
                student=student_user,
                recording=recording,
                notification_type='new_video',
                title=f'學生 {student_name} 上傳了新影片',
                message=f'學生 {student_name} 上傳了新的練習影片《{recording.piece}》，請查看並提供回饋。'
            )
            
        logger.info(f"Created notifications for {teacher_relations.count()} teachers for student {student_name}")
        
    except Exception as e:
        logger.error(f"Error creating teacher notifications: {str(e)}")


@page_exception_handler 
def teacher_video_dashboard(request):
    """教師影片儀表板 - 查看學生影片和通知"""
    if not (hasattr(request.user, 'profile') and request.user.profile.is_teacher):
        raise APIException("您沒有權限訪問教師儀表板")
    
    from .models.recordings import PracticeRecording, TeacherNotification
    from .models.user_profile import StudentTeacherRelation
    from django.core.paginator import Paginator
    
    teacher = request.user
    
    # 獲取該教師的所有學生
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=teacher,
        is_active=True
    ).select_related('student')
    
    student_users = [relation.student for relation in student_relations]
    student_names = []
    
    for student_user in student_users:
        if hasattr(student_user, 'profile'):
            student_names.append(student_user.profile.display_name)
        else:
            student_names.append(student_user.username)
    
    # 獲取學生的影片（根據隱私設定）
    student_videos = PracticeRecording.objects.filter(
        student_name__in=student_names,
        recording_type='video',
        status='ready',
        privacy_level__in=['teacher_only', 'public']  # 教師可以看到的影片
    ).order_by('-upload_date')
    
    # 分頁
    paginator = Paginator(student_videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 獲取未讀通知
    unread_notifications = TeacherNotification.objects.filter(
        teacher=teacher,
        is_read=False
    ).order_by('-created_at')[:10]
    
    # 統計數據
    total_students = len(student_names)
    total_videos = student_videos.count()
    pending_feedback = student_videos.filter(teacher_feedback='').count()
    
    context = {
        'title': '教師影片儀表板',
        'page_obj': page_obj,
        'unread_notifications': unread_notifications,
        'students': student_relations,
        'stats': {
            'total_students': total_students,
            'total_videos': total_videos,
            'pending_feedback': pending_feedback,
            'unread_notifications': unread_notifications.count(),
        }
    }
    
    return render(request, 'practice_logs/teacher_video_dashboard.html', context)


@api_exception_handler
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """標記通知為已讀"""
    from .models.recordings import TeacherNotification
    from django.shortcuts import get_object_or_404
    
    notification = get_object_or_404(
        TeacherNotification,
        id=notification_id,
        teacher=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'message': '通知已標記為已讀'
    })


# ============ 教師回饋系統 ============

@page_exception_handler
def teacher_feedback_form_view(request, practice_log_id):
    """教師回饋表單頁面"""
    if not (request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_teacher):
        raise APIException("您沒有權限訪問此頁面", status_code=403)
    
    from django.shortcuts import get_object_or_404
    from .models.feedback import TeacherFeedback
    
    # 獲取練習記錄
    practice_log = get_object_or_404(PracticeLog, id=practice_log_id)
    
    # 檢查是否已有回饋
    existing_feedback = None
    try:
        existing_feedback = TeacherFeedback.objects.get(practice_log=practice_log)
    except TeacherFeedback.DoesNotExist:
        pass
    
    if request.method == 'POST':
        try:
            # 獲取教師姓名
            teacher_name = request.user.profile.display_name or request.user.username
            
            # 準備回饋數據
            feedback_data = {
                'practice_log': practice_log,
                'teacher_name': teacher_name,
                'feedback_type': request.POST.get('feedback_type'),
                'feedback_text': request.POST.get('feedback_text'),
                'technique_rating': int(request.POST.get('technique_rating', 3)),
                'musicality_rating': int(request.POST.get('musicality_rating', 3)),
                'progress_rating': int(request.POST.get('progress_rating', 3)),
                'mastery_level': request.POST.get('mastery_level', 'developing'),
                'need_retry': 'need_retry' in request.POST,
                'mastered_well': 'mastered_well' in request.POST,
                'suggested_focus': request.POST.get('suggested_focus', ''),
                'practice_tips': request.POST.get('practice_tips', ''),
                'suggested_pieces': request.POST.get('suggested_pieces', ''),
                'notify_parents': 'notify_parents' in request.POST,
                'is_public': 'is_public' in request.POST,
                'is_featured': 'is_featured' in request.POST,
            }
            
            # 處理語音回饋檔案
            voice_file = request.FILES.get('voice_feedback')
            if voice_file:
                feedback_data['voice_feedback'] = voice_file
            
            # 驗證必填欄位
            if not feedback_data['feedback_type'] or not feedback_data['feedback_text']:
                raise APIException("請填寫回饋類型和詳細內容")
            
            if len(feedback_data['feedback_text']) < 10:
                raise APIException("回饋內容至少需要10個字符")
            
            # 創建或更新回饋
            if existing_feedback:
                # 更新現有回饋
                for key, value in feedback_data.items():
                    if key != 'practice_log':  # 不更新關聯欄位
                        setattr(existing_feedback, key, value)
                existing_feedback.save()
                feedback = existing_feedback
                action = "更新"
            else:
                # 創建新回饋
                feedback = TeacherFeedback.objects.create(**feedback_data)
                action = "創建"
            
            # 創建學生通知
            try:
                from .models.recordings import TeacherNotification
                from django.contrib.auth.models import User
                
                # 通過練習記錄的學生姓名找到用戶
                student_user = User.objects.filter(
                    Q(profile__display_name=practice_log.student_name) |
                    Q(username=practice_log.student_name)
                ).first()
                
                if student_user:
                    TeacherNotification.objects.create(
                        teacher=request.user,
                        student=student_user,
                        notification_type='feedback',
                        title=f'收到教師回饋',
                        message=f'教師 {teacher_name} 為您的練習《{practice_log.piece}》提供了詳細回饋。'
                    )
            except Exception as e:
                logger.warning(f"Failed to create student notification: {str(e)}")
            
            from django.contrib import messages
            messages.success(request, f'回饋已成功{action}！')
            return redirect('practice_logs:teacher_video_dashboard')
            
        except ValueError as e:
            raise APIException(f"數據格式錯誤: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating/updating teacher feedback: {str(e)}")
            raise APIException(f"{action}回饋失敗，請稍後再試")
    
    # 獲取選項數據
    context = {
        'title': f'教師回饋 - {practice_log.piece}',
        'practice_log': practice_log,
        'existing_feedback': existing_feedback,
        'feedback_type_choices': TeacherFeedback.FEEDBACK_TYPE_CHOICES,
        'mastery_level_choices': TeacherFeedback.MASTERY_LEVEL_CHOICES,
    }
    
    return render(request, 'practice_logs/teacher_feedback_form.html', context)


@page_exception_handler  
def feedback_detail_view(request, feedback_id):
    """查看回饋詳情頁面"""
    from django.shortcuts import get_object_or_404
    from .models.feedback import TeacherFeedback
    
    feedback = get_object_or_404(TeacherFeedback, id=feedback_id)
    
    # 權限檢查：只有相關的學生、教師或管理員可以查看
    can_view = False
    if request.user.is_authenticated:
        if request.user.is_superuser:
            can_view = True
        elif hasattr(request.user, 'profile'):
            user_name = request.user.profile.display_name or request.user.username
            # 檢查是否是學生本人
            if user_name == feedback.practice_log.student_name:
                can_view = True
                # 標記學生已讀
                if not feedback.student_read:
                    feedback.student_read = True
                    feedback.save(update_fields=['student_read'])
            # 檢查是否是回饋的教師
            elif user_name == feedback.teacher_name:
                can_view = True
    
    if not can_view:
        raise APIException("您沒有權限查看此回饋", status_code=403)
    
    context = {
        'title': f'回饋詳情 - {feedback.practice_log.piece}',
        'feedback': feedback,
        'practice_log': feedback.practice_log,
    }
    
    return render(request, 'practice_logs/feedback_detail.html', context)


@api_exception_handler
@require_http_methods(["POST"])
def student_feedback_response(request, feedback_id):
    """學生回覆教師回饋API"""
    if not request.user.is_authenticated:
        raise APIException("請先登入", status_code=401)
    
    from django.shortcuts import get_object_or_404
    from .models.feedback import TeacherFeedback
    
    feedback = get_object_or_404(TeacherFeedback, id=feedback_id)
    
    # 權限檢查：只有相關學生可以回覆
    if hasattr(request.user, 'profile'):
        user_name = request.user.profile.display_name or request.user.username
        if user_name != feedback.practice_log.student_name:
            raise APIException("您只能回覆自己的回饋", status_code=403)
    else:
        raise APIException("請先完善個人資料", status_code=403)
    
    try:
        import json
        data = json.loads(request.body)
        response_text = data.get('response', '').strip()
        
        if not response_text:
            raise APIException("請輸入回覆內容")
        
        if len(response_text) > 300:
            raise APIException("回覆內容不能超過300字符")
        
        # 更新學生回覆
        feedback.student_response = response_text
        feedback.student_read = True
        feedback.save(update_fields=['student_response', 'student_read'])
        
        return JsonResponse({
            'success': True,
            'message': '回覆已提交',
            'response': response_text
        })
        
    except json.JSONDecodeError:
        raise APIException("請求數據格式錯誤")
    except Exception as e:
        logger.error(f"Error submitting student response: {str(e)}")
        raise APIException("提交回覆失敗，請稍後再試")


@page_exception_handler
def feedback_history_view(request):
    """回饋歷史記錄頁面"""
    if not request.user.is_authenticated:
        return redirect('practice_logs:login')
    
    from .models.feedback import TeacherFeedback
    from django.core.paginator import Paginator
    
    user_name = None
    if hasattr(request.user, 'profile'):
        user_name = request.user.profile.display_name or request.user.username
    
    if not user_name:
        raise APIException("請先完善個人資料")
    
    # 根據用戶角色獲取回饋
    if request.user.profile.is_teacher:
        # 教師查看自己提供的回饋
        feedbacks = TeacherFeedback.objects.filter(
            teacher_name=user_name
        ).select_related('practice_log').order_by('-created_at')
        view_type = 'teacher'
    else:
        # 學生查看收到的回饋
        feedbacks = TeacherFeedback.objects.filter(
            practice_log__student_name=user_name
        ).select_related('practice_log').order_by('-created_at')
        view_type = 'student'
    
    # 分頁
    paginator = Paginator(feedbacks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 統計數據
    total_feedbacks = feedbacks.count()
    if view_type == 'student':
        unread_count = feedbacks.filter(student_read=False).count()
        positive_count = feedbacks.filter(mastered_well=True).count()
        need_retry_count = feedbacks.filter(need_retry=True).count()
        stats = {
            'total_feedbacks': total_feedbacks,
            'unread_count': unread_count,
            'positive_count': positive_count,
            'need_retry_count': need_retry_count,
        }
    else:
        recent_count = feedbacks.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()
        stats = {
            'total_feedbacks': total_feedbacks,
            'recent_count': recent_count,
        }
    
    context = {
        'title': '回饋歷史記錄',
        'page_obj': page_obj,
        'view_type': view_type,
        'stats': stats,
    }
    
    return render(request, 'practice_logs/feedback_history.html', context)


# 匯入教師系統視圖
from .teacher_hub import (
    teacher_hub_dashboard, get_student_progress_api,
    get_pending_items_api, quick_stats_api
)
from .student_management import (
    student_management_page, student_detail_view,
    update_student_group, batch_send_message,
    update_student_progress
)
from .qa_center import (
    qa_center_dashboard, question_list_view, answer_question_view,
    student_ask_question_view, student_questions_view,
    faq_management_view, toggle_faq_publish, mark_question_closed,
    rate_answer, public_faq_view, track_faq_view
)