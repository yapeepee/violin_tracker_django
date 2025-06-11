"""
遊戲化系統核心服務類
整合成就、挑戰、錄音等系統，提供統一的遊戲化體驗
"""

from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import date, timedelta
from .achievement_service import AchievementService
from .challenge_service import ChallengeService
from .recording_service import RecordingService
from ..models import PracticeLog, StudentLevel
import logging

logger = logging.getLogger(__name__)


class GamificationService:
    """遊戲化系統核心服務類"""
    
    @staticmethod
    def process_practice_log_creation(practice_log):
        """處理練習記錄創建後的遊戲化邏輯"""
        try:
            student_name = practice_log.student_name
            practice_date = practice_log.date
            
            # 1. 更新練習連續天數
            AchievementService.update_practice_streak(student_name, practice_date)
            
            # 2. 檢查成就進度
            newly_earned_achievements = AchievementService.check_achievements_for_student(student_name)
            
            # 3. 更新挑戰進度
            ChallengeService.update_challenge_progress(student_name)
            
            # 4. 更新目標進度
            ChallengeService.update_goal_progress(student_name)
            
            # 5. 更新學生等級的總練習時間
            student_level, created = StudentLevel.objects.get_or_create(
                student_name=student_name,
                defaults={'level': 1, 'total_points': 0}
            )
            student_level.total_practice_time += practice_log.minutes
            student_level.save()
            
            logger.info(f"處理練習記錄的遊戲化邏輯: {student_name}")
            
            return {
                'newly_earned_achievements': newly_earned_achievements,
                'level_info': AchievementService.get_student_level_info(student_name)
            }
            
        except Exception as e:
            logger.error(f"處理練習記錄遊戲化邏輯時發生錯誤: {str(e)}")
            return {'newly_earned_achievements': [], 'level_info': None}
    
    @staticmethod
    def get_student_dashboard(student_name):
        """獲取學生遊戲化儀表板數據"""
        try:
            # 基本等級信息
            level_info = AchievementService.get_student_level_info(student_name)
            
            # 最近獲得的成就
            recent_achievements = AchievementService.get_recent_achievements(student_name, days=7)
            
            # 當前週的挑戰
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            current_challenges = ChallengeService.get_student_challenges(
                student_name, week_start=week_start, status='active'
            )
            
            # 待完成的任務
            pending_tasks = ChallengeService.get_student_tasks(
                student_name, status='active', limit=5
            )
            
            # 錄音統計
            recording_stats = RecordingService.get_recording_statistics(student_name)
            
            # 挑戰統計
            challenge_stats = ChallengeService.get_challenge_statistics(student_name)
            
            # 本週練習統計
            week_practice_stats = GamificationService._get_week_practice_stats(student_name)
            
            dashboard = {
                'level_info': level_info,
                'recent_achievements': list(recent_achievements),
                'current_challenges': list(current_challenges),
                'pending_tasks': list(pending_tasks),
                'recording_stats': recording_stats,
                'challenge_stats': challenge_stats,
                'week_practice_stats': week_practice_stats,
                'motivation_message': GamificationService._get_motivation_message(
                    level_info, week_practice_stats
                )
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"獲取學生儀表板時發生錯誤: {str(e)}")
            return {}
    
    @staticmethod
    def _get_week_practice_stats(student_name):
        """獲取本週練習統計"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_logs = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=week_start,
            date__lte=min(week_end, today)
        )
        
        stats = week_logs.aggregate(
            total_minutes=Sum('minutes'),
            total_sessions=Count('id'),
            avg_rating=Avg('rating')
        )
        
        # 計算練習天數
        practice_days = week_logs.values('date').distinct().count()
        
        return {
            'total_minutes': stats['total_minutes'] or 0,
            'total_sessions': stats['total_sessions'] or 0,
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'practice_days': practice_days,
            'target_days': 5,  # 目標每週練習5天
            'days_remaining': max(0, (week_end - today).days + 1)
        }
    
    @staticmethod
    def _get_motivation_message(level_info, week_stats):
        """生成激勵消息"""
        if not level_info:
            return "歡迎開始你的小提琴學習之旅！"
        
        messages = []
        
        # 基於等級的消息
        if level_info['level'] < 5:
            messages.append("你正在建立良好的練習習慣，繼續保持！")
        elif level_info['level'] < 10:
            messages.append("你的進步很穩定，技巧正在不斷提升！")
        else:
            messages.append("你已經是一位經驗豐富的練習者了！")
        
        # 基於本週練習的消息
        if week_stats['practice_days'] >= 5:
            messages.append("本週你的練習非常規律，棒極了！")
        elif week_stats['practice_days'] >= 3:
            messages.append("本週練習不錯，再加把勁達成每週5天的目標！")
        elif week_stats['practice_days'] > 0:
            messages.append("記住，每天一點點練習，積少成多！")
        else:
            messages.append("新的一週開始了，讓我們一起練習吧！")
        
        # 基於連續天數的消息
        if level_info['current_streak'] >= 7:
            messages.append(f"連續練習{level_info['current_streak']}天，你的毅力令人敬佩！")
        elif level_info['current_streak'] >= 3:
            messages.append(f"連續練習{level_info['current_streak']}天，良好的習慣正在形成！")
        
        return " ".join(messages[:2])  # 最多返回兩條消息
    
    @staticmethod
    def initialize_student_gamification(student_name):
        """初始化學生的遊戲化系統"""
        try:
            # 創建學生等級記錄
            student_level, created = StudentLevel.objects.get_or_create(
                student_name=student_name,
                defaults={
                    'level': 1,
                    'total_points': 0,
                    'title': '初學者'
                }
            )
            
            if created:
                logger.info(f"初始化學生遊戲化系統: {student_name}")
            
            # 生成本週挑戰
            ChallengeService.generate_weekly_challenges(student_name)
            
            # 檢查成就進度
            AchievementService.check_achievements_for_student(student_name)
            
            return student_level
            
        except Exception as e:
            logger.error(f"初始化學生遊戲化系統時發生錯誤: {str(e)}")
            return None
    
    @staticmethod
    def get_leaderboard(limit=10):
        """獲取排行榜"""
        try:
            # 按等級和積分排序
            top_students = StudentLevel.objects.all().order_by(
                '-level', '-total_points'
            )[:limit]
            
            leaderboard = []
            for rank, student in enumerate(top_students, 1):
                # 獲取最近30天的統計
                thirty_days_ago = date.today() - timedelta(days=30)
                recent_stats = PracticeLog.objects.filter(
                    student_name=student.student_name,
                    date__gte=thirty_days_ago
                ).aggregate(
                    total_minutes=Sum('minutes'),
                    avg_rating=Avg('rating')
                )
                
                leaderboard.append({
                    'rank': rank,
                    'student_name': student.student_name,
                    'level': student.level,
                    'title': student.title,
                    'total_points': student.total_points,
                    'current_streak': student.current_streak,
                    'longest_streak': student.longest_streak,
                    'recent_practice_minutes': recent_stats['total_minutes'] or 0,
                    'recent_avg_rating': round(recent_stats['avg_rating'] or 0, 2)
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"獲取排行榜時發生錯誤: {str(e)}")
            return []
    
    @staticmethod
    def get_system_overview():
        """獲取系統概覽統計"""
        try:
            from ..models import Achievement, PracticeRecording, WeeklyChallenge
            
            # 統計總數
            total_students = StudentLevel.objects.count()
            total_practice_logs = PracticeLog.objects.count()
            total_achievements = Achievement.objects.filter(is_active=True).count()
            total_recordings = PracticeRecording.objects.filter(status='ready').count()
            
            # 活躍度統計
            today = date.today()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            active_students_week = PracticeLog.objects.filter(
                date__gte=week_ago
            ).values('student_name').distinct().count()
            
            active_students_month = PracticeLog.objects.filter(
                date__gte=month_ago
            ).values('student_name').distinct().count()
            
            # 挑戰完成率
            total_challenges = WeeklyChallenge.objects.count()
            completed_challenges = WeeklyChallenge.objects.filter(is_completed=True).count()
            challenge_completion_rate = (
                completed_challenges / total_challenges * 100 
                if total_challenges > 0 else 0
            )
            
            return {
                'total_students': total_students,
                'total_practice_logs': total_practice_logs,
                'total_achievements': total_achievements,
                'total_recordings': total_recordings,
                'active_students_week': active_students_week,
                'active_students_month': active_students_month,
                'challenge_completion_rate': round(challenge_completion_rate, 2),
                'system_health': 'healthy' if active_students_week > 0 else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"獲取系統概覽時發生錯誤: {str(e)}")
            return {}
    
    @staticmethod
    def suggest_next_actions(student_name):
        """為學生建議下一步行動"""
        try:
            suggestions = []
            
            # 檢查未完成的任務
            overdue_tasks = ChallengeService.get_student_tasks(
                student_name, status='overdue'
            )
            if overdue_tasks:
                suggestions.append({
                    'type': 'urgent_task',
                    'message': f"你有 {len(overdue_tasks)} 個逾期任務需要完成",
                    'action': 'complete_tasks',
                    'priority': 'high'
                })
            
            # 檢查未完成的挑戰
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            active_challenges = ChallengeService.get_student_challenges(
                student_name, week_start=week_start, status='active'
            )
            
            for challenge in active_challenges:
                if challenge.progress_percentage < 50 and challenge.days_remaining <= 2:
                    suggestions.append({
                        'type': 'challenge_reminder',
                        'message': f"挑戰「{challenge.title}」還有{challenge.days_remaining}天截止",
                        'action': 'practice_now',
                        'priority': 'medium'
                    })
            
            # 檢查錄音上傳
            recent_recordings = RecordingService.get_student_recordings(
                student_name, limit=1
            )
            if not recent_recordings:
                suggestions.append({
                    'type': 'recording_suggestion',
                    'message': "考慮上傳一段練習錄音來追蹤你的進步",
                    'action': 'upload_recording',
                    'priority': 'low'
                })
            
            # 檢查練習頻率
            week_stats = GamificationService._get_week_practice_stats(student_name)
            if week_stats['practice_days'] < 3 and week_stats['days_remaining'] > 0:
                suggestions.append({
                    'type': 'practice_reminder',
                    'message': "本週練習次數較少，建議增加練習頻率",
                    'action': 'practice_today',
                    'priority': 'medium'
                })
            
            return suggestions[:3]  # 最多返回3個建議
            
        except Exception as e:
            logger.error(f"生成建議時發生錯誤: {str(e)}")
            return []