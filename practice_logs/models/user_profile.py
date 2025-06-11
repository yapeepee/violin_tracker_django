"""
用戶資料擴展模型 - 基於Django內建User模型
"""

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from PIL import Image
import os


class UserProfile(models.Model):
    """
    用戶資料擴展模型，與Django內建User一對一關聯
    """
    
    # 用戶角色選項
    ROLE_CHOICES = [
        ('student', '學生'),
        ('teacher', '教師'),
        ('admin', '系統管理員'),
        ('parent', '家長'),
    ]
    
    # 學習程度選項
    SKILL_LEVEL_CHOICES = [
        ('beginner', '初學者'),
        ('intermediate', '中級'),
        ('advanced', '高級'),
        ('professional', '專業級'),
    ]
    
    # 與Django內建User的一對一關聯
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="用戶"
    )
    
    # 基本資訊
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name="用戶角色",
        help_text="選擇用戶在系統中的角色"
    )
    
    chinese_name = models.CharField(
        max_length=50,
        verbose_name="中文姓名",
        help_text="用戶的中文姓名",
        blank=True
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="電話號碼格式：+999999999，最多15位數字"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name="聯絡電話"
    )
    
    # 個人資料
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="出生日期"
    )
    
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="頭像",
        help_text="上傳個人頭像圖片"
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="個人簡介",
        help_text="簡短描述自己的音樂背景或學習目標"
    )
    
    # 音樂相關資訊
    skill_level = models.CharField(
        max_length=20,
        choices=SKILL_LEVEL_CHOICES,
        default='beginner',
        verbose_name="小提琴程度",
        help_text="當前的小提琴演奏程度"
    )
    
    learning_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="開始學習日期",
        help_text="開始學習小提琴的日期"
    )
    
    # 學習目標與喜好
    learning_goals = models.TextField(
        blank=True,
        max_length=1000,
        verbose_name="學習目標",
        help_text="描述學習小提琴的目標和期望"
    )
    
    favorite_composers = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="喜愛的作曲家",
        help_text="例如：巴哈、莫札特、貝多芬"
    )
    
    # 隱私設定
    profile_public = models.BooleanField(
        default=False,
        verbose_name="公開個人資料",
        help_text="是否允許其他用戶查看個人資料"
    )
    
    practice_logs_public = models.BooleanField(
        default=False,
        verbose_name="公開練習記錄",
        help_text="是否允許其他用戶查看練習記錄"
    )
    
    # 通知設定
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="電子郵件通知",
        help_text="接收系統通知和提醒"
    )
    
    practice_reminders = models.BooleanField(
        default=True,
        verbose_name="練習提醒",
        help_text="接收練習提醒通知"
    )
    
    # 教師專業資訊（僅教師使用）
    specialization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="專業領域",
        help_text="教師的專業領域，例如：古典音樂、流行音樂、室內樂等"
    )
    
    years_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="教學經驗年數",
        help_text="教學經驗的年數"
    )
    
    education_background = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="教育背景",
        help_text="教師的音樂教育背景和資歷"
    )
    
    teaching_philosophy = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name="教學理念",
        help_text="教師的教學方法和理念"
    )
    
    # 學生分組（教師使用）
    student_group = models.CharField(
        max_length=50,
        blank=True,
        default='ungrouped',
        verbose_name="學生分組",
        help_text="教師為學生設定的分組"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更新時間")
    
    class Meta:
        verbose_name = "用戶資料"
        verbose_name_plural = "用戶資料"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['chinese_name']),
            models.Index(fields=['skill_level']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        display_name = self.display_name
        return f"{display_name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """自動處理頭像圖片大小"""
        super().save(*args, **kwargs)
        
        if self.avatar:
            self._resize_avatar()
    
    def _resize_avatar(self):
        """調整頭像圖片大小"""
        try:
            img = Image.open(self.avatar.path)
            
            # 限制最大尺寸為 300x300
            max_size = (300, 300)
            if img.height > max_size[0] or img.width > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(self.avatar.path, optimize=True, quality=95)
        except Exception:
            # 如果圖片處理失敗，忽略錯誤
            pass
    
    @property
    def display_name(self):
        """返回顯示用的姓名"""
        return self.chinese_name or self.user.username
    
    @property
    def age(self):
        """計算年齡"""
        if not self.birth_date:
            return None
        
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def learning_duration_days(self):
        """計算學習天數"""
        if not self.learning_start_date:
            return None
        
        today = timezone.now().date()
        return (today - self.learning_start_date).days
    
    @property
    def is_student(self):
        """檢查是否為學生"""
        return self.role == 'student'
    
    @property
    def is_teacher(self):
        """檢查是否為教師"""
        return self.role == 'teacher'
    
    @property
    def is_parent(self):
        """檢查是否為家長"""
        return self.role == 'parent'
    
    def get_practice_stats(self):
        """獲取練習統計數據"""
        from .practice import PracticeLog
        
        if not self.is_student:
            return None
            
        practice_logs = PracticeLog.objects.filter(student_name=self.display_name)
        
        return {
            'total_sessions': practice_logs.count(),
            'total_minutes': practice_logs.aggregate(
                total=models.Sum('minutes')
            )['total'] or 0,
            'average_rating': practice_logs.aggregate(
                avg=models.Avg('rating')
            )['avg'] or 0,
            'recent_sessions': practice_logs.filter(
                date__gte=timezone.now().date() - timezone.timedelta(days=7)
            ).count()
        }
    
    def get_teaching_stats(self):
        """獲取教學統計數據（針對教師）"""
        if not self.is_teacher:
            return None
            
        from .feedback import TeacherFeedback
        
        teacher_name = self.display_name or self.user.username
        
        feedback_count = TeacherFeedback.objects.filter(
            teacher_name=teacher_name
        ).count()
        
        return {
            'total_feedback_given': feedback_count,
            'students_taught': TeacherFeedback.objects.filter(
                teacher_name=teacher_name
            ).values('practice_log__student_name').distinct().count()
        }


class StudentTeacherRelation(models.Model):
    """
    學生-教師關係模型
    管理學生與教師之間的師生關係
    """
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_relations',
        verbose_name="學生"
    )
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_relations',
        verbose_name="教師"
    )
    
    start_date = models.DateField(
        default=timezone.now,
        verbose_name="開始時間",
        help_text="師生關係建立的時間"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="結束時間",
        help_text="師生關係結束的時間（如果適用）"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="關係狀態",
        help_text="師生關係是否仍然有效"
    )
    
    notes = models.TextField(
        blank=True,
        max_length=500,
        verbose_name="備註",
        help_text="關於這個師生關係的特殊說明"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "師生關係"
        verbose_name_plural = "師生關係"
        unique_together = ['student', 'teacher', 'start_date']
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['start_date']),
        ]
    
    def __str__(self):
        status = "進行中" if self.is_active else "已結束"
        student_name = getattr(self.student.profile, 'display_name', self.student.username)
        teacher_name = getattr(self.teacher.profile, 'display_name', self.teacher.username)
        return f"{student_name} - {teacher_name} ({status})"
    
    @property
    def duration_days(self):
        """計算師生關係持續天數"""
        end_date = self.end_date or timezone.now().date()
        return (end_date - self.start_date).days
    
    @property
    def is_current(self):
        """檢查關係是否為當前有效"""
        if not self.is_active:
            return False
        
        if self.end_date and self.end_date < timezone.now().date():
            return False
        
        return True


class UserLoginLog(models.Model):
    """
    用戶登入記錄模型
    追蹤用戶的登入活動以提升安全性
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_logs',
        verbose_name="用戶"
    )
    
    login_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="登入時間"
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name="IP位址"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="瀏覽器資訊"
    )
    
    login_successful = models.BooleanField(
        default=True,
        verbose_name="登入成功",
        help_text="登入是否成功"
    )
    
    logout_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="登出時間"
    )
    
    session_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name="會話時長"
    )
    
    class Meta:
        verbose_name = "登入記錄"
        verbose_name_plural = "登入記錄"
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'login_time']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['login_time']),
        ]
    
    def __str__(self):
        status = "成功" if self.login_successful else "失敗"
        display_name = getattr(self.user.profile, 'display_name', self.user.username)
        return f"{display_name} - {self.login_time.strftime('%Y-%m-%d %H:%M')} ({status})"
    
    def save(self, *args, **kwargs):
        """計算會話時長"""
        if self.logout_time and self.login_time:
            self.session_duration = self.logout_time - self.login_time
        
        super().save(*args, **kwargs)
    
    @property
    def session_duration_minutes(self):
        """返回會話時長（分鐘）"""
        if not self.session_duration:
            return None
        
        return int(self.session_duration.total_seconds() / 60)


# 信號處理器：自動為新用戶創建Profile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """當創建新用戶時，自動創建對應的UserProfile"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存用戶時，同時保存UserProfile"""
    if hasattr(instance, 'profile'):
        instance.profile.save()