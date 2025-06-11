"""
小提琴練習記錄系統 - 模型模組
包含所有數據模型的定義
"""

# 核心功能模型
from .practice import PracticeLog
from .feedback import TeacherFeedback
from .achievements import Achievement, StudentAchievement, StudentLevel
from .user_profile import UserProfile, StudentTeacherRelation, UserLoginLog

# 教師系統模型
from .qa_system import StudentQuestion, TeacherAnswer, QuestionCategory, FAQ
from .teacher_resources import ResourceCategory, TeacherResource, ResourceCollection, ResourceUsageLog
from .lesson_management import LessonSchedule, StudentProgress, LessonNote

# 暫時移除的模型 (未來實作)
# from .recordings import PracticeRecording, RecordingComment, RecordingProgress
# from .challenges import WeeklyChallenge, PracticeTask, StudentGoal

__all__ = [
    # 核心模型
    'PracticeLog',
    'TeacherFeedback',
    
    # 用戶認證模型
    'UserProfile',
    'StudentTeacherRelation',
    'UserLoginLog',
    
    # 成就系統模型
    'Achievement',
    'StudentAchievement', 
    'StudentLevel',
    
    # 教師系統模型
    'StudentQuestion',
    'TeacherAnswer',
    'QuestionCategory',
    'FAQ',
    'ResourceCategory',
    'TeacherResource',
    'ResourceCollection',
    'ResourceUsageLog',
    'LessonSchedule',
    'StudentProgress',
    'LessonNote',
    
    # 未來模型 (暫時移除)
    # 'PracticeRecording',
    # 'RecordingComment',
    # 'RecordingProgress',
    # 'WeeklyChallenge',
    # 'PracticeTask',
    # 'StudentGoal',
]