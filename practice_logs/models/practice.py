"""
練習記錄模型 - 從原有models.py遷移過來
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
    
    # 心情選擇選項 - 古典樂風格
    MOOD_CHOICES = [
        ('joyful', '愉悅如莫札特 😊'),
        ('peaceful', '平靜如德布西 😌'),
        ('focused', '專注如巴哈 🎯'),
        ('melancholic', '憂鬱如蕭邦 😔'),
        ('passionate', '熱情如柴可夫斯基 🔥'),
        ('contemplative', '沉思如貝多芬 🤔')
    ]
    
    # 練習重點對應的評分維度配置
    FOCUS_RATING_CONFIG = {
        'technique': {
            'name': '技巧練習',
            'ratings': [
                ('technique_bow_control', '運弓控制', '運弓技巧和控制力'),
                ('technique_finger_position', '按弦準確度', '左手按弦位置準確性'),
                ('technique_intonation', '音準', '音高準確度'),
            ]
        },
        'expression': {
            'name': '表現力',
            'ratings': [
                ('expression_dynamics', '力度變化', '音量強弱的表現控制'),
                ('expression_phrasing', '樂句處理', '音樂線條與樂句表現'),
                ('expression_emotion', '情感表達', '音樂情感的傳達'),
            ]
        },
        'rhythm': {
            'name': '節奏',
            'ratings': [
                ('rhythm_tempo_stability', '速度穩定度', '節拍速度保持穩定'),
                ('rhythm_pattern_accuracy', '節奏型準確度', '複雜節奏型的準確演奏'),
                ('technique_intonation', '音準配合', '節奏中的音準維持'),
            ]
        },
        'sight_reading': {
            'name': '視奏',
            'ratings': [
                ('sight_reading_fluency', '視奏流暢度', '第一次看譜演奏的流暢程度'),
                ('sight_reading_accuracy', '視奏準確度', '音符、節奏讀譜準確度'),
                ('rhythm_tempo_stability', '速度控制', '視奏時的速度穩定性'),
            ]
        },
        'memorization': {
            'name': '記譜',
            'ratings': [
                ('memorization_stability', '記憶穩定度', '背譜演奏的穩定程度'),
                ('memorization_confidence', '記譜信心', '背譜演奏的自信程度'),
                ('technique_intonation', '音準穩定', '背譜時的音準維持'),
            ]
        },
        'ensemble': {
            'name': '重奏',
            'ratings': [
                ('ensemble_listening', '聆聽配合', '與其他聲部的聆聽配合'),
                ('ensemble_timing', '時間同步', '與其他樂器的時間同步'),
                ('expression_dynamics', '音量平衡', '在合奏中的音量控制'),
            ]
        },
        'other': {
            'name': '其他',
            'ratings': [
                ('technique_bow_control', '技巧表現', '整體技巧展現'),
                ('expression_emotion', '音樂表現', '整體音樂性表現'),
                ('rhythm_tempo_stability', '穩定度', '整體演奏穩定性'),
            ]
        }
    }
    
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
    
    # ===== 新增：影片上傳系統 =====
    video_file = models.FileField(
        upload_to='practice_videos/%Y/%m/',
        verbose_name="練習影片",
        help_text="上傳練習過程的影片記錄",
        blank=True,
        null=True
    )
    
    video_thumbnail = models.ImageField(
        upload_to='video_thumbnails/%Y/%m/',
        verbose_name="影片縮圖",
        help_text="自動生成的影片預覽圖",
        blank=True,
        null=True
    )
    
    # ===== 新增：情緒追蹤 =====
    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        verbose_name="練習心情",
        help_text="練習時的心情狀態",
        default='focused',
        blank=True
    )
    
    # ===== 新增：針對性評分系統 (依練習重點而定) =====
    # 技巧練習相關評分
    technique_bow_control = models.PositiveIntegerField(
        verbose_name="運弓控制",
        help_text="運弓技巧控制度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    technique_finger_position = models.PositiveIntegerField(
        verbose_name="按弦準確度",
        help_text="左手按弦位置準確度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    technique_intonation = models.PositiveIntegerField(
        verbose_name="音準",
        help_text="音準準確度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    # 表現力相關評分
    expression_dynamics = models.PositiveIntegerField(
        verbose_name="力度變化",
        help_text="音量強弱控制（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    expression_phrasing = models.PositiveIntegerField(
        verbose_name="樂句處理",
        help_text="音樂線條與樂句表現（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    expression_emotion = models.PositiveIntegerField(
        verbose_name="情感表達",
        help_text="音樂情感傳達（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    # 節奏相關評分
    rhythm_tempo_stability = models.PositiveIntegerField(
        verbose_name="速度穩定度",
        help_text="節拍速度保持穩定（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    rhythm_pattern_accuracy = models.PositiveIntegerField(
        verbose_name="節奏型準確度",
        help_text="複雜節奏型的準確演奏（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    # 視奏相關評分
    sight_reading_fluency = models.PositiveIntegerField(
        verbose_name="視奏流暢度",
        help_text="第一次看譜演奏的流暢程度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    sight_reading_accuracy = models.PositiveIntegerField(
        verbose_name="視奏準確度",
        help_text="音符、節奏讀譜準確度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    # 記譜相關評分
    memorization_stability = models.PositiveIntegerField(
        verbose_name="記憶穩定度",
        help_text="背譜演奏的穩定程度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    memorization_confidence = models.PositiveIntegerField(
        verbose_name="記譜信心",
        help_text="背譜演奏的自信程度（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    # 重奏相關評分
    ensemble_listening = models.PositiveIntegerField(
        verbose_name="聆聽配合",
        help_text="與其他聲部的聆聽配合（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    ensemble_timing = models.PositiveIntegerField(
        verbose_name="時間同步",
        help_text="與其他樂器的時間同步（1-5星）",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        blank=True,
        null=True
    )
    
    # ===== 新增：給老師的留言 =====
    student_notes_to_teacher = models.TextField(
        verbose_name="給老師的話",
        help_text="想對老師說的話或需要幫助的地方",
        blank=True,
        max_length=500
    )
    
    # ===== 新增：檔案元資料 =====
    video_duration = models.DurationField(
        verbose_name="影片長度",
        help_text="影片播放時間長度",
        blank=True,
        null=True
    )
    
    file_size = models.PositiveIntegerField(
        verbose_name="檔案大小(MB)",
        help_text="影片檔案大小",
        blank=True,
        null=True
    )
    
    # ===== 新增：時間戳記 =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="建立時間",
        null=True,
        blank=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "練習記錄"
        verbose_name_plural = "練習記錄"
        ordering = ['-date', 'student_name']
        indexes = [
            models.Index(fields=['student_name', 'date'], name='idx_stud_date'),
            models.Index(fields=['date'], name='idx_date'),
            models.Index(fields=['student_name', 'piece'], name='idx_stud_piece'),
            models.Index(fields=['mood'], name='idx_mood'),
            models.Index(fields=['created_at'], name='idx_created'),
            models.Index(fields=['student_name', 'created_at'], name='idx_stud_created'),
            models.Index(fields=['focus', 'date'], name='idx_focus_date'),
            models.Index(fields=['rating', 'date'], name='idx_rating_date'),
            models.Index(fields=['-date', 'student_name'], name='idx_date_desc_stud'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(minutes__gte=1) & models.Q(minutes__lte=600),
                name='valid_practice_minutes'
            ),
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='valid_rating_range'
            ),
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
    
    # ===== 新增：心情和評分相關方法 =====
    def get_mood_display_emoji(self):
        """返回心情的表情符號和描述。"""
        mood_map = {
            'joyful': '😊 愉悅如莫札特',
            'peaceful': '😌 平靜如德布西', 
            'focused': '🎯 專注如巴哈',
            'melancholic': '😔 憂鬱如蕭邦',
            'passionate': '🔥 熱情如柴可夫斯基',
            'contemplative': '🤔 沉思如貝多芬'
        }
        return mood_map.get(self.mood, '🎵 音樂心情')
    
    def get_focus_ratings(self):
        """根據練習重點獲取對應的評分數據。"""
        if self.focus not in self.FOCUS_RATING_CONFIG:
            return []
        
        config = self.FOCUS_RATING_CONFIG[self.focus]
        ratings = []
        
        for field_name, display_name, description in config['ratings']:
            value = getattr(self, field_name, None)
            if value is not None:
                ratings.append({
                    'field': field_name,
                    'name': display_name,
                    'description': description,
                    'value': value,
                    'stars': self.get_rating_stars_for_field(field_name)
                })
        
        return ratings
    
    def get_rating_stars_for_field(self, field_name):
        """返回特定評分欄位的星級視覺化表示。"""
        value = getattr(self, field_name, 0) or 0
        full_stars = '♪' * value
        empty_stars = '♫' * (5 - value)
        return full_stars + empty_stars
    
    def get_overall_performance_score(self):
        """計算整體表現分數 (基於練習重點的相關評分平均)。"""
        focus_ratings = self.get_focus_ratings()
        if not focus_ratings:
            return self.rating  # 回到原始評分
        
        total_score = sum(rating['value'] for rating in focus_ratings if rating['value'])
        valid_ratings = len([r for r in focus_ratings if r['value']])
        
        if valid_ratings == 0:
            return self.rating
        
        return round(total_score / valid_ratings, 1)
    
    def get_focus_strengths_and_weaknesses(self):
        """分析練習重點的強項和弱項。"""
        focus_ratings = self.get_focus_ratings()
        if not focus_ratings:
            return {'strengths': [], 'weaknesses': []}
        
        strengths = [r for r in focus_ratings if r['value'] >= 4]
        weaknesses = [r for r in focus_ratings if r['value'] <= 2]
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'overall_score': self.get_overall_performance_score()
        }
    
    def get_video_duration_display(self):
        """返回格式化的影片時長。"""
        if not self.video_duration:
            return "無影片"
        
        total_seconds = int(self.video_duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_file_size_display(self):
        """返回格式化的檔案大小。"""
        if not self.file_size:
            return "未知大小"
        
        if self.file_size < 1024:
            return f"{self.file_size} MB"
        else:
            return f"{self.file_size / 1024:.1f} GB"
    
    @property
    def has_video(self):
        """檢查是否有上傳影片。"""
        return bool(self.video_file)
    
    @property
    def has_teacher_feedback(self):
        """檢查是否有教師回饋。"""
        return hasattr(self, 'teacher_feedback') and self.teacher_feedback is not None
    
    @property 
    def is_recent(self):
        """檢查是否為最近三天內的練習記錄。"""
        from datetime import timedelta
        return (timezone.now().date() - self.date) <= timedelta(days=3)

    @classmethod
    def get_piece_progress(cls, student_name, piece):
        """計算特定曲目的練習進步情況"""
        logs = cls.objects.filter(
            student_name=student_name,
            piece=piece
        ).order_by('date')
        
        if not logs:
            return 0
        
        # 計算評分的移動平均
        window_size = 3
        ratings = list(logs.values_list('rating', flat=True))
        
        if len(ratings) < 2:
            return 0
            
        # 計算開始和結束的移動平均
        start_avg = sum(ratings[:window_size]) / min(window_size, len(ratings))
        end_avg = sum(ratings[-window_size:]) / min(window_size, len(ratings))
        
        return end_avg - start_avg

    @classmethod
    def get_practice_efficiency(cls, student_name, piece):
        """計算練習效率（評分提升/練習時間）"""
        progress = cls.get_piece_progress(student_name, piece)
        total_time = cls.objects.filter(
            student_name=student_name,
            piece=piece
        ).aggregate(total_minutes=models.Sum('minutes'))['total_minutes'] or 0
        
        if total_time == 0:
            return 0
            
        return progress / total_time