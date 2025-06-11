"""
創建示例數據的管理命令
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from practice_logs.models.user_profile import UserProfile, StudentTeacherRelation
from practice_logs.models import PracticeLog
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = '創建示例數據用於測試師生關係系統'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除現有數據'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('清除現有數據...')
            User.objects.filter(username__startswith='test_').delete()
            PracticeLog.objects.filter(student_name__startswith='測試').delete()

        self.stdout.write('創建示例教師...')
        
        # 創建教師
        teachers = []
        teacher_data = [
            {
                'username': 'test_teacher1',
                'email': 'teacher1@example.com',
                'first_name': '王',
                'last_name': '老師',
                'chinese_name': '王雅文',
                'specialization': '古典音樂、室內樂',
                'years_experience': 15,
                'education_background': '台北藝術大學音樂系碩士',
                'teaching_philosophy': '注重基礎技巧培養，強調音樂表現力'
            },
            {
                'username': 'test_teacher2',
                'email': 'teacher2@example.com',
                'first_name': '李',
                'last_name': '教授',
                'chinese_name': '李明華',
                'specialization': '巴洛克音樂、現代音樂',
                'years_experience': 20,
                'education_background': '維也納音樂學院博士',
                'teaching_philosophy': '因材施教，培養學生的音樂感受力'
            }
        ]
        
        for data in teacher_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='testpass123',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            
            # 更新profile
            profile = user.profile
            profile.role = 'teacher'
            profile.chinese_name = data['chinese_name']
            profile.specialization = data['specialization']
            profile.years_experience = data['years_experience']
            profile.education_background = data['education_background']
            profile.teaching_philosophy = data['teaching_philosophy']
            profile.save()
            
            teachers.append(user)
            self.stdout.write(f'  創建教師: {data["chinese_name"]}')

        self.stdout.write('創建示例學生...')
        
        # 創建學生
        students = []
        student_data = [
            {
                'username': 'test_student1',
                'email': 'student1@example.com',
                'chinese_name': '張小明',
                'skill_level': 'beginner'
            },
            {
                'username': 'test_student2',
                'email': 'student2@example.com',
                'chinese_name': '陳美玲',
                'skill_level': 'intermediate'
            },
            {
                'username': 'test_student3',
                'email': 'student3@example.com',
                'chinese_name': '林志偉',
                'skill_level': 'advanced'
            }
        ]
        
        for data in student_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='testpass123'
            )
            
            # 更新profile
            profile = user.profile
            profile.role = 'student'
            profile.chinese_name = data['chinese_name']
            profile.skill_level = data['skill_level']
            profile.learning_start_date = date.today() - timedelta(days=random.randint(30, 365))
            profile.save()
            
            students.append(user)
            self.stdout.write(f'  創建學生: {data["chinese_name"]}')

        self.stdout.write('創建師生關係...')
        
        # 創建師生關係
        StudentTeacherRelation.objects.create(
            student=students[0],  # 張小明
            teacher=teachers[0],  # 王老師
            is_active=True
        )
        
        StudentTeacherRelation.objects.create(
            student=students[1],  # 陳美玲
            teacher=teachers[0],  # 王老師
            is_active=True
        )
        
        StudentTeacherRelation.objects.create(
            student=students[2],  # 林志偉
            teacher=teachers[1],  # 李教授
            is_active=True
        )

        self.stdout.write('創建練習記錄...')
        
        # 為每個學生創建一些練習記錄
        pieces = [
            '巴哈小提琴奏鳴曲第一號',
            '莫札特小提琴協奏曲第三號',
            '貝多芬小提琴奏鳴曲春天',
            '韋瓦第四季-春',
            '帕格尼尼隨想曲第24號'
        ]
        
        focus_options = ['technique', 'expression', 'rhythm', 'sight_reading', 'memorization']
        
        for student in students:
            student_name = student.profile.chinese_name
            
            # 創建過去30天的練習記錄
            for i in range(random.randint(10, 20)):
                practice_date = date.today() - timedelta(days=random.randint(0, 30))
                
                PracticeLog.objects.create(
                    student_name=student_name,
                    date=practice_date,
                    piece=random.choice(pieces),
                    minutes=random.randint(30, 120),
                    focus=random.choice(focus_options),
                    rating=random.randint(3, 5),
                    notes=f'今天練習{random.choice(["順利", "有進步", "需要加強", "技巧改善"])}，{random.choice(["節拍感", "音準", "表現力", "技巧"])}還需要多練習。'
                )
            
            self.stdout.write(f'  為 {student_name} 創建練習記錄')

        self.stdout.write(
            self.style.SUCCESS(
                '\n示例數據創建完成！\n\n'
                '教師帳號：\n'
                '  用戶名: test_teacher1, 密碼: testpass123 (王雅文老師)\n'
                '  用戶名: test_teacher2, 密碼: testpass123 (李明華教授)\n\n'
                '學生帳號：\n'
                '  用戶名: test_student1, 密碼: testpass123 (張小明)\n'
                '  用戶名: test_student2, 密碼: testpass123 (陳美玲)\n'
                '  用戶名: test_student3, 密碼: testpass123 (林志偉)\n'
            )
        )