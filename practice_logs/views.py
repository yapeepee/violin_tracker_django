"""
小提琴練習記錄系統的視圖處理模組。
這個模組包含了所有的視圖函數，用於處理：
- 練習記錄的創建和顯示
- 數據分析和統計
- API 端點
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from .models import PracticeLog
import logging
from django.views.decorators.http import require_http_methods
from django.conf import settings
from functools import wraps

# 設置日誌記錄器
logger = logging.getLogger(__name__)

def api_view(f):
    """API視圖裝飾器，用於處理API響應和錯誤。"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            response = f(*args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"API錯誤: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return wrapper

# 常量定義
DEFAULT_DAYS = 30  # 預設顯示最近30天的數據
MAX_DAYS = 365    # 最多顯示一年的數據
RECENT_DAYS = 7   # 最近趨勢的天數

# ============ 輔助函數 ============

def handle_student_name(request, required=True):
    """
    處理請求中的學生名字參數。
    
    Args:
        request: HTTP請求對象
        required: 是否為必需參數（默認為True）
    
    Returns:
        str or JsonResponse: 如果找到學生名字則返回名字，否則返回錯誤響應
    """
    student_name = request.GET.get('student_name')
    if required and not student_name:
        return JsonResponse({'error': '未提供學生姓名'}, status=400)
    return student_name

def get_date_range(request):
    """
    從請求中獲取日期範圍。
    
    Args:
        request: HTTP請求對象
    
    Returns:
        tuple: (start_date, end_date) 日期範圍
    """
    end_date = request.GET.get('end_date')
    end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else timezone.now().date()
    
    start_date = request.GET.get('start_date')
    if start_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        # 確保日期範圍不超過最大限制
        if (end_date - start_date).days > MAX_DAYS:
            start_date = end_date - timedelta(days=MAX_DAYS)
    else:
        start_date = end_date - timedelta(days=DEFAULT_DAYS)
    
    return start_date, end_date

# ============ 頁面視圖 ============

