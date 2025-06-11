"""
小提琴練習記錄系統 - 優化的 Django Admin 配置
包含查詢優化、批量操作和性能改進
"""

from django.contrib import admin
from django.db.models import Count, Sum, Avg, Q, F, Prefetch
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.cache import cache
from functools import wraps
import json

from .models import (
    PracticeLog, TeacherFeedback,
    Achievement, StudentAchievement, StudentLevel,
    StudentQuestion, TeacherAnswer, QuestionCategory, FAQ,
    ResourceCategory, TeacherResource, ResourceCollection, ResourceUsageLog,
    LessonSchedule, StudentProgress, LessonNote,
    UserProfile, StudentTeacherRelation, UserLoginLog
)


# ============ 優化的基礎 Admin 類 ============
class OptimizedModelAdmin(admin.ModelAdmin):
    """優化的 ModelAdmin 基礎類"""
    show_full_result_count = False  # 不顯示總數以提升性能
    list_per_page = 50  # 每頁顯示數量
    list_max_show_all = 200  # 最大顯示全部數量
    
    def get_queryset(self, request):
        """優化查詢集"""
        qs = super().get_queryset(request)
        
        # 自動添加 select_related
        if hasattr(self, 'select_related_fields'):
            qs = qs.select_related(*self.select_related_fields)
        
        # 自動添加 prefetch_related
        if hasattr(self, 'prefetch_related_fields'):
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        
        # 只選擇需要的欄位
        if hasattr(self, 'list_select_fields'):
            qs = qs.only(*self.list_select_fields)
        
        return qs
    
    def changelist_view(self, request, extra_context=None):
        """優化列表視圖，添加快取"""
        # 生成快取鍵
        cache_key = f"admin:{self.model._meta.label}:changelist:{request.GET.urlencode()}"
        
        # 嘗試從快取獲取
        cached_response = cache.get(cache_key)
        if cached_response and not request.GET.get('no_cache'):
            return cached_response
        
        # 獲取響應
        response = super().changelist_view(request, extra_context)
        
        # 快取響應（5分鐘）
        if hasattr(response, 'render'):
            cache.set(cache_key, response, 300)
        
        return response


