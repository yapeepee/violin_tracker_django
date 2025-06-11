"""
資源庫系統視圖
提供教學資源上傳、分類、分享功能
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Count, Q, F
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
import json
import os
import mimetypes

from .models import (
    TeacherResource, ResourceCategory, ResourceCollection,
    ResourceUsageLog, StudentTeacherRelation
)
from .decorators import teacher_required
from django.contrib.auth.models import User


@login_required
@teacher_required
def resource_library_home(request):
    """資源庫首頁"""
    teacher = request.user
    
    # 獲取資源分類
    categories = ResourceCategory.objects.all().order_by('order')
    
    # 搜尋和篩選
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category')
    resource_type = request.GET.get('type')
    difficulty = request.GET.get('difficulty')
    
    # 基礎查詢 - 教師自己的資源和公開資源
    resources = TeacherResource.objects.filter(
        Q(teacher=teacher) | Q(is_public=True)
    ).select_related('teacher__profile', 'category')
    
    # 應用篩選
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(piece_name__icontains=search_query) |
            Q(composer__icontains=search_query)
        )
    
    if category_id:
        resources = resources.filter(category_id=category_id)
    
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    
    if difficulty:
        resources = resources.filter(difficulty_level=difficulty)
    
    # 排序
    sort_by = request.GET.get('sort', '-created_at')
    resources = resources.order_by(sort_by)
    
    # 分頁
    paginator = Paginator(resources, 12)
    page = request.GET.get('page', 1)
    resources_page = paginator.get_page(page)
    
    # 獲取教師的收藏夾
    collections = ResourceCollection.objects.filter(
        teacher=teacher
    ).annotate(
        resource_count=Count('resources')
    ).order_by('-created_at')[:5]
    
    # 統計數據
    stats = {
        'total_resources': TeacherResource.objects.filter(teacher=teacher).count(),
        'shared_resources': TeacherResource.objects.filter(teacher=teacher, is_public=True).count(),
        'total_downloads': ResourceUsageLog.objects.filter(
            resource__teacher=teacher
        ).count(),
        'collections_count': collections.count()
    }
    
    # 最近上傳
    recent_uploads = TeacherResource.objects.filter(
        teacher=teacher
    ).order_by('-created_at')[:5]
    
    # 熱門資源（根據下載次數）
    popular_resources = TeacherResource.objects.filter(
        Q(teacher=teacher) | Q(is_public=True)
    ).order_by('-download_count')[:5]
    
    context = {
        'categories': categories,
        'resources': resources_page,
        'collections': collections,
        'stats': stats,
        'recent_uploads': recent_uploads,
        'popular_resources': popular_resources,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_type': resource_type,
        'selected_difficulty': difficulty,
        'sort_by': sort_by,
    }
    
    return render(request, 'practice_logs/teacher/resource_library.html', context)


@login_required
@teacher_required
def upload_resource(request):
    """上傳新資源"""
    if request.method == 'POST':
        try:
            # 處理檔案上傳
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return JsonResponse({'success': False, 'error': '請選擇檔案'})
            
            # 檢查檔案大小
            max_size = 50 * 1024 * 1024  # 50MB
            if uploaded_file.size > max_size:
                return JsonResponse({'success': False, 'error': '檔案大小不能超過50MB'})
            
            # 創建資源
            resource = TeacherResource(
                teacher=request.user,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                category_id=request.POST.get('category'),
                resource_type=request.POST.get('resource_type', 'other'),
                difficulty_level=request.POST.get('difficulty_level', 'all'),
                file=uploaded_file,
                tags=request.POST.get('tags', ''),
                composer=request.POST.get('composer', ''),
                piece_name=request.POST.get('piece_name', ''),
                is_public=request.POST.get('is_public') == 'true'
            )
            
            # 處理外部連結
            external_link = request.POST.get('external_link', '').strip()
            if external_link:
                resource.external_link = external_link
            
            resource.save()
            
            # 處理分享給特定學生
            shared_students = request.POST.getlist('shared_students[]')
            if shared_students:
                students = User.objects.filter(id__in=shared_students)
                resource.shared_with_students.set(students)
            
            messages.success(request, f'資源「{resource.title}」已成功上傳')
            
            return JsonResponse({
                'success': True,
                'resource_id': resource.id,
                'message': '資源上傳成功'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET請求 - 顯示上傳表單
    categories = ResourceCategory.objects.all().order_by('order')
    
    # 獲取教師的學生列表
    students = User.objects.filter(
        teacher_relations__teacher=request.user,
        teacher_relations__is_active=True
    ).distinct()
    
    context = {
        'categories': categories,
        'students': students,
        'resource_types': TeacherResource.RESOURCE_TYPES,
        'difficulty_levels': TeacherResource.DIFFICULTY_LEVELS,
    }
    
    return render(request, 'practice_logs/teacher/upload_resource.html', context)


@login_required
@teacher_required
def resource_detail(request, resource_id):
    """資源詳情頁面"""
    resource = get_object_or_404(TeacherResource, id=resource_id)
    
    # 檢查訪問權限
    can_access = (
        resource.teacher == request.user or
        resource.is_public or
        request.user in resource.shared_with_students.all()
    )
    
    if not can_access:
        messages.error(request, '您沒有權限查看此資源')
        return redirect('practice_logs:teacher_resources')
    
    # 增加瀏覽次數
    resource.view_count = F('view_count') + 1
    resource.save(update_fields=['view_count'])
    
    # 記錄使用日誌
    ResourceUsageLog.objects.create(
        resource=resource,
        user=request.user,
        action='view'
    )
    
    # 相關資源
    related_resources = TeacherResource.objects.filter(
        Q(category=resource.category) | Q(tags__icontains=resource.tags.split(',')[0] if resource.tags else ''),
        Q(teacher=request.user) | Q(is_public=True)
    ).exclude(id=resource.id).order_by('-created_at')[:6]
    
    # 檢查是否在收藏夾中
    in_collections = ResourceCollection.objects.filter(
        teacher=request.user,
        resources=resource
    ).values_list('id', 'name')
    
    context = {
        'resource': resource,
        'related_resources': related_resources,
        'in_collections': list(in_collections),
        'can_edit': resource.teacher == request.user,
    }
    
    return render(request, 'practice_logs/teacher/resource_detail.html', context)


@login_required
@teacher_required
def download_resource(request, resource_id):
    """下載資源檔案"""
    resource = get_object_or_404(TeacherResource, id=resource_id)
    
    # 檢查訪問權限
    can_access = (
        resource.teacher == request.user or
        resource.is_public or
        request.user in resource.shared_with_students.all()
    )
    
    if not can_access:
        messages.error(request, '您沒有權限下載此資源')
        return redirect('practice_logs:teacher_resources')
    
    if not resource.file:
        messages.error(request, '此資源沒有可下載的檔案')
        return redirect('practice_logs:resource_detail', resource_id=resource_id)
    
    # 增加下載次數
    resource.download_count = F('download_count') + 1
    resource.save(update_fields=['download_count'])
    
    # 記錄使用日誌
    ResourceUsageLog.objects.create(
        resource=resource,
        user=request.user,
        action='download'
    )
    
    # 返回檔案
    file_path = resource.file.path
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
    else:
        messages.error(request, '檔案不存在')
        return redirect('practice_logs:resource_detail', resource_id=resource_id)


@login_required
@teacher_required
def manage_collections(request):
    """管理資源收藏夾"""
    teacher = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            # 創建新收藏夾
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            collection = ResourceCollection.objects.create(
                teacher=teacher,
                name=name,
                description=description
            )
            
            messages.success(request, f'收藏夾「{name}」已創建')
            return redirect('practice_logs:manage_collections')
        
        elif action == 'delete':
            # 刪除收藏夾
            collection_id = request.POST.get('collection_id')
            collection = get_object_or_404(ResourceCollection, id=collection_id, teacher=teacher)
            name = collection.name
            collection.delete()
            
            messages.success(request, f'收藏夾「{name}」已刪除')
            return redirect('practice_logs:manage_collections')
    
    # 獲取所有收藏夾
    collections = ResourceCollection.objects.filter(
        teacher=teacher
    ).annotate(
        resource_count=Count('resources')
    ).order_by('-created_at')
    
    context = {
        'collections': collections
    }
    
    return render(request, 'practice_logs/teacher/manage_collections.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def add_to_collection(request):
    """將資源加入收藏夾（AJAX）"""
    try:
        data = json.loads(request.body)
        resource_id = data.get('resource_id')
        collection_id = data.get('collection_id')
        
        resource = get_object_or_404(TeacherResource, id=resource_id)
        collection = get_object_or_404(ResourceCollection, id=collection_id, teacher=request.user)
        
        # 檢查權限
        can_access = (
            resource.teacher == request.user or
            resource.is_public or
            request.user in resource.shared_with_students.all()
        )
        
        if not can_access:
            return JsonResponse({'success': False, 'error': '無權限訪問此資源'})
        
        # 加入收藏夾
        collection.resources.add(resource)
        
        return JsonResponse({
            'success': True,
            'message': f'已將資源加入「{collection.name}」'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@teacher_required
@require_http_methods(["POST"])
def remove_from_collection(request):
    """從收藏夾移除資源（AJAX）"""
    try:
        data = json.loads(request.body)
        resource_id = data.get('resource_id')
        collection_id = data.get('collection_id')
        
        resource = get_object_or_404(TeacherResource, id=resource_id)
        collection = get_object_or_404(ResourceCollection, id=collection_id, teacher=request.user)
        
        # 從收藏夾移除
        collection.resources.remove(resource)
        
        return JsonResponse({
            'success': True,
            'message': f'已從「{collection.name}」移除資源'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@teacher_required
def collection_detail(request, collection_id):
    """收藏夾詳情頁面"""
    collection = get_object_or_404(ResourceCollection, id=collection_id)
    
    # 檢查訪問權限
    can_access = (
        collection.teacher == request.user or
        collection.is_public or
        request.user in collection.shared_with_students.all()
    )
    
    if not can_access:
        messages.error(request, '您沒有權限查看此收藏夾')
        return redirect('practice_logs:manage_collections')
    
    # 獲取收藏夾中的資源
    resources = collection.resources.all().order_by('-created_at')
    
    # 分頁
    paginator = Paginator(resources, 12)
    page = request.GET.get('page', 1)
    resources_page = paginator.get_page(page)
    
    context = {
        'collection': collection,
        'resources': resources_page,
        'can_edit': collection.teacher == request.user,
    }
    
    return render(request, 'practice_logs/teacher/collection_detail.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def delete_resource(request, resource_id):
    """刪除資源"""
    resource = get_object_or_404(TeacherResource, id=resource_id, teacher=request.user)
    
    title = resource.title
    
    # 刪除實際檔案
    if resource.file:
        try:
            os.remove(resource.file.path)
        except:
            pass
    
    # 刪除縮圖
    if resource.thumbnail:
        try:
            os.remove(resource.thumbnail.path)
        except:
            pass
    
    # 刪除資源記錄
    resource.delete()
    
    messages.success(request, f'資源「{title}」已刪除')
    return redirect('practice_logs:resource_library')


@login_required
@teacher_required
def resource_analytics(request):
    """資源使用分析"""
    teacher = request.user
    
    # 獲取日期範圍
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timezone.timedelta(days=days)
    
    # 資源使用統計
    usage_stats = ResourceUsageLog.objects.filter(
        resource__teacher=teacher,
        timestamp__gte=start_date
    ).values('action').annotate(
        count=Count('id')
    )
    
    # 熱門資源
    popular_resources = TeacherResource.objects.filter(
        teacher=teacher
    ).annotate(
        total_usage=Count('usage_logs')
    ).order_by('-total_usage')[:10]
    
    # 按類別統計
    category_stats = TeacherResource.objects.filter(
        teacher=teacher
    ).values('category__name').annotate(
        count=Count('id'),
        total_downloads=Sum('download_count'),
        total_views=Sum('view_count')
    )
    
    # 每日使用趨勢
    daily_usage = []
    for i in range(days):
        date = timezone.now().date() - timezone.timedelta(days=i)
        usage = ResourceUsageLog.objects.filter(
            resource__teacher=teacher,
            timestamp__date=date
        ).count()
        daily_usage.append({
            'date': date.strftime('%m/%d'),
            'usage': usage
        })
    daily_usage.reverse()
    
    context = {
        'usage_stats': {stat['action']: stat['count'] for stat in usage_stats},
        'popular_resources': popular_resources,
        'category_stats': category_stats,
        'daily_usage': json.dumps(daily_usage),
        'days': days,
    }
    
    return render(request, 'practice_logs/teacher/resource_analytics.html', context)