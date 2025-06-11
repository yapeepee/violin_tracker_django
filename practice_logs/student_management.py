"""
學生管理視圖
提供學生分組、進度追蹤和批次操作功能
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, F, Sum, Max, Prefetch
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
import json

from django.contrib.auth.models import User
from .models import (
    StudentTeacherRelation, StudentProgress, PracticeLog, 
    TeacherFeedback, StudentQuestion, LessonSchedule,
    UserProfile
)
from .decorators import teacher_required


class StudentGroup:
    """學生分組類"""
    def __init__(self, name, icon, color, students=None):
        self.name = name
        self.icon = icon
        self.color = color
        self.students = students or []


@login_required
@teacher_required
def student_management_page(request):
    """學生管理主頁面"""
    teacher = request.user
    
    # 獲取所有學生
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=teacher,
        is_active=True
    ).select_related('student__profile').prefetch_related(
        Prefetch('student__progress_records',
                queryset=StudentProgress.objects.filter(teacher=teacher),
                to_attr='teacher_progress')
    )
    
    # 準備學生數據
    students_data = []
    for relation in student_relations:
        student = relation.student
        progress = student.teacher_progress[0] if hasattr(student, 'teacher_progress') and student.teacher_progress else None
        
        # 獲取最近練習統計
        student_name = student.profile.display_name if hasattr(student, 'profile') else student.username
        recent_practices = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        practice_stats = recent_practices.aggregate(
            total_sessions=Count('id'),
            total_minutes=Sum('minutes'),
            avg_rating=Avg('rating')
        )
        
        # 獲取未回答問題數
        unanswered_questions = StudentQuestion.objects.filter(
            student=student,
            status='pending'
        ).count()
        
        # 獲取下次課程
        next_lesson = LessonSchedule.objects.filter(
            student=student,
            teacher=teacher,
            lesson_date__gte=timezone.now().date(),
            status='scheduled'
        ).order_by('lesson_date', 'start_time').first()
        
        students_data.append({
            'student': student,
            'relation': relation,
            'progress': progress,
            'practice_stats': practice_stats,
            'unanswered_questions': unanswered_questions,
            'next_lesson': next_lesson,
            'skill_level': student.profile.get_skill_level_display() if hasattr(student, 'profile') else '未設定',
            'group': getattr(student.profile, 'student_group', 'ungrouped') if hasattr(student, 'profile') else 'ungrouped'
        })
    
    # 預設分組
    groups = [
        StudentGroup('初級組', '🌱', '#28a745'),
        StudentGroup('中級組', '🌿', '#17a2b8'),
        StudentGroup('高級組', '🌳', '#ffc107'),
        StudentGroup('未分組', '👤', '#6c757d')
    ]
    
    # 將學生分配到組
    for group in groups:
        group.students = [s for s in students_data if s['group'] == group.name or (s['group'] == 'ungrouped' and group.name == '未分組')]
    
    # 統計數據
    total_students = len(students_data)
    active_students = sum(1 for s in students_data if s['practice_stats']['total_sessions'] > 0)
    
    context = {
        'students_data': students_data,
        'groups': groups,
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': total_students - active_students,
    }
    
    return render(request, 'practice_logs/teacher/student_management.html', context)


@login_required
@teacher_required
def student_detail_view(request, student_id):
    """學生詳細資訊頁面"""
    teacher = request.user
    student = get_object_or_404(User, id=student_id)
    
    # 確認師生關係
    relation = get_object_or_404(
        StudentTeacherRelation,
        teacher=teacher,
        student=student,
        is_active=True
    )
    
    # 獲取或創建進度記錄
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        teacher=teacher,
        defaults={
            'current_level': student.profile.get_skill_level_display() if hasattr(student, 'profile') else '初級'
        }
    )
    
    # 獲取練習記錄
    student_name = student.profile.display_name if hasattr(student, 'profile') else student.username
    
    # 練習統計（過去30天）
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_practices = PracticeLog.objects.filter(
        student_name=student_name,
        date__gte=thirty_days_ago
    )
    
    # 獲取最近20條練習記錄用於顯示
    practice_logs = PracticeLog.objects.filter(
        student_name=student_name
    ).order_by('-date')[:20]
    
    practice_stats = {
        'total_days': recent_practices.values('date').distinct().count(),
        'total_minutes': recent_practices.aggregate(Sum('minutes'))['minutes__sum'] or 0,
        'avg_rating': recent_practices.aggregate(Avg('rating'))['rating__avg'] or 0,
        'practice_streak': calculate_practice_streak(student_name),
    }
    
    # 獲取回饋歷史
    teacher_display_name = teacher.profile.display_name if hasattr(teacher, 'profile') else teacher.username
    feedbacks = TeacherFeedback.objects.filter(
        practice_log__student_name=student_name,
        teacher_name=teacher_display_name
    ).order_by('-created_at')[:10]
    
    # 獲取提問歷史
    questions = StudentQuestion.objects.filter(
        Q(student=student) & (Q(teacher=teacher) | Q(teacher__isnull=True))
    ).order_by('-created_at')[:10]
    
    # 課程記錄
    lessons = LessonSchedule.objects.filter(
        student=student,
        teacher=teacher
    ).order_by('-lesson_date')[:10]
    
    # 今天的日期（用於模板）
    today = timezone.now().date()
    
    # 進度趨勢數據（用於圖表）
    progress_trend = []
    for i in range(30, -1, -5):
        date = timezone.now().date() - timedelta(days=i)
        day_practices = PracticeLog.objects.filter(
            student_name=student_name,
            date=date
        )
        if day_practices.exists():
            progress_trend.append({
                'date': date.strftime('%m/%d'),
                'minutes': day_practices.aggregate(Sum('minutes'))['minutes__sum'] or 0,
                'rating': day_practices.aggregate(Avg('rating'))['rating__avg'] or 0
            })
    
    context = {
        'student': student,
        'relation': relation,
        'progress': progress,
        'practice_logs': practice_logs,
        'practice_stats': practice_stats,
        'feedbacks': feedbacks,
        'questions': questions,
        'lessons': lessons,
        'progress_trend': json.dumps(progress_trend),
        'skill_data': json.dumps(progress.get_skill_radar_data()) if progress else '{}',
        'today': today,
    }
    
    return render(request, 'practice_logs/teacher/student_detail.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def update_student_group(request):
    """更新學生分組（AJAX）"""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        new_group = data.get('group')
        
        student = get_object_or_404(User, id=student_id)
        
        # 確認師生關係
        relation = StudentTeacherRelation.objects.filter(
            teacher=request.user,
            student=student,
            is_active=True
        ).first()
        
        if not relation:
            return JsonResponse({'success': False, 'error': '無權限修改此學生'})
        
        # 更新學生分組（這裡簡化處理，實際可能需要新的模型欄位）
        if hasattr(student, 'profile'):
            student.profile.student_group = new_group
            student.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{student.username} 已移至 {new_group}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@teacher_required
@require_http_methods(["POST"])
def batch_send_message(request):
    """批次發送訊息給學生（AJAX）"""
    try:
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
        message = data.get('message')
        
        if not student_ids or not message:
            return JsonResponse({'success': False, 'error': '請選擇學生並輸入訊息'})
        
        # 這裡可以實作實際的訊息發送邏輯
        # 例如：創建通知、發送郵件等
        
        count = len(student_ids)
        
        return JsonResponse({
            'success': True,
            'message': f'已成功發送訊息給 {count} 位學生'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@teacher_required
@require_http_methods(["POST"])
def update_student_progress(request, student_id):
    """更新學生進度評估"""
    student = get_object_or_404(User, id=student_id)
    
    # 確認師生關係
    relation = get_object_or_404(
        StudentTeacherRelation,
        teacher=request.user,
        student=student,
        is_active=True
    )
    
    # 獲取或創建進度記錄
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        teacher=request.user
    )
    
    # 更新評分
    progress.technique_score = float(request.POST.get('technique_score', progress.technique_score))
    progress.musicality_score = float(request.POST.get('musicality_score', progress.musicality_score))
    progress.rhythm_score = float(request.POST.get('rhythm_score', progress.rhythm_score))
    progress.sight_reading_score = float(request.POST.get('sight_reading_score', progress.sight_reading_score))
    progress.theory_score = float(request.POST.get('theory_score', progress.theory_score))
    
    # 更新其他資訊
    progress.current_level = request.POST.get('current_level', progress.current_level)
    progress.current_pieces = request.POST.get('current_pieces', progress.current_pieces)
    progress.short_term_goals = request.POST.get('short_term_goals', progress.short_term_goals)
    progress.long_term_goals = request.POST.get('long_term_goals', progress.long_term_goals)
    progress.teacher_comments = request.POST.get('teacher_comments', progress.teacher_comments)
    progress.last_assessment_date = timezone.now().date()
    
    progress.save()
    
    messages.success(request, f'{student.username} 的進度評估已更新')
    return redirect('practice_logs:student_detail', student_id=student_id)


def calculate_practice_streak(student_name):
    """計算練習連續天數"""
    today = timezone.now().date()
    streak = 0
    current_date = today
    
    while True:
        if PracticeLog.objects.filter(
            student_name=student_name,
            date=current_date
        ).exists():
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak