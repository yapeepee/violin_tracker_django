"""
小提琴練習記錄系統的數據模型定義。
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class PracticeLog(models.Model):
    """
    練習記錄模型。
    
    記錄學生的每次小提琴練習情況，包括：
    - 學生姓名
    - 練習的樂曲
    - 練習時間（分鐘）
    - 練習評分（1-5分）
    - 練習日期
    - 練習重點
    - 練習筆記
    """
    
    # 練習重點選項
    FOCUS_CHOICES = [
        ('technique', '技巧練習'),
        ('expression', '表現力'),
        ('rhythm', '節奏'),
        ('sight_reading', '視奏'),
        ('memorization', '記譜'),
        ('ensemble', '重奏'),
        ('other', '其他')
    ]
    
    student_name = models.CharField(
        max_length=100,
        verbose_name="學生姓名",
        help_text="練習學生的姓名",
        db_index=True
    )
    
    date = models.DateField(
        verbose_name="練習日期",
        help_text="練習的日期",
        default=timezone.now,
        db_index=True
    )
    
    piece = models.CharField(
        max_length=200,
        verbose_name="練習曲目",
        help_text="練習的樂曲名稱"
    )
    
    minutes = models.PositiveIntegerField(
        verbose_name="練習時間（分鐘）",
        help_text="練習時間長度",
        validators=[MinValueValidator(1)]
    )
    
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="練習評分",
        help_text="練習效果自評（1-5分）",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    focus = models.CharField(
        max_length=20,
        choices=FOCUS_CHOICES,
        default='technique',
        verbose_name="練習重點",
        help_text="本次練習的重點項目"
    )
    
    notes = models.TextField(
        verbose_name="練習筆記",
        help_text="練習過程中的觀察和心得",
        blank=True
    )

    class Meta:
        verbose_name = "練習記錄"
        verbose_name_plural = "練習記錄"
        ordering = ['-date', 'student_name']
        indexes = [
            models.Index(fields=['student_name', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.piece} ({self.date})"

    def get_rating_display_emoji(self):
        """返回評分的表情符號表示。"""
        emoji_map = {
            1: "😢",
            2: "😕",
            3: "😊",
            4: "😄",
            5: "🌟"
        }
        return emoji_map.get(self.rating, "❓")
    
    def get_duration_display(self):
        """返回格式化的練習時間。"""
        hours = self.minutes // 60
        minutes = self.minutes % 60
        if hours > 0:
            return f"{hours}小時{minutes}分鐘" if minutes > 0 else f"{hours}小時"
        return f"{minutes}分鐘"
    
    @property
    def is_today(self):
        """判斷是否為今天的練習記錄。"""
        return self.date == timezone.now().date()
    
    @property
    def focus_display(self):
        """返回練習重點的顯示文字。"""
        return dict(self.FOCUS_CHOICES).get(self.focus, '其他')

# Create your models here.
