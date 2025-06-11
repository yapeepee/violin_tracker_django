"""
挑戰與任務系統服務類
處理每週挑戰生成、任務管理、目標追蹤等業務邏輯
"""

from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import date, timedelta, datetime
from ..models import (
    PracticeLog, WeeklyChallenge, PracticeTask, StudentGoal, StudentLevel
)
import logging
import random

logger = logging.getLogger(__name__)


class ChallengeService:
    """挑戰與任務系統服務類"""
    
    @staticmethod
    def generate_weekly_challenges(student_name, week_start=None):
        """為學生生成每週挑戰"""
        if not week_start:
            # 獲取當週的週一
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        try:
            # 檢查是否已有本週挑戰
            existing_challenges = WeeklyChallenge.objects.filter(
                student_name=student_name,
                week_start=week_start
            )
            
            if existing_challenges.exists():
                logger.info(f"學生 {student_name} 本週已有挑戰")
                return list(existing_challenges)
            
            # 獲取學生歷史數據以生成個人化挑戰
            student_stats = ChallengeService._get_student_stats(student_name)
            
            # 生成挑戰
            challenges = []
            challenge_templates = ChallengeService._get_challenge_templates()
            
            # 隨機選擇3-4個挑戰
            selected_templates = random.sample(challenge_templates, min(4, len(challenge_templates)))
            
            for template in selected_templates:
                challenge_data = ChallengeService._customize_challenge(
                    template, student_stats, week_start
                )
                challenge_data['student_name'] = student_name
                
                challenge = WeeklyChallenge.objects.create(**challenge_data)
                challenges.append(challenge)
                
                logger.info(f"為 {student_name} 創建挑戰: {challenge.title}")
            
            return challenges
            
        except Exception as e:
            logger.error(f"生成每週挑戰時發生錯誤: {str(e)}")
            return []
    
    @staticmethod
    def _get_student_stats(student_name):
        """獲取學生統計數據用於個人化挑戰"""
        # 最近30天的統計
        thirty_days_ago = date.today() - timedelta(days=30)
        
        recent_logs = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=thirty_days_ago
        )
        
        stats = recent_logs.aggregate(
            avg_daily_minutes=Avg('minutes'),
            total_sessions=Count('id'),
            avg_rating=Avg('rating')
        )
        
        # 獲取最常練習的曲目
        popular_pieces = recent_logs.values('piece').annotate(
            count=Count('piece')
        ).order_by('-count')[:3]
        
        # 獲取最常練習的重點
        popular_focus = recent_logs.values('focus').annotate(
            count=Count('focus')
        ).order_by('-count').first()
        
        return {
            'avg_daily_minutes': stats['avg_daily_minutes'] or 30,
            'total_sessions': stats['total_sessions'] or 0,
            'avg_rating': stats['avg_rating'] or 3.0,
            'popular_pieces': [p['piece'] for p in popular_pieces],
            'popular_focus': popular_focus['focus'] if popular_focus else 'technique'
        }
    
    @staticmethod
    def _get_challenge_templates():
        """獲取挑戰模板"""
        return [
            {
                'challenge_type': 'practice_time',
                'title_template': '本週練習達人',
                'description_template': '本週累計練習時間達到 {target} 分鐘',
                'base_target': 150,
                'difficulty_multiplier': {'easy': 0.7, 'medium': 1.0, 'hard': 1.3},
                'points_base': 60
            },
            {
                'challenge_type': 'consecutive_days',
                'title_template': '堅持練習王',
                'description_template': '連續 {target} 天練習，培養好習慣',
                'base_target': 5,
                'difficulty_multiplier': {'easy': 0.6, 'medium': 1.0, 'hard': 1.4},
                'points_base': 80
            },
            {
                'challenge_type': 'rating_improvement',
                'title_template': '品質提升者',
                'description_template': '本週平均評分達到 {target} 分',
                'base_target': 4.0,
                'difficulty_multiplier': {'easy': 0.9, 'medium': 1.0, 'hard': 1.1},
                'points_base': 70
            },
            {
                'challenge_type': 'skill_focus',
                'title_template': '技巧專精挑戰',
                'description_template': '本週專注於{focus_name}練習 {target} 分鐘',
                'base_target': 60,
                'difficulty_multiplier': {'easy': 0.8, 'medium': 1.0, 'hard': 1.2},
                'points_base': 50
            },
            {
                'challenge_type': 'variety_practice',
                'title_template': '多樣化練習',
                'description_template': '本週練習 {target} 首不同的曲目',
                'base_target': 3,
                'difficulty_multiplier': {'easy': 0.7, 'medium': 1.0, 'hard': 1.5},
                'points_base': 40
            }
        ]
    
    @staticmethod
    def _customize_challenge(template, student_stats, week_start):
        """根據學生數據自定義挑戰"""
        # 根據學生歷史表現調整難度
        if student_stats['total_sessions'] < 10:
            difficulty = 'easy'
        elif student_stats['avg_rating'] > 4.0:
            difficulty = 'hard'
        else:
            difficulty = 'medium'
        
        # 計算目標值
        multiplier = template['difficulty_multiplier'][difficulty]
        
        if template['challenge_type'] == 'practice_time':
            # 基於歷史平均練習時間調整
            avg_weekly = student_stats['avg_daily_minutes'] * 7
            target = max(template['base_target'], avg_weekly * multiplier)
            
        elif template['challenge_type'] == 'rating_improvement':
            # 基於當前平均評分調整
            current_avg = student_stats['avg_rating']
            target = min(5.0, current_avg + (template['base_target'] - current_avg) * multiplier)
            
        else:
            target = template['base_target'] * multiplier
        
        # 生成挑戰數據
        challenge_data = {
            'week_start': week_start,
            'challenge_type': template['challenge_type'],
            'title': template['title_template'],
            'target_value': target,
            'difficulty': difficulty,
            'points_reward': int(template['points_base'] * multiplier),
            'created_by': 'auto'
        }
        
        # 自定義描述
        if template['challenge_type'] == 'skill_focus':
            focus_map = {
                'technique': '技巧',
                'expression': '表現力',
                'rhythm': '節奏',
                'sight_reading': '視奏'
            }
            focus_name = focus_map.get(student_stats['popular_focus'], '技巧')
            challenge_data['description'] = template['description_template'].format(
                target=int(target), focus_name=focus_name
            )
        else:
            challenge_data['description'] = template['description_template'].format(
                target=int(target) if target > 1 else f"{target:.1f}"
            )
        
        return challenge_data
    
    @staticmethod
    def update_challenge_progress(student_name):
        """更新學生的挑戰進度"""
        try:
            # 獲取當前週的挑戰
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            
            active_challenges = WeeklyChallenge.objects.filter(
                student_name=student_name,
                week_start=week_start,
                status='active'
            )
            
            for challenge in active_challenges:
                progress = ChallengeService._calculate_challenge_progress(
                    student_name, challenge
                )
                challenge.update_progress(progress)
            
            logger.info(f"更新了 {student_name} 的 {active_challenges.count()} 個挑戰進度")
            
        except Exception as e:
            logger.error(f"更新挑戰進度時發生錯誤: {str(e)}")
    
    @staticmethod
    def _calculate_challenge_progress(student_name, challenge):
        """計算特定挑戰的進度"""
        week_start = challenge.week_start
        week_end = week_start + timedelta(days=6)
        
        week_logs = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=week_start,
            date__lte=week_end
        )
        
        if challenge.challenge_type == 'practice_time':
            total_minutes = week_logs.aggregate(
                total=Sum('minutes')
            )['total'] or 0
            return total_minutes
        
        elif challenge.challenge_type == 'consecutive_days':
            # 計算本週的連續練習天數
            practice_dates = set(week_logs.values_list('date', flat=True))
            consecutive_days = 0
            current_date = week_start
            
            while current_date <= min(week_end, date.today()):
                if current_date in practice_dates:
                    consecutive_days += 1
                else:
                    consecutive_days = 0
                current_date += timedelta(days=1)
            
            return consecutive_days
        
        elif challenge.challenge_type == 'rating_improvement':
            avg_rating = week_logs.aggregate(
                avg=Avg('rating')
            )['avg'] or 0
            return avg_rating
        
        elif challenge.challenge_type == 'skill_focus':
            # 假設專注於技巧練習
            focus_minutes = week_logs.filter(focus='technique').aggregate(
                total=Sum('minutes')
            )['total'] or 0
            return focus_minutes
        
        elif challenge.challenge_type == 'variety_practice':
            unique_pieces = week_logs.values('piece').distinct().count()
            return unique_pieces
        
        return 0
    
    @staticmethod
    def create_practice_task(student_name, title, description, task_type, 
                           due_date, priority='medium', assigned_by='system',
                           related_piece=None, estimated_minutes=None):
        """創建練習任務"""
        try:
            task_data = {
                'student_name': student_name,
                'title': title,
                'description': description,
                'task_type': task_type,
                'due_date': due_date,
                'priority': priority,
                'assigned_by': assigned_by,
                'estimated_minutes': estimated_minutes
            }
            
            # 只有在提供related_piece時才添加
            if related_piece:
                task_data['related_piece'] = related_piece
            
            task = PracticeTask.objects.create(**task_data)
            
            logger.info(f"為 {student_name} 創建任務: {title}")
            return task
            
        except Exception as e:
            logger.error(f"創建練習任務時發生錯誤: {str(e)}")
            raise
    
    @staticmethod
    def complete_task(task_id, completion_notes=""):
        """完成任務"""
        try:
            task = PracticeTask.objects.get(id=task_id)
            task.mark_completed(completion_notes)
            
            # 給學生增加積分
            student_level, created = StudentLevel.objects.get_or_create(
                student_name=task.student_name,
                defaults={'level': 1, 'total_points': 0}
            )
            student_level.add_experience(task.points_reward)
            
            logger.info(f"任務完成: {task.title} ({task.student_name})")
            return task
            
        except PracticeTask.DoesNotExist:
            logger.error(f"任務不存在: {task_id}")
            raise
        except Exception as e:
            logger.error(f"完成任務時發生錯誤: {str(e)}")
            raise
    
    @staticmethod
    def get_student_tasks(student_name, status=None, limit=None):
        """獲取學生任務列表"""
        query = PracticeTask.objects.filter(student_name=student_name)
        
        if status:
            if status == 'active':
                query = query.filter(is_completed=False)
            elif status == 'completed':
                query = query.filter(is_completed=True)
            elif status == 'overdue':
                query = query.filter(is_completed=False, due_date__lt=date.today())
        
        query = query.order_by('-priority', 'due_date')
        
        if limit:
            query = query[:limit]
        
        return query
    
    @staticmethod
    def get_student_challenges(student_name, week_start=None, status=None):
        """獲取學生挑戰列表"""
        query = WeeklyChallenge.objects.filter(student_name=student_name)
        
        if week_start:
            query = query.filter(week_start=week_start)
        
        if status:
            query = query.filter(status=status)
        
        return query.order_by('-week_start', '-priority')
    
    @staticmethod
    def create_student_goal(student_name, title, description, goal_type,
                          target_date, progress_metric, target_value):
        """創建學生目標"""
        try:
            goal = StudentGoal.objects.create(
                student_name=student_name,
                title=title,
                description=description,
                goal_type=goal_type,
                target_date=target_date,
                progress_metric=progress_metric,
                target_value=target_value
            )
            
            logger.info(f"為 {student_name} 創建目標: {title}")
            return goal
            
        except Exception as e:
            logger.error(f"創建學生目標時發生錯誤: {str(e)}")
            raise
    
    @staticmethod
    def update_goal_progress(student_name):
        """更新學生目標進度"""
        try:
            active_goals = StudentGoal.objects.filter(
                student_name=student_name,
                status='active'
            )
            
            for goal in active_goals:
                # 根據進度指標計算當前值
                if goal.progress_metric == '練習時間':
                    current_value = PracticeLog.objects.filter(
                        student_name=student_name
                    ).aggregate(total=Sum('minutes'))['total'] or 0
                
                elif goal.progress_metric == '平均評分':
                    current_value = PracticeLog.objects.filter(
                        student_name=student_name
                    ).aggregate(avg=Avg('rating'))['avg'] or 0
                
                elif goal.progress_metric == '練習次數':
                    current_value = PracticeLog.objects.filter(
                        student_name=student_name
                    ).count()
                
                else:
                    continue
                
                goal.update_progress(current_value)
            
            logger.info(f"更新了 {student_name} 的 {active_goals.count()} 個目標進度")
            
        except Exception as e:
            logger.error(f"更新目標進度時發生錯誤: {str(e)}")
    
    @staticmethod
    def get_challenge_statistics(student_name):
        """獲取挑戰統計信息"""
        challenges = WeeklyChallenge.objects.filter(student_name=student_name)
        
        stats = {
            'total_challenges': challenges.count(),
            'completed_challenges': challenges.filter(is_completed=True).count(),
            'active_challenges': challenges.filter(status='active').count(),
            'total_points_earned': sum(
                c.total_points for c in challenges.filter(is_completed=True)
            )
        }
        
        stats['completion_rate'] = (
            stats['completed_challenges'] / stats['total_challenges'] * 100
            if stats['total_challenges'] > 0 else 0
        )
        
        return stats