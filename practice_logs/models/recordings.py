"""
錄音與回顧系統模型
實現音頻/影片上傳、評論、AI分析等功能
"""

import os
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from django.conf import settings


def recording_upload_path(instance, filename):
    """生成錄音檔案的上傳路徑"""
    # 按年/月/學生姓名組織檔案
    date = timezone.now()
    student_name = instance.student_name.replace(' ', '_')
    
    # 獲取檔案擴展名
    ext = filename.split('.')[-1].lower()
    
    # 生成新的檔案名（避免重複）
    new_filename = f"{date.strftime('%Y%m%d_%H%M%S')}_{student_name}.{ext}"
    
    return f"recordings/{date.year}/{date.month:02d}/{student_name}/{new_filename}"


class PracticeRecording(models.Model):
    """練習錄音模型"""
    
    RECORDING_TYPE_CHOICES = [
        ('audio', '音頻'),
        ('video', '影片')
    ]
    
    STATUS_CHOICES = [
        ('processing', '處理中'),
        ('ready', '就緒'),
        ('failed', '失敗'),
        ('archived', '已歸檔')
    ]
    
    PRIVACY_CHOICES = [
        ('public', '公開'),
        ('teacher_only', '僅教師可見'),
        ('private', '私人')
    ]
    
    student_name = models.CharField(
        max_length=100, 
        verbose_name="學生姓名",
        db_index=True
    )
    
    piece = models.CharField(
        max_length=200, 
        verbose_name="演奏曲目",
        help_text="演奏的樂曲名稱"
    )
    
    recording_type = models.CharField(
        max_length=10, 
        choices=RECORDING_TYPE_CHOICES,
        verbose_name="錄音類型"
    )
    
    file_path = models.FileField(
        upload_to=recording_upload_path,
        verbose_name="檔案路徑",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp3', 'wav', 'ogg', 'mp4', 'avi', 'mov', 'webm']
            )
        ]
    )
    
    thumbnail = models.ImageField(
        upload_to='recordings/thumbnails/',
        null=True,
        blank=True,
        verbose_name="縮圖",
        help_text="影片縮圖或音頻波形圖"
    )
    
    recording_date = models.DateField(
        verbose_name="錄音日期",
        help_text="實際錄製這個影片的日期",
        null=True,
        blank=True
    )
    
    upload_date = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="上傳時間"
    )
    
    week_number = models.PositiveIntegerField(
        verbose_name="第幾週錄音",
        help_text="記錄這是第幾週的練習錄音",
        null=True,
        blank=True
    )
    
    privacy_level = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='private',
        verbose_name="隱私設定",
        help_text="控制誰可以觀看此影片"
    )
    
    duration = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="時長（秒）",
        help_text="錄音或影片的時長"
    )
    
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="檔案大小（bytes）"
    )
    
    notes = models.TextField(
        blank=True, 
        verbose_name="練習筆記",
        help_text="關於這次錄音的備註"
    )
    
    self_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="自我評分",
        help_text="學生對自己演奏的評分（1-5分）"
    )
    
    teacher_score = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="教師評分",
        help_text="教師給出的專業評分",
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    teacher_feedback = models.TextField(
        blank=True,
        verbose_name="教師回饋",
        help_text="教師的詳細回饋與建議"
    )
    
    is_featured = models.BooleanField(
        default=False, 
        verbose_name="是否為精選",
        help_text="是否在展示頁面中突出顯示"
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name="是否公開",
        help_text="是否允許其他人查看"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing',
        verbose_name="處理狀態"
    )
    
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="觀看次數"
    )
    
    class Meta:
        verbose_name = "練習錄音"
        verbose_name_plural = "練習錄音"
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['student_name', 'upload_date']),
            models.Index(fields=['piece', 'week_number']),
            models.Index(fields=['is_featured', 'is_public']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.piece} (第{self.week_number}週)"

    @property
    def file_extension(self):
        """獲取檔案擴展名"""
        if self.file_path:
            return os.path.splitext(self.file_path.name)[1].lower()
        return ''

    @property
    def duration_display(self):
        """格式化顯示時長"""
        if not self.duration:
            return "未知"
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def file_size_display(self):
        """格式化顯示檔案大小"""
        if not self.file_size:
            return "未知"
        
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

    @property
    def average_rating(self):
        """計算平均評分（包括自評、教師評分和他人評分）"""
        ratings = [self.self_rating]
        
        # 如果有教師評分，加入計算（權重較高）
        if self.teacher_score:
            # 教師評分需要轉換為1-5分制，並且算作兩票（權重更高）
            teacher_rating_scaled = (self.teacher_score / 10) * 5
            ratings.extend([teacher_rating_scaled, teacher_rating_scaled])
        
        # 加入評論中的評分
        comments_with_rating = self.comments.filter(rating__isnull=False)
        if comments_with_rating.exists():
            ratings.extend(list(comments_with_rating.values_list('rating', flat=True)))
        
        return sum(ratings) / len(ratings)

    def increment_view_count(self):
        """增加觀看次數"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_teacher_feedback_summary(self):
        """獲取教師回饋摘要"""
        if not self.teacher_feedback:
            return "尚未收到教師回饋"
        
        # 如果回饋內容較長，只顯示前100個字符
        if len(self.teacher_feedback) > 100:
            return self.teacher_feedback[:100] + "..."
        
        return self.teacher_feedback
    
    @property
    def has_teacher_review(self):
        """檢查是否有教師評價"""
        return bool(self.teacher_score or self.teacher_feedback)
    
    @property
    def teacher_score_display(self):
        """格式化顯示教師評分"""
        if not self.teacher_score:
            return "未評分"
        return f"{self.teacher_score:.1f}/10"


class RecordingComment(models.Model):
    """錄音評論模型"""
    
    COMMENTER_TYPE_CHOICES = [
        ('teacher', '教師'),
        ('parent', '家長'),
        ('self', '自己'),
        ('peer', '同伴'),
        ('system', '系統')
    ]
    
    recording = models.ForeignKey(
        PracticeRecording, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="錄音"
    )
    
    commenter_type = models.CharField(
        max_length=10, 
        choices=COMMENTER_TYPE_CHOICES,
        verbose_name="評論者類型"
    )
    
    commenter_name = models.CharField(
        max_length=100, 
        verbose_name="評論者姓名"
    )
    
    comment = models.TextField(
        verbose_name="評論內容"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="評論時間"
    )
    
    rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="評分",
        help_text="可選的評分（1-5分）"
    )
    
    is_encouraging = models.BooleanField(
        default=True, 
        verbose_name="是否為鼓勵性評論",
        help_text="標記為正面鼓勵的評論"
    )
    
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="是否置頂",
        help_text="重要評論可以置頂顯示"
    )
    
    reply_to = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name="回覆給",
        help_text="如果是回覆其他評論"
    )
    
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="點讚數"
    )
    
    class Meta:
        verbose_name = "錄音評論"
        verbose_name_plural = "錄音評論"
        ordering = ['-is_pinned', '-timestamp']
        indexes = [
            models.Index(fields=['recording', 'timestamp']),
            models.Index(fields=['commenter_type']),
            models.Index(fields=['is_pinned', 'is_encouraging']),
        ]

    def __str__(self):
        rating_text = f" ({self.rating}⭐)" if self.rating else ""
        return f"{self.commenter_name} → {self.recording.piece}{rating_text}"

    @property
    def is_recent(self):
        """判斷是否為最近的評論（24小時內）"""
        return (timezone.now() - self.timestamp).total_seconds() < 86400

    @property
    def commenter_display_name(self):
        """格式化顯示評論者名稱"""
        type_icons = {
            'teacher': '👨‍🏫',
            'parent': '👨‍👩‍👧‍👦',
            'self': '👤',
            'peer': '👥',
            'system': '🤖'
        }
        icon = type_icons.get(self.commenter_type, '💬')
        return f"{icon} {self.commenter_name}"

    def get_replies(self):
        """獲取此評論的回覆"""
        return RecordingComment.objects.filter(reply_to=self).order_by('timestamp')


class RecordingProgress(models.Model):
    """錄音進步追蹤模型"""
    
    student_name = models.CharField(
        max_length=100,
        verbose_name="學生姓名",
        db_index=True
    )
    
    piece = models.CharField(
        max_length=200,
        verbose_name="曲目"
    )
    
    first_recording = models.ForeignKey(
        PracticeRecording,
        on_delete=models.CASCADE,
        related_name='progress_as_first',
        verbose_name="第一次錄音"
    )
    
    latest_recording = models.ForeignKey(
        PracticeRecording,
        on_delete=models.CASCADE,
        related_name='progress_as_latest',
        verbose_name="最新錄音"
    )
    
    improvement_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="進步分數",
        help_text="計算得出的進步程度評分"
    )
    
    total_recordings = models.PositiveIntegerField(
        default=0,
        verbose_name="總錄音數"
    )
    
    weeks_span = models.PositiveIntegerField(
        default=0,
        verbose_name="跨越週數"
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="創建時間"
    )
    
    updated_date = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間"
    )
    
    class Meta:
        verbose_name = "錄音進步追蹤"
        verbose_name_plural = "錄音進步追蹤"
        unique_together = ['student_name', 'piece']
        ordering = ['-updated_date']

    def __str__(self):
        return f"{self.student_name} - {self.piece} 進步追蹤"

    @property
    def improvement_percentage(self):
        """計算進步百分比"""
        if not self.improvement_score:
            return 0
        return min(100, max(0, self.improvement_score * 20))  # 轉換為0-100的百分比

    def calculate_improvement(self):
        """計算進步分數"""
        if not self.first_recording or not self.latest_recording:
            return 0
        
        # 基於評分的改善
        first_rating = self.first_recording.average_rating
        latest_rating = self.latest_recording.average_rating
        rating_improvement = latest_rating - first_rating
        
        # 基於教師評分的改善（如果有的話）
        teacher_improvement = 0
        if (self.first_recording.teacher_score and self.latest_recording.teacher_score):
            # 教師評分是1-10分制，需要轉換為1-5分制來與自評對比
            first_teacher = (self.first_recording.teacher_score / 10) * 5
            latest_teacher = (self.latest_recording.teacher_score / 10) * 5
            teacher_improvement = latest_teacher - first_teacher
        
        # 綜合計算（自評權重50%，教師評分權重50%）
        if teacher_improvement:
            self.improvement_score = rating_improvement * 0.5 + teacher_improvement * 0.5
        else:
            self.improvement_score = rating_improvement
        
        self.save()
        return self.improvement_score


class TeacherNotification(models.Model):
    """教師通知模型"""
    
    NOTIFICATION_TYPES = [
        ('new_video', '新影片上傳'),
        ('video_comment', '影片評論'),
        ('student_feedback', '學生回饋'),
        ('system', '系統通知')
    ]
    
    teacher = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name="教師",
        help_text="接收通知的教師"
    )
    
    student = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name="學生",
        help_text="觸發通知的學生",
        related_name='notifications_as_student'
    )
    
    recording = models.ForeignKey(
        PracticeRecording,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="相關影片"
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name="通知類型"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="通知標題"
    )
    
    message = models.TextField(
        verbose_name="通知內容"
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name="是否已讀"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="建立時間"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="閱讀時間"
    )
    
    class Meta:
        verbose_name = "教師通知"
        verbose_name_plural = "教師通知"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.teacher.username} - {self.title}"
    
    def mark_as_read(self):
        """標記為已讀"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def is_recent(self):
        """判斷是否為最近的通知（24小時內）"""
        return (timezone.now() - self.created_at).total_seconds() < 86400