"""
成就徽章與等級系統模型
實現遊戲化的成就機制，包括徽章獲得、等級進階等功能
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Achievement(models.Model):
    """成就徽章模型"""
    
    CATEGORY_CHOICES = [
        ('persistence', '堅持類'),
        ('quality', '品質類'),
        ('milestone', '里程碑類'),
        ('skill', '技能類'),
        ('challenge', '挑戰類')
    ]
    
    REQUIREMENT_TYPE_CHOICES = [
        ('consecutive_days', '連續練習天數'),
        ('total_hours', '總練習時間'),
        ('average_rating', '平均評分'),
        ('focus_hours', '專項練習時間'),
        ('piece_mastery', '曲目掌握'),
        ('challenge_complete', '挑戰完成'),
        ('total_sessions', '總練習次數'),
        ('week_consistency', '週練習一致性'),
        ('improvement_rate', '進步速度')
    ]
    
    RARITY_CHOICES = [
        ('common', '普通'),
        ('rare', '稀有'),
        ('epic', '史詩'),
        ('legendary', '傳奇')
    ]
    
    name = models.CharField(
        max_length=100, 
        verbose_name="徽章名稱",
        help_text="成就徽章的顯示名稱"
    )
    
    description = models.TextField(
        verbose_name="徽章描述",
        help_text="詳細描述如何獲得此徽章"
    )
    
    icon = models.CharField(
        max_length=50, 
        verbose_name="徽章圖示",
        help_text="Font Awesome圖示類名或emoji",
        default="🏆"
    )
    
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES,
        verbose_name="徽章類別"
    )
    
    requirement_type = models.CharField(
        max_length=30, 
        choices=REQUIREMENT_TYPE_CHOICES,
        verbose_name="達成條件類型"
    )
    
    requirement_value = models.FloatField(
        verbose_name="達成條件數值",
        help_text="需要達到的數值（如：7天、100小時、4.5分等）"
    )
    
    points = models.IntegerField(
        default=10, 
        verbose_name="獲得積分",
        validators=[MinValueValidator(1)]
    )
    
    rarity = models.CharField(
        max_length=10, 
        choices=RARITY_CHOICES,
        default='common', 
        verbose_name="稀有度"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否啟用",
        help_text="停用的徽章不會被檢查或獲得"
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="創建時間"
    )
    
    class Meta:
        verbose_name = "成就徽章"
        verbose_name_plural = "成就徽章"
        ordering = ['category', 'requirement_value']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['requirement_type']),
        ]

    def __str__(self):
        return f"{self.icon} {self.name}"

    @property
    def rarity_color(self):
        """根據稀有度返回對應的顏色類"""
        color_map = {
            'common': 'text-secondary',
            'rare': 'text-primary', 
            'epic': 'text-warning',
            'legendary': 'text-danger'
        }
        return color_map.get(self.rarity, 'text-secondary')

    @property
    def category_display_icon(self):
        """根據類別返回對應的圖示"""
        icon_map = {
            'persistence': '🔥',
            'quality': '⭐',
            'milestone': '🏆',
            'skill': '🎵',
            'challenge': '🎯'
        }
        return icon_map.get(self.category, '🏅')


class StudentAchievement(models.Model):
    """學生成就記錄"""
    
    student_name = models.CharField(
        max_length=100, 
        verbose_name="學生姓名",
        db_index=True
    )
    
    achievement = models.ForeignKey(
        Achievement, 
        on_delete=models.CASCADE, 
        verbose_name="成就"
    )
    
    earned_date = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="獲得時間"
    )
    
    progress = models.FloatField(
        default=0, 
        verbose_name="進度百分比",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="當前達成進度，0-100"
    )
    
    is_earned = models.BooleanField(
        default=False, 
        verbose_name="是否已獲得"
    )
    
    notification_sent = models.BooleanField(
        default=False,
        verbose_name="是否已發送通知"
    )
    
    class Meta:
        verbose_name = "學生成就"
        verbose_name_plural = "學生成就"
        unique_together = ['student_name', 'achievement']
        ordering = ['-earned_date']
        indexes = [
            models.Index(fields=['student_name', 'is_earned']),
            models.Index(fields=['earned_date']),
        ]

    def __str__(self):
        status = "✅" if self.is_earned else f"{self.progress:.0f}%"
        return f"{self.student_name} - {self.achievement.name} ({status})"

    @property
    def progress_percentage(self):
        """返回格式化的進度百分比"""
        return min(100, max(0, self.progress))

    def mark_as_earned(self):
        """標記為已獲得"""
        self.is_earned = True
        self.progress = 100
        self.earned_date = timezone.now()
        self.save()


class StudentLevel(models.Model):
    """學生等級系統"""
    
    TITLE_CHOICES = [
        ('初學者', '初學者'),
        ('入門學徒', '入門學徒'),
        ('練習新手', '練習新手'),
        ('音律探索者', '音律探索者'),
        ('弦音學者', '弦音學者'),
        ('旋律織造者', '旋律織造者'),
        ('和聲大師', '和聲大師'),
        ('音樂詩人', '音樂詩人'),
        ('琴弦聖手', '琴弦聖手'),
        ('樂章傳奇', '樂章傳奇')
    ]
    
    student_name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="學生姓名"
    )
    
    level = models.IntegerField(
        default=1, 
        verbose_name="等級",
        validators=[MinValueValidator(1)]
    )
    
    total_points = models.IntegerField(
        default=0, 
        verbose_name="總積分",
        validators=[MinValueValidator(0)]
    )
    
    current_experience = models.IntegerField(
        default=0, 
        verbose_name="當前經驗值",
        validators=[MinValueValidator(0)]
    )
    
    current_streak = models.IntegerField(
        default=0, 
        verbose_name="連續練習天數",
        validators=[MinValueValidator(0)]
    )
    
    longest_streak = models.IntegerField(
        default=0, 
        verbose_name="最長連續天數",
        validators=[MinValueValidator(0)]
    )
    
    title = models.CharField(
        max_length=50, 
        choices=TITLE_CHOICES,
        default='初學者', 
        verbose_name="稱號"
    )
    
    last_practice_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="最後練習日期"
    )
    
    total_practice_time = models.IntegerField(
        default=0,
        verbose_name="總練習時間（分鐘）",
        validators=[MinValueValidator(0)]
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
        verbose_name = "學生等級"
        verbose_name_plural = "學生等級"
        ordering = ['-level', '-total_points']

    def __str__(self):
        return f"{self.student_name} - Lv.{self.level} {self.title}"

    @property
    def experience_to_next_level(self):
        """計算到下一等級需要的經驗值"""
        return self.get_level_requirement(self.level + 1) - self.current_experience

    @property
    def experience_progress_percentage(self):
        """計算當前等級的經驗值進度百分比"""
        current_level_req = self.get_level_requirement(self.level)
        next_level_req = self.get_level_requirement(self.level + 1)
        
        if next_level_req == current_level_req:
            return 100
            
        progress = (self.current_experience - current_level_req) / (next_level_req - current_level_req)
        return min(100, max(0, progress * 100))

    @staticmethod
    def get_level_requirement(level):
        """計算指定等級需要的總經驗值"""
        if level <= 1:
            return 0
        # 經驗值計算公式：level^2 * 100
        return (level - 1) ** 2 * 100

    def add_experience(self, points):
        """增加經驗值，並檢查是否升級"""
        self.current_experience += points
        self.total_points += points
        
        # 檢查升級
        while self.current_experience >= self.get_level_requirement(self.level + 1):
            self.level_up()
        
        self.save()
        return self.level

    def level_up(self):
        """升級處理"""
        self.level += 1
        
        # 更新稱號
        title_mapping = {
            1: '初學者',
            2: '入門學徒', 
            3: '練習新手',
            5: '音律探索者',
            8: '弦音學者',
            12: '旋律織造者',
            17: '和聲大師',
            23: '音樂詩人',
            30: '琴弦聖手',
            40: '樂章傳奇'
        }
        
        new_title = title_mapping.get(self.level)
        if new_title:
            self.title = new_title

    def update_streak(self, practice_date):
        """更新連續練習天數"""
        if not self.last_practice_date:
            self.current_streak = 1
        elif practice_date == self.last_practice_date:
            # 同一天，不更新
            return
        elif (practice_date - self.last_practice_date).days == 1:
            # 連續的一天
            self.current_streak += 1
        else:
            # 中斷了，重新開始
            self.current_streak = 1
        
        # 更新最長連續記錄
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_practice_date = practice_date
        self.save()