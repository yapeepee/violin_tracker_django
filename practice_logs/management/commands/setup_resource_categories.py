"""
設置資源庫分類
"""
from django.core.management.base import BaseCommand
from practice_logs.models import ResourceCategory


class Command(BaseCommand):
    help = '設置資源庫分類'

    def handle(self, *args, **kwargs):
        categories = [
            {
                'name': '樂譜',
                'icon': 'fas fa-music',
                'color': '#1976d2',
                'description': '各類樂譜資源',
                'order': 1
            },
            {
                'name': '教學影片',
                'icon': 'fas fa-video',
                'color': '#f57c00',
                'description': '示範和教學影片',
                'order': 2
            },
            {
                'name': '練習曲',
                'icon': 'fas fa-dumbbell',
                'color': '#388e3c',
                'description': '技巧練習曲目',
                'order': 3
            },
            {
                'name': '音頻示範',
                'icon': 'fas fa-headphones',
                'color': '#7b1fa2',
                'description': '音頻演奏示範',
                'order': 4
            },
            {
                'name': '教學講義',
                'icon': 'fas fa-file-alt',
                'color': '#d32f2f',
                'description': '理論和教學文件',
                'order': 5
            },
            {
                'name': '參考資料',
                'icon': 'fas fa-book',
                'color': '#00796b',
                'description': '其他參考資源',
                'order': 6
            }
        ]
        
        for cat_data in categories:
            category, created = ResourceCategory.objects.get_or_create(
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
        
        self.stdout.write(self.style.SUCCESS('✅ 資源庫分類設置完成'))