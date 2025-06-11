"""
錄音系統服務類
處理錄音上傳、教師評分、進度追蹤等業務邏輯
"""

import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Avg, Count
from django.utils import timezone
from ..models import PracticeRecording, RecordingComment, RecordingProgress
import logging

logger = logging.getLogger(__name__)


class RecordingService:
    """錄音系統服務類"""
    
    @staticmethod
    def validate_recording_file(file):
        """驗證錄音檔案"""
        errors = []
        
        # 檢查檔案大小
        max_size = settings.RECORDING_UPLOAD_SETTINGS.get('MAX_FILE_SIZE', 100 * 1024 * 1024)
        if file.size > max_size:
            errors.append(f"檔案大小不能超過 {max_size // (1024*1024)}MB")
        
        # 檢查檔案類型
        file_ext = os.path.splitext(file.name)[1].lower().replace('.', '')
        allowed_audio = settings.RECORDING_UPLOAD_SETTINGS.get('ALLOWED_AUDIO_EXTENSIONS', [])
        allowed_video = settings.RECORDING_UPLOAD_SETTINGS.get('ALLOWED_VIDEO_EXTENSIONS', [])
        allowed_extensions = allowed_audio + allowed_video
        
        if file_ext not in allowed_extensions:
            errors.append(f"不支援的檔案格式。支援的格式: {', '.join(allowed_extensions)}")
        
        return errors
    
    @staticmethod
    def create_recording(student_name, piece, recording_type, file, week_number, 
                        self_rating, notes=""):
        """創建新的錄音記錄"""
        try:
            # 驗證檔案
            errors = RecordingService.validate_recording_file(file)
            if errors:
                raise ValueError("; ".join(errors))
            
            # 創建錄音記錄
            recording = PracticeRecording.objects.create(
                student_name=student_name,
                piece=piece,
                recording_type=recording_type,
                file_path=file,
                week_number=week_number,
                self_rating=self_rating,
                notes=notes,
                file_size=file.size,
                status='ready'  # 直接設為就緒，因為我們不做複雜的處理
            )
            
            # 更新進度追蹤
            RecordingService.update_recording_progress(student_name, piece)
            
            logger.info(f"創建錄音記錄: {student_name} - {piece}")
            return recording
            
        except Exception as e:
            logger.error(f"創建錄音記錄時發生錯誤: {str(e)}")
            raise
    
    @staticmethod
    def add_teacher_feedback(recording_id, teacher_name, teacher_score=None, feedback=""):
        """添加教師回饋"""
        try:
            recording = PracticeRecording.objects.get(id=recording_id)
            
            # 更新教師評分和回饋
            if teacher_score is not None:
                recording.teacher_score = teacher_score
            if feedback:
                recording.teacher_feedback = feedback
            
            recording.save()
            
            # 創建系統評論記錄
            if feedback:
                RecordingComment.objects.create(
                    recording=recording,
                    commenter_type='teacher',
                    commenter_name=teacher_name,
                    comment=feedback,
                    rating=teacher_score if teacher_score else None,
                    is_encouraging=True,
                    is_pinned=True  # 教師評論預設置頂
                )
            
            # 更新進度追蹤
            RecordingService.update_recording_progress(
                recording.student_name, recording.piece
            )
            
            logger.info(f"教師 {teacher_name} 對錄音 {recording_id} 添加了回饋")
            return recording
            
        except PracticeRecording.DoesNotExist:
            logger.error(f"錄音記錄不存在: {recording_id}")
            raise
        except Exception as e:
            logger.error(f"添加教師回饋時發生錯誤: {str(e)}")
            raise
    
    @staticmethod
    def add_comment(recording_id, commenter_name, commenter_type, comment, 
                   rating=None, reply_to=None):
        """添加評論"""
        try:
            recording = PracticeRecording.objects.get(id=recording_id)
            
            comment_obj = RecordingComment.objects.create(
                recording=recording,
                commenter_type=commenter_type,
                commenter_name=commenter_name,
                comment=comment,
                rating=rating,
                reply_to_id=reply_to,
                is_encouraging=True  # 預設為鼓勵性評論
            )
            
            logger.info(f"{commenter_name} 對錄音 {recording_id} 添加了評論")
            return comment_obj
            
        except PracticeRecording.DoesNotExist:
            logger.error(f"錄音記錄不存在: {recording_id}")
            raise
        except Exception as e:
            logger.error(f"添加評論時發生錯誤: {str(e)}")
            raise
    
    @staticmethod
    def update_recording_progress(student_name, piece):
        """更新錄音進度追蹤"""
        try:
            recordings = PracticeRecording.objects.filter(
                student_name=student_name,
                piece=piece,
                status='ready'
            ).order_by('upload_date')
            
            if not recordings.exists():
                return
            
            first_recording = recordings.first()
            latest_recording = recordings.last()
            
            # 計算週數跨度
            weeks_span = 0
            if recordings.count() > 1:
                first_week = first_recording.week_number
                latest_week = latest_recording.week_number
                weeks_span = latest_week - first_week + 1
            
            # 更新或創建進度記錄
            progress, created = RecordingProgress.objects.update_or_create(
                student_name=student_name,
                piece=piece,
                defaults={
                    'first_recording': first_recording,
                    'latest_recording': latest_recording,
                    'total_recordings': recordings.count(),
                    'weeks_span': weeks_span
                }
            )
            
            # 計算進步分數
            progress.calculate_improvement()
            
            if created:
                logger.info(f"創建進度追蹤: {student_name} - {piece}")
            else:
                logger.info(f"更新進度追蹤: {student_name} - {piece}")
            
            return progress
            
        except Exception as e:
            logger.error(f"更新錄音進度時發生錯誤: {str(e)}")
            return None
    
    @staticmethod
    def get_student_recordings(student_name, piece=None, limit=None):
        """獲取學生的錄音列表"""
        query = PracticeRecording.objects.filter(
            student_name=student_name,
            status='ready'
        ).order_by('-upload_date')
        
        if piece:
            query = query.filter(piece=piece)
        
        if limit:
            query = query[:limit]
        
        return query
    
    @staticmethod
    def get_recordings_needing_feedback():
        """獲取需要教師回饋的錄音"""
        return PracticeRecording.objects.filter(
            status='ready',
            teacher_score__isnull=True,
            teacher_feedback=""
        ).order_by('upload_date')
    
    @staticmethod
    def get_featured_recordings(limit=10):
        """獲取精選錄音"""
        return PracticeRecording.objects.filter(
            is_featured=True,
            is_public=True,
            status='ready'
        ).order_by('-upload_date')[:limit]
    
    @staticmethod
    def get_recording_statistics(student_name):
        """獲取錄音統計信息"""
        recordings = PracticeRecording.objects.filter(
            student_name=student_name,
            status='ready'
        )
        
        stats = recordings.aggregate(
            total_recordings=Count('id'),
            avg_self_rating=Avg('self_rating'),
            avg_teacher_score=Avg('teacher_score')
        )
        
        # 計算有教師評分的錄音數量
        with_teacher_feedback = recordings.filter(
            teacher_score__isnull=False
        ).count()
        
        # 計算精選錄音數量
        featured_count = recordings.filter(is_featured=True).count()
        
        # 最近的錄音
        recent_recording = recordings.first()
        
        return {
            'total_recordings': stats['total_recordings'] or 0,
            'avg_self_rating': round(stats['avg_self_rating'] or 0, 2),
            'avg_teacher_score': round(stats['avg_teacher_score'] or 0, 2),
            'with_teacher_feedback': with_teacher_feedback,
            'featured_count': featured_count,
            'recent_recording': recent_recording,
            'feedback_percentage': (with_teacher_feedback / (stats['total_recordings'] or 1)) * 100
        }
    
    @staticmethod
    def get_improvement_summary(student_name, piece=None):
        """獲取進步摘要"""
        query = RecordingProgress.objects.filter(student_name=student_name)
        
        if piece:
            query = query.filter(piece=piece)
        
        progress_records = query.order_by('-improvement_score')
        
        summary = {
            'total_pieces': progress_records.count(),
            'improving_pieces': progress_records.filter(improvement_score__gt=0).count(),
            'stable_pieces': progress_records.filter(improvement_score=0).count(),
            'declining_pieces': progress_records.filter(improvement_score__lt=0).count(),
            'best_improvement': progress_records.first(),
            'progress_records': list(progress_records[:5])  # 前5個進步最多的曲目
        }
        
        return summary
    
    @staticmethod
    def delete_old_recordings():
        """刪除過期的錄音檔案（系統維護用）"""
        if not settings.RECORDING_UPLOAD_SETTINGS.get('AUTO_DELETE_OLD_FILES', False):
            return 0
        
        days_to_keep = settings.RECORDING_UPLOAD_SETTINGS.get('DAYS_TO_KEEP_FILES', 365)
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        
        old_recordings = PracticeRecording.objects.filter(
            upload_date__lt=cutoff_date
        )
        
        deleted_count = 0
        for recording in old_recordings:
            try:
                # 刪除檔案
                if recording.file_path:
                    default_storage.delete(recording.file_path.name)
                if recording.thumbnail:
                    default_storage.delete(recording.thumbnail.name)
                
                # 刪除記錄
                recording.delete()
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"刪除舊錄音時發生錯誤: {str(e)}")
        
        logger.info(f"刪除了 {deleted_count} 個過期錄音")
        return deleted_count