"""
問答中心視圖
處理學生提問和教師回答功能
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, F, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
import json
import logging

from django.contrib.auth.models import User
from .models import (
    StudentQuestion, TeacherAnswer, QuestionCategory, FAQ,
    StudentTeacherRelation, UserProfile
)
from .decorators import teacher_required

logger = logging.getLogger(__name__)


@login_required
@teacher_required
def qa_center_dashboard(request):
    """問答中心主頁面"""
    teacher = request.user
    
    # 獲取師生關係
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=teacher,
        is_active=True
    ).select_related('student__profile')
    
    students = [relation.student for relation in student_relations]
    
    # 獲取待回答問題
    pending_questions = StudentQuestion.objects.filter(
        Q(teacher=teacher) | Q(teacher__isnull=True, student__in=students),
        status='pending'
    ).select_related('student__profile', 'category').order_by('-created_at')
    
    # 獲取最近已回答問題
    recent_answered = StudentQuestion.objects.filter(
        teacher=teacher,
        status='answered'
    ).select_related('student__profile', 'category').prefetch_related(
        Prefetch('answers', queryset=TeacherAnswer.objects.select_related('teacher__profile'))
    ).order_by('-updated_at')[:5]
    
    # 獲取問題分類統計
    category_stats = StudentQuestion.objects.filter(
        Q(teacher=teacher) | Q(student__in=students)
    ).values('category__name', 'category__icon', 'category__color').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 獲取常見問題
    faqs = FAQ.objects.filter(
        is_published=True
    ).order_by('display_order', '-view_count')[:10]
    
    # 統計數據
    stats = {
        'total_questions': StudentQuestion.objects.filter(
            Q(teacher=teacher) | Q(student__in=students)
        ).count(),
        'pending_count': pending_questions.count(),
        'answered_count': StudentQuestion.objects.filter(
            teacher=teacher,
            status='answered'
        ).count(),
        'this_week': StudentQuestion.objects.filter(
            Q(teacher=teacher) | Q(student__in=students),
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
    }
    
    context = {
        'pending_questions': pending_questions[:10],  # 顯示前10個
        'recent_answered': recent_answered,
        'category_stats': category_stats,
        'faqs': faqs,
        'stats': stats,
        'has_more_pending': pending_questions.count() > 10,
    }
    
    return render(request, 'practice_logs/teacher/qa_center.html', context)


@login_required
@teacher_required
def question_list_view(request):
    """問題列表頁面"""
    teacher = request.user
    
    # 獲取篩選參數
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('q', '')
    
    # 獲取師生關係
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=teacher,
        is_active=True
    ).select_related('student')
    students = [relation.student for relation in student_relations]
    
    # 基礎查詢
    questions = StudentQuestion.objects.filter(
        Q(teacher=teacher) | Q(teacher__isnull=True, student__in=students)
    ).select_related('student__profile', 'category').prefetch_related(
        Prefetch('answers', queryset=TeacherAnswer.objects.select_related('teacher__profile'))
    )
    
    # 應用篩選
    if status_filter != 'all':
        questions = questions.filter(status=status_filter)
    
    if priority_filter != 'all':
        questions = questions.filter(priority=priority_filter)
    
    if category_filter != 'all':
        try:
            category_id = int(category_filter)
            questions = questions.filter(category_id=category_id)
        except (ValueError, TypeError):
            pass
    
    if search_query:
        questions = questions.filter(
            Q(title__icontains=search_query) |
            Q(question_text__icontains=search_query) |
            Q(student__profile__display_name__icontains=search_query) |
            Q(student__username__icontains=search_query)
        )
    
    # 排序
    sort_by = request.GET.get('sort', '-created_at')
    questions = questions.order_by(sort_by)
    
    # 分頁
    paginator = Paginator(questions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 獲取所有分類
    categories = QuestionCategory.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'category': category_filter,
            'q': search_query,
            'sort': sort_by,
        },
        'status_choices': StudentQuestion.STATUS_CHOICES,
        'priority_choices': StudentQuestion.PRIORITY_LEVELS,
    }
    
    return render(request, 'practice_logs/teacher/question_list.html', context)


@login_required
@teacher_required
def answer_question_view(request, question_id):
    """回答問題頁面"""
    teacher = request.user
    question = get_object_or_404(StudentQuestion, id=question_id)
    
    # 檢查權限
    student_relations = StudentTeacherRelation.objects.filter(
        teacher=teacher,
        student=question.student,
        is_active=True
    ).exists()
    
    if not (question.teacher == teacher or (question.teacher is None and student_relations)):
        messages.error(request, '您沒有權限回答此問題')
        return redirect('practice_logs:teacher_qa')
    
    if request.method == 'POST':
        answer_text = request.POST.get('answer_text', '').strip()
        is_public = request.POST.get('is_public') == 'on'
        add_to_faq = request.POST.get('add_to_faq') == 'on'
        
        if not answer_text:
            messages.error(request, '請輸入回答內容')
        else:
            # 創建回答
            answer = TeacherAnswer.objects.create(
                question=question,
                teacher=teacher,
                answer_text=answer_text,
                is_public=is_public
            )
            
            # 更新問題狀態
            question.status = 'answered'
            question.teacher = teacher
            question.save()
            
            # 如果標記為FAQ
            if add_to_faq:
                FAQ.objects.create(
                    question=question.title,
                    answer=answer_text,
                    category=question.category,
                    created_by=teacher,
                    is_published=False  # 需要審核
                )
            
            messages.success(request, '回答已提交')
            
            # 發送通知給學生
            try:
                from .models.recordings import TeacherNotification
                TeacherNotification.objects.create(
                    teacher=teacher,
                    student=question.student,
                    notification_type='qa_answer',
                    title='您的問題已獲得回答',
                    message=f'教師 {teacher.profile.display_name} 回答了您的問題：{question.title}'
                )
            except Exception as e:
                logger.warning(f"Failed to create notification: {str(e)}")
            
            return redirect('practice_logs:teacher_qa')
    
    # 獲取相關問題
    related_questions = StudentQuestion.objects.filter(
        category=question.category
    ).exclude(id=question_id).order_by('-view_count')[:5]
    
    # 增加查看次數
    question.view_count = F('view_count') + 1
    question.save(update_fields=['view_count'])
    
    context = {
        'question': question,
        'related_questions': related_questions,
        'existing_answers': question.answers.all(),
    }
    
    return render(request, 'practice_logs/teacher/answer_question.html', context)


@login_required
def student_ask_question_view(request):
    """學生提問頁面"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, '請先完善個人資料')
        return redirect('practice_logs:profile')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        question_text = request.POST.get('question_text', '').strip()
        category_id = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')
        teacher_id = request.POST.get('teacher')
        
        if not all([title, question_text, category_id]):
            messages.error(request, '請填寫所有必填欄位')
        else:
            try:
                category = QuestionCategory.objects.get(id=category_id)
                teacher = None
                
                if teacher_id:
                    teacher = User.objects.get(id=teacher_id)
                    # 檢查師生關係
                    if not StudentTeacherRelation.objects.filter(
                        student=request.user,
                        teacher=teacher,
                        is_active=True
                    ).exists():
                        messages.error(request, '無效的教師選擇')
                        return render(request, 'practice_logs/student/ask_question.html', get_question_context(request))
                
                question = StudentQuestion.objects.create(
                    student=request.user,
                    teacher=teacher,
                    category=category,
                    title=title,
                    question_text=question_text,
                    priority=priority
                )
                
                messages.success(request, '問題已提交，教師將盡快回覆')
                return redirect('practice_logs:student_questions')
                
            except (QuestionCategory.DoesNotExist, User.DoesNotExist):
                messages.error(request, '提交失敗，請重試')
    
    context = get_question_context(request)
    return render(request, 'practice_logs/student/ask_question.html', context)


