"""
課程管理模型
用於教師管理學生課程、排程和進度追蹤
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime


class LessonSchedule(models.Model):
    """課程排程模型"""
    
    STATUS_CHOICES = [
        ('scheduled', '已排定'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('rescheduled', '已改期'),
        ('no_show', '學生缺席')
    ]
    
    LESSON_TYPES = [
        ('regular', '常規課程'),
        ('makeup', '補課'),
        ('trial', '試聽課'),
        ('masterclass', '大師班'),
        ('group', '團體課'),
        ('online', '線上課程')
    ]
    
    # 基本資訊
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_lessons',
        verbose_name="教師"
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='learning_lessons',
        verbose_name="學生"
    )
    
    # 課程詳情
    lesson_date = models.DateField(
        verbose_name="上課日期"
    )
    
    start_time = models.TimeField(
        verbose_name="開始時間"
    )
    
    duration_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(180)],
        verbose_name="課程時長（分鐘）"
    )
    
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPES,
        default='regular',
        verbose_name="課程類型"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name="狀態"
    )
    
    # 課程內容
    topic = models.CharField(
        max_length=200,
        verbose_name="課程主題",
        help_text="本次課程的主要內容"
    )
    
    objectives = models.TextField(
        blank=True,
        verbose_name="學習目標",
        help_text="本次課程希望達成的目標"
    )
    
    materials_needed = models.TextField(
        blank=True,
        verbose_name="所需教材",
        help_text="學生需要準備的樂譜或其他材料"
    )
    
    # 課後記錄
    lesson_notes = models.TextField(
        blank=True,
        verbose_name="課程筆記",
        help_text="課程中的重點記錄"
    )
    
    homework = models.TextField(
        blank=True,
        verbose_name="課後作業",
        help_text="學生需要完成的練習任務"
    )
    
    student_performance = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="學生表現評分",
        help_text="1-5分評價學生本次課程的表現"
    )
    
    # 進度追蹤
    pieces_covered = models.TextField(
        blank=True,
        verbose_name="練習曲目",
        help_text="本次課程練習的曲目"
    )
    
    skills_focus = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="技巧重點",
        help_text="本次課程著重的技巧"
    )
    
    # 改期資訊
    original_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="原定日期",
        help_text="如果是改期的課程，記錄原本的日期"
    )
    
    reschedule_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="改期原因"
    )
    
    # 提醒設定
    reminder_sent = models.BooleanField(
        default=False,
        verbose_name="已發送提醒"
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
        verbose_name = "課程排程"
        verbose_name_plural = "課程排程"
        ordering = ['-lesson_date', '-start_time']
        indexes = [
            models.Index(fields=['teacher', 'lesson_date']),
            models.Index(fields=['student', 'lesson_date']),
            models.Index(fields=['status']),
            models.Index(fields=['lesson_date', 'start_time']),
        ]
        unique_together = ['teacher', 'lesson_date', 'start_time']
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson_date} {self.start_time}"
    
    @property
    def end_time(self):
        """計算課程結束時間"""
        start_datetime = datetime.datetime.combine(
            self.lesson_date, 
            self.start_time
        )
        end_datetime = start_datetime + datetime.timedelta(minutes=self.duration_minutes)
        return end_datetime.time()
    
    @property
    def is_past(self):
        """檢查課程是否已過期"""
        lesson_datetime = datetime.datetime.combine(self.lesson_date, self.start_time)
        return lesson_datetime < timezone.now()
    
    @property
    def is_today(self):
        """檢查是否為今天的課程"""
        return self.lesson_date == timezone.now().date()
    
    @property
    def is_upcoming(self):
        """檢查是否為即將到來的課程"""
        return self.lesson_date > timezone.now().date()
    
    def mark_completed(self):
        """標記課程為已完成"""
        self.status = 'completed'
        self.save()
    
    def cancel(self, reason=''):
        """取消課程"""
        self.status = 'cancelled'
        if reason:
            self.reschedule_reason = reason
        self.save()


class StudentProgress(models.Model):
    """學生進度追蹤模型"""
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name="學生"
    )
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_progress_records',
        verbose_name="教師"
    )
    
    # 技能評估
    technique_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="技巧分數"
    )
    
    musicality_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="音樂性分數"
    )
    
    rhythm_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="節奏分數"
    )
    
    sight_reading_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="視譜能力分數"
    )
    
    theory_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="樂理知識分數"
    )
    
    # 進度里程碑
    current_level = models.CharField(
        max_length=50,
        verbose_name="當前程度",
        help_text="例如：初級、中級、高級"
    )
    
    current_pieces = models.TextField(
        blank=True,
        verbose_name="目前練習曲目"
    )
    
    completed_pieces = models.TextField(
        blank=True,
        verbose_name="已完成曲目"
    )
    
    # 目標設定
    short_term_goals = models.TextField(
        blank=True,
        verbose_name="短期目標",
        help_text="1-3個月內的目標"
    )
    
    long_term_goals = models.TextField(
        blank=True,
        verbose_name="長期目標",
        help_text="6個月以上的目標"
    )
    
    # 練習統計
    average_practice_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="平均每日練習時間（分鐘）"
    )
    
    practice_consistency = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="練習穩定度（%）",
        help_text="過去30天的練習頻率"
    )
    
    # 成就和獎勵
    achievements = models.TextField(
        blank=True,
        verbose_name="獲得成就",
        help_text="考試成績、比賽獎項等"
    )
    
    # 教師評語
    teacher_comments = models.TextField(
        blank=True,
        verbose_name="教師評語",
        help_text="對學生整體進度的評價"
    )
    
    # 更新記錄
    last_assessment_date = models.DateField(
        default=timezone.now,
        verbose_name="最後評估日期"
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
        verbose_name = "學生進度"
        verbose_name_plural = "學生進度"
        unique_together = ['student', 'teacher']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['student', 'teacher']),
            models.Index(fields=['last_assessment_date']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - 進度記錄"
    
    @property
    def overall_score(self):
        """計算總體評分"""
        scores = [
            self.technique_score,
            self.musicality_score,
            self.rhythm_score,
            self.sight_reading_score,
            self.theory_score
        ]
        return sum(scores) / len(scores)
    
    @property
    def progress_percentage(self):
        """計算進度百分比（基於評分）"""
        return (self.overall_score / 10) * 100
    
    def get_skill_radar_data(self):
        """獲取技能雷達圖數據"""
        return {
            '技巧': self.technique_score,
            '音樂性': self.musicality_score,
            '節奏': self.rhythm_score,
            '視譜': self.sight_reading_score,
            '樂理': self.theory_score
        }


class LessonNote(models.Model):
    """課程筆記模型 - 用於詳細記錄每次課程"""
    
    lesson = models.OneToOneField(
        LessonSchedule,
        on_delete=models.CASCADE,
        related_name='detailed_note',
        verbose_name="相關課程"
    )
    
    # 課前準備
    pre_lesson_plan = models.TextField(
        blank=True,
        verbose_name="課前計畫"
    )
    
    # 課程記錄
    warm_up_exercises = models.TextField(
        blank=True,
        verbose_name="熱身練習"
    )
    
    technique_work = models.TextField(
        blank=True,
        verbose_name="技巧練習"
    )
    
    repertoire_covered = models.TextField(
        blank=True,
        verbose_name="曲目練習"
    )
    
    # 問題與解決
    problems_identified = models.TextField(
        blank=True,
        verbose_name="發現的問題"
    )
    
    solutions_provided = models.TextField(
        blank=True,
        verbose_name="提供的解決方案"
    )
    
    # 進步記錄
    improvements_noted = models.TextField(
        blank=True,
        verbose_name="進步之處"
    )
    
    areas_need_work = models.TextField(
        blank=True,
        verbose_name="需要加強的地方"
    )
    
    # 下次課程計畫
    next_lesson_plan = models.TextField(
        blank=True,
        verbose_name="下次課程計畫"
    )
    
    # 家長溝通
    parent_communication = models.TextField(
        blank=True,
        verbose_name="家長溝通記錄",
        help_text="需要告知家長的事項"
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
        verbose_name = "課程詳細筆記"
        verbose_name_plural = "課程詳細筆記"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"筆記 - {self.lesson}"