"""
課程管理系統視圖
提供課程排程、出席記錄、課程筆記等功能
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, F, Prefetch
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
import json

from .models import (
    LessonSchedule, StudentProgress, LessonNote
)
from .models.user_profile import StudentTeacherRelation
from .decorators import teacher_required
from django.contrib.auth.models import User


@login_required
@teacher_required
def lesson_calendar_view(request):
    """課程日曆主頁面"""
    teacher = request.user
    
    # 獲取查詢參數
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # 獲取當月的第一天和最後一天
    first_day = selected_date.replace(day=1)
    if first_day.month == 12:
        last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)
    
    # 獲取當月的所有課程
    month_lessons = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date__gte=first_day,
        lesson_date__lte=last_day
    ).select_related('student__profile').order_by('lesson_date', 'start_time')
    
    # 將課程按日期分組（轉換為可序列化的格式）
    lessons_by_date = {}
    for lesson in month_lessons:
        date_str = lesson.lesson_date.strftime('%Y-%m-%d')
        if date_str not in lessons_by_date:
            lessons_by_date[date_str] = []
        lessons_by_date[date_str].append({
            'id': lesson.id,
            'start_time': lesson.start_time.strftime('%H:%M') if lesson.start_time else '',
            'end_time': lesson.end_time.strftime('%H:%M') if lesson.end_time else '',
            'student__username': lesson.student.username,
            'student__profile__display_name': getattr(lesson.student.profile, 'display_name', None) if hasattr(lesson.student, 'profile') else None,
            'status': lesson.status,
            'topic': lesson.topic,
        })
    
    # 獲取今天的課程
    today_lessons = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date=timezone.now().date()
    ).select_related('student__profile').order_by('start_time')
    
    # 獲取本週的課程統計
    week_start = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    week_end = week_start + timedelta(days=6)
    
    week_stats = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date__gte=week_start,
        lesson_date__lte=week_end
    ).aggregate(
        total_lessons=Count('id'),
        completed_lessons=Count('id', filter=Q(status='completed')),
        cancelled_lessons=Count('id', filter=Q(status='cancelled'))
    )
    
    # 獲取待完成的課程
    pending_lessons = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date__lt=timezone.now().date(),
        status='scheduled'
    ).select_related('student__profile').order_by('-lesson_date', '-start_time')[:10]
    
    # 獲取教師的所有學生
    students = User.objects.filter(
        teacher_relations__teacher=teacher,
        teacher_relations__is_active=True
    ).distinct()
    
    context = {
        'selected_date': selected_date,
        'first_day': first_day,
        'last_day': last_day,
        'lessons_by_date': json.dumps(lessons_by_date),
        'today_lessons': today_lessons,
        'week_stats': week_stats,
        'pending_lessons': pending_lessons,
        'month_lessons': month_lessons,
        'students': students,  # Add students for the modal form
    }
    
    return render(request, 'practice_logs/teacher/lesson_calendar.html', context)


@login_required
@teacher_required
def create_lesson_view(request):
    """創建新課程"""
    if request.method == 'POST':
        try:
            # 獲取表單數據
            student_id = request.POST.get('student')
            lesson_date = request.POST.get('lesson_date')
            start_time = request.POST.get('start_time')
            duration = request.POST.get('duration_minutes', 60)
            lesson_type = request.POST.get('lesson_type', 'regular')
            topic = request.POST.get('topic', '')
            objectives = request.POST.get('objectives', '')
            materials = request.POST.get('materials_needed', '')
            
            # 驗證學生
            student = get_object_or_404(User, id=student_id)
            relation = StudentTeacherRelation.objects.filter(
                teacher=request.user,
                student=student,
                is_active=True
            ).first()
            
            if not relation:
                messages.error(request, '您沒有權限為此學生排課')
                return redirect('practice_logs:lesson_calendar')
            
            # 創建課程
            lesson = LessonSchedule.objects.create(
                teacher=request.user,
                student=student,
                lesson_date=lesson_date,
                start_time=start_time,
                duration_minutes=int(duration),
                lesson_type=lesson_type,
                topic=topic,
                objectives=objectives,
                materials_needed=materials,
                status='scheduled'
            )
            
            messages.success(request, f'已成功為 {student.profile.display_name} 安排課程')
            
            # 如果是AJAX請求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'lesson_id': lesson.id,
                    'message': '課程已創建'
                })
            
            return redirect('practice_logs:lesson_calendar')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            
            messages.error(request, f'創建課程時發生錯誤: {str(e)}')
            return redirect('practice_logs:lesson_calendar')
    
    # GET請求 - 顯示創建表單
    # 獲取教師的所有學生
    students = User.objects.filter(
        teacher_relations__teacher=request.user,
        teacher_relations__is_active=True
    ).distinct()
    
    context = {
        'students': students,
        'lesson_types': LessonSchedule.LESSON_TYPES,
        'default_date': request.GET.get('date', timezone.now().date()),
        'default_time': request.GET.get('time', '14:00'),
    }
    
    return render(request, 'practice_logs/teacher/create_lesson.html', context)


@login_required
@teacher_required
def lesson_detail_view(request, lesson_id):
    """課程詳情頁面"""
    lesson = get_object_or_404(LessonSchedule, id=lesson_id, teacher=request.user)
    
    # 獲取或創建課程筆記
    try:
        lesson_note = lesson.detailed_note
    except LessonNote.DoesNotExist:
        lesson_note = None
    
    # 獲取學生的進度記錄
    progress = StudentProgress.objects.filter(
        student=lesson.student,
        teacher=request.user
    ).first()
    
    # 獲取該學生的歷史課程
    history_lessons = LessonSchedule.objects.filter(
        teacher=request.user,
        student=lesson.student
    ).exclude(id=lesson_id).order_by('-lesson_date')[:10]
    
    context = {
        'lesson': lesson,
        'lesson_note': lesson_note,
        'progress': progress,
        'history_lessons': history_lessons,
    }
    
    return render(request, 'practice_logs/teacher/lesson_detail.html', context)


@login_required
@teacher_required
def update_lesson_status(request, lesson_id):
    """更新課程狀態（AJAX）"""
    if request.method == 'POST':
        try:
            lesson = get_object_or_404(LessonSchedule, id=lesson_id, teacher=request.user)
            
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status not in dict(LessonSchedule.STATUS_CHOICES):
                return JsonResponse({'success': False, 'error': '無效的狀態'})
            
            lesson.status = new_status
            
            # 如果標記為完成，更新相關欄位
            if new_status == 'completed':
                lesson.student_performance = data.get('performance_rating')
                lesson.lesson_notes = data.get('notes', '')
                lesson.homework = data.get('homework', '')
                lesson.pieces_covered = data.get('pieces', '')
                lesson.skills_focus = data.get('skills', '')
            
            # 如果是取消或改期，記錄原因
            if new_status in ['cancelled', 'rescheduled']:
                lesson.reschedule_reason = data.get('reason', '')
                if new_status == 'rescheduled' and lesson.lesson_date:
                    lesson.original_date = lesson.lesson_date
            
            lesson.save()
            
            return JsonResponse({
                'success': True,
                'message': f'課程狀態已更新為: {lesson.get_status_display()}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': '只接受POST請求'})


@login_required
@teacher_required
def reschedule_lesson(request, lesson_id):
    """改期課程"""
    lesson = get_object_or_404(LessonSchedule, id=lesson_id, teacher=request.user)
    
    if request.method == 'POST':
        try:
            # 保存原始日期
            lesson.original_date = lesson.lesson_date
            
            # 更新新的日期和時間
            lesson.lesson_date = request.POST.get('new_date')
            lesson.start_time = request.POST.get('new_time')
            lesson.reschedule_reason = request.POST.get('reason', '')
            lesson.status = 'rescheduled'
            
            lesson.save()
            
            messages.success(request, '課程已成功改期')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '課程已改期'})
            
            return redirect('practice_logs:lesson_detail', lesson_id=lesson.id)
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            
            messages.error(request, f'改期失敗: {str(e)}')
            return redirect('practice_logs:lesson_detail', lesson_id=lesson.id)
    
    context = {
        'lesson': lesson,
        'min_date': timezone.now().date(),
    }
    
    return render(request, 'practice_logs/teacher/reschedule_lesson.html', context)


@login_required
@teacher_required
def create_lesson_note(request, lesson_id):
    """創建或更新課程筆記"""
    lesson = get_object_or_404(LessonSchedule, id=lesson_id, teacher=request.user)
    
    if request.method == 'POST':
        try:
            # 獲取或創建課程筆記
            lesson_note, created = LessonNote.objects.get_or_create(lesson=lesson)
            
            # 更新筆記內容
            lesson_note.pre_lesson_plan = request.POST.get('pre_lesson_plan', '')
            lesson_note.warm_up_exercises = request.POST.get('warm_up_exercises', '')
            lesson_note.technique_work = request.POST.get('technique_work', '')
            lesson_note.repertoire_covered = request.POST.get('repertoire_covered', '')
            lesson_note.problems_identified = request.POST.get('problems_identified', '')
            lesson_note.solutions_provided = request.POST.get('solutions_provided', '')
            lesson_note.improvements_noted = request.POST.get('improvements_noted', '')
            lesson_note.areas_need_work = request.POST.get('areas_need_work', '')
            lesson_note.next_lesson_plan = request.POST.get('next_lesson_plan', '')
            lesson_note.parent_communication = request.POST.get('parent_communication', '')
            
            lesson_note.save()
            
            # 同時更新課程的基本筆記
            lesson.lesson_notes = request.POST.get('summary', '')
            lesson.save()
            
            messages.success(request, '課程筆記已保存')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '筆記已保存',
                    'created': created
                })
            
            return redirect('practice_logs:lesson_detail', lesson_id=lesson.id)
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            
            messages.error(request, f'保存筆記時發生錯誤: {str(e)}')
            return redirect('practice_logs:lesson_detail', lesson_id=lesson.id)
    
    # GET請求 - 顯示筆記表單
    try:
        lesson_note = lesson.detailed_note
    except LessonNote.DoesNotExist:
        lesson_note = None
    
    context = {
        'lesson': lesson,
        'lesson_note': lesson_note,
    }
    
    return render(request, 'practice_logs/teacher/lesson_note_form.html', context)


@login_required
@teacher_required
def lesson_list_view(request):
    """課程列表頁面"""
    teacher = request.user
    
    # 篩選參數
    student_id = request.GET.get('student')
    status = request.GET.get('status')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    lesson_type = request.GET.get('type')
    
    # 基礎查詢
    lessons = LessonSchedule.objects.filter(teacher=teacher).select_related('student__profile')
    
    # 應用篩選
    if student_id:
        lessons = lessons.filter(student_id=student_id)
    
    if status:
        lessons = lessons.filter(status=status)
    
    if date_from:
        lessons = lessons.filter(lesson_date__gte=date_from)
    
    if date_to:
        lessons = lessons.filter(lesson_date__lte=date_to)
    
    if lesson_type:
        lessons = lessons.filter(lesson_type=lesson_type)
    
    # 排序
    sort_by = request.GET.get('sort', '-lesson_date')
    lessons = lessons.order_by(sort_by, '-start_time')
    
    # 分頁
    paginator = Paginator(lessons, 20)
    page = request.GET.get('page', 1)
    lessons_page = paginator.get_page(page)
    
    # 獲取學生列表（用於篩選）
    students = User.objects.filter(
        teacher_relations__teacher=teacher,
        teacher_relations__is_active=True
    ).distinct()
    
    # 統計數據
    stats = {
        'total_lessons': lessons.count(),
        'completed_lessons': lessons.filter(status='completed').count(),
        'scheduled_lessons': lessons.filter(status='scheduled', lesson_date__gte=timezone.now().date()).count(),
        'cancelled_lessons': lessons.filter(status='cancelled').count(),
    }
    
    context = {
        'lessons': lessons_page,
        'students': students,
        'stats': stats,
        'status_choices': LessonSchedule.STATUS_CHOICES,
        'type_choices': LessonSchedule.LESSON_TYPES,
        'selected_student': student_id,
        'selected_status': status,
        'selected_type': lesson_type,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
    }
    
    return render(request, 'practice_logs/teacher/lesson_list.html', context)


@login_required
@teacher_required
def batch_create_lessons(request):
    """批次創建課程（例如：每週固定課程）"""
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            weekdays = request.POST.getlist('weekdays')  # 星期幾
            start_time = request.POST.get('start_time')
            duration = int(request.POST.get('duration_minutes', 60))
            lesson_type = request.POST.get('lesson_type', 'regular')
            
            # 驗證學生
            student = get_object_or_404(User, id=student_id)
            relation = StudentTeacherRelation.objects.filter(
                teacher=request.user,
                student=student,
                is_active=True
            ).first()
            
            if not relation:
                messages.error(request, '您沒有權限為此學生排課')
                return redirect('practice_logs:lesson_calendar')
            
            # 轉換日期
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 創建課程
            created_count = 0
            current_date = start_date
            
            while current_date <= end_date:
                # 檢查是否為選定的星期幾
                if str(current_date.weekday()) in weekdays:
                    # 檢查是否已存在同時間的課程
                    existing = LessonSchedule.objects.filter(
                        teacher=request.user,
                        lesson_date=current_date,
                        start_time=start_time
                    ).exists()
                    
                    if not existing:
                        LessonSchedule.objects.create(
                            teacher=request.user,
                            student=student,
                            lesson_date=current_date,
                            start_time=start_time,
                            duration_minutes=duration,
                            lesson_type=lesson_type,
                            topic=f'{student.profile.display_name} - 定期課程',
                            status='scheduled'
                        )
                        created_count += 1
                
                current_date += timedelta(days=1)
            
            messages.success(request, f'已成功創建 {created_count} 堂課程')
            return redirect('practice_logs:lesson_calendar')
            
        except Exception as e:
            messages.error(request, f'批次創建課程時發生錯誤: {str(e)}')
            return redirect('practice_logs:lesson_calendar')
    
    # GET請求 - 顯示批次創建表單
    students = User.objects.filter(
        teacher_relations__teacher=request.user,
        teacher_relations__is_active=True
    ).distinct()
    
    context = {
        'students': students,
        'lesson_types': LessonSchedule.LESSON_TYPES,
        'weekdays': [
            (0, '星期一'),
            (1, '星期二'),
            (2, '星期三'),
            (3, '星期四'),
            (4, '星期五'),
            (5, '星期六'),
            (6, '星期日'),
        ],
    }
    
    return render(request, 'practice_logs/teacher/batch_create_lessons.html', context)


@login_required
@teacher_required
def lesson_analytics(request):
    """課程分析頁面"""
    teacher = request.user
    
    # 獲取日期範圍
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    # 基礎統計
    total_stats = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date__gte=start_date
    ).aggregate(
        total_lessons=Count('id'),
        completed_lessons=Count('id', filter=Q(status='completed')),
        cancelled_lessons=Count('id', filter=Q(status='cancelled')),
        no_show_lessons=Count('id', filter=Q(status='no_show'))
    )
    
    # 按學生統計
    student_stats = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date__gte=start_date
    ).values('student__id', 'student__profile__display_name').annotate(
        total_lessons=Count('id'),
        completed_lessons=Count('id', filter=Q(status='completed')),
        attendance_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
    ).order_by('-total_lessons')
    
    # 按課程類型統計
    type_stats = LessonSchedule.objects.filter(
        teacher=teacher,
        lesson_date__gte=start_date
    ).values('lesson_type').annotate(
        count=Count('id')
    )
    
    # 每日課程趨勢
    daily_trend = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        day_lessons = LessonSchedule.objects.filter(
            teacher=teacher,
            lesson_date=date
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        )
        daily_trend.append({
            'date': date.strftime('%m/%d'),
            'total': day_lessons['total'],
            'completed': day_lessons['completed']
        })
    daily_trend.reverse()
    
    # 學生表現評分分布
    performance_dist = LessonSchedule.objects.filter(
        teacher=teacher,
        status='completed',
        student_performance__isnull=False,
        lesson_date__gte=start_date
    ).values('student_performance').annotate(
        count=Count('id')
    ).order_by('student_performance')
    
    context = {
        'total_stats': total_stats,
        'student_stats': student_stats,
        'type_stats': type_stats,
        'daily_trend': json.dumps(daily_trend),
        'performance_dist': performance_dist,
        'days': days,
        'lesson_types': LessonSchedule.LESSON_TYPES,  # Add this for the template
    }
    
    return render(request, 'practice_logs/teacher/lesson_analytics.html', context)