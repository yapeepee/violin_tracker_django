"""
批次處理服務
處理大量資料的批次操作，提高效能
"""
from django.db import transaction, connection
from django.db.models import F, Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
import csv
import json

from practice_logs.models.practice import PracticeLog
from practice_logs.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """批次處理服務"""
    
    # 批次大小設定
    BATCH_SIZE_SMALL = 100
    BATCH_SIZE_MEDIUM = 500
    BATCH_SIZE_LARGE = 1000
    
    @classmethod
    @transaction.atomic
    def bulk_update_practice_stats(cls, student_name: str, date_from: datetime.date = None):
        """
        批次更新練習統計資料
        
        Args:
            student_name: 學生姓名
            date_from: 起始日期（預設為30天前）
        """
        if not date_from:
            date_from = timezone.now().date() - timedelta(days=30)
            
        # 獲取需要更新的記錄
        practices = PracticeLog.objects.filter(
            student_name=student_name,
            date__gte=date_from
        ).select_for_update()
        
        # 批次更新週數和年月
        updates = []
        for practice in practices.iterator(chunk_size=cls.BATCH_SIZE_MEDIUM):
            practice.week_number = practice.date.isocalendar()[1]
            practice.month_year = practice.date.strftime('%Y-%m')
            updates.append(practice)
            
            if len(updates) >= cls.BATCH_SIZE_MEDIUM:
                PracticeLog.objects.bulk_update(
                    updates, 
                    ['week_number', 'month_year'],
                    batch_size=cls.BATCH_SIZE_MEDIUM
                )
                updates = []
        
        # 更新剩餘的記錄
        if updates:
            PracticeLog.objects.bulk_update(
                updates, 
                ['week_number', 'month_year'],
                batch_size=cls.BATCH_SIZE_MEDIUM
            )
            
        logger.info(f"Updated stats for {student_name} from {date_from}")
    
    @classmethod
    def batch_calculate_streaks(cls, student_names: List[str] = None):
        """
        批次計算連續練習天數
        
        Args:
            student_names: 學生姓名列表，如果為空則處理所有學生
        """
        if not student_names:
            # 獲取所有活躍學生
            student_names = PracticeLog.objects.filter(
                date__gte=timezone.now().date() - timedelta(days=30)
            ).values_list('student_name', flat=True).distinct()
        
        results = {}
        
        # 使用原生 SQL 提高效能
        with connection.cursor() as cursor:
            for student_name in student_names:
                cursor.execute("""
                    WITH practice_dates AS (
                        SELECT DISTINCT date 
                        FROM practice_logs_practicelog 
                        WHERE student_name = %s 
                        ORDER BY date DESC 
                        LIMIT 30
                    ),
                    date_groups AS (
                        SELECT 
                            date,
                            date - ROW_NUMBER() OVER (ORDER BY date DESC)::integer AS group_date
                        FROM practice_dates
                    )
                    SELECT 
                        COUNT(*) as streak_length,
                        MAX(date) as last_date
                    FROM date_groups
                    GROUP BY group_date
                    ORDER BY last_date DESC
                    LIMIT 1
                """, [student_name])
                
                result = cursor.fetchone()
                if result:
                    streak_length, last_date = result
                    # 檢查是否包含今天或昨天
                    today = timezone.now().date()
                    if last_date == today or last_date == today - timedelta(days=1):
                        results[student_name] = streak_length
                    else:
                        results[student_name] = 0
                else:
                    results[student_name] = 0
                    
        return results
    
    @classmethod
    def batch_export_practices(cls, student_name: str, format: str = 'csv',
                             date_from: datetime.date = None, 
                             date_to: datetime.date = None) -> str:
        """
        批次匯出練習記錄
        
        Args:
            student_name: 學生姓名
            format: 匯出格式 ('csv' 或 'json')
            date_from: 開始日期
            date_to: 結束日期
            
        Returns:
            str: 匯出的檔案路徑
        """
        # 設定日期範圍
        if not date_to:
            date_to = timezone.now().date()
        if not date_from:
            date_from = date_to - timedelta(days=365)
            
        # 使用 values 減少記憶體使用
        practices = PracticeLog.objects.filter(
            student_name=student_name,
            date__range=[date_from, date_to]
        ).values(
            'date', 'piece', 'minutes', 'rating', 
            'practice_focus', 'notes', 'instrument__name'
        ).order_by('date')
        
        # 生成檔案名稱
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"practice_export_{student_name}_{timestamp}.{format}"
        filepath = f"/tmp/{filename}"
        
        if format == 'csv':
            cls._export_to_csv(practices, filepath)
        elif format == 'json':
            cls._export_to_json(practices, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return filepath
    
    @classmethod
    def _export_to_csv(cls, queryset, filepath):
        """匯出為 CSV 格式"""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['日期', '曲目', '練習時間(分鐘)', '評分', 
                         '練習重點', '筆記', '樂器']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for practice in queryset.iterator(chunk_size=cls.BATCH_SIZE_LARGE):
                writer.writerow({
                    '日期': practice['date'].strftime('%Y-%m-%d'),
                    '曲目': practice['piece'],
                    '練習時間(分鐘)': practice['minutes'],
                    '評分': practice['rating'],
                    '練習重點': practice['practice_focus'],
                    '筆記': practice['notes'] or '',
                    '樂器': practice['instrument__name'] or ''
                })
    
    @classmethod
    def _export_to_json(cls, queryset, filepath):
        """匯出為 JSON 格式"""
        data = []
        for practice in queryset.iterator(chunk_size=cls.BATCH_SIZE_LARGE):
            data.append({
                'date': practice['date'].strftime('%Y-%m-%d'),
                'piece': practice['piece'],
                'minutes': practice['minutes'],
                'rating': practice['rating'],
                'practice_focus': practice['practice_focus'],
                'notes': practice['notes'],
                'instrument': practice['instrument__name']
            })
            
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
    
    @classmethod
    @transaction.atomic
    def batch_import_practices(cls, student_name: str, file_path: str, 
                             format: str = 'csv') -> Dict[str, Any]:
        """
        批次匯入練習記錄
        
        Args:
            student_name: 學生姓名
            file_path: 檔案路徑
            format: 檔案格式
            
        Returns:
            dict: 匯入結果統計
        """
        if format == 'csv':
            data = cls._read_csv(file_path)
        elif format == 'json':
            data = cls._read_json(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        # 準備批次插入的資料
        practices_to_create = []
        existing_count = 0
        error_count = 0
        
        for row in data:
            try:
                # 解析日期
                date = datetime.strptime(row.get('date', ''), '%Y-%m-%d').date()
                
                # 檢查是否已存在
                exists = PracticeLog.objects.filter(
                    student_name=student_name,
                    date=date,
                    piece=row.get('piece', '')
                ).exists()
                
                if exists:
                    existing_count += 1
                    continue
                    
                # 準備新記錄
                practice = PracticeLog(
                    student_name=student_name,
                    date=date,
                    piece=row.get('piece', ''),
                    minutes=int(row.get('minutes', 0)),
                    rating=int(row.get('rating', 3)),
                    practice_focus=row.get('practice_focus', 'general'),
                    notes=row.get('notes', '')
                )
                
                practices_to_create.append(practice)
                
                # 批次插入
                if len(practices_to_create) >= cls.BATCH_SIZE_MEDIUM:
                    PracticeLog.objects.bulk_create(
                        practices_to_create,
                        batch_size=cls.BATCH_SIZE_MEDIUM
                    )
                    practices_to_create = []
                    
            except Exception as e:
                logger.error(f"Error importing row: {row}, error: {e}")
                error_count += 1
        
        # 插入剩餘的記錄
        if practices_to_create:
            created_count = len(practices_to_create)
            PracticeLog.objects.bulk_create(
                practices_to_create,
                batch_size=cls.BATCH_SIZE_MEDIUM
            )
        else:
            created_count = 0
            
        # 清除快取
        CacheManager.clear_student_cache(student_name)
        
        return {
            'total_rows': len(data),
            'created': created_count,
            'existing': existing_count,
            'errors': error_count
        }
    
    @staticmethod
    def _read_csv(file_path: str) -> List[Dict[str, Any]]:
        """讀取 CSV 檔案"""
        data = []
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 映射欄位名稱
                data.append({
                    'date': row.get('日期', row.get('date', '')),
                    'piece': row.get('曲目', row.get('piece', '')),
                    'minutes': row.get('練習時間(分鐘)', row.get('minutes', 0)),
                    'rating': row.get('評分', row.get('rating', 3)),
                    'practice_focus': row.get('練習重點', row.get('practice_focus', 'general')),
                    'notes': row.get('筆記', row.get('notes', ''))
                })
        return data
    
    @staticmethod
    def _read_json(file_path: str) -> List[Dict[str, Any]]:
        """讀取 JSON 檔案"""
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            return json.load(jsonfile)
    
    @classmethod
    def batch_clean_old_data(cls, days_to_keep: int = 365) -> int:
        """
        批次清理舊資料
        
        Args:
            days_to_keep: 保留多少天的資料
            
        Returns:
            int: 刪除的記錄數
        """
        cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
        
        # 先統計要刪除的數量
        delete_count = PracticeLog.objects.filter(
            date__lt=cutoff_date
        ).count()
        
        if delete_count > 0:
            logger.info(f"Preparing to delete {delete_count} old practice records")
            
            # 批次刪除
            deleted = 0
            while True:
                # 每次刪除一批
                batch = PracticeLog.objects.filter(
                    date__lt=cutoff_date
                )[:cls.BATCH_SIZE_LARGE]
                
                if not batch:
                    break
                    
                batch_ids = list(batch.values_list('id', flat=True))
                PracticeLog.objects.filter(id__in=batch_ids).delete()
                deleted += len(batch_ids)
                
                logger.info(f"Deleted {deleted}/{delete_count} records")
                
        return delete_count