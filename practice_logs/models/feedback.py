"""
教師回饋系統模型
優雅的師生互動平台
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .practice import PracticeLog


class TeacherFeedback(models.Model):
    """
    教師回饋模型 - 如音樂廳中的大師指導
    
    為每個練習記錄提供專業的教師評價和建議，
    營造溫暖而專業的教學氛圍。
    """
    
    # 回饋類型選項
    FEEDBACK_TYPE_CHOICES = [
        ('encouragement', '鼓勵讚美 🌟'),
        ('technical_guidance', '技巧指導 🎼'),
        ('artistic_advice', '藝術建議 🎨'),
        ('practice_suggestion', '練習建議 📝'),
        ('performance_feedback', '演出回饋 🎭'),
    ]
    
    # 掌握程度評估
    MASTERY_LEVEL_CHOICES = [
        ('beginner', '初學階段 🌱'),
        ('developing', '發展中 🌿'),
        ('proficient', '熟練 🌳'),
        ('advanced', '進階 🏆'),
        ('masterful', '大師級 👑'),
    ]
    
    # 關聯到練習記錄
    practice_log = models.OneToOneField(
        PracticeLog,
        on_delete=models.CASCADE,
        related_name='teacher_feedback',
        verbose_name="對應練習記錄"
    )
    
    # 教師資訊
    teacher_name = models.CharField(
        max_length=100,
        verbose_name="教師姓名",
        help_text="提供回饋的教師",
        db_index=True
    )
    
    # ===== 回饋內容 =====
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPE_CHOICES,
        default='encouragement',
        verbose_name="回饋類型",
        help_text="選擇回饋的主要類型"
    )
    
    feedback_text = models.TextField(
        verbose_name="文字回饋",
        help_text="給學生的詳細建議和評語",
        max_length=1000
    )
    
    voice_feedback = models.FileField(
        upload_to='teacher_voice_feedback/%Y/%m/',
        verbose_name="語音回饋",
        help_text="錄製語音回饋 (選填)",
        blank=True,
        null=True
    )
    
    # ===== 技術評估 =====
    technique_rating = models.PositiveIntegerField(
        verbose_name="技巧評分",
        help_text="技巧掌握程度 (1-5星)",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    
    musicality_rating = models.PositiveIntegerField(
        verbose_name="音樂性評分", 
        help_text="音樂表現力 (1-5星)",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    
    progress_rating = models.PositiveIntegerField(
        verbose_name="進步程度",
        help_text="與上次相比的進步 (1-5星)",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    
    # ===== 學習狀態評估 =====
    mastery_level = models.CharField(
        max_length=15,
        choices=MASTERY_LEVEL_CHOICES,
        default='developing',
        verbose_name="掌握程度",
        help_text="當前技能掌握水平"
    )
    
    need_retry = models.BooleanField(
        default=False,
        verbose_name="需要重練",
        help_text="勾選表示建議學生重新練習此部分"
    )
    
    mastered_well = models.BooleanField(
        default=False,
        verbose_name="掌握良好",
        help_text="勾選表示學生已很好掌握此部分"
    )
    
    # ===== 互動設定 =====
    notify_parents = models.BooleanField(
        default=False,
        verbose_name="通知家長",
        help_text="是否將此回饋發送給家長"
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name="公開展示",
        help_text="是否在班級中公開展示 (鼓勵用)"
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name="精選回饋",
        help_text="標記為精選，將在首頁展示"
    )
    
    # ===== 練習建議 =====
    suggested_focus = models.CharField(
        max_length=200,
        verbose_name="建議練習重點",
        help_text="下次練習應該專注的方面",
        blank=True
    )
    
    suggested_pieces = models.TextField(
        verbose_name="推薦曲目",
        help_text="推薦學生練習的其他曲目",
        blank=True,
        max_length=300
    )
    
    practice_tips = models.TextField(
        verbose_name="練習小貼士",
        help_text="具體的練習方法和技巧提示",
        blank=True,
        max_length=500
    )
    
    # ===== 時間戳記 =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="回饋時間"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="最後更新"
    )
    
    # ===== 互動追蹤 =====
    student_read = models.BooleanField(
        default=False,
        verbose_name="學生已讀",
        help_text="學生是否已查看此回饋"
    )
    
    parent_read = models.BooleanField(
        default=False,
        verbose_name="家長已讀",
        help_text="家長是否已查看此回饋"
    )
    
    student_response = models.TextField(
        verbose_name="學生回覆",
        help_text="學生對回饋的回應",
        blank=True,
        max_length=300
    )

    class Meta:
        verbose_name = "教師回饋"
        verbose_name_plural = "教師回饋"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher_name', 'created_at']),
            models.Index(fields=['practice_log', 'created_at']),
            models.Index(fields=['mastery_level']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['notify_parents']),
        ]

    def __str__(self):
        return f"{self.teacher_name} → {self.practice_log.student_name} ({self.get_feedback_type_display()})"
    
    # ===== 顯示方法 =====
    def get_overall_rating(self):
        """計算整體評分平均值。"""
        return round((self.technique_rating + self.musicality_rating + self.progress_rating) / 3, 1)
    
    def get_rating_stars_display(self, rating_type):
        """返回星級評分的音符表示。"""
        rating_map = {
            'technique': self.technique_rating,
            'musicality': self.musicality_rating,
            'progress': self.progress_rating,
            'overall': self.get_overall_rating()
        }
        rating = rating_map.get(rating_type, 0)
        return '🎵' * int(rating) + '♪' * (5 - int(rating))
    
    def get_status_display(self):
        """返回學習狀態的圖示化描述。"""
        if self.mastered_well:
            return "✅ 掌握優秀"
        elif self.need_retry:
            return "🔄 建議重練"
        else:
            return "📚 持續練習"
    
    def get_feedback_summary(self):
        """生成回饋摘要 (前50字)。"""
        return self.feedback_text[:50] + "..." if len(self.feedback_text) > 50 else self.feedback_text
    
    @property
    def is_positive(self):
        """判斷是否為正面回饋。"""
        return self.get_overall_rating() >= 4.0 or self.mastered_well
    
    @property
    def is_recent(self):
        """判斷是否為最近一週的回饋。"""
        from datetime import timedelta
        return (timezone.now() - self.created_at) <= timedelta(days=7)
    
    @property
    def has_voice_feedback(self):
        """檢查是否有語音回饋。"""
        return bool(self.voice_feedback)
    
    # ===== 統計方法 =====
    @classmethod
    def get_teacher_stats(cls, teacher_name, days=30):
        """獲取教師回饋統計。"""
        from datetime import timedelta
        recent_feedbacks = cls.objects.filter(
            teacher_name=teacher_name,
            created_at__gte=timezone.now() - timedelta(days=days)
        )
        
        return {
            'total_feedbacks': recent_feedbacks.count(),
            'average_rating': recent_feedbacks.aggregate(
                models.Avg('technique_rating')
            )['technique_rating__avg'] or 0,
            'positive_rate': recent_feedbacks.filter(
                technique_rating__gte=4
            ).count() / max(recent_feedbacks.count(), 1) * 100
        }
    
    @classmethod
    def get_student_feedback_summary(cls, student_name, days=30):
        """獲取學生收到的回饋摘要。"""
        from datetime import timedelta
        from django.db.models import Avg, Count
        
        recent_feedbacks = cls.objects.filter(
            practice_log__student_name=student_name,
            created_at__gte=timezone.now() - timedelta(days=days)
        )
        
        return {
            'total_received': recent_feedbacks.count(),
            'unread_count': recent_feedbacks.filter(student_read=False).count(),
            'average_technique': recent_feedbacks.aggregate(
                Avg('technique_rating')
            )['technique_rating__avg'] or 0,
            'average_musicality': recent_feedbacks.aggregate(
                Avg('musicality_rating')
            )['musicality_rating__avg'] or 0,
            'mastered_count': recent_feedbacks.filter(mastered_well=True).count(),
            'retry_count': recent_feedbacks.filter(need_retry=True).count(),
        }