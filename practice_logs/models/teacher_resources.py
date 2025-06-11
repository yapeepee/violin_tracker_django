"""
教師資源管理模型
用於管理教學材料、樂譜、影片等資源
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os


class ResourceCategory(models.Model):
    """資源分類模型"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="分類名稱"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="分類描述"
    )
    
    icon = models.CharField(
        max_length=50,
        default='folder',
        verbose_name="圖標",
        help_text="FontAwesome圖標名稱"
    )
    
    color = models.CharField(
        max_length=7,
        default='#6DB3D1',
        verbose_name="顏色代碼",
        help_text="用於UI顯示的顏色"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="排序"
    )
    
    class Meta:
        verbose_name = "資源分類"
        verbose_name_plural = "資源分類"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


def resource_upload_path(instance, filename):
    """生成資源上傳路徑"""
    # 按照類型和日期組織檔案
    date = timezone.now()
    teacher_name = instance.teacher.username
    resource_type = instance.resource_type
    
    # 獲取檔案擴展名
    ext = filename.split('.')[-1].lower()
    
    # 生成新的檔案名
    new_filename = f"{date.strftime('%Y%m%d_%H%M%S')}_{filename}"
    
    return f"resources/{teacher_name}/{resource_type}/{date.year}/{date.month:02d}/{new_filename}"


class TeacherResource(models.Model):
    """教師資源模型"""
    
    RESOURCE_TYPES = [
        ('sheet_music', '樂譜'),
        ('video_tutorial', '教學影片'),
        ('audio', '音頻資料'),
        ('document', '文件'),
        ('image', '圖片'),
        ('link', '外部連結'),
        ('other', '其他')
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', '初級'),
        ('intermediate', '中級'),
        ('advanced', '高級'),
        ('all', '所有程度')
    ]
    
    # 基本資訊
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_resources',
        verbose_name="教師"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="資源標題"
    )
    
    description = models.TextField(
        verbose_name="資源描述",
        help_text="詳細描述這個資源的內容和用途"
    )
    
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resources',
        verbose_name="分類"
    )
    
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPES,
        verbose_name="資源類型"
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='all',
        verbose_name="難度等級"
    )
    
    # 檔案或連結
    file = models.FileField(
        upload_to=resource_upload_path,
        null=True,
        blank=True,
        verbose_name="檔案",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'mp3', 'wav', 'mp4', 'mov', 'doc', 'docx', 'ppt', 'pptx']
            )
        ]
    )
    
    external_link = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="外部連結",
        help_text="YouTube、Google Drive或其他網站連結"
    )
    
    # 縮圖
    thumbnail = models.ImageField(
        upload_to='resources/thumbnails/',
        null=True,
        blank=True,
        verbose_name="縮圖"
    )
    
    # 標籤和元數據
    tags = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="標籤",
        help_text="用逗號分隔多個標籤"
    )
    
    composer = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="作曲家",
        help_text="如果是樂譜，請填寫作曲家名稱"
    )
    
    piece_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="曲目名稱"
    )
    
    # 分享設定
    is_public = models.BooleanField(
        default=False,
        verbose_name="公開資源",
        help_text="是否允許所有學生查看"
    )
    
    shared_with_students = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_resources',
        verbose_name="分享給特定學生",
        limit_choices_to={'profile__role': 'student'}
    )
    
    # 統計
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name="下載次數"
    )
    
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="瀏覽次數"
    )
    
    # 版本控制
    version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name="版本"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上傳時間"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間"
    )
    
    class Meta:
        verbose_name = "教學資源"
        verbose_name_plural = "教學資源"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', 'resource_type']),
            models.Index(fields=['category', 'difficulty_level']),
            models.Index(fields=['is_public']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.teacher.username}"
    
    @property
    def file_size_mb(self):
        """返回檔案大小（MB）"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """返回檔案擴展名"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
    
    @property
    def is_downloadable(self):
        """檢查是否可下載"""
        return bool(self.file)
    
    def increment_download_count(self):
        """增加下載次數"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def increment_view_count(self):
        """增加瀏覽次數"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def can_access(self, user):
        """檢查用戶是否可以訪問此資源"""
        # 教師自己的資源
        if self.teacher == user:
            return True
        
        # 公開資源
        if self.is_public:
            return True
        
        # 特定分享的學生
        if user in self.shared_with_students.all():
            return True
        
        return False


class ResourceCollection(models.Model):
    """資源集合模型 - 用於組織相關資源"""
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resource_collections',
        verbose_name="教師"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="集合名稱"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="集合描述"
    )
    
    resources = models.ManyToManyField(
        TeacherResource,
        related_name='collections',
        verbose_name="包含的資源"
    )
    
    # 分享設定
    is_public = models.BooleanField(
        default=False,
        verbose_name="公開集合"
    )
    
    shared_with_students = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_collections',
        verbose_name="分享給特定學生",
        limit_choices_to={'profile__role': 'student'}
    )
    
    # 排序
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="排序"
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
        verbose_name = "資源集合"
        verbose_name_plural = "資源集合"
        ordering = ['order', '-created_at']
        unique_together = ['teacher', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.teacher.username}"
    
    @property
    def resource_count(self):
        """返回資源數量"""
        return self.resources.count()


class ResourceUsageLog(models.Model):
    """資源使用記錄"""
    
    ACTION_TYPES = [
        ('view', '瀏覽'),
        ('download', '下載'),
        ('share', '分享')
    ]
    
    resource = models.ForeignKey(
        TeacherResource,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        verbose_name="資源"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resource_usage_logs',
        verbose_name="使用者"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name="動作"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="時間"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP地址"
    )
    
    class Meta:
        verbose_name = "資源使用記錄"
        verbose_name_plural = "資源使用記錄"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['resource', 'timestamp']),
            models.Index(fields=['user', 'action']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} {self.resource.title}"