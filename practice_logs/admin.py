"""
小提琴練習記錄系統 - Django Admin 配置
為所有模型提供完整的管理介面
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    PracticeLog, TeacherFeedback,
    Achievement, StudentAchievement, StudentLevel,
    StudentQuestion, TeacherAnswer, QuestionCategory, FAQ,
    ResourceCategory, TeacherResource, ResourceCollection,
    LessonSchedule, StudentProgress, LessonNote,
    # PracticeRecording, RecordingComment, RecordingProgress,
    # WeeklyChallenge, PracticeTask, StudentGoal
)


# ============ 原有模型的Admin ============
@admin.register(PracticeLog)
class PracticeLogAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'piece', 'date', 'minutes', 'rating_display', 'focus_display']
    list_filter = ['date', 'focus', 'rating']
    search_fields = ['student_name', 'piece', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', 'student_name']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student_name', 'piece', 'date')
        }),
        ('練習詳情', {
            'fields': ('minutes', 'rating', 'focus', 'notes')
        }),
    )
    
    def rating_display(self, obj):
        return f"{obj.get_rating_display_emoji()} {obj.rating}分"
    rating_display.short_description = "評分"
    
    def focus_display(self, obj):
        return obj.focus_display
    focus_display.short_description = "練習重點"


# ============ 教師回饋系統Admin ============
@admin.register(TeacherFeedback)
class TeacherFeedbackAdmin(admin.ModelAdmin):
    list_display = ['teacher_name', 'practice_log_display', 'feedback_type', 'overall_rating_display', 
                   'mastery_level', 'created_at', 'student_read', 'notify_parents']
    list_filter = ['feedback_type', 'mastery_level', 'need_retry', 'mastered_well', 
                   'notify_parents', 'is_featured', 'created_at']
    search_fields = ['teacher_name', 'practice_log__student_name', 'practice_log__piece', 'feedback_text']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('回饋基本資訊', {
            'fields': ('practice_log', 'teacher_name', 'feedback_type')
        }),
        ('回饋內容', {
            'fields': ('feedback_text', 'voice_feedback')
        }),
        ('技術評估', {
            'fields': ('technique_rating', 'musicality_rating', 'progress_rating', 'mastery_level')
        }),
        ('學習狀態', {
            'fields': ('need_retry', 'mastered_well')
        }),
        ('練習建議', {
            'fields': ('suggested_focus', 'suggested_pieces', 'practice_tips')
        }),
        ('互動設定', {
            'fields': ('notify_parents', 'is_public', 'is_featured')
        }),
        ('追蹤狀態', {
            'fields': ('student_read', 'parent_read', 'student_response')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def practice_log_display(self, obj):
        return f"{obj.practice_log.student_name} - {obj.practice_log.piece} ({obj.practice_log.date})"
    practice_log_display.short_description = "練習記錄"
    
    def overall_rating_display(self, obj):
        rating = obj.get_overall_rating()
        stars = obj.get_rating_stars_display('overall')
        return f"{stars} {rating}"
    overall_rating_display.short_description = "整體評分"


# ============ 成就系統Admin ============
@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['icon_display', 'name', 'category', 'requirement_display', 'points', 'rarity', 'is_active']
    list_filter = ['category', 'rarity', 'is_active', 'requirement_type']
    search_fields = ['name', 'description']
    ordering = ['category', 'requirement_value']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'icon')
        }),
        ('分類與稀有度', {
            'fields': ('category', 'rarity', 'is_active')
        }),
        ('達成條件', {
            'fields': ('requirement_type', 'requirement_value', 'points')
        }),
    )
    
    def icon_display(self, obj):
        return obj.icon
    icon_display.short_description = "圖示"
    
    def requirement_display(self, obj):
        return f"{obj.get_requirement_type_display()}: {obj.requirement_value}"
    requirement_display.short_description = "達成條件"


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'achievement_display', 'progress_display', 'earned_date', 'is_earned']
    list_filter = ['is_earned', 'earned_date', 'achievement__category']
    search_fields = ['student_name', 'achievement__name']
    date_hierarchy = 'earned_date'
    
    def achievement_display(self, obj):
        return f"{obj.achievement.icon} {obj.achievement.name}"
    achievement_display.short_description = "成就"
    
    def progress_display(self, obj):
        if obj.is_earned:
            return "✅ 已獲得"
        return f"🔄 {obj.progress:.1f}%"
    progress_display.short_description = "進度"


@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'level', 'title', 'total_points', 'current_streak', 'longest_streak']
    list_filter = ['level', 'title']
    search_fields = ['student_name']
    ordering = ['-level', '-total_points']
    
    fieldsets = (
        ('學生信息', {
            'fields': ('student_name', 'level', 'title')
        }),
        ('積分與經驗', {
            'fields': ('total_points', 'current_experience')
        }),
        ('練習記錄', {
            'fields': ('current_streak', 'longest_streak', 'last_practice_date', 'total_practice_time')
        }),
    )
    
    readonly_fields = ['created_date', 'updated_date']


# ============ 錄音系統Admin ============
# @admin.register(PracticeRecording)
class PracticeRecordingAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'piece', 'recording_type', 'week_number', 'duration_display', 
                   'self_rating', 'teacher_score_display', 'upload_date', 'status']
    list_filter = ['recording_type', 'status', 'is_featured', 'upload_date']
    search_fields = ['student_name', 'piece', 'notes']
    date_hierarchy = 'upload_date'
    ordering = ['-upload_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student_name', 'piece', 'recording_type', 'week_number')
        }),
        ('檔案信息', {
            'fields': ('file_path', 'thumbnail', 'duration', 'file_size', 'status')
        }),
        ('評分與回饋', {
            'fields': ('self_rating', 'teacher_score', 'teacher_feedback')
        }),
        ('顯示設定', {
            'fields': ('is_featured', 'is_public', 'view_count')
        }),
        ('備註', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['upload_date', 'view_count']
    
    def teacher_score_display(self, obj):
        return obj.teacher_score_display
    teacher_score_display.short_description = "教師評分"


# @admin.register(RecordingComment)
class RecordingCommentAdmin(admin.ModelAdmin):
    list_display = ['commenter_display', 'recording', 'rating', 'timestamp', 'is_encouraging', 'is_pinned']
    list_filter = ['commenter_type', 'is_encouraging', 'is_pinned', 'timestamp']
    search_fields = ['commenter_name', 'comment', 'recording__piece']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def commenter_display(self, obj):
        return obj.commenter_display_name
    commenter_display.short_description = "評論者"


# @admin.register(RecordingProgress)
class RecordingProgressAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'piece', 'total_recordings', 'weeks_span', 'improvement_percentage', 'updated_date']
    list_filter = ['updated_date']
    search_fields = ['student_name', 'piece']
    ordering = ['-updated_date']
    
    def improvement_percentage(self, obj):
        percentage = obj.improvement_percentage
        if percentage > 0:
            return f"📈 +{percentage:.1f}%"
        elif percentage < 0:
            return f"📉 {percentage:.1f}%"
        return "➡️ 0%"
    improvement_percentage.short_description = "進步程度"


# ============ 挑戰系統Admin ============
# @admin.register(WeeklyChallenge)
class WeeklyChallengeAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'title', 'challenge_type', 'progress_display', 
                   'week_start', 'difficulty', 'status', 'points_reward']
    list_filter = ['challenge_type', 'difficulty', 'status', 'week_start']
    search_fields = ['student_name', 'title', 'description']
    date_hierarchy = 'week_start'
    ordering = ['-week_start', 'student_name']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student_name', 'title', 'description', 'challenge_type')
        }),
        ('時間與難度', {
            'fields': ('week_start', 'difficulty', 'created_by')
        }),
        ('進度與狀態', {
            'fields': ('target_value', 'current_progress', 'status')
        }),
        ('獎勵設定', {
            'fields': ('points_reward', 'bonus_points')
        }),
    )
    
    readonly_fields = ['created_date']
    
    def progress_display(self, obj):
        percentage = obj.progress_percentage
        if obj.is_completed:
            return f"✅ {percentage:.1f}%"
        return f"🔄 {percentage:.1f}%"
    progress_display.short_description = "進度"


# @admin.register(PracticeTask)
class PracticeTaskAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'title', 'task_type', 'priority_display', 
                   'due_date', 'status', 'urgency_display', 'points_reward']
    list_filter = ['task_type', 'priority', 'status', 'due_date']
    search_fields = ['student_name', 'title', 'description']
    date_hierarchy = 'due_date'
    ordering = ['-priority', 'due_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student_name', 'title', 'description', 'task_type')
        }),
        ('時間與優先級', {
            'fields': ('due_date', 'estimated_minutes', 'priority')
        }),
        ('相關內容', {
            'fields': ('related_piece', 'related_focus')
        }),
        ('完成狀態', {
            'fields': ('status', 'completion_date', 'completion_notes')
        }),
        ('分配信息', {
            'fields': ('assigned_by', 'points_reward')
        }),
    )
    
    readonly_fields = ['created_date', 'updated_date']
    
    def priority_display(self, obj):
        return f"{obj.priority_icon} {obj.get_priority_display()}"
    priority_display.short_description = "優先級"
    
    def urgency_display(self, obj):
        urgency = obj.urgency_level
        urgency_icons = {
            'completed': '✅',
            'overdue': '🔴',
            'due_today': '⚠️',
            'due_tomorrow': '🟡',
            'due_soon': '🟠',
            'normal': '🔵'
        }
        return f"{urgency_icons.get(urgency, '⚪')} {urgency.replace('_', ' ').title()}"
    urgency_display.short_description = "緊急程度"


# @admin.register(StudentGoal)
class StudentGoalAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'title', 'goal_type', 'progress_display', 
                   'target_date', 'status', 'is_public']
    list_filter = ['goal_type', 'status', 'is_public', 'target_date']
    search_fields = ['student_name', 'title', 'description']
    date_hierarchy = 'target_date'
    ordering = ['-created_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student_name', 'title', 'description', 'goal_type')
        }),
        ('目標設定', {
            'fields': ('target_date', 'progress_metric', 'target_value', 'current_value')
        }),
        ('狀態設定', {
            'fields': ('status', 'is_public')
        }),
    )
    
    readonly_fields = ['created_date', 'achieved_date']
    
    def progress_display(self, obj):
        percentage = obj.progress_percentage
        if obj.status == 'achieved':
            return f"🎯 {percentage:.1f}%"
        return f"📊 {percentage:.1f}%"
    progress_display.short_description = "進度"


# ============ 教師系統模型Admin ============
@admin.register(StudentQuestion)
class StudentQuestionAdmin(admin.ModelAdmin):
    list_display = ['student', 'title', 'question_type', 'priority', 'status', 'teacher', 'created_at']
    list_filter = ['question_type', 'priority', 'status', 'created_at']
    search_fields = ['student__username', 'teacher__username', 'title', 'question_text']
    date_hierarchy = 'created_at'
    ordering = ['-priority', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student', 'teacher', 'title', 'question_text')
        }),
        ('分類與優先級', {
            'fields': ('question_type', 'priority', 'status')
        }),
        ('附件與關聯', {
            'fields': ('attachment', 'related_practice_log')
        }),
        ('顯示設定', {
            'fields': ('is_public', 'tags', 'view_count')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'answered_at', 'view_count']


@admin.register(TeacherAnswer)
class TeacherAnswerAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'question', 'created_at', 'is_helpful']
    list_filter = ['created_at', 'is_helpful']
    search_fields = ['teacher__username', 'answer_text']
    date_hierarchy = 'created_at'
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'view_count', 'helpful_count', 'is_featured', 'is_published']
    list_filter = ['category', 'is_featured', 'is_published']
    search_fields = ['question', 'answer']
    ordering = ['category', 'display_order']
    
    readonly_fields = ['view_count', 'helpful_count', 'created_at', 'updated_at']


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'order']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(TeacherResource)
class TeacherResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'resource_type', 'category', 'difficulty_level', 
                   'is_public', 'download_count', 'created_at']
    list_filter = ['resource_type', 'category', 'difficulty_level', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'teacher__username', 'tags']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('teacher', 'title', 'description', 'category')
        }),
        ('資源詳情', {
            'fields': ('resource_type', 'difficulty_level', 'file', 'external_link', 'thumbnail')
        }),
        ('元數據', {
            'fields': ('tags', 'composer', 'piece_name', 'version')
        }),
        ('分享設定', {
            'fields': ('is_public', 'shared_with_students')
        }),
        ('統計', {
            'fields': ('download_count', 'view_count')
        }),
    )
    
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']
    filter_horizontal = ['shared_with_students']


@admin.register(ResourceCollection)
class ResourceCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'resource_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'teacher__username']
    
    filter_horizontal = ['resources', 'shared_with_students']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LessonSchedule)
class LessonScheduleAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher', 'lesson_date', 'start_time', 'duration_minutes', 
                   'lesson_type', 'status', 'topic']
    list_filter = ['status', 'lesson_type', 'lesson_date']
    search_fields = ['student__username', 'teacher__username', 'topic']
    date_hierarchy = 'lesson_date'
    ordering = ['-lesson_date', '-start_time']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('teacher', 'student', 'lesson_date', 'start_time', 'duration_minutes')
        }),
        ('課程詳情', {
            'fields': ('lesson_type', 'status', 'topic', 'objectives', 'materials_needed')
        }),
        ('課後記錄', {
            'fields': ('lesson_notes', 'homework', 'student_performance', 'pieces_covered', 'skills_focus')
        }),
        ('改期信息', {
            'fields': ('original_date', 'reschedule_reason')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher', 'overall_score', 'current_level', 
                   'practice_consistency', 'last_assessment_date']
    list_filter = ['current_level', 'last_assessment_date']
    search_fields = ['student__username', 'teacher__username']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('student', 'teacher', 'current_level')
        }),
        ('技能評估', {
            'fields': ('technique_score', 'musicality_score', 'rhythm_score', 
                      'sight_reading_score', 'theory_score')
        }),
        ('進度與目標', {
            'fields': ('current_pieces', 'completed_pieces', 'short_term_goals', 'long_term_goals')
        }),
        ('練習統計', {
            'fields': ('average_practice_minutes', 'practice_consistency')
        }),
        ('成就與評語', {
            'fields': ('achievements', 'teacher_comments')
        }),
        ('更新記錄', {
            'fields': ('last_assessment_date',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'overall_score']


@admin.register(LessonNote)
class LessonNoteAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'created_at']
    search_fields = ['lesson__student__username', 'lesson__teacher__username']
    date_hierarchy = 'created_at'
    
    readonly_fields = ['created_at', 'updated_at']


# ============ Admin站點自定義 ============
admin.site.site_header = "🎻 小提琴練習追蹤系統"
admin.site.site_title = "練習管理"
admin.site.index_title = "歡迎來到小提琴練習管理系統"