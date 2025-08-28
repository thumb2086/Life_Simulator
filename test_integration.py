#!/usr/bin/env python3
"""
統一系統整合測試腳本
測試所有新整合的功能是否正常運作
"""

import os
import sys
import json
import time
from datetime import datetime

# 確保可以匯入模組
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
modules_dir = os.path.join(parent_dir, 'modules')

sys.path.insert(0, parent_dir)  # 加入專案根目錄
sys.path.insert(0, modules_dir)  # 加入模組目錄

# 匯入模組
try:
    from game_data import GameData
    from unified_data_manager import UnifiedDataManager
    from unified_stock_manager import UnifiedStockManager
    from unified_achievement_manager import UnifiedAchievementManager
except ImportError as e:
    print(f"❌ 模組匯入失敗: {e}")
    print("請確保所有必要檔案都存在且路徑正確")
    sys.exit(1)


class IntegrationTestSuite:
    """整合測試套件"""

    def __init__(self):
        self.test_results = []
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'test_app.db')
        self.json_save_dir = os.path.join(os.path.dirname(__file__), '..', 'test_saves')

        # 確保測試目錄存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.json_save_dir, exist_ok=True)

        # 初始化測試管理器
        self.data_manager = UnifiedDataManager(db_path=self.db_path)
        self.stock_manager = UnifiedStockManager(db_path=self.db_path)
        self.achievement_manager = UnifiedAchievementManager(db_path=self.db_path)

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """記錄測試結果"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")

    def test_game_data_creation(self):
        """測試遊戲資料建立"""
        try:
            game_data = GameData()
            game_data.cash = 50000
            game_data.days = 30
            game_data.stocks['TSMC']['owned'] = 10
            self.log_test_result("GameData Creation", True, "成功建立遊戲資料對象")
            return game_data
        except Exception as e:
            self.log_test_result("GameData Creation", False, f"建立失敗: {e}")
            return None

    def test_data_manager_save_load(self):
        """測試資料管理器儲存載入"""
        try:
            # 建立測試資料
            game_data = self.test_game_data_creation()
            if not game_data:
                return False

            username = "test_user"
            save_name = "integration_test"

            # 測試儲存
            success = self.data_manager.save_game_data(game_data, username, save_name, 'web')
            if not success:
                self.log_test_result("Data Manager Save/Load", False, "儲存失敗")
                return False

            # 測試載入
            loaded_data = self.data_manager.load_game_data(username, save_name, 'web')
            if not loaded_data:
                self.log_test_result("Data Manager Save/Load", False, "載入失敗")
                return False

            # 驗證資料完整性
            if (loaded_data.cash == game_data.cash and
                loaded_data.days == game_data.days and
                loaded_data.stocks['TSMC']['owned'] == game_data.stocks['TSMC']['owned']):
                self.log_test_result("Data Manager Save/Load", True, "儲存載入功能正常")
                return True
            else:
                self.log_test_result("Data Manager Save/Load", False, "資料完整性檢查失敗")
                return False

        except Exception as e:
            self.log_test_result("Data Manager Save/Load", False, f"測試異常: {e}")
            return False

    def test_stock_manager_operations(self):
        """測試股票管理器操作"""
        try:
            # 獲取股票價格
            prices = self.stock_manager.sync_prices_from_database()
            if not prices:
                self.log_test_result("Stock Manager Operations", False, "無法獲取股票價格")
                return False

            # 測試投資組合價值計算
            holdings = {
                'TSMC': {'qty': 10, 'avg_cost': 90.0},
                'HONHAI': {'qty': 5, 'avg_cost': 70.0}
            }

            portfolio_value = self.stock_manager.calculate_portfolio_value(holdings, prices)
            if portfolio_value > 0:
                self.log_test_result("Stock Manager Operations", True, f"投資組合價值計算正常: ${portfolio_value:.2f}")
                return True
            else:
                self.log_test_result("Stock Manager Operations", False, "投資組合價值計算失敗")
                return False

        except Exception as e:
            self.log_test_result("Stock Manager Operations", False, f"測試異常: {e}")
            return False

    def test_achievement_system(self):
        """測試成就系統"""
        try:
            # 建立測試遊戲資料
            game_data = GameData()
            game_data.cash = 20000  # 應該解鎖"資產破萬"成就
            game_data.days = 50     # 應該解鎖"生存者"成就
            game_data.stocks['TSMC']['owned'] = 5  # 應該解鎖"第一次買股票"成就

            # 檢查成就
            newly_unlocked = self.achievement_manager.check_achievements(game_data, "test_user")

            if len(newly_unlocked) >= 2:  # 至少應該解鎖2個成就
                achievement_names = [a.name for a in newly_unlocked]
                self.log_test_result("Achievement System", True, f"成功解鎖成就: {', '.join(achievement_names)}")
                return True
            else:
                self.log_test_result("Achievement System", False, f"成就解鎖數量不足: {len(newly_unlocked)}")
                return False

        except Exception as e:
            self.log_test_result("Achievement System", False, f"測試異常: {e}")
            return False

    def test_cross_platform_migration(self):
        """測試跨平台存檔遷移"""
        try:
            # 建立來源資料
            source_data = GameData()
            source_data.cash = 75000
            source_data.days = 100
            source_data.stocks['TSMC']['owned'] = 20

            # 儲存為桌面版格式
            success1 = self.data_manager.save_game_data(source_data, "migrate_test", "desktop_save", 'desktop')
            if not success1:
                self.log_test_result("Cross Platform Migration", False, "來源儲存失敗")
                return False

            # 遷移到Web版
            success2 = self.data_manager.migrate_save(
                "migrate_test", 'desktop', "desktop_save",
                "migrate_test", 'web', "web_save"
            )

            if not success2:
                self.log_test_result("Cross Platform Migration", False, "遷移操作失敗")
                return False

            # 驗證遷移結果
            migrated_data = self.data_manager.load_game_data("migrate_test", "web_save", 'web')
            if (migrated_data and
                migrated_data.cash == source_data.cash and
                migrated_data.days == source_data.days):
                self.log_test_result("Cross Platform Migration", True, "跨平台遷移成功")
                return True
            else:
                self.log_test_result("Cross Platform Migration", False, "遷移資料驗證失敗")
                return False

        except Exception as e:
            self.log_test_result("Cross Platform Migration", False, f"測試異常: {e}")
            return False

    def test_api_endpoints_simulation(self):
        """模擬API端點測試"""
        try:
            # 模擬Web API調用
            username = "api_test_user"
            game_data = GameData()
            game_data.cash = 30000
            game_data.days = 75

            # 測試存檔API
            save_success = self.data_manager.save_game_data(game_data, username, 'default', 'web')

            # 測試載入API
            load_data = self.data_manager.load_game_data(username, 'default', 'web')

            # 測試成就檢查API
            achievements = self.achievement_manager.check_achievements(load_data, username)

            if save_success and load_data and len(achievements) >= 1:
                self.log_test_result("API Endpoints Simulation", True, "API模擬測試通過")
                return True
            else:
                self.log_test_result("API Endpoints Simulation", False, "API模擬測試失敗")
                return False

        except Exception as e:
            self.log_test_result("API Endpoints Simulation", False, f"測試異常: {e}")
            return False

    def test_data_integrity(self):
        """測試資料完整性"""
        try:
            # 建立複雜的遊戲資料
            game_data = GameData()
            game_data.cash = 150000
            game_data.days = 365
            game_data.happiness = 85
            game_data.intelligence = 80
            game_data.stocks['TSMC']['owned'] = 50
            game_data.stocks['HONHAI']['owned'] = 30
            game_data.job = {'name': '工程師', 'level': 2}
            game_data.education_level = '碩士'

            # 序列化測試
            username = "integrity_test"
            save_success = self.data_manager.save_game_data(game_data, username, 'complex', 'web')

            # 反序列化測試
            load_data = self.data_manager.load_game_data(username, 'complex', 'web')

            # 完整性檢查
            checks = [
                load_data.cash == game_data.cash,
                load_data.days == game_data.days,
                load_data.happiness == game_data.happiness,
                load_data.stocks['TSMC']['owned'] == game_data.stocks['TSMC']['owned'],
                load_data.education_level == game_data.education_level
            ]

            if save_success and load_data and all(checks):
                self.log_test_result("Data Integrity", True, "資料完整性測試通過")
                return True
            else:
                failed_checks = [i for i, check in enumerate(checks) if not check]
                self.log_test_result("Data Integrity", False, f"完整性檢查失敗: {failed_checks}")
                return False

        except Exception as e:
            self.log_test_result("Data Integrity", False, f"測試異常: {e}")
            return False

    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始執行統一系統整合測試...")
        print("=" * 50)

        test_methods = [
            self.test_game_data_creation,
            self.test_data_manager_save_load,
            self.test_stock_manager_operations,
            self.test_achievement_system,
            self.test_cross_platform_migration,
            self.test_api_endpoints_simulation,
            self.test_data_integrity
        ]

        passed = 0
        total = len(test_methods)

        for test_method in test_methods:
            print(f"\n🔍 執行測試: {test_method.__name__}")
            if test_method():
                passed += 1
            time.sleep(0.1)  # 小延遲避免資源衝突

        print("\n" + "=" * 50)
        print(f"📊 測試結果總結: {passed}/{total} 通過")

        if passed == total:
            print("🎉 所有測試通過！統一系統整合成功！")
            success_rate = 100.0
        else:
            print(f"⚠️  有 {total - passed} 項測試失敗，需要檢查")
            success_rate = (passed / total) * 100

        # 生成測試報告
        self.generate_test_report(success_rate)

        return passed == total

    def generate_test_report(self, success_rate: float):
        """生成測試報告"""
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r['success']]),
                'failed_tests': len([r for r in self.test_results if not r['success']]),
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': os.getcwd()
            }
        }

        report_path = os.path.join(self.json_save_dir, 'integration_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📝 測試報告已儲存至: {report_path}")

        # 顯示失敗的測試
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n❌ 失敗的測試:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")


def main():
    """主測試函數"""
    try:
        test_suite = IntegrationTestSuite()
        success = test_suite.run_all_tests()

        if success:
            print("\n✅ 整合測試完成 - 所有系統運行正常！")
            return 0
        else:
            print("\n❌ 整合測試完成 - 發現問題需要修復")
            return 1

    except Exception as e:
        print(f"\n💥 測試套件執行失敗: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
