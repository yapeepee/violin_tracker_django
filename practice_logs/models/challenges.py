"""
挑戰與任務系統模型
實現每週挑戰、練習任務、目標設定等功能
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta


class WeeklyChallenge(models.Model):
    """每週挑戰模型"""
    
    CHALLENGE_TYPE_CHOICES = [
        ('practice_time', '練習時間挑戰'),
        ('consecutive_days', '連續練習挑戰'),
        ('skill_focus', '技巧專注挑戰'),
        ('piece_mastery', '曲目精通挑戰'),
        ('rating_improvement', '評分提升挑戰'),
        ('recording_upload', '錄音上傳挑戰'),
        ('variety_practice', '多樣化練習挑戰')
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', '簡單'),
        ('medium', '中等'),
        ('hard', '困難'),
        ('expert', '專家')
    ]
    
    STATUS_CHOICES = [
        ('active', '進行中'),
        ('completed', '已完成'),
        ('failed', '已失敗'),
        ('expired', '已過期')
    ]
    
    student_name = models.CharField(
        max_length=100, 
        verbose_name="學生姓名",
        db_index=True
    )
    
    week_start = models.DateField(
        verbose_name="週開始日期",
        help_text="挑戰週期的開始日期（週一）"
    )
    
    challenge_type = models.CharField(
        max_length=30, 
        choices=CHALLENGE_TYPE_CHOICES,
        verbose_name="挑戰類型"
    )
    
    title = models.CharField(
        max_length=200, 
        verbose_name="挑戰標題"
    )
    
    description = models.TextField(
        verbose_name="挑戰描述",
        help_text="詳細描述挑戰的要求和規則"
    )
    
    target_value = models.FloatField(
        verbose_name="目標數值",
        help_text="需要達到的目標值（如：120分鐘、5天、3.5分等）"
    )
    
    current_progress = models.FloatField(
        default=0, 
        verbose_name="當前進度",
        help_text="目前已達成的數值"
    )
    
    is_completed = models.BooleanField(
        default=False, 
        verbose_name="是否完成"
    )
    
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="完成時間"
    )
    
    points_reward = models.IntegerField(
        default=50, 
        verbose_name="獎勵積分",
        validators=[MinValueValidator(1)]
    )
    
    bonus_points = models.IntegerField(
        default=0,
        verbose_name="額外獎勵積分",
        help_text="提前完成或超額完成的額外獎勵"
    )
    
    created_by = models.CharField(
        max_length=20, 
        choices=[
            ('auto', '自動生成'),
            ('teacher', '教師創建'),
            ('system', '系統推薦')
        ], 
        default='auto', 
        verbose_name="創建者"
    )
    
    difficulty = models.CharField(
        max_length=10, 
        choices=DIFFICULTY_CHOICES,
        default='medium', 
        verbose_name="難度"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="狀態"
    )
    
    priority = models.IntegerField(
        default=1,
        verbose_name="優先級",
        help_text="數字越大優先級越高"
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="創建時間"
    )
    
    class Meta:
        verbose_name = "每週挑戰"
        verbose_name_plural = "每週挑戰"
        unique_together = ['student_name', 'week_start', 'challenge_type']
        ordering = ['-priority', '-week_start']
        indexes = [
            models.Index(fields=['student_name', 'week_start']),
            models.Index(fields=['status', 'week_start']),
            models.Index(fields=['challenge_type']),
        ]

    def __str__(self):
        status_icon = "✅" if self.is_completed else f"{self.progress_percentage:.0f}%"
        return f"{self.student_name} - {self.title} ({status_icon})"

    @property
    def week_end(self):
        """計算週結束日期"""
        return self.week_start + timedelta(days=6)

    @property
    def progress_percentage(self):
        """計算進度百分比"""
        if self.target_value <= 0:
            return 0
        return min(100, (self.current_progress / self.target_value) * 100)

    @property
    def is_expired(self):
        """檢查是否已過期"""
        return date.today() > self.week_end and not self.is_completed

    @property
    def days_remaining(self):
        """計算剩餘天數"""
        remaining = (self.week_end - date.today()).days
        return max(0, remaining)

    @property
    def difficulty_color(self):
        """根據難度返回顏色類"""
        color_map = {
            'easy': 'success',
            'medium': 'primary',
            'hard': 'warning',
            'expert': 'danger'
        }
        return color_map.get(self.difficulty, 'secondary')

    def update_progress(self, new_progress):
        """更新挑戰進度"""
        self.current_progress = new_progress
        
        # 檢查是否完成
        if not self.is_completed and self.current_progress >= self.target_value:
            self.complete_challenge()
        
        # 檢查是否過期
        if self.is_expired and not self.is_completed:
            self.status = 'expired'
        
        self.save()

    def complete_challenge(self):
        """完成挑戰"""
        self.is_completed = True
        self.completion_date = timezone.now()
        self.status = 'completed'
        
        # 計算額外獎勵（提前完成或超額完成）
        if self.current_progress > self.target_value:
            # 超額完成獎勵
            excess_ratio = (self.current_progress - self.target_value) / self.target_value
            self.bonus_points = int(self.points_reward * excess_ratio * 0.5)
        
        # 提前完成獎勵
        if self.days_remaining > 0:
            early_bonus = self.days_remaining * 5  # 每提前一天5分
            self.bonus_points += early_bonus
        
        self.save()

    @property
    def total_points(self):
        """總獎勵積分"""
        return self.points_reward + self.bonus_points

    def get_progress_description(self):
        """獲取進度描述"""
        if self.is_completed:
            return "挑戰完成！"
        elif self.is_expired:
            return "挑戰已過期"
        else:
            return f"進度：{self.current_progress:.1f}/{self.target_value:.1f}"


class PracticeTask(models.Model):
    """練習任務模型"""
    
    TASK_TYPE_CHOICES = [
        ('focus_practice', '專項練習'),
        ('time_goal', '時間目標'),
        ('piece_mastery', '曲目掌握'),
        ('technique_improvement', '技巧改進'),
        ('recording_upload', '錄音上傳'),
        ('theory_study', '樂理學習'),
        ('sight_reading', '視奏練習'),
        ('memorization', '背譜練習')
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '緊急')
    ]
    
    STATUS_CHOICES = [
        ('pending', '待開始'),
        ('in_progress', '進行中'),
        ('completed', '已完成'),
        ('overdue', '已逾期'),
        ('cancelled', '已取消')
    ]
    
    student_name = models.CharField(
        max_length=100, 
        verbose_name="學生姓名",
        db_index=True
    )
    
    task_type = models.CharField(
        max_length=30, 
        choices=TASK_TYPE_CHOICES,
        verbose_name="任務類型"
    )
    
    title = models.CharField(
        max_length=200, 
        verbose_name="任務標題"
    )
    
    description = models.TextField(
        verbose_name="任務描述",
        help_text="詳細描述任務要求和完成標準"
    )
    
    due_date = models.DateField(
        verbose_name="截止日期"
    )
    
    estimated_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="預估所需時間（分鐘）"
    )
    
    is_completed = models.BooleanField(
        default=False, 
        verbose_name="是否完成"
    )
    
    completion_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="完成時間"
    )
    
    completion_notes = models.TextField(
        blank=True,
        verbose_name="完成備註",
        help_text="學生完成任務時的心得或備註"
    )
    
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES,
        default='medium', 
        verbose_name="優先級"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="狀態"
    )
    
    points_reward = models.IntegerField(
        default=25, 
        verbose_name="獎勵積分",
        validators=[MinValueValidator(1)]
    )
    
    assigned_by = models.CharField(
        max_length=100, 
        default='system', 
        verbose_name="分配者",
        help_text="任務的分配者（教師姓名或system）"
    )
    
    related_piece = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="相關曲目",
        help_text="如果任務與特定曲目相關"
    )
    
    related_focus = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="相關練習重點"
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
        verbose_name = "練習任務"
        verbose_name_plural = "練習任務"
        ordering = ['-priority', 'due_date', '-created_date']
        indexes = [
            models.Index(fields=['student_name', 'status']),
            models.Index(fields=['due_date', 'is_completed']),
            models.Index(fields=['task_type']),
            models.Index(fields=['priority', 'due_date']),
        ]

    def __str__(self):
        status_icon = "✅" if self.is_completed else "⏳"
        return f"{status_icon} {self.title} ({self.student_name})"

    @property
    def is_overdue(self):
        """檢查是否已逾期"""
        return date.today() > self.due_date and not self.is_completed

    @property
    def days_until_due(self):
        """計算距離截止日期的天數"""
        delta = self.due_date - date.today()
        return delta.days

    @property
    def urgency_level(self):
        """計算緊急程度"""
        if self.is_completed:
            return "completed"
        elif self.is_overdue:
            return "overdue"
        elif self.days_until_due <= 0:
            return "due_today"
        elif self.days_until_due <= 1:
            return "due_tomorrow"
        elif self.days_until_due <= 3:
            return "due_soon"
        else:
            return "normal"

    @property
    def priority_color(self):
        """根據優先級返回顏色類"""
        color_map = {
            'low': 'secondary',
            'medium': 'primary',
            'high': 'warning',
            'urgent': 'danger'
        }
        return color_map.get(self.priority, 'secondary')

    @property
    def priority_icon(self):
        """根據優先級返回圖示"""
        icon_map = {
            'low': '🔵',
            'medium': '🟡',
            'high': '🟠',
            'urgent': '🔴'
        }
        return icon_map.get(self.priority, '⚪')

    def mark_completed(self, completion_notes=""):
        """標記任務為已完成"""
        self.is_completed = True
        self.completion_date = timezone.now()
        self.completion_notes = completion_notes
        self.status = 'completed'
        self.save()

    def update_status(self):
        """根據當前狀態更新任務狀態"""
        if self.is_completed:
            self.status = 'completed'
        elif self.is_overdue:
            self.status = 'overdue'
        elif not self.is_completed and self.status == 'pending':
            # 檢查是否應該變為進行中
            if self.days_until_due <= 7:  # 一週內的任務自動變為進行中
                self.status = 'in_progress'
        
        self.save()

    @classmethod
    def get_upcoming_tasks(cls, student_name, days=7):
        """獲取即將到期的任務"""
        cutoff_date = date.today() + timedelta(days=days)
        return cls.objects.filter(
            student_name=student_name,
            is_completed=False,
            due_date__lte=cutoff_date
        ).order_by('due_date')

    @classmethod
    def get_overdue_tasks(cls, student_name):
        """獲取逾期任務"""
        return cls.objects.filter(
            student_name=student_name,
            is_completed=False,
            due_date__lt=date.today()
        ).order_by('due_date')


class StudentGoal(models.Model):
    """學生目標模型"""
    
    GOAL_TYPE_CHOICES = [
        ('weekly', '週目標'),
        ('monthly', '月目標'),
        ('semester', '學期目標'),
        ('yearly', '年度目標'),
        ('custom', '自定義目標')
    ]
    
    STATUS_CHOICES = [
        ('active', '進行中'),
        ('achieved', '已達成'),
        ('paused', '暫停'),
        ('cancelled', '已取消')
    ]
    
    student_name = models.CharField(
        max_length=100,
        verbose_name="學生姓名",
        db_index=True
    )
    
    goal_type = models.CharField(
        max_length=20,
        choices=GOAL_TYPE_CHOICES,
        verbose_name="目標類型"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="目標標題"
    )
    
    description = models.TextField(
        verbose_name="目標描述"
    )
    
    target_date = models.DateField(
        verbose_name="目標達成日期"
    )
    
    progress_metric = models.CharField(
        max_length=50,
        verbose_name="進度指標",
        help_text="如：練習時間、掌握曲目數、評分等"
    )
    
    target_value = models.FloatField(
        verbose_name="目標數值"
    )
    
    current_value = models.FloatField(
        default=0,
        verbose_name="當前數值"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="狀態"
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name="是否公開",
        help_text="是否在展示頁面中顯示"
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="創建時間"
    )
    
    achieved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="達成時間"
    )
    
    class Meta:
        verbose_name = "學生目標"
        verbose_name_plural = "學生目標"
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['student_name', 'status']),
            models.Index(fields=['target_date']),
            models.Index(fields=['goal_type']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.title}"

    @property
    def progress_percentage(self):
        """計算進度百分比"""
        if self.target_value <= 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)

    @property
    def days_remaining(self):
        """計算剩餘天數"""
        delta = self.target_date - date.today()
        return max(0, delta.days)

    @property
    def is_overdue(self):
        """檢查是否已逾期"""
        return date.today() > self.target_date and self.status == 'active'

    def update_progress(self, new_value):
        """更新目標進度"""
        self.current_value = new_value
        
        # 檢查是否達成
        if self.current_value >= self.target_value and self.status == 'active':
            self.status = 'achieved'
            self.achieved_date = timezone.now()
        
        self.save()