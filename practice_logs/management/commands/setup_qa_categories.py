"""
設置問答系統分類
"""
from django.core.management.base import BaseCommand
from practice_logs.models import QuestionCategory


class Command(BaseCommand):
    help = '設置問答系統分類'

    def handle(self, *args, **kwargs):
        categories = [
            {
                'name': '演奏技巧',
                'icon': 'fas fa-music',
                'color': '#2c5f3d',
                'description': '關於小提琴演奏技巧的問題',
                'order': 1
            },
            {
                'name': '樂理知識',
                'icon': 'fas fa-book',
                'color': '#1976d2',
                'description': '音樂理論相關問題',
                'order': 2
            },
            {
                'name': '曲目相關',
                'icon': 'fas fa-file-music',
                'color': '#7b1fa2',
                'description': '特定曲目的演奏問題',
                'order': 3
            },
            {
                'name': '練習方法',
                'icon': 'fas fa-dumbbell',
                'color': '#d32f2f',
                'description': '練習技巧和方法',
                'order': 4
            },
            {
                'name': '器材設備',
                'icon': 'fas fa-violin',
                'color': '#f57c00',
                'description': '小提琴、弓、松香等器材問題',
                'order': 5
            },
            {
                'name': '其他問題',
                'icon': 'fas fa-question-circle',
                'color': '#616161',
                'description': '其他類型的問題',
                'order': 6
            }
        ]
        
        for cat_data in categories:
            category, created = QuestionCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'description': cat_data['description'],
                    'order': cat_data['order']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'創建分類: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'分類已存在: {category.name}')
                )
        
        self.stdout.write(self.style.SUCCESS('✅ 問答系統分類設置完成'))