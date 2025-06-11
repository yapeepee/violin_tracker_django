"""
用戶認證相關視圖
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import logging

from django.contrib.auth.models import User
from .models.user_profile import UserProfile, StudentTeacherRelation, UserLoginLog
from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    UserProfileForm,
    AvatarUploadForm,
    StudentTeacherRelationForm,
    PasswordChangeForm
)

logger = logging.getLogger(__name__)


def register_view(request):
    """用戶註冊視圖"""
    if request.user.is_authenticated:
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return JsonResponse({'success': True, 'redirect': True})
        return redirect('practice_logs:index')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # 記錄註冊日誌
                logger.info(f"New user registered: {user.username} ({user.profile.role if hasattr(user, 'profile') else 'unknown'})")
                
                # 自動登入
                login(request, user)
                
                # 記錄登入日誌
                _create_login_log(request, user, True)
                
                display_name = user.profile.display_name if hasattr(user, 'profile') else user.username
                messages.success(request, f'歡迎加入小提琴練習系統，{display_name}！')
                
                # 檢查是否為AJAX請求
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
                    return JsonResponse({'success': True, 'message': f'歡迎加入，{display_name}！'})
                
                # 根據角色重定向到不同頁面
                if hasattr(user, 'profile'):
                    if user.profile.is_student:
                        return redirect('practice_logs:student_dashboard')
                    elif user.profile.is_teacher:
                        return redirect('practice_logs:teacher_dashboard')
                    else:
                        return redirect('practice_logs:index')
                else:
                    return redirect('practice_logs:index')
                    
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': '註冊過程中發生錯誤，請稍後再試'})
                messages.error(request, '註冊過程中發生錯誤，請稍後再試')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '註冊信息有誤，請檢查並重新填寫'})
            messages.error(request, '註冊信息有誤，請檢查並重新填寫')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'practice_logs/auth/register.html', {
        'form': form,
        'title': '註冊新帳戶'
    })


def login_view(request):
    """用戶登入視圖"""
    if request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect': True})
        return redirect('practice_logs:index')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            try:
                # 登入用戶
                login(request, user)
                
                # 記錄登入IP（通過UserProfile或直接記錄在log中）
                # Django User模型沒有last_login_ip字段，我們透過登入記錄追蹤
                
                # 記錄登入日誌
                _create_login_log(request, user, True)
                
                display_name = user.profile.display_name if hasattr(user, 'profile') else user.username
                messages.success(request, f'歡迎回來，{display_name}！')
                
                # 檢查是否為AJAX請求
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f'歡迎回來，{display_name}！'})
                
                # 重定向到下一頁或默認頁面
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # 根據角色重定向
                if hasattr(user, 'profile'):
                    if user.profile.is_student:
                        return redirect('practice_logs:student_dashboard')
                    elif user.profile.is_teacher:
                        return redirect('practice_logs:teacher_dashboard')
                    else:
                        return redirect('practice_logs:index')
                else:
                    return redirect('practice_logs:index')
                    
            except Exception as e:
                logger.error(f"Login error for user {user.username}: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': '登入過程中發生錯誤'})
                messages.error(request, '登入過程中發生錯誤')
        else:
            # 記錄失敗的登入嘗試
            username = request.POST.get('username', '')
            if username:
                _create_login_log(request, None, False, username)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '用戶名或密碼錯誤'})
            messages.error(request, '用戶名或密碼錯誤')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'practice_logs/auth/login.html', {
        'form': form,
        'title': '登入'
    })


@login_required
def logout_view(request):
    """用戶登出視圖"""
    user = request.user
    
    try:
        # 更新登入記錄的登出時間
        latest_login = UserLoginLog.objects.filter(
            user=user,
            logout_time__isnull=True
        ).order_by('-login_time').first()
        
        if latest_login:
            latest_login.logout_time = timezone.now()
            latest_login.save()
        
        logger.info(f"User logged out: {user.username}")
        
    except Exception as e:
        logger.error(f"Logout error for user {user.username}: {str(e)}")
    
    logout(request)
    messages.success(request, '您已成功登出')
    return redirect('practice_logs:login')


@login_required
def profile_view(request):
    """用戶個人資料頁面"""
    user = request.user
    
    context = {
        'user': user,
        'title': '個人資料',
        'practice_stats': user.profile.get_practice_stats() if hasattr(user, 'profile') and user.profile.is_student else None,
        'teaching_stats': user.profile.get_teaching_stats() if hasattr(user, 'profile') and user.profile.is_teacher else None,
    }
    
    # 獲取師生關係
    if hasattr(user, 'profile') and user.profile.is_student:
        context['teachers'] = StudentTeacherRelation.objects.filter(
            student=user, is_active=True
        ).select_related('teacher')
    elif hasattr(user, 'profile') and user.profile.is_teacher:
        context['students'] = StudentTeacherRelation.objects.filter(
            teacher=user, is_active=True
        ).select_related('student')
    
    return render(request, 'practice_logs/auth/profile.html', context)


@login_required
def edit_profile_view(request):
    """編輯個人資料"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '個人資料已更新')
                return redirect('practice_logs:profile')
            except Exception as e:
                logger.error(f"Profile update error for user {user.username}: {str(e)}")
                messages.error(request, '更新資料時發生錯誤')
        else:
            messages.error(request, '資料格式有誤，請檢查並重新填寫')
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'practice_logs/auth/edit_profile.html', {
        'form': form,
        'title': '編輯個人資料'
    })


