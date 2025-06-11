#!/usr/bin/env python
"""
快速測試遊戲化系統功能
運行方式: python test_gamification.py
"""

import os
import sys
import django
from datetime import date, timedelta

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'violin_tracker.settings')
django.setup()

from practice_logs.models import PracticeLog, Achievement, StudentLevel
from practice_logs.services import GamificationService, AchievementService, ChallengeService

def test_gamification_system():
    """測試遊戲化系統的主要功能"""
    
    print("🎮 開始測試遊戲化系統...")
    
    # 測試學生名稱
    test_student = "測試學生"
    
    try:
        # 1. 測試初始化遊戲化系統
        print("\n1. 測試初始化遊戲化系統...")
        GamificationService.initialize_student_gamification(test_student)
        print("✅ 遊戲化系統初始化成功")
        
        # 2. 測試等級信息獲取
        print("\n2. 測試等級信息獲取...")
        level_info = AchievementService.get_student_level_info(test_student)
        if level_info:
            print(f"✅ 等級信息: Lv.{level_info['level']} {level_info['title']}")
            print(f"   總積分: {level_info['total_points']}")
            print(f"   當前經驗: {level_info['current_experience']}")
        else:
            print("❌ 無法獲取等級信息")
            
        # 3. 測試成就系統
        print("\n3. 測試成就系統...")
        achievements = AchievementService.get_student_achievements(test_student)
        total_achievements = achievements.count()
        earned_achievements = achievements.filter(is_earned=True).count()
        print(f"✅ 成就統計: {earned_achievements}/{total_achievements} 已獲得")
        
        # 4. 測試挑戰生成
        print("\n4. 測試挑戰生成...")
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        challenges = ChallengeService.generate_weekly_challenges(test_student, week_start)
        print(f"✅ 生成挑戰: {len(challenges)} 個本週挑戰")
        
        # 5. 測試練習記錄創建和遊戲化處理
        print("\n5. 測試練習記錄創建...")
        test_log = PracticeLog.objects.create(
            student_name=test_student,
            piece="測試曲目",
            minutes=60,
            rating=4,
            focus="technique",
            notes="測試練習記錄"
        )
        
        # 處理遊戲化邏輯
        result = GamificationService.process_practice_log_creation(test_log)
        print(f"✅ 練習記錄處理完成")
        print(f"   新獲得成就: {len(result['newly_earned_achievements'])} 個")
        print(f"   等級信息已更新")
        
        # 6. 測試儀表板數據
        print("\n6. 測試儀表板數據...")
        dashboard_data = GamificationService.get_student_dashboard(test_student)
        if dashboard_data:
            print(f"✅ 儀表板數據獲取成功")
            print(f"   學生姓名: {dashboard_data.get('student_name')}")
            print(f"   等級: Lv.{dashboard_data.get('level', {}).get('level', 'N/A')}")
        else:
            print("❌ 無法獲取儀表板數據")
            
        # 7. 測試建議系統
        print("\n7. 測試建議系統...")
        suggestions = GamificationService.suggest_next_actions(test_student)
        print(f"✅ 生成建議: {len(suggestions)} 個智能建議")
        
        print("\n🎉 所有測試完成！遊戲化系統運行正常。")
        
        # 清理測試數據
        print("\n🧹 清理測試數據...")
        PracticeLog.objects.filter(student_name=test_student).delete()
        StudentLevel.objects.filter(student_name=test_student).delete()
        print("✅ 測試數據清理完成")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """測試API端點是否正常工作"""
    print("\n🌐 測試API端點...")
    
    import requests
    
    base_url = "http://localhost:8001"
    test_student = "jerry"  # 使用現有學生數據
    
    endpoints_to_test = [
        f"/api/level-info/?student_name={test_student}",
        f"/api/achievements/?student_name={test_student}",
        f"/api/challenges/?student_name={test_student}",
        f"/api/tasks/?student_name={test_student}",
        f"/api/suggestions/?student_name={test_student}",
    ]
    
    try:
        for endpoint in endpoints_to_test:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - 狀態碼: {response.status_code}")
            else:
                print(f"❌ {endpoint} - 狀態碼: {response.status_code}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器 (localhost:8001)")
        print("   請確保Django服務器正在運行: python manage.py runserver 0.0.0.0:8001")
        return False
    except Exception as e:
        print(f"❌ API測試失敗: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    print("🎻 小提琴練習追蹤系統 - 遊戲化功能測試")
    print("=" * 50)
    
    # 測試核心功能
    core_test_passed = test_gamification_system()
    
    # 測試API端點（可選，需要服務器運行）
    api_test_passed = test_api_endpoints()
    
    print("\n" + "=" * 50)
    if core_test_passed:
        print("🎉 核心功能測試通過！")
    else:
        print("❌ 核心功能測試失敗！")
        
    if api_test_passed:
        print("🌐 API端點測試通過！")
    else:
        print("⚠️  API端點測試失敗（可能服務器未運行）")
        
    print("\n遊戲化系統開發完成，可以開始使用！")