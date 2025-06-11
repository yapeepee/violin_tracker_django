"""
問答系統模型
支援學生提問與教師回答的互動功能
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class StudentQuestion(models.Model):
    """學生提問模型"""
    
    QUESTION_TYPES = [
        ('technique', '演奏技巧'),
        ('theory', '樂理知識'),
        ('piece', '曲目相關'),
        ('practice', '練習方法'),
        ('equipment', '器材設備'),
        ('other', '其他')
    ]
    
    PRIORITY_LEVELS = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '緊急')
    ]
    
    STATUS_CHOICES = [
        ('pending', '待回答'),
        ('answered', '已回答'),
        ('closed', '已關閉')
    ]
    
    # 基本資訊
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='asked_questions',
        verbose_name="提問學生"
    )
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_questions',
        verbose_name="指定教師",
        help_text="可選擇特定教師回答"
    )
    
    # 問題內容
    title = models.CharField(
        max_length=200,
        verbose_name="問題標題",
        help_text="簡短描述您的問題"
    )
    
    question_text = models.TextField(
        verbose_name="問題詳情",
        help_text="詳細說明您的問題"
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='technique',
        verbose_name="問題類型"
    )
    
    category = models.ForeignKey(
        'QuestionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name="問題分類"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name="優先級"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="狀態"
    )
    
    # 附件
    attachment = models.FileField(
        upload_to='questions/attachments/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="附件",
        help_text="可上傳圖片、音頻或影片",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp3', 'wav', 'mp4', 'mov', 'pdf']
            )
        ]
    )
    
    # 相關練習記錄
    related_practice_log = models.ForeignKey(
        'PracticeLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name="相關練習記錄"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="提問時間"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間"
    )
    
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="回答時間"
    )
    
    # 統計
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="瀏覽次數"
    )
    
    is_public = models.BooleanField(
        default=True,
        verbose_name="公開問題",
        help_text="是否允許其他學生查看此問題"
    )
    
    # 標籤
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="標籤",
        help_text="用逗號分隔多個標籤"
    )
    
    class Meta:
        verbose_name = "學生提問"
        verbose_name_plural = "學生提問"
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['question_type', 'priority']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.title}"
    
    @property
    def is_urgent(self):
        """檢查是否為緊急問題"""
        return self.priority == 'urgent'
    
    @property
    def days_since_asked(self):
        """計算提問後經過的天數"""
        return (timezone.now() - self.created_at).days
    
    @property
    def response_time_hours(self):
        """計算回答時間（小時）"""
        if self.answered_at:
            return (self.answered_at - self.created_at).total_seconds() / 3600
        return None
    
    def mark_as_answered(self, teacher):
        """標記為已回答"""
        self.status = 'answered'
        self.teacher = teacher
        self.answered_at = timezone.now()
        self.save()


class TeacherAnswer(models.Model):
    """教師回答模型"""
    
    question = models.ForeignKey(
        StudentQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="相關問題"
    )
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_answers',
        verbose_name="回答教師"
    )
    
    answer_text = models.TextField(
        verbose_name="回答內容"
    )
    
    # 多媒體回答
    voice_answer = models.FileField(
        upload_to='answers/voice/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="語音回答",
        validators=[
            FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'm4a'])
        ]
    )
    
    video_answer = models.FileField(
        upload_to='answers/video/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="影片回答",
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi'])
        ]
    )
    
    # 參考資源
    reference_links = models.TextField(
        blank=True,
        verbose_name="參考連結",
        help_text="相關的學習資源連結，每行一個"
    )
    
    # 評價
    is_helpful = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="學生認為有幫助"
    )
    
    helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name="有幫助次數"
    )
    
    unhelpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name="沒幫助次數"
    )
    
    student_feedback = models.TextField(
        blank=True,
        verbose_name="學生回饋"
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name="公開回答",
        help_text="是否允許其他學生查看此回答"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="回答時間"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間"
    )
    
    class Meta:
        verbose_name = "教師回答"
        verbose_name_plural = "教師回答"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['question', 'created_at']),
            models.Index(fields=['teacher']),
        ]
    
    def __str__(self):
        return f"回答 by {self.teacher.username} - {self.question.title}"


class QuestionCategory(models.Model):
    """問題分類模型"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="分類名稱"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="分類描述"
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='fas fa-question-circle',
        verbose_name="圖標類別",
        help_text="FontAwesome圖標類別名稱"
    )
    
    color = models.CharField(
        max_length=7,
        default='#2c5f3d',
        verbose_name="顏色代碼",
        help_text="HEX顏色代碼"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="排序"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="啟用"
    )
    
    class Meta:
        verbose_name = "問題分類"
        verbose_name_plural = "問題分類"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class FAQ(models.Model):
    """常見問題模型"""
    
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name="分類"
    )
    
    question = models.CharField(
        max_length=300,
        verbose_name="問題"
    )
    
    answer = models.TextField(
        verbose_name="答案"
    )
    
    # 相關資源
    related_video = models.URLField(
        blank=True,
        verbose_name="相關影片",
        help_text="YouTube或其他影片連結"
    )
    
    related_resources = models.ManyToManyField(
        'TeacherResource',
        blank=True,
        related_name='related_faqs',
        verbose_name="相關資源"
    )
    
    # 統計
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="瀏覽次數"
    )
    
    helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name="有幫助次數"
    )
    
    # 排序與狀態
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="顯示順序"
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name="精選問題"
    )
    
    is_published = models.BooleanField(
        default=False,
        verbose_name="已發布"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_faqs',
        verbose_name="創建者"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="創建時間"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間"
    )
    
    class Meta:
        verbose_name = "常見問題"
        verbose_name_plural = "常見問題"
        ordering = ['category', 'display_order', '-helpful_count']
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.question}"
    
    def increment_view_count(self):
        """增加瀏覽次數"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def mark_helpful(self):
        """標記為有幫助"""
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])