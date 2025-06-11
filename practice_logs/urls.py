"""
小提琴練習記錄系統的URL配置。
定義了所有的URL路由和對應的視圖函數。
"""

from django.urls import path
from . import views
from . import auth_views
from . import teacher_hub
from . import student_management
from . import qa_center
from . import resource_library
from . import lesson_management

app_name = 'practice_logs'

# URL patterns grouped by functionality
urlpatterns = [
    # 頁面路由
    path('', views.index, name='index'),
    path('add/', views.add_log, name='add_log'),
    path('my-practices/', views.my_practices, name='my_practices'),
    path('achievements/', views.achievements_page, name='achievements'),
    path('analytics/<str:student_name>/', views.analytics, name='analytics'),
    path('upload/', views.practice_upload_page, name='practice_upload'),
    
    # 影片管理系統路由
    path('videos/upload/', views.video_upload_view, name='video_upload'),
    path('videos/library/', views.video_library_view, name='video_library'),
    path('videos/player/<int:recording_id>/', views.video_player_view, name='video_player'),
    
    # 遊戲化頁面路由 (已暫時移除)
    # path('dashboard/<str:student_name>/', views.gamification_dashboard, name='gamification_dashboard'),
    # path('achievements/<str:student_name>/', views.achievements_page, name='achievements'),
    # path('challenges/<str:student_name>/', views.challenges_page, name='challenges'),
    
    # 數據圖表API
    path('api/chart-data', views.chart_data, name='chart_data'),
    path('api/weekly-practice/', views.get_weekly_practice_data, name='weekly_practice'),
    path('api/piece-practice/', views.get_piece_practice_data, name='piece_practice'),
    
    # 練習統計API
    path('api/recent-trend/', views.get_recent_trend_data, name='recent_trend'),
    path('api/rest-days/', views.get_rest_day_stats, name='rest_days'),
    path('api/piece-switching/', views.get_piece_switching_stats, name='piece_switching'),
    path('api/focus-stats/', views.get_focus_stats, name='focus_stats'),
    path('api/student-pieces/', views.get_student_pieces, name='student_pieces'),
    path('api/period-stats/', views.get_period_stats, name='period_stats'),
    
    # 練習記錄上傳API
    path('api/upload-practice/', views.upload_practice_record, name='upload_practice'),
    
    # 測試頁面
    path('test-rating/', views.test_rating_page, name='test_rating'),
    
    # 用戶認證路由
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/register/', auth_views.register_view, name='register'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/profile/', auth_views.profile_view, name='profile'),
    path('auth/edit-profile/', auth_views.edit_profile_view, name='edit_profile'),
    path('auth/change-password/', auth_views.change_password_view, name='change_password'),
    path('auth/upload-avatar/', auth_views.upload_avatar_view, name='upload_avatar'),
    path('auth/login-history/', auth_views.login_history_view, name='login_history'),
    
    # 儀表板路由
    path('dashboard/student/', auth_views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/teacher/', auth_views.teacher_dashboard_view, name='teacher_dashboard'),
    
    # 技能分析API
    path('api/focus-skill-analysis/', views.get_focus_skill_analysis, name='focus_skill_analysis'),
    path('api/skill-comparison/', views.get_skill_comparison_chart, name='skill_comparison'),
    
    # 影片管理API
    path('api/videos/<int:recording_id>/comment/', views.add_video_comment, name='add_video_comment'),
    path('api/video-progress/', views.video_progress_api, name='video_progress'),
    
    # 師生關係管理
    path('teachers/selection/', views.teacher_selection_view, name='teacher_selection'),
    path('api/teachers/select/', views.select_teacher_api, name='select_teacher'),
    path('api/teachers/remove/<int:relation_id>/', views.remove_teacher_api, name='remove_teacher'),
    
    # 教師影片管理
    path('teacher/videos/', views.teacher_video_dashboard, name='teacher_video_dashboard'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # 教師回饋系統
    path('feedback/form/<int:practice_log_id>/', views.teacher_feedback_form_view, name='teacher_feedback_form'),
    path('feedback/detail/<int:feedback_id>/', views.feedback_detail_view, name='feedback_detail'),
    path('feedback/history/', views.feedback_history_view, name='feedback_history'),
    path('api/feedback/<int:feedback_id>/response/', views.student_feedback_response, name='student_feedback_response'),
    
    # 新版教師系統路由
    path('teacher/hub/', teacher_hub.teacher_hub_dashboard, name='teacher_hub'),
    path('teacher/students/', student_management.student_management_page, name='teacher_students'),
    path('teacher/students/<int:student_id>/', student_management.student_detail_view, name='student_detail'),
    path('teacher/students/<int:student_id>/update-progress/', student_management.update_student_progress, name='update_student_progress'),
    
    # 問答中心路由
    path('teacher/qa/', qa_center.qa_center_dashboard, name='teacher_qa'),
    path('teacher/questions/', qa_center.question_list_view, name='teacher_question_list'),
    path('teacher/questions/<int:question_id>/answer/', qa_center.answer_question_view, name='answer_question'),
    path('teacher/faq/', qa_center.faq_management_view, name='faq_management'),
    path('teacher/faq/create/', qa_center.create_faq_view, name='create_faq'),
    path('teacher/faq/<int:faq_id>/edit/', qa_center.edit_faq_view, name='edit_faq'),
    path('teacher/faq/<int:faq_id>/delete/', qa_center.delete_faq_view, name='delete_faq'),
    
    # 學生問題路由
    path('student/ask-question/', qa_center.student_ask_question, name='student_ask_question'),
    path('student/my-questions/', qa_center.student_questions, name='student_questions'),
    path('faq/', qa_center.public_faq, name='public_faq'),
    path('api/save-question-draft/', qa_center.save_question_draft, name='save_question_draft'),
    
    # 資源庫路由
    path('teacher/resources/', resource_library.resource_library_home, name='teacher_resources'),
    path('teacher/resources/upload/', resource_library.upload_resource, name='upload_resource'),
    path('teacher/resources/<int:resource_id>/', resource_library.resource_detail, name='resource_detail'),
    path('teacher/resources/<int:resource_id>/download/', resource_library.download_resource, name='download_resource'),
    path('teacher/resources/<int:resource_id>/delete/', resource_library.delete_resource, name='delete_resource'),
    path('teacher/collections/', resource_library.manage_collections, name='manage_collections'),
    path('teacher/collections/<int:collection_id>/', resource_library.collection_detail, name='collection_detail'),
    path('teacher/resources/analytics/', resource_library.resource_analytics, name='resource_analytics'),
    
    # 資源庫 API
    path('api/resources/add-to-collection/', resource_library.add_to_collection, name='add_to_collection'),
    path('api/resources/remove-from-collection/', resource_library.remove_from_collection, name='remove_from_collection'),
    
    # 課程管理系統路由
    path('teacher/lessons/', lesson_management.lesson_calendar_view, name='lesson_calendar'),
    path('teacher/lessons/create/', lesson_management.create_lesson_view, name='create_lesson'),
    path('teacher/lessons/<int:lesson_id>/', lesson_management.lesson_detail_view, name='lesson_detail'),
    path('teacher/lessons/<int:lesson_id>/update-status/', lesson_management.update_lesson_status, name='update_lesson_status'),
    path('teacher/lessons/<int:lesson_id>/reschedule/', lesson_management.reschedule_lesson, name='reschedule_lesson'),
    path('teacher/lessons/<int:lesson_id>/note/', lesson_management.create_lesson_note, name='create_lesson_note'),
    path('teacher/lessons/list/all/', lesson_management.lesson_list_view, name='lesson_list'),
    path('teacher/lessons/batch-create/', lesson_management.batch_create_lessons, name='batch_create_lessons'),
    path('teacher/lessons/analytics/', lesson_management.lesson_analytics, name='lesson_analytics'),
    
    path('teacher/feedback-center/', teacher_hub.teacher_hub_dashboard, name='feedback_center'),  # 暫時指向hub
    
    # 教師系統API
    path('api/teacher/student-progress/', teacher_hub.get_student_progress_api, name='api_student_progress'),
    path('api/teacher/pending-items/', teacher_hub.get_pending_items_api, name='api_pending_items'),
    path('api/teacher/quick-stats/', teacher_hub.quick_stats_api, name='api_quick_stats'),
    path('api/teacher/update-student-group/', student_management.update_student_group, name='api_update_student_group'),
    path('api/teacher/batch-message/', student_management.batch_send_message, name='api_batch_message'),
    
    # 遊戲化API (已暫時移除)
    # path('api/dashboard/', views.get_student_dashboard, name='get_student_dashboard'),
    # path('api/achievements/', views.get_achievements, name='get_achievements'),
    # path('api/level-info/', views.get_level_info, name='get_level_info'),
    # path('api/challenges/', views.get_challenges, name='get_challenges'),
    # path('api/tasks/', views.get_tasks, name='get_tasks'),
    # path('api/tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    # path('api/leaderboard/', views.get_leaderboard, name='get_leaderboard'),
    # path('api/suggestions/', views.get_suggestions, name='get_suggestions'),
]
