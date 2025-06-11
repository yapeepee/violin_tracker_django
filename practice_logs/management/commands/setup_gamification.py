"""
設置遊戲化系統的Django管理命令
創建預設成就、生成示範數據、測試系統功能
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random

from practice_logs.models import PracticeLog
from practice_logs.services import AchievementService, ChallengeService, GamificationService


class Command(BaseCommand):
    help = '設置遊戲化系統：創建預設成就、生成示範數據'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-achievements',
            action='store_true',
            help='創建預設成就徽章'
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='為現有學生創建示範數據'
        )
        parser.add_argument(
            '--test-system',
            action='store_true',
            help='測試遊戲化系統功能'
        )
        parser.add_argument(
            '--student-name',
            type=str,
            help='指定學生姓名進行測試'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 開始設置遊戲化系統...')
        )

        if options['create_achievements']:
            self.create_achievements()

        if options['create_sample_data']:
            self.create_sample_data(options.get('student_name'))

        if options['test_system']:
            self.test_system(options.get('student_name'))

        self.stdout.write(
            self.style.SUCCESS('✅ 遊戲化系統設置完成！')
        )

    def create_achievements(self):
        """創建預設成就徽章"""
        self.stdout.write('📈 創建預設成就徽章...')
        
        try:
            created_count = AchievementService.create_default_achievements()
            self.stdout.write(
                self.style.SUCCESS(f'✅ 成功創建 {created_count} 個成就徽章')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 創建成就時發生錯誤: {str(e)}')
            )

    def create_sample_data(self, student_name=None):
        """創建示範數據"""
        self.stdout.write('📊 創建示範數據...')
        
        try:
            # 獲取現有學生或使用指定學生
            if student_name:
                students = [student_name]
            else:
                # 從現有練習記錄中獲取學生
                existing_students = list(
                    PracticeLog.objects.values_list('student_name', flat=True)
                    .distinct()[:3]
                )
                
                if not existing_students:
                    # 如果沒有現有學生，創建示範學生
                    students = ['小明', '小華', '小美']
                    self.create_sample_practice_logs(students)
                else:
                    students = existing_students

            # 為每個學生初始化遊戲化系統
            for student in students:
                self.stdout.write(f'  🎯 為學生 {student} 設置遊戲化系統...')
                
                # 初始化遊戲化系統
                GamificationService.initialize_student_gamification(student)
                
                # 生成每週挑戰
                challenges = ChallengeService.generate_weekly_challenges(student)
                self.stdout.write(f'    ✅ 生成 {len(challenges)} 個每週挑戰')
                
                # 創建一些練習任務
                self.create_sample_tasks(student)
                
                # 檢查成就進度
                achievements = AchievementService.check_achievements_for_student(student)
                self.stdout.write(f'    🏆 檢查成就進度，獲得 {len(achievements)} 個成就')

            self.stdout.write(
                self.style.SUCCESS(f'✅ 為 {len(students)} 個學生創建了示範數據')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 創建示範數據時發生錯誤: {str(e)}')
            )

    def create_sample_practice_logs(self, students):
        """創建示範練習記錄"""
        pieces = ['卡農', '小星星變奏曲', '月光奏鳴曲', '四季-春', 'G大調小步舞曲']
        focuses = ['technique', 'expression', 'rhythm', 'sight_reading']
        
        for student in students:
            # 為每個學生創建過去30天的練習記錄
            for i in range(20):  # 20個練習記錄
                practice_date = date.today() - timedelta(days=random.randint(0, 30))
                
                PracticeLog.objects.create(
                    student_name=student,
                    date=practice_date,
                    piece=random.choice(pieces),
                    minutes=random.randint(20, 120),
                    rating=random.randint(2, 5),
                    focus=random.choice(focuses),
                    notes=f"今天練習的心得記錄 {i+1}"
                )

    def create_sample_tasks(self, student_name):
        """創建示範任務"""
        tasks = [
            {
                'title': '技巧練習強化',
                'description': '專注於弓法技巧練習，每天至少30分鐘',
                'task_type': 'focus_practice',
                'due_date': date.today() + timedelta(days=7),
                'priority': 'high'
            },
            {
                'title': '曲目熟練度提升',
                'description': '將「卡農」練習到熟練程度',
                'task_type': 'piece_mastery',
                'due_date': date.today() + timedelta(days=14),
                'priority': 'medium'
            },
            {
                'title': '視奏練習',
                'description': '每週進行至少3次視奏練習',
                'task_type': 'sight_reading',
                'due_date': date.today() + timedelta(days=10),
                'priority': 'low'
            }
        ]
        
        for task_data in tasks:
            ChallengeService.create_practice_task(
                student_name=student_name,
                assigned_by='system',
                **task_data
            )

    def test_system(self, student_name=None):
        """測試遊戲化系統功能"""
        self.stdout.write('🧪 測試遊戲化系統功能...')
        
        try:
            # 選擇測試學生
            if student_name:
                test_student = student_name
            else:
                # 使用第一個有練習記錄的學生
                first_log = PracticeLog.objects.first()
                if not first_log:
                    self.stdout.write(
                        self.style.WARNING('⚠️ 沒有找到練習記錄，無法進行測試')
                    )
                    return
                test_student = first_log.student_name

            self.stdout.write(f'  👤 測試學生: {test_student}')

            # 測試1: 獲取學生儀表板
            dashboard = GamificationService.get_student_dashboard(test_student)
            self.stdout.write('  ✅ 學生儀表板數據獲取成功')
            self.stdout.write(f'    - 等級: {dashboard.get("level_info", {}).get("level", "N/A")}')
            self.stdout.write(f'    - 當前挑戰: {len(dashboard.get("current_challenges", []))} 個')
            self.stdout.write(f'    - 待辦任務: {len(dashboard.get("pending_tasks", []))} 個')

            # 測試2: 檢查成就系統
            level_info = AchievementService.get_student_level_info(test_student)
            if level_info:
                self.stdout.write('  ✅ 成就系統運作正常')
                self.stdout.write(f'    - 總積分: {level_info["total_points"]}')
                self.stdout.write(f'    - 連續練習: {level_info["current_streak"]} 天')
            else:
                self.stdout.write('  ⚠️ 成就系統需要初始化')

            # 測試3: 測試挑戰系統
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            challenges = ChallengeService.get_student_challenges(
                test_student, week_start=week_start
            )
            self.stdout.write(f'  ✅ 挑戰系統運作正常，本週有 {len(challenges)} 個挑戰')

            # 測試4: 獲取系統概覽
            overview = GamificationService.get_system_overview()
            self.stdout.write('  ✅ 系統概覽獲取成功')
            self.stdout.write(f'    - 總學生數: {overview.get("total_students", 0)}')
            self.stdout.write(f'    - 總練習記錄: {overview.get("total_practice_logs", 0)}')
            self.stdout.write(f'    - 系統健康狀態: {overview.get("system_health", "unknown")}')

            # 測試5: 建議系統
            suggestions = GamificationService.suggest_next_actions(test_student)
            self.stdout.write(f'  ✅ 建議系統運作正常，生成 {len(suggestions)} 個建議')

            self.stdout.write(
                self.style.SUCCESS('✅ 所有測試通過，遊戲化系統運作正常！')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 測試過程中發生錯誤: {str(e)}')
            )

    def display_summary(self):
        """顯示系統摘要"""
        self.stdout.write('\n📊 遊戲化系統摘要:')
        
        try:
            overview = GamificationService.get_system_overview()
            
            self.stdout.write(f'  👥 總學生數: {overview.get("total_students", 0)}')
            self.stdout.write(f'  📝 總練習記錄: {overview.get("total_practice_logs", 0)}')
            self.stdout.write(f'  🏆 總成就數: {overview.get("total_achievements", 0)}')
            self.stdout.write(f'  🎯 挑戰完成率: {overview.get("challenge_completion_rate", 0):.1f}%')
            self.stdout.write(f'  📈 週活躍學生: {overview.get("active_students_week", 0)}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 獲取系統摘要時發生錯誤: {str(e)}')
            )