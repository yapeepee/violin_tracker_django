"""
教師中心儀表板視圖
專注於學生管理，移除教師自己的練習記錄
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, F, Sum, Max
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
import json

from .models import (
    StudentTeacherRelation, StudentQuestion, TeacherResource,
    LessonSchedule, StudentProgress, PracticeLog, TeacherFeedback
)
from .decorators import teacher_required


@login_required
@teacher_required
def teacher_hub_dashboard(request):
    """教師中心儀表板 - 無教師練習記錄"""
    user = request.user
    today = timezone.now().date()
    
    # 獲取教師的所有學生
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=user,
        is_active=True
    ).select_related('student__profile')
    
    students = [relation.student for relation in student_relations]
    student_names = [s.profile.display_name if hasattr(s, 'profile') else s.username for s in students]
    
    # 待處理事項統計
    pending_questions = StudentQuestion.objects.filter(
        Q(teacher=user) | Q(teacher__isnull=True),
        student__in=students,
        status='pending'
    ).count()
    
    # 需要回饋的練習記錄
    teacher_name = user.profile.display_name if hasattr(user, 'profile') else user.username
    pending_feedback = PracticeLog.objects.filter(
        student_name__in=student_names
    ).exclude(
        id__in=TeacherFeedback.objects.filter(
            teacher_name=teacher_name
        ).values_list('practice_log_id', flat=True)
    ).count()
    
    # 今日課程
    today_lessons = LessonSchedule.objects.filter(
        teacher=user,
        lesson_date=today,
        status='scheduled'
    ).select_related('student__profile').order_by('start_time')
    
    # 本週課程統計
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_lessons = LessonSchedule.objects.filter(
        teacher=user,
        lesson_date__range=[week_start, week_end]
    ).exclude(status='cancelled')
    
    # 學生練習活躍度（過去7天）
    week_ago = today - timedelta(days=7)
    active_students = PracticeLog.objects.filter(
        student_name__in=student_names,
        date__gte=week_ago
    ).values('student_name').distinct().count()
    
    # 學生進度概覽
    student_progress_data = []
    for student in students[:6]:  # 只顯示前6個學生
        progress = StudentProgress.objects.filter(
            student=student,
            teacher=user
        ).first()
        
        # 獲取最近練習
        student_name = student.profile.display_name if hasattr(student, 'profile') else student.username
        recent_practice = PracticeLog.objects.filter(
            student_name=student_name
        ).order_by('-date').first()
        
        # 獲取未回答問題數
        unanswered_questions = StudentQuestion.objects.filter(
            student=student,
            status='pending'
        ).count()
        
        student_progress_data.append({
            'student': student,
            'progress': progress,
            'recent_practice': recent_practice,
            'unanswered_questions': unanswered_questions,
            'practice_days': PracticeLog.objects.filter(
                student_name=student_name,
                date__gte=week_ago
            ).values('date').distinct().count()
        })
    
    # 最新學生提問
    recent_questions = StudentQuestion.objects.filter(
        Q(teacher=user) | Q(teacher__isnull=True),
        student__in=students
    ).select_related('student__profile').order_by('-created_at')[:5]
    
    # 即將到來的課程（下7天）
    upcoming_lessons = LessonSchedule.objects.filter(
        teacher=user,
        lesson_date__gt=today,
        lesson_date__lte=today + timedelta(days=7),
        status='scheduled'
    ).select_related('student__profile').order_by('lesson_date', 'start_time')[:5]
    
    # 學生練習趨勢數據（用於圖表）
    practice_trend_data = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = PracticeLog.objects.filter(
            student_name__in=student_names,
            date=date
        ).count()
        practice_trend_data.append({
            'date': date.strftime('%m/%d'),
            'count': count
        })
    practice_trend_data.reverse()
    
    context = {
        'students': students,
        'student_count': len(students),
        'pending_questions': pending_questions,
        'pending_feedback': pending_feedback,
        'today_lessons': today_lessons,
        'week_lesson_count': week_lessons.count(),
        'active_students': active_students,
        'student_progress_data': student_progress_data,
        'recent_questions': recent_questions,
        'upcoming_lessons': upcoming_lessons,
        'practice_trend_data': json.dumps(practice_trend_data),
        'today': today,
    }
    
    return render(request, 'practice_logs/teacher/hub_dashboard.html', context)


@login_required
@teacher_required
@require_http_methods(["GET"])
def get_student_progress_api(request):
    """API：獲取學生進度數據"""
    user = request.user
    student_id = request.GET.get('student_id')
    
    if student_id:
        # 獲取特定學生的進度
        student = get_object_or_404(User, id=student_id)
        progress = StudentProgress.objects.filter(
            student=student,
            teacher=user
        ).first()
        
        if progress:
            data = {
                'success': True,
                'student_name': student.profile.display_name if hasattr(student, 'profile') else student.username,
                'overall_score': progress.overall_score,
                'skills': progress.get_skill_radar_data(),
                'practice_consistency': progress.practice_consistency,
                'current_level': progress.current_level,
                'last_assessment': progress.last_assessment_date.strftime('%Y-%m-%d')
            }
        else:
            data = {'success': False, 'message': '尚未建立進度記錄'}
    else:
        # 獲取所有學生的進度概覽
        student_relations = StudentTeacherRelation.objects.filter(
            teacher=user,
            is_active=True
        ).select_related('student__profile')
        
        progress_data = []
        for relation in student_relations:
            student = relation.student
            progress = StudentProgress.objects.filter(
                student=student,
                teacher=user
            ).first()
            
            if progress:
                progress_data.append({
                    'student_id': student.id,
                    'student_name': student.profile.display_name if hasattr(student, 'profile') else student.username,
                    'overall_score': progress.overall_score,
                    'progress_percentage': progress.progress_percentage
                })
        
        data = {
            'success': True,
            'students': progress_data
        }
    
    return JsonResponse(data)


@login_required
@teacher_required
@require_http_methods(["GET"])
def get_pending_items_api(request):
    """API：獲取待處理事項"""
    user = request.user
    
    # 獲取教師的學生
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=user,
        is_active=True
    )
    students = [relation.student for relation in student_relations]
    student_names = [s.profile.display_name if hasattr(s, 'profile') else s.username for s in students]
    
    # 待回答問題
    pending_questions = StudentQuestion.objects.filter(
        Q(teacher=user) | (Q(teacher__isnull=True) & Q(student__in=students)),
        status='pending'
    ).select_related('student__profile', 'category').order_by('-created_at')[:10]
    
    # 需要回饋的練習
    teacher_name = user.profile.display_name if hasattr(user, 'profile') else user.username
    pending_practices = PracticeLog.objects.filter(
        student_name__in=student_names
    ).exclude(
        id__in=TeacherFeedback.objects.filter(
            teacher_name=teacher_name
        ).values_list('practice_log_id', flat=True)
    ).order_by('-date')[:10]
    
    # 格式化數據
    questions_data = [{
        'id': q.id,
        'student_name': q.student.profile.display_name if hasattr(q.student, 'profile') else q.student.username,
        'title': q.title,
        'priority': q.get_priority_display(),
        'category': q.category.name if q.category else '未分類',
        'created_at': q.created_at.strftime('%Y-%m-%d %H:%M'),
        'days_ago': q.days_since_asked
    } for q in pending_questions]
    
    practices_data = [{
        'id': p.id,
        'student_name': p.student_name,
        'date': p.date.strftime('%Y-%m-%d'),
        'minutes': p.minutes,
        'rating': p.rating,
        'focus': p.focus or '一般練習'
    } for p in pending_practices]
    
    data = {
        'success': True,
        'pending_questions': questions_data,
        'pending_practices': practices_data,
        'total_pending': len(questions_data) + len(practices_data)
    }
    
    return JsonResponse(data)


@login_required
@teacher_required
def quick_stats_api(request):
    """API：獲取快速統計數據"""
    user = request.user
    today = timezone.now().date()
    
    # 獲取統計數據
    stats = {
        'total_students': StudentTeacherRelation.objects.filter(
            teacher=user,
            is_active=True
        ).count(),
        
        'today_lessons': LessonSchedule.objects.filter(
            teacher=user,
            lesson_date=today,
            status='scheduled'
        ).count(),
        
        'week_practice_sessions': PracticeLog.objects.filter(
            student_name__in=StudentTeacherRelation.objects.filter(
                teacher=user,
                is_active=True
            ).values_list('student__profile__chinese_name', flat=True),
            date__gte=today - timedelta(days=7)
        ).count(),
        
        'resources_shared': TeacherResource.objects.filter(
            teacher=user
        ).count()
    }
    
    return JsonResponse(stats)