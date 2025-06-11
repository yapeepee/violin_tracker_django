"""
成就系統服務類
處理成就檢查、徽章獲得、等級計算等業務邏輯
"""

from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import date, timedelta
from ..models import (
    PracticeLog, Achievement, StudentAchievement, StudentLevel
)
import logging

logger = logging.getLogger(__name__)


class AchievementService:
    """成就系統服務類"""
    
    @staticmethod
    def check_achievements_for_student(student_name):
        """檢查並更新學生的所有成就進度"""
        try:
            # 獲取或創建學生等級記錄
            student_level, created = StudentLevel.objects.get_or_create(
                student_name=student_name,
                defaults={'level': 1, 'total_points': 0}
            )
            
            if created:
                logger.info(f"創建新的學生等級記錄: {student_name}")
            
            # 獲取所有啟用的成就
            achievements = Achievement.objects.filter(is_active=True)
            
            newly_earned = []
            
            for achievement in achievements:
                student_achievement, created = StudentAchievement.objects.get_or_create(
                    student_name=student_name,
                    achievement=achievement,
                    defaults={'progress': 0, 'is_earned': False}
                )
                
                # 如果已經獲得，跳過
                if student_achievement.is_earned:
                    continue
                
                # 計算進度
                progress = AchievementService._calculate_achievement_progress(
                    student_name, achievement
                )
                
                student_achievement.progress = min(100, progress)
                
                # 檢查是否達成
                if progress >= 100 and not student_achievement.is_earned:
                    student_achievement.mark_as_earned()
                    newly_earned.append(achievement)
                    
                    # 增加經驗值和積分
                    student_level.add_experience(achievement.points)
                    
                    logger.info(f"{student_name} 獲得成就: {achievement.name}")
                
                student_achievement.save()
            
            return newly_earned
            
        except Exception as e:
            logger.error(f"檢查成就時發生錯誤 ({student_name}): {str(e)}")
            return []
    
    @staticmethod
    def _calculate_achievement_progress(student_name, achievement):
        """計算特定成就的進度"""
        requirement_type = achievement.requirement_type
        target_value = achievement.requirement_value
        
        try:
            if requirement_type == 'consecutive_days':
                return AchievementService._get_consecutive_days_progress(student_name, target_value)
            
            elif requirement_type == 'total_hours':
                return AchievementService._get_total_hours_progress(student_name, target_value)
            
            elif requirement_type == 'average_rating':
                return AchievementService._get_average_rating_progress(student_name, target_value)
            
            elif requirement_type == 'focus_hours':
                return AchievementService._get_focus_hours_progress(student_name, target_value)
            
            elif requirement_type == 'total_sessions':
                return AchievementService._get_total_sessions_progress(student_name, target_value)
            
            elif requirement_type == 'week_consistency':
                return AchievementService._get_week_consistency_progress(student_name, target_value)
            
            else:
                logger.warning(f"未知的成就類型: {requirement_type}")
                return 0
                
        except Exception as e:
            logger.error(f"計算成就進度時發生錯誤: {str(e)}")
            return 0
    
    @staticmethod
    def _get_consecutive_days_progress(student_name, target_days):
        """計算連續練習天數進度"""
        student_level = StudentLevel.objects.filter(student_name=student_name).first()
        if not student_level:
            return 0
        
        current_streak = student_level.current_streak
        return (current_streak / target_days) * 100
    
    @staticmethod
    def _get_total_hours_progress(student_name, target_hours):
        """計算總練習時間進度"""
        total_minutes = PracticeLog.objects.filter(
            student_name=student_name
        ).aggregate(total=Sum('minutes'))['total'] or 0
        
        total_hours = total_minutes / 60
        return (total_hours / target_hours) * 100
    
    @staticmethod
    def _get_average_rating_progress(student_name, target_rating):
        """計算平均評分進度"""
        avg_rating = PracticeLog.objects.filter(
            student_name=student_name
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        return (avg_rating / target_rating) * 100
    
    @staticmethod
    def _get_focus_hours_progress(student_name, target_hours):
        """計算專項練習時間進度（以技巧練習為例）"""
        focus_minutes = PracticeLog.objects.filter(
            student_name=student_name,
            focus='technique'
        ).aggregate(total=Sum('minutes'))['total'] or 0
        
        focus_hours = focus_minutes / 60
        return (focus_hours / target_hours) * 100
    
    @staticmethod
    def _get_total_sessions_progress(student_name, target_sessions):
        """計算總練習次數進度"""
        total_sessions = PracticeLog.objects.filter(
            student_name=student_name
        ).count()
        
        return (total_sessions / target_sessions) * 100
    
    @staticmethod
    def _get_week_consistency_progress(student_name, target_weeks):
        """計算週練習一致性進度"""
        # 計算最近N週的練習一致性
        weeks_ago = date.today() - timedelta(weeks=int(target_weeks))
        
        # 按週分組統計練習天數
        logs = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=weeks_ago
        ).values('date').distinct()
        
        if not logs:
            return 0
        
        # 計算每週至少練習3天的週數
        consistent_weeks = 0
        current_week = None
        days_in_week = 0
        
        for log in logs.order_by('date'):
            week = log['date'].isocalendar()[1]
            if week != current_week:
                if current_week is not None and days_in_week >= 3:
                    consistent_weeks += 1
                current_week = week
                days_in_week = 1
            else:
                days_in_week += 1
        
        # 檢查最後一週
        if days_in_week >= 3:
            consistent_weeks += 1
        
        return (consistent_weeks / target_weeks) * 100
    
    @staticmethod
    def get_student_level_info(student_name):
        """獲取學生等級信息"""
        try:
            student_level = StudentLevel.objects.get(student_name=student_name)
            return {
                'level': student_level.level,
                'title': student_level.title,
                'total_points': student_level.total_points,
                'current_experience': student_level.current_experience,
                'experience_to_next_level': student_level.experience_to_next_level,
                'experience_progress_percentage': student_level.experience_progress_percentage,
                'current_streak': student_level.current_streak,
                'longest_streak': student_level.longest_streak,
                'total_practice_time': student_level.total_practice_time
            }
        except StudentLevel.DoesNotExist:
            return None
    
    @staticmethod
    def get_student_achievements(student_name, category=None, earned_only=False):
        """獲取學生成就列表"""
        query = StudentAchievement.objects.filter(student_name=student_name)
        
        if category:
            query = query.filter(achievement__category=category)
        
        if earned_only:
            query = query.filter(is_earned=True)
        
        return query.select_related('achievement').order_by('-earned_date', '-progress')
    
    @staticmethod
    def get_recent_achievements(student_name, days=7):
        """獲取最近獲得的成就"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return StudentAchievement.objects.filter(
            student_name=student_name,
            is_earned=True,
            earned_date__gte=cutoff_date
        ).select_related('achievement').order_by('-earned_date')
    
    @staticmethod
    def update_practice_streak(student_name, practice_date):
        """更新練習連續天數"""
        try:
            student_level, created = StudentLevel.objects.get_or_create(
                student_name=student_name,
                defaults={'level': 1, 'total_points': 0}
            )
            
            student_level.update_streak(practice_date)
            
            # 檢查連續練習相關的成就
            AchievementService.check_achievements_for_student(student_name)
            
        except Exception as e:
            logger.error(f"更新練習連續天數時發生錯誤: {str(e)}")
    
    @staticmethod
    def create_default_achievements():
        """創建預設的成就徽章"""
        default_achievements = [
            # 連續練習類
            {
                'name': '初心者',
                'description': '連續練習3天，展現你的決心！',
                'icon': '🔥',
                'category': 'persistence',
                'requirement_type': 'consecutive_days',
                'requirement_value': 3,
                'points': 20,
                'rarity': 'common'
            },
            {
                'name': '堅持不懈',
                'description': '連續練習一週，習慣正在養成！',
                'icon': '🌟',
                'category': 'persistence',
                'requirement_type': 'consecutive_days',
                'requirement_value': 7,
                'points': 50,
                'rarity': 'rare'
            },
            {
                'name': '鋼鐵意志',
                'description': '連續練習一個月，你的毅力令人敬佩！',
                'icon': '💎',
                'category': 'persistence',
                'requirement_type': 'consecutive_days',
                'requirement_value': 30,
                'points': 200,
                'rarity': 'epic'
            },
            
            # 練習時間類
            {
                'name': '時間管理者',
                'description': '累計練習達到10小時',
                'icon': '⏰',
                'category': 'milestone',
                'requirement_type': 'total_hours',
                'requirement_value': 10,
                'points': 30,
                'rarity': 'common'
            },
            {
                'name': '勤奮學習者',
                'description': '累計練習達到100小時',
                'icon': '📚',
                'category': 'milestone',
                'requirement_type': 'total_hours',
                'requirement_value': 100,
                'points': 150,
                'rarity': 'rare'
            },
            {
                'name': '練習大師',
                'description': '累計練習達到500小時',
                'icon': '🏆',
                'category': 'milestone',
                'requirement_type': 'total_hours',
                'requirement_value': 500,
                'points': 500,
                'rarity': 'legendary'
            },
            
            # 品質提升類
            {
                'name': '品質追求者',
                'description': '平均評分達到4.0分',
                'icon': '⭐',
                'category': 'quality',
                'requirement_type': 'average_rating',
                'requirement_value': 4.0,
                'points': 40,
                'rarity': 'rare'
            },
            {
                'name': '完美主義者',
                'description': '平均評分達到4.5分',
                'icon': '🌟',
                'category': 'quality',
                'requirement_type': 'average_rating',
                'requirement_value': 4.5,
                'points': 80,
                'rarity': 'epic'
            },
            
            # 技能專精類
            {
                'name': '技巧專家',
                'description': '技巧練習累計達到20小時',
                'icon': '🎯',
                'category': 'skill',
                'requirement_type': 'focus_hours',
                'requirement_value': 20,
                'points': 60,
                'rarity': 'rare'
            },
            
            # 練習次數類
            {
                'name': '勤練不輟',
                'description': '完成50次練習記錄',
                'icon': '📝',
                'category': 'milestone',
                'requirement_type': 'total_sessions',
                'requirement_value': 50,
                'points': 75,
                'rarity': 'rare'
            }
        ]
        
        created_count = 0
        for achievement_data in default_achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
            if created:
                created_count += 1
                logger.info(f"創建成就: {achievement.name}")
        
        return created_count