def get_question_context(request):
    """獲取提問頁面的上下文"""
    # 獲取學生的教師列表
    my_teachers = []
    if request.user.is_authenticated:
        relations = StudentTeacherRelation.objects.filter(
            student=request.user,
            is_active=True
        ).select_related('teacher__profile')
        my_teachers = [rel.teacher for rel in relations]
    
    # 獲取問題分類
    categories = QuestionCategory.objects.filter(is_active=True)
    
    return {
        'categories': categories,
        'my_teachers': my_teachers,
        'priority_choices': StudentQuestion.PRIORITY_LEVELS,
    }


@login_required
def student_questions_view(request):
    """學生查看自己的問題"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, '請先完善個人資料')
        return redirect('practice_logs:profile')
    
    # 獲取學生的所有問題
    questions = StudentQuestion.objects.filter(
        student=request.user
    ).select_related('category', 'teacher__profile').prefetch_related(
        Prefetch('answers', queryset=TeacherAnswer.objects.select_related('teacher__profile'))
    ).order_by('-created_at')
    
    # 分頁
    paginator = Paginator(questions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 統計
    stats = {
        'total': questions.count(),
        'pending': questions.filter(status='pending').count(),
        'answered': questions.filter(status='answered').count(),
        'closed': questions.filter(status='closed').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
    }
    
    return render(request, 'practice_logs/student/my_questions.html', context)


@login_required
@teacher_required
def faq_management_view(request):
    """FAQ管理頁面"""
    teacher = request.user
    
    # 獲取FAQ列表
    faqs = FAQ.objects.all().select_related('category', 'created_by__profile')
    
    # 如果不是管理員，只顯示自己創建的
    if not teacher.is_superuser:
        faqs = faqs.filter(created_by=teacher)
    
    faqs = faqs.order_by('-created_at')
    
    # 分頁
    paginator = Paginator(faqs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'can_publish': teacher.is_superuser,
    }
    
    return render(request, 'practice_logs/teacher/faq_management.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def toggle_faq_publish(request, faq_id):
    """切換FAQ發布狀態"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '權限不足'})
    
    faq = get_object_or_404(FAQ, id=faq_id)
    faq.is_published = not faq.is_published
    faq.save()
    
    return JsonResponse({
        'success': True,
        'is_published': faq.is_published,
        'message': f'FAQ已{"發布" if faq.is_published else "取消發布"}'
    })


