#!/usr/bin/env python3
"""
全面測試腳本：驗證所有匯入和常數是否正確
"""

import sys
import os

def test_all_imports():
    """測試所有模組匯入"""
    try:
        # 設定模組路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, 'modules')

        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        print("🔍 測試所有模組匯入...")

        # 測試 config 常數匯入
        from config import (
            PERSIST_DEBOUNCE_MS, UNIFIED_TICK_MS, API_BASE_URL, API_KEY,
            STOCK_UPDATE_TICKS, TIME_LABEL_MS, LEADERBOARD_REFRESH_MS,
            BTC_VOLATILITY, BTC_MIN_PRICE, CRYPTO_MINED_PER_HASHRATE, MONTH_DAYS
        )

        print("✅ config 常數匯入成功")
        print(f"   PERSIST_DEBOUNCE_MS = {PERSIST_DEBOUNCE_MS}")
        print(f"   UNIFIED_TICK_MS = {UNIFIED_TICK_MS}")
        print(f"   TIME_LABEL_MS = {TIME_LABEL_MS}")
        print(f"   LEADERBOARD_REFRESH_MS = {LEADERBOARD_REFRESH_MS}")
        print(f"   BTC_VOLATILITY = {BTC_VOLATILITY}")
        print(f"   BTC_MIN_PRICE = {BTC_MIN_PRICE}")
        print(f"   MONTH_DAYS = {MONTH_DAYS}")

        # 測試系統模組匯入
        from bank_game import BankGame
        from dividend_manager import DividendManager
        from debug_panel import DebugPanel
        from social_system import SocialSystem
        from housing_system import HousingSystem
        from seasonal_system import SeasonalSystem
        from education_career_system import EducationCareerSystem
        from health_system import HealthSystem
        from investment_portfolio_manager import InvestmentPortfolioManager

        print("✅ 所有系統模組匯入成功")

        # 測試核心模組匯入
        from game_data import GameData
        from stock_manager import StockManager
        from entrepreneurship import EntrepreneurshipManager
        from reports_charts import ReportsChartsManager
        from store_expenses import StoreExpensesManager
        from logger import GameLogger
        from job_manager import JobManager
        from achievement_gallery import AchievementGallery
        from travel_system import TravelSystem
        from achievements import AchievementsManager
        from events import EventManager
        from leaderboard import Leaderboard
        from slot_machine import SlotMachine

        print("✅ 所有核心模組匯入成功")

        return True

    except ImportError as e:
        print(f"❌ 匯入錯誤：{e}")
        return False
    except NameError as e:
        print(f"❌ 常數未定義錯誤：{e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤：{e}")
        return False

def test_bank_game_initialization():
    """測試 BankGame 初始化"""
    try:
        print("\n🔍 測試 BankGame 初始化...")

        # 設定模組路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, 'modules')

        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        import tkinter as tk
        from game_data import GameData
        from bank_game import BankGame

        # 創建隱藏的 root 視窗進行測試
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗

        data = GameData()
        game = BankGame(root, data)

        print("✅ BankGame 初始化成功")
        print("✅ 所有系統管理器已正確建立")

        # 清理
        root.destroy()

        return True

    except Exception as e:
        print(f"❌ BankGame 初始化失敗：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 全面測試開始...")

    success1 = test_all_imports()
    success2 = test_bank_game_initialization()

    if success1 and success2:
        print("\n🎉 所有測試通過！程式應該可以正常運行。")
        print("💡 現在您可以嘗試運行 main.py")
    else:
        print("\n💥 測試失敗！請檢查錯誤訊息。")

    print("\n" + "="*50)
    print("📋 測試結果摘要:")
    print(f"   模組匯入測試: {'✅ 通過' if success1 else '❌ 失敗'}")
    print(f"   BankGame 初始化測試: {'✅ 通過' if success2 else '❌ 失敗'}")