def index(request):
    """首頁視圖，處理練習記錄的創建和顯示。"""
    if request.method == 'POST':
        try:
            # 驗證必填字段
            required_fields = ['student_name', 'piece', 'minutes', 'rating']
            for field in required_fields:
                if not request.POST.get(field):
                    raise ValueError(f'缺少必填字段：{field}')
            
            # 創建練習記錄
            PracticeLog.objects.create(
                student_name=request.POST['student_name'],
                piece=request.POST['piece'],
                minutes=int(request.POST['minutes']),
                rating=int(request.POST['rating']),
                focus=request.POST.get('focus', 'technique'),
                notes=request.POST.get('notes', ''),
                date=request.POST.get('date') or timezone.now().date()
            )
            return redirect('/?student=' + request.POST['student_name'])
        except ValueError as e:
            logger.warning(f"創建練習記錄時的輸入錯誤: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"創建練習記錄時發生錯誤: {str(e)}")
            return JsonResponse({'error': '創建練習記錄時發生錯誤'}, status=500)

    # 獲取當前學生的最近練習記錄
    student_name = request.GET.get('student')
    recent_logs = []
    if student_name:
        recent_logs = (PracticeLog.objects
                      .filter(student_name=student_name)
                      .order_by('-date')[:5])

    return render(request, 'practice_logs/index.html', {
        'current_student': student_name,
        'recent_logs': recent_logs,
        'focus_choices': PracticeLog.FOCUS_CHOICES
    })

def analytics(request, student_name):
    """分析頁面視圖，顯示練習數據的圖表和統計。"""
    # 獲取學生的基本統計數據
    stats = PracticeLog.objects.filter(student_name=student_name).aggregate(
        total_practice_time=Sum('minutes'),
        total_sessions=Count('id'),
        avg_rating=Avg('rating'),
        avg_session_length=Avg('minutes')
    )
    
    return render(request, 'practice_logs/analytics.html', {
        'student_name': student_name,
        'stats': stats
    })

# ============ API 端點 ============

@api_view
def chart_data(request):
    """獲取練習時間圖表數據的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    data = (PracticeLog.objects
           .filter(
               student_name=student_name,
               date__gte=start_date,
               date__lte=end_date
           )
           .values('piece')
           .annotate(
               total_minutes=Sum('minutes'),
               avg_rating=Avg('rating')
           )
           .order_by('-total_minutes'))

    return JsonResponse(list(data), safe=False)

@api_view
def get_weekly_practice_data(request):
    """獲取每週練習總時數的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    data = (PracticeLog.objects
            .filter(
                student_name=student_name,
                date__gte=start_date,
                date__lte=end_date
            )
            .values('date')
            .annotate(
                total_minutes=Sum('minutes'),
                avg_rating=Avg('rating')
            )
            .order_by('date'))
    
    return JsonResponse(list(data), safe=False)

@api_view
def get_piece_practice_data(request):
    """獲取各樂曲練習總時間的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    data = (PracticeLog.objects
           .filter(
               student_name=student_name,
               date__gte=start_date,
               date__lte=end_date
           )
           .values('piece')
           .annotate(
               total_minutes=Sum('minutes'),
               practice_count=Count('id'),
               avg_rating=Avg('rating'),
               avg_session_length=Avg('minutes')
           )
           .order_by('-total_minutes'))

    return JsonResponse(list(data), safe=False)

@api_view
def get_recent_trend_data(request):
    """獲取最近練習趨勢的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    data = (PracticeLog.objects
            .filter(
                student_name=student_name,
                date__gte=start_date,
                date__lte=end_date
            )
            .values('date')
            .annotate(
                total_minutes=Sum('minutes'),
                pieces_practiced=Count('piece', distinct=True),
                avg_rating=Avg('rating')
            )
            .order_by('date'))

    return JsonResponse(list(data), safe=False)

@api_view
def get_rest_day_stats(request):
    """獲取休息日統計的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    practice_dates = set(
        PracticeLog.objects
        .filter(
            student_name=student_name,
            date__gte=start_date,
            date__lte=end_date
        )
        .values_list('date', flat=True)
    )

    if not practice_dates:
        return JsonResponse({'error': '找不到練習記錄'}, status=404)

    current_date = start_date
    rest_days = []
    practice_days = []

    while current_date <= end_date:
        if current_date in practice_dates:
            practice_days.append(current_date)
        else:
            rest_days.append(current_date)
        current_date += timedelta(days=1)

    return JsonResponse({
        'total_days': (end_date - start_date).days + 1,
        'practice_days': len(practice_days),
        'rest_days': len(rest_days),
        'practice_dates': [d.strftime('%Y-%m-%d') for d in practice_days],
        'rest_dates': [d.strftime('%Y-%m-%d') for d in rest_days],
        'practice_ratio': len(practice_days) / ((end_date - start_date).days + 1)
    })

@api_view
def get_piece_switching_stats(request):
    """獲取樂曲切換頻率統計的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    data = (PracticeLog.objects
            .filter(
                student_name=student_name,
                date__gte=start_date,
                date__lte=end_date
            )
            .values('date')
            .annotate(
                pieces_count=Count('piece', distinct=True),
                total_sessions=Count('id'),
                total_minutes=Sum('minutes'),
                avg_rating=Avg('rating')
            )
            .order_by('date'))

    return JsonResponse(list(data), safe=False)

@api_view
def get_focus_stats(request):
    """獲取練習重點統計的API端點。"""
    student_name = handle_student_name(request)
    if isinstance(student_name, JsonResponse):
        return student_name

    start_date, end_date = get_date_range(request)
    
    # 獲取所有練習重點的統計數據
    focus_stats = (PracticeLog.objects
            .filter(
                student_name=student_name,
                date__gte=start_date,
                date__lte=end_date
            )
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

# Create your views here.