@login_required
@teacher_required
@require_http_methods(["POST"])
def mark_question_closed(request, question_id):
    """標記問題為已關閉"""
    question = get_object_or_404(StudentQuestion, id=question_id)
    
    # 檢查權限
    if question.teacher != request.user:
        return JsonResponse({'success': False, 'error': '權限不足'})
    
    question.status = 'closed'
    question.save()
    
    return JsonResponse({
        'success': True,
        'message': '問題已關閉'
    })


@login_required
@require_http_methods(["POST"])
def rate_answer(request, answer_id):
    """評價回答"""
    answer = get_object_or_404(TeacherAnswer, id=answer_id)
    
    # 檢查權限（只有提問的學生可以評價）
    if answer.question.student != request.user:
        return JsonResponse({'success': False, 'error': '權限不足'})
    
    try:
        data = json.loads(request.body)
        helpful = data.get('helpful', False)
        
        if helpful:
            answer.helpful_count = F('helpful_count') + 1
        else:
            answer.unhelpful_count = F('unhelpful_count') + 1
        
        answer.save()
        
        return JsonResponse({
            'success': True,
            'message': '感謝您的評價'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def public_faq_view(request):
    """公開FAQ頁面（無需登入）"""
    categories = QuestionCategory.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch('faqs', 
                queryset=FAQ.objects.filter(is_published=True).order_by('display_order'))
    )
    
    # 搜尋功能
    search_query = request.GET.get('q', '')
    if search_query:
        faqs = FAQ.objects.filter(
            Q(question__icontains=search_query) | Q(answer__icontains=search_query),
            is_published=True
        ).select_related('category')
    else:
        faqs = None
    
    context = {
        'categories': categories,
        'search_query': search_query,
        'search_results': faqs,
    }
    
    return render(request, 'practice_logs/public/faq.html', context)


@require_http_methods(["POST"])
def track_faq_view(request, faq_id):
    """追蹤FAQ查看次數"""
    faq = get_object_or_404(FAQ, id=faq_id)
    faq.view_count = F('view_count') + 1
    faq.save()
    
    return JsonResponse({'success': True})


@login_required
@teacher_required
def create_faq_view(request):
    """創建新的FAQ"""
    if request.method == 'POST':
        category_id = request.POST.get('category')
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        is_featured = request.POST.get('is_featured') == 'on'
        
        faq = FAQ.objects.create(
            category_id=category_id,
            question=question,
            answer=answer,
            is_featured=is_featured,
            is_published=False,  # 預設不發布，需要審核
            created_by=request.user
        )
        
        messages.success(request, 'FAQ已創建，待審核後將公開顯示')
        return redirect('practice_logs:faq_management')
    
    categories = QuestionCategory.objects.filter(is_active=True)
    return render(request, 'practice_logs/teacher/create_faq.html', {
        'categories': categories
    })


@login_required
@teacher_required
def edit_faq_view(request, faq_id):
    """編輯FAQ"""
    faq = get_object_or_404(FAQ, id=faq_id)
    
    # 檢查權限 - 只有創建者或管理員可以編輯
    if faq.created_by != request.user and not request.user.is_superuser:
        messages.error(request, '您沒有權限編輯此FAQ')
        return redirect('practice_logs:faq_management')
    
    if request.method == 'POST':
        faq.category_id = request.POST.get('category')
        faq.question = request.POST.get('question')
        faq.answer = request.POST.get('answer')
        faq.is_featured = request.POST.get('is_featured') == 'on'
        faq.save()
        
        messages.success(request, 'FAQ已更新')
        return redirect('practice_logs:faq_management')
    
    categories = QuestionCategory.objects.filter(is_active=True)
    return render(request, 'practice_logs/teacher/edit_faq.html', {
        'faq': faq,
        'categories': categories
    })


@login_required
@teacher_required
@require_http_methods(["POST"])
def delete_faq_view(request, faq_id):
    """刪除FAQ"""
    faq = get_object_or_404(FAQ, id=faq_id)
    
    # 檢查權限
    if faq.created_by != request.user and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': '您沒有權限刪除此FAQ'
        })
    
    faq.delete()
    messages.success(request, 'FAQ已刪除')
    
    return redirect('practice_logs:faq_management')


# 學生問答相關函數（簡化版本）
def student_ask_question(request):
    """學生提問頁面的簡化版本"""
    return student_ask_question_view(request)


def student_questions(request):
    """學生問題列表的簡化版本"""
    return student_questions_view(request)


def public_faq(request):
    """公開FAQ頁面的簡化版本"""
    return public_faq_view(request)


@require_http_methods(["POST"])
def save_question_draft(request):
    """保存問題草稿（AJAX）"""
    try:
        data = json.loads(request.body)
        draft_data = {
            'title': data.get('title', ''),
            'question_text': data.get('question_text', ''),
            'category': data.get('category', ''),
            'priority': data.get('priority', 'medium'),
        }
        
        # 將草稿存儲在session中
        request.session['question_draft'] = draft_data
        
        return JsonResponse({
            'success': True,
            'message': '草稿已保存'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })