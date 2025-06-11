"""
用戶認證和資料表單
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models.user_profile import UserProfile, StudentTeacherRelation


class CustomUserCreationForm(UserCreationForm):
    """
    自定義用戶註冊表單
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-classical',
            'placeholder': '電子郵件地址'
        })
    )
    
    chinese_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-classical',
            'placeholder': '中文姓名'
        })
    )
    
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-classical'
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-classical',
            'placeholder': '聯絡電話（選填）'
        })
    )
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-classical',
            'type': 'date'
        })
    )
    
    skill_level = forms.ChoiceField(
        choices=UserProfile.SKILL_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-classical'
        }),
        help_text="僅學生角色需要填寫"
    )
    
    learning_goals = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-classical',
            'rows': 3,
            'placeholder': '描述您的學習目標...'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 自定義表單控件樣式
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-classical',
            'placeholder': '用戶名'
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control form-control-classical',
            'placeholder': '密碼'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control form-control-classical',
            'placeholder': '確認密碼'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('此電子郵件地址已被使用')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        skill_level = cleaned_data.get('skill_level')
        
        # 如果是學生角色，必須選擇技能等級
        if role == 'student' and not skill_level:
            self.add_error('skill_level', '學生角色必須選擇技能等級')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # 創建或更新用戶Profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.chinese_name = self.cleaned_data['chinese_name']
            profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.birth_date = self.cleaned_data.get('birth_date')
            profile.skill_level = self.cleaned_data.get('skill_level', 'beginner')
            profile.learning_goals = self.cleaned_data.get('learning_goals', '')
            profile.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    自定義登入表單
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 自定義表單控件樣式
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-classical',
            'placeholder': '用戶名或電子郵件'
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-classical',
            'placeholder': '密碼'
        })
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username is not None and password:
            # 允許使用電子郵件登入
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                except User.DoesNotExist:
                    pass
            
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """
    用戶資料編輯表單
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-classical'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'chinese_name', 'phone_number', 'birth_date',
            'bio', 'skill_level', 'learning_goals', 'favorite_composers',
            'profile_public', 'practice_logs_public', 'email_notifications',
            'practice_reminders'
        ]
        
        widgets = {
            'chinese_name': forms.TextInput(attrs={
                'class': 'form-control form-control-classical'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control form-control-classical'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control form-control-classical',
                'type': 'date'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control form-control-classical',
                'rows': 4
            }),
            'skill_level': forms.Select(attrs={
                'class': 'form-control form-control-classical'
            }),
            'learning_goals': forms.Textarea(attrs={
                'class': 'form-control form-control-classical',
                'rows': 3
            }),
            'favorite_composers': forms.TextInput(attrs={
                'class': 'form-control form-control-classical'
            }),
            'profile_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'practice_logs_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'practice_reminders': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # 同時更新User的email
            if 'email' in self.cleaned_data:
                profile.user.email = self.cleaned_data['email']
                profile.user.save()
            profile.save()
        return profile


class AvatarUploadForm(forms.ModelForm):
    """
    頭像上傳表單
    """
    
    class Meta:
        model = UserProfile
        fields = ['avatar']
        
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # 檢查文件大小（5MB）
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('頭像圖片大小不能超過 5MB')
            
            # 檢查文件類型
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar.content_type not in allowed_types:
                raise ValidationError('只允許上傳 JPG、PNG 或 GIF 格式的圖片')
        
        return avatar


class StudentTeacherRelationForm(forms.ModelForm):
    """
    師生關係建立表單
    """
    
    class Meta:
        model = StudentTeacherRelation
        fields = ['student', 'teacher', 'start_date', 'notes']
        
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control form-control-classical'
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-control form-control-classical'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control form-control-classical',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-classical',
                'rows': 3
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 限制選項範圍 
        self.fields['student'].queryset = User.objects.filter(profile__role='student')
        self.fields['teacher'].queryset = User.objects.filter(profile__role='teacher')


class PasswordChangeForm(forms.Form):
    """
    密碼變更表單
    """
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-classical',
            'placeholder': '目前密碼'
        }),
        label="目前密碼"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-classical',
            'placeholder': '新密碼'
        }),
        label="新密碼",
        help_text="密碼至少需要8個字符，不能全為數字"
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-classical',
            'placeholder': '確認新密碼'
        }),
        label="確認新密碼"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('目前密碼不正確')
        return old_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError('兩次輸入的新密碼不一致')
            
            # 密碼強度檢查
            if len(new_password1) < 8:
                raise ValidationError('密碼長度至少需要8個字符')
            
            if new_password1.isdigit():
                raise ValidationError('密碼不能全為數字')
        
        return cleaned_data
    
    def save(self):
        new_password = self.cleaned_data['new_password1']
        self.user.set_password(new_password)
        self.user.save()
        return self.user