# ============ 練習記錄 Admin ============
@admin.register(PracticeLog)
class PracticeLogAdmin(OptimizedModelAdmin):
    """優化的練習記錄管理"""
    list_display = [
        'id', 'student_name_link', 'piece_display', 'date', 
        'minutes_bar', 'rating_stars', 'focus_badge', 
        'mood_icon', 'has_video_icon', 'quick_actions'
    ]
    list_filter = [
        'date', 'focus', 'mood', 'rating',
        ('student_name', admin.filters.AllValuesFieldListFilter)
    ]
    search_fields = ['student_name', 'piece', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', 'student_name']
    
    # 查詢優化
    select_related_fields = []  # 如果有外鍵關聯
    list_select_fields = [
        'id', 'student_name', 'piece', 'date', 'minutes', 
        'rating', 'focus', 'mood', 'video_file'
    ]
    
    # 只讀欄位（提升性能）
    readonly_fields = [
        'created_at', 'updated_at', 'video_duration', 
        'file_size', 'get_overall_performance_score',
        'practice_statistics'
    ]
    
    # 欄位集組織
    fieldsets = [
        ('基本信息', {
            'fields': ('student_name', 'date', 'piece', 'minutes', 'rating')
        }),
        ('練習詳情', {
            'fields': ('focus', 'mood', 'notes', 'student_notes_to_teacher')
        }),
        ('評分詳情', {
            'fields': (
                'technique_bow_control', 'technique_finger_position', 'technique_intonation',
                'expression_dynamics', 'expression_phrasing', 'expression_emotion',
                'rhythm_tempo_stability', 'rhythm_pattern_accuracy',
                'sight_reading_fluency', 'sight_reading_accuracy',
                'memorization_stability', 'memorization_confidence',
                'ensemble_listening', 'ensemble_timing'
            ),
            'classes': ('collapse',)  # 預設收起
        }),
        ('影片資料', {
            'fields': ('video_file', 'video_thumbnail', 'video_duration', 'file_size'),
            'classes': ('collapse',)
        }),
        ('統計信息', {
            'fields': ('practice_statistics', 'get_overall_performance_score'),
            'classes': ('collapse',)
        }),
        ('系統信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    # ===== 自定義顯示方法 =====
    def student_name_link(self, obj):
        """學生姓名連結"""
        url = f"{reverse('admin:practice_logs_practicelog_changelist')}?student_name={obj.student_name}"
        return format_html('<a href="{}">{}</a>', url, obj.student_name)
    student_name_link.short_description = '學生姓名'
    student_name_link.admin_order_field = 'student_name'
    
    def piece_display(self, obj):
        """曲目顯示（截斷過長文字）"""
        if len(obj.piece) > 30:
            return f"{obj.piece[:30]}..."
        return obj.piece
    piece_display.short_description = '練習曲目'
    piece_display.admin_order_field = 'piece'
    
    def minutes_bar(self, obj):
        """練習時間條形圖"""
        percentage = min(obj.minutes / 120 * 100, 100)  # 最大120分鐘
        color = '#4CAF50' if obj.minutes >= 60 else '#FFC107' if obj.minutes >= 30 else '#F44336'
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; text-align: center; color: white;">'
            '{} 分</div></div>',
            percentage, color, obj.minutes
        )
    minutes_bar.short_description = '練習時間'
    minutes_bar.admin_order_field = 'minutes'
    
    def rating_stars(self, obj):
        """評分星星顯示"""
        full_stars = '★' * obj.rating
        empty_stars = '☆' * (5 - obj.rating)
        color = self.get_rating_color(obj.rating)
        return format_html(
            '<span style="color: {}; font-size: 16px;">{}{}</span>',
            color, full_stars, empty_stars
        )
    rating_stars.short_description = '評分'
    rating_stars.admin_order_field = 'rating'
    
    def focus_badge(self, obj):
        """練習重點徽章"""
        focus_colors = {
            'technique': '#3F51B5',
            'expression': '#9C27B0',
            'rhythm': '#F44336',
            'sight_reading': '#FF9800',
            'memorization': '#4CAF50',
            'ensemble': '#00BCD4',
            'other': '#607D8B'
        }
        color = focus_colors.get(obj.focus, '#607D8B')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_focus_display()
        )
    focus_badge.short_description = '練習重點'
    focus_badge.admin_order_field = 'focus'
    
    def mood_icon(self, obj):
        """心情圖標"""
        mood_map = {
            'joyful': '😊',
            'peaceful': '😌',
            'focused': '🎯',
            'melancholic': '😔',
            'passionate': '🔥',
            'contemplative': '🤔'
        }
        return format_html(
            '<span style="font-size: 20px;" title="{}">{}</span>',
            dict(PracticeLog.MOOD_CHOICES).get(obj.mood, ''),
            mood_map.get(obj.mood, '🎵')
        )
    mood_icon.short_description = '心情'
    mood_icon.admin_order_field = 'mood'
    
    def has_video_icon(self, obj):
        """影片圖標"""
        if obj.video_file:
            return format_html('<span style="color: #4CAF50; font-size: 18px;">📹</span>')
        return format_html('<span style="color: #ccc;">-</span>')
    has_video_icon.short_description = '影片'
    has_video_icon.admin_order_field = 'video_file'
    
    def quick_actions(self, obj):
        """快速操作按鈕"""
        buttons = []
        
        # 查看詳情按鈕
        view_url = reverse('admin:practice_logs_practicelog_change', args=[obj.pk])
        buttons.append(f'<a href="{view_url}" class="button small">查看</a>')
        
        # 添加回饋按鈕
        if not hasattr(obj, 'teacher_feedback'):
            feedback_url = f"{reverse('admin:practice_logs_teacherfeedback_add')}?practice_log={obj.pk}"
            buttons.append(f'<a href="{feedback_url}" class="button small">添加回饋</a>')
        
        return format_html(' '.join(buttons))
    quick_actions.short_description = '操作'
    
    def practice_statistics(self, obj):
        """練習統計信息"""
        # 使用快取避免重複計算
        cache_key = f"practice_stats:{obj.student_name}:{obj.piece}"
        stats = cache.get(cache_key)
        
        if not stats:
            # 計算統計數據
            piece_logs = PracticeLog.objects.filter(
                student_name=obj.student_name,
                piece=obj.piece
            ).aggregate(
                total_minutes=Sum('minutes'),
                avg_rating=Avg('rating'),
                count=Count('id')
            )
            
            stats = f"""
            <strong>此曲目統計：</strong><br>
            總練習時間：{piece_logs['total_minutes'] or 0} 分鐘<br>
            平均評分：{piece_logs['avg_rating'] or 0:.1f} 分<br>
            練習次數：{piece_logs['count']} 次
            """
            
            cache.set(cache_key, stats, 3600)  # 快取1小時
        
        return format_html(stats)
    practice_statistics.short_description = '統計信息'
    
    @staticmethod
    def get_rating_color(rating):
        """獲取評分顏色"""
        colors = {
            1: '#F44336',
            2: '#FF9800',
            3: '#FFC107',
            4: '#8BC34A',
            5: '#4CAF50'
        }
        return colors.get(rating, '#757575')
    
    # ===== 批量操作 =====
    actions = ['export_to_csv', 'batch_analyze', 'clear_cache']
    
    def export_to_csv(self, request, queryset):
        """導出為 CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="practice_logs.csv"'
        
        # 添加 BOM 以支援 Excel 開啟中文
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            '學生姓名', '日期', '曲目', '練習時間(分)', '評分', 
            '練習重點', '心情', '筆記'
        ])
        
        # 使用 values_list 提升性能
        for log in queryset.values_list(
            'student_name', 'date', 'piece', 'minutes', 
            'rating', 'focus', 'mood', 'notes'
        ):
            writer.writerow(log)
        
        self.message_user(request, f"已導出 {queryset.count()} 條記錄")
        return response
    export_to_csv.short_description = '導出選中的記錄為 CSV'
    
    def batch_analyze(self, request, queryset):
        """批量分析"""
        # 使用聚合查詢一次性獲取所有統計
        stats = queryset.aggregate(
            total_minutes=Sum('minutes'),
            avg_rating=Avg('rating'),
            total_sessions=Count('id'),
            unique_students=Count('student_name', distinct=True),
            unique_pieces=Count('piece', distinct=True),
            excellent_sessions=Count(
                'id', filter=Q(rating__gte=4)
            ),
            long_sessions=Count(
                'id', filter=Q(minutes__gte=60)
            )
        )
        
        message = f"""
        分析結果：
        - 總練習時間：{stats['total_minutes']} 分鐘
        - 平均評分：{stats['avg_rating']:.2f} 分
        - 總練習次數：{stats['total_sessions']} 次
        - 涉及學生數：{stats['unique_students']} 人
        - 不同曲目數：{stats['unique_pieces']} 首
        - 優秀練習（≥4分）：{stats['excellent_sessions']} 次
        - 長時練習（≥60分）：{stats['long_sessions']} 次
        """
        
        self.message_user(request, message)
    batch_analyze.short_description = '分析選中的記錄'
    
    def clear_cache(self, request, queryset):
        """清除相關快取"""
        student_names = set(queryset.values_list('student_name', flat=True))
        
        # 清除快取
        cache_keys = []
        for name in student_names:
            cache_keys.extend([
                f"practice_stats:{name}:*",
                f"student_stats:{name}",
                f"analytics:student_name:{name}"
            ])
        
        # 使用 delete_pattern（如果支援）或逐個刪除
        deleted_count = 0
        for key in cache_keys:
            if cache.delete(key):
                deleted_count += 1
        
        self.message_user(
            request, 
            f"已清除 {len(student_names)} 位學生的快取（約 {deleted_count} 個快取項）"
        )
    clear_cache.short_description = '清除相關快取'
    
    # ===== 自定義過濾器 =====
    def get_list_filter(self, request):
        """動態獲取過濾器"""
        filters = list(self.list_filter)
        
        # 如果是超級用戶，添加更多過濾選項
        if request.user.is_superuser:
            filters.extend(['created_at', 'has_video'])
        
        return filters
    
    # ===== 性能優化方法 =====
    def get_search_results(self, request, queryset, search_term):
        """優化搜索功能"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # 如果搜索詞較短，使用更精確的搜索
        if search_term and len(search_term) < 3:
            queryset = queryset.filter(
                Q(student_name__istartswith=search_term) |
                Q(piece__istartswith=search_term)
            )
        
        return queryset, use_distinct


# ============ 教師回饋 Admin ============
@admin.register(TeacherFeedback)
class TeacherFeedbackAdmin(OptimizedModelAdmin):
    """優化的教師回饋管理"""
    list_display = [
        'id', 'practice_log_link', 'teacher_name', 'feedback_date',
        'overall_rating_bar', 'mastery_badge', 'status_icons', 'quick_preview'
    ]
    list_filter = [
        'feedback_date', 'overall_rating', 'mastery_level',
        'need_retry', 'mastered_well', 'notify_parents'
    ]
    search_fields = ['teacher_name', 'practice_log__student_name', 'feedback_text']
    date_hierarchy = 'feedback_date'
    
    # 查詢優化
    select_related_fields = ['practice_log']
    list_select_fields = [
        'id', 'teacher_name', 'feedback_date', 'overall_rating',
        'mastery_level', 'need_retry', 'mastered_well', 'notify_parents',
        'student_read', 'practice_log__student_name', 'practice_log__piece'
    ]
    
    raw_id_fields = ['practice_log']  # 使用原始ID欄位以提升性能
    
    def practice_log_link(self, obj):
        """練習記錄連結"""
        return format_html(
            '<a href="{}">{} - {}</a>',
            reverse('admin:practice_logs_practicelog_change', args=[obj.practice_log.pk]),
            obj.practice_log.student_name,
            obj.practice_log.piece[:20] + '...' if len(obj.practice_log.piece) > 20 else obj.practice_log.piece
        )
    practice_log_link.short_description = '練習記錄'
    
    def overall_rating_bar(self, obj):
        """整體評分條形圖"""
        rating = obj.overall_rating or 0
        percentage = rating * 20  # 轉換為百分比
        color = '#4CAF50' if rating >= 4 else '#FFC107' if rating >= 3 else '#F44336'
        
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px; margin-right: 5px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px;"></div>'
            '</div>'
            '<span>{}/5</span>'
            '</div>',
            percentage, color, rating
        )
    overall_rating_bar.short_description = '整體評分'
    overall_rating_bar.admin_order_field = 'overall_rating'
    
    def mastery_badge(self, obj):
        """精通程度徽章"""
        mastery_colors = {
            'beginner': '#9E9E9E',
            'developing': '#FF9800',
            'competent': '#2196F3',
            'proficient': '#4CAF50',
            'mastery': '#9C27B0'
        }
        color = mastery_colors.get(obj.mastery_level, '#9E9E9E')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_mastery_level_display()
        )
    mastery_badge.short_description = '精通程度'
    
    def status_icons(self, obj):
        """狀態圖標"""
        icons = []
        
        if obj.need_retry:
            icons.append('<span title="需要重練" style="color: #F44336;">🔄</span>')
        if obj.mastered_well:
            icons.append('<span title="掌握良好" style="color: #4CAF50;">✅</span>')
        if obj.notify_parents:
            icons.append('<span title="通知家長" style="color: #2196F3;">👨‍👩‍👧</span>')
        if obj.student_read:
            icons.append('<span title="學生已讀" style="color: #4CAF50;">👁️</span>')
        
        return format_html(' '.join(icons) if icons else '-')
    status_icons.short_description = '狀態'
    
    def quick_preview(self, obj):
        """快速預覽"""
        preview_text = obj.feedback_text[:100] + '...' if len(obj.feedback_text) > 100 else obj.feedback_text
        return format_html(
            '<div style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" '
            'title="{}">{}</div>',
            obj.feedback_text, preview_text
        )
    quick_preview.short_description = '回饋預覽'


# ============ 成就系統 Admin ============
@admin.register(Achievement)
class AchievementAdmin(OptimizedModelAdmin):
    """優化的成就管理"""
    list_display = [
        'id', 'icon_display', 'name', 'category_badge', 
        'points_display', 'tier_badge', 'requirement_info', 'is_active_toggle'
    ]
    list_filter = ['category', 'tier', 'is_active', 'requirement_type']
    search_fields = ['name', 'description']
    ordering = ['category', '-tier', 'requirement_value']
    
    def icon_display(self, obj):
        return format_html('<span style="font-size: 24px;">{}</span>', obj.icon)
    icon_display.short_description = '圖標'
    
    def category_badge(self, obj):
        category_colors = {
            'practice_time': '#2196F3',
            'practice_days': '#4CAF50',
            'pieces_mastered': '#FF9800',
            'perfect_practices': '#9C27B0',
            'challenge_complete': '#F44336',
            'special': '#FFD700'
        }
        color = category_colors.get(obj.category, '#9E9E9E')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = '類別'
    
    def points_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #FF9800;">+{} pts</span>',
            obj.points
        )
    points_display.short_description = '點數'
    
    def tier_badge(self, obj):
        tier_styles = {
            'bronze': 'background: #CD7F32; color: white;',
            'silver': 'background: #C0C0C0; color: black;',
            'gold': 'background: #FFD700; color: black;',
            'platinum': 'background: #E5E4E2; color: black;',
            'diamond': 'background: #B9F2FF; color: black;'
        }
        style = tier_styles.get(obj.tier, '')
        return format_html(
            '<span style="{}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            style, obj.get_tier_display()
        )
    tier_badge.short_description = '等級'
    
    def requirement_info(self, obj):
        return format_html(
            '<small>{}: {}</small>',
            obj.get_requirement_type_display(),
            obj.requirement_value
        )
    requirement_info.short_description = '達成條件'
    
    def is_active_toggle(self, obj):
        """可切換的啟用狀態"""
        if obj.is_active:
            return format_html('<span style="color: #4CAF50;">✓ 啟用</span>')
        return format_html('<span style="color: #9E9E9E;">✗ 停用</span>')
    is_active_toggle.short_description = '狀態'


# ============ 註冊其他優化的 Admin ============
admin.site.register(StudentAchievement, OptimizedModelAdmin)
admin.site.register(StudentLevel, OptimizedModelAdmin)
admin.site.register(UserProfile, OptimizedModelAdmin)
admin.site.register(StudentTeacherRelation, OptimizedModelAdmin)
admin.site.register(UserLoginLog, OptimizedModelAdmin)
admin.site.register(StudentQuestion, OptimizedModelAdmin)
admin.site.register(TeacherAnswer, OptimizedModelAdmin)
admin.site.register(QuestionCategory, OptimizedModelAdmin)
admin.site.register(FAQ, OptimizedModelAdmin)
admin.site.register(ResourceCategory, OptimizedModelAdmin)
admin.site.register(TeacherResource, OptimizedModelAdmin)
admin.site.register(ResourceCollection, OptimizedModelAdmin)
admin.site.register(ResourceUsageLog, OptimizedModelAdmin)
admin.site.register(LessonSchedule, OptimizedModelAdmin)
admin.site.register(StudentProgress, OptimizedModelAdmin)
admin.site.register(LessonNote, OptimizedModelAdmin)

# ============ 自定義管理站點 ============
admin.site.site_header = '🎻 小提琴練習追蹤系統 - 管理後台'
admin.site.site_title = '小提琴練習管理'
admin.site.index_title = '歡迎使用小提琴練習追蹤系統'

# 添加自定義 CSS 和 JavaScript
class CustomAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = """
        <style>
            .module h2 { background: #4CAF50; }
            .button.small { padding: 5px 10px; font-size: 12px; }
            .dashboard .module table th { background: #f5f5f5; }
        </style>
        """
        return context