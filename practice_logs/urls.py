"""
小提琴練習記錄系統的URL配置。
定義了所有的URL路由和對應的視圖函數。
"""

from django.urls import path
from . import views

app_name = 'practice_logs'

# URL patterns grouped by functionality
urlpatterns = [
    # 頁面路由
    path('', views.index, name='index'),
    path('analytics/<str:student_name>/', views.analytics, name='analytics'),
    
    # 數據圖表API
    path('api/chart-data', views.chart_data, name='chart_data'),
    path('api/weekly-practice/', views.get_weekly_practice_data, name='weekly_practice'),
    path('api/piece-practice/', views.get_piece_practice_data, name='piece_practice'),
    
    # 練習統計API
    path('api/recent-trend/', views.get_recent_trend_data, name='recent_trend'),
    path('api/rest-days/', views.get_rest_day_stats, name='rest_days'),
    path('api/piece-switching/', views.get_piece_switching_stats, name='piece_switching'),
    path('api/focus-stats/', views.get_focus_stats, name='focus_stats'),
]