@login_required
@require_http_methods(["POST"])
def upload_avatar_view(request):
    """上傳頭像"""
    user = request.user
    form = AvatarUploadForm(request.POST, request.FILES, instance=user)
    
    if form.is_valid():
        try:
            form.save()
            messages.success(request, '頭像已更新')
            return JsonResponse({
                'success': True,
                'avatar_url': user.avatar.url if user.avatar else None
            })
        except Exception as e:
            logger.error(f"Avatar upload error for user {user.username}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '上傳頭像時發生錯誤'
            })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@login_required
def change_password_view(request):
    """變更密碼"""
    user = request.user
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            try:
                form.save()
                update_session_auth_hash(request, user)  # 保持登入狀態
                messages.success(request, '密碼已成功變更')
                return redirect('practice_logs:profile')
            except Exception as e:
                logger.error(f"Password change error for user {user.username}: {str(e)}")
                messages.error(request, '變更密碼時發生錯誤')
        else:
            messages.error(request, '密碼格式有誤，請檢查並重新填寫')
    else:
        form = PasswordChangeForm(user)
    
    return render(request, 'practice_logs/auth/change_password.html', {
        'form': form,
        'title': '變更密碼'
    })


@login_required
def login_history_view(request):
    """登入記錄查看"""
    user = request.user
    
    login_logs = UserLoginLog.objects.filter(user=user).order_by('-login_time')
    
    # 分頁
    paginator = Paginator(login_logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'practice_logs/auth/login_history.html', {
        'page_obj': page_obj,
        'title': '登入記錄'
    })


@login_required
def student_dashboard_view(request):
    """學生儀表板"""
    if not (hasattr(request.user, 'profile') and request.user.profile.is_student):
        messages.error(request, '您沒有權限訪問學生儀表板')
        return redirect('practice_logs:index')
    
    user = request.user
    
    # 獲取學生統計數據
    practice_stats = user.profile.get_practice_stats()
    
    # 獲取最近的練習記錄
    from .models import PracticeLog
    display_name = user.profile.display_name if hasattr(user, 'profile') else user.username
    recent_practices = PracticeLog.objects.filter(
        student_name=display_name
    ).order_by('-date')[:5]
    
    # 獲取教師
    teachers = StudentTeacherRelation.objects.filter(
        student=user, is_active=True
    ).select_related('teacher')
    
    context = {
        'user': user,
        'practice_stats': practice_stats,
        'recent_practices': recent_practices,
        'teachers': teachers,
        'title': '學生儀表板'
    }
    
    return render(request, 'practice_logs/auth/student_dashboard.html', context)


@login_required
def teacher_dashboard_view(request):
    """教師儀表板 - 重定向到新的教師中心"""
    if not (hasattr(request.user, 'profile') and request.user.profile.is_teacher):
        messages.error(request, '您沒有權限訪問教師儀表板')
        return redirect('practice_logs:index')
    
    # 重定向到新的教師中心
    return redirect('practice_logs:teacher_hub')


# ============ 輔助函數 ============

def _get_client_ip(request):
    """獲取客戶端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _create_login_log(request, user, success, attempted_username=None):
    """創建登入記錄"""
    try:
        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if success and user:
            UserLoginLog.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                login_successful=True
            )
        else:
            # 失敗的登入嘗試
            if attempted_username:
                try:
                    attempted_user = User.objects.get(username=attempted_username)
                    UserLoginLog.objects.create(
                        user=attempted_user,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        login_successful=False
                    )
                except User.DoesNotExist:
                    # 用戶不存在，不記錄
                    pass
    except Exception as e:
        logger.error(f"Error creating login log: {str(e)}")