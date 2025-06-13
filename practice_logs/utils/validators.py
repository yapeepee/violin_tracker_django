"""
參數驗證工具
統一處理所有參數驗證邏輯，避免重複程式碼
"""
from datetime import datetime, timedelta
from django.utils import timezone
from practice_logs.utils.constants import Constants
import logging

logger = logging.getLogger(__name__)


class ParameterValidator:
    """參數驗證器，提供統一的驗證方法"""
    
    @staticmethod
    def validate_days(days_param, default=None, min_days=1, max_days=None):
        """
        驗證天數參數
        
        Args:
            days_param: 輸入的天數參數（可能是字串或數字）
            default: 預設值（如果沒有指定，使用 Constants.DEFAULT_DAYS）
            min_days: 最小天數（預設為1）
            max_days: 最大天數（如果沒有指定，使用 Constants.MAX_DAYS）
            
        Returns:
            int: 驗證後的天數
        """
        if default is None:
            default = Constants.DEFAULT_DAYS
        if max_days is None:
            max_days = Constants.MAX_DAYS
            
        try:
            days = int(days_param)
            return max(min_days, min(days, max_days))
        except (ValueError, TypeError):
            logger.warning(f"Invalid days parameter: {days_param}, using default: {default}")
            return default
    
    @staticmethod
    def validate_date_range(start_date_str, end_date_str, max_range_days=None):
        """
        驗證日期範圍
        
        Args:
            start_date_str: 開始日期字串
            end_date_str: 結束日期字串
            max_range_days: 最大允許的日期範圍（天數）
            
        Returns:
            tuple: (start_date, end_date) 或 (None, None) 如果驗證失敗
        """
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                # 預設為30天前
                start_date = timezone.now().date() - timedelta(days=30)
                
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                # 預設為今天
                end_date = timezone.now().date()
                
            # 確保開始日期不晚於結束日期
            if start_date > end_date:
                start_date, end_date = end_date, start_date
                
            # 檢查日期範圍
            if max_range_days:
                date_diff = (end_date - start_date).days
                if date_diff > max_range_days:
                    # 調整開始日期
                    start_date = end_date - timedelta(days=max_range_days)
                    logger.warning(f"Date range too large, adjusted to {max_range_days} days")
                    
            return start_date, end_date
            
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return None, None
    
    @staticmethod
    def validate_rating(rating_param, min_rating=1, max_rating=5):
        """
        驗證評分參數
        
        Args:
            rating_param: 輸入的評分參數
            min_rating: 最小評分（預設1）
            max_rating: 最大評分（預設5）
            
        Returns:
            int: 驗證後的評分，如果無效則返回 None
        """
        try:
            rating = int(rating_param)
            if min_rating <= rating <= max_rating:
                return rating
            logger.warning(f"Rating {rating} out of range [{min_rating}, {max_rating}]")
            return None
        except (ValueError, TypeError):
            logger.warning(f"Invalid rating parameter: {rating_param}")
            return None
    
    @staticmethod
    def validate_minutes(minutes_param, min_minutes=1, max_minutes=480):
        """
        驗證練習分鐘數
        
        Args:
            minutes_param: 輸入的分鐘數參數
            min_minutes: 最小分鐘數（預設1）
            max_minutes: 最大分鐘數（預設480，即8小時）
            
        Returns:
            int: 驗證後的分鐘數，如果無效則返回 None
        """
        try:
            minutes = int(minutes_param)
            if min_minutes <= minutes <= max_minutes:
                return minutes
            logger.warning(f"Minutes {minutes} out of range [{min_minutes}, {max_minutes}]")
            return None
        except (ValueError, TypeError):
            logger.warning(f"Invalid minutes parameter: {minutes_param}")
            return None
    
    @staticmethod
    def validate_pagination(page_param, per_page_param=None, max_per_page=100):
        """
        驗證分頁參數
        
        Args:
            page_param: 頁碼參數
            per_page_param: 每頁項目數參數
            max_per_page: 每頁最大項目數
            
        Returns:
            tuple: (page, per_page)
        """
        # 驗證頁碼
        try:
            page = max(1, int(page_param))
        except (ValueError, TypeError):
            page = 1
            
        # 驗證每頁項目數
        if per_page_param:
            try:
                per_page = int(per_page_param)
                per_page = max(1, min(per_page, max_per_page))
            except (ValueError, TypeError):
                per_page = 20
        else:
            per_page = 20
            
        return page, per_page
    
    @staticmethod
    def validate_sort_order(sort_param, allowed_fields=None, default='date'):
        """
        驗證排序參數
        
        Args:
            sort_param: 排序參數（例如 'date-desc', 'rating-asc'）
            allowed_fields: 允許的排序欄位列表
            default: 預設排序欄位
            
        Returns:
            tuple: (field, order) 例如 ('date', 'desc')
        """
        if not allowed_fields:
            allowed_fields = ['date', 'rating', 'minutes', 'piece']
            
        if not sort_param:
            return default, 'desc'
            
        parts = sort_param.lower().split('-')
        
        if len(parts) == 2:
            field, order = parts
            if field in allowed_fields and order in ['asc', 'desc']:
                return field, order
                
        logger.warning(f"Invalid sort parameter: {sort_param}, using default")
        return default, 'desc'
    
    @staticmethod
    def validate_student_name(student_name, allow_empty=False):
        """
        驗證學生姓名
        
        Args:
            student_name: 學生姓名
            allow_empty: 是否允許空值
            
        Returns:
            str: 清理後的學生姓名，如果無效則返回 None
        """
        if not student_name:
            return None if not allow_empty else ''
            
        # 清理字串
        cleaned_name = str(student_name).strip()
        
        # 檢查長度
        if len(cleaned_name) < 1 or len(cleaned_name) > 100:
            logger.warning(f"Invalid student name length: {len(cleaned_name)}")
            return None
            
        # 檢查是否包含無效字元
        invalid_chars = ['<', '>', '"', "'", '&', '/', '\\']
        for char in invalid_chars:
            if char in cleaned_name:
                logger.warning(f"Invalid character in student name: {char}")
                return None
                
        return cleaned_name
    
    @staticmethod
    def validate_instrument_code(instrument_code, valid_codes=None):
        """
        驗證樂器代碼
        
        Args:
            instrument_code: 樂器代碼
            valid_codes: 有效的樂器代碼列表
            
        Returns:
            str: 驗證後的樂器代碼，如果無效則返回 None
        """
        if not instrument_code:
            return None
            
        code = str(instrument_code).upper().strip()
        
        if valid_codes:
            if code not in valid_codes:
                logger.warning(f"Invalid instrument code: {code}")
                return None
                
        return code
    
    @staticmethod
    def sanitize_search_query(query, max_length=100):
        """
        清理搜尋查詢字串
        
        Args:
            query: 搜尋查詢字串
            max_length: 最大長度
            
        Returns:
            str: 清理後的查詢字串
        """
        if not query:
            return ''
            
        # 移除多餘空白
        cleaned = ' '.join(query.strip().split())
        
        # 限制長度
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
            
        # 移除可能的 SQL 注入字元
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            cleaned = cleaned.replace(char, '')
            
        return cleaned