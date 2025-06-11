"""
自定義裝飾器
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def teacher_required(view_func):
    """需要教師權限的裝飾器"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "請先登入")
            return redirect('practice_logs:login')
        
        if not hasattr(request.user, 'profile') or not request.user.profile.is_teacher:
            messages.error(request, "您沒有權限訪問此頁面")
            return redirect('practice_logs:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def student_required(view_func):
    """需要學生權限的裝飾器"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "請先登入")
            return redirect('practice_logs:login')
        
        if not hasattr(request.user, 'profile') or not request.user.profile.is_student:
            messages.error(request, "您沒有權限訪問此頁面")
            return redirect('practice_logs:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view