#!/usr/bin/env python3
"""
整體程式碼掃描與修復腳本
系統性檢查所有模組、匯入、常數和功能
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

class CodeScanner:
    """程式碼掃描器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.modules_dir = self.project_root / "modules"
        self.issues = []
        self.fixed = []

    def log_issue(self, category, message, severity="error"):
        """記錄問題"""
        self.issues.append({
            'category': category,
            'message': message,
            'severity': severity
        })
        print(f"[{severity.upper()}] {category}: {message}")

    def log_fix(self, message):
        """記錄修復"""
        self.fixed.append(message)
        print(f"[FIXED] {message}")

    def scan_modules(self):
        """掃描所有模組"""
        print("🔍 掃描模組目錄...")

        if not self.modules_dir.exists():
            self.log_issue("directory", f"模組目錄不存在: {self.modules_dir}")
            return

        py_files = list(self.modules_dir.glob("*.py"))
        print(f"發現 {len(py_files)} 個 Python 模組檔案")

        for py_file in py_files:
            self.scan_module_file(py_file)

    def scan_module_file(self, file_path):
        """掃描單個模組檔案"""
        try:
            module_name = file_path.stem

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查匯入語句
            self.check_imports(content, module_name, file_path)

            # 檢查常數使用
            self.check_constants(content, module_name, file_path)

            # 檢查類別定義
            self.check_classes(content, module_name, file_path)

        except Exception as e:
            self.log_issue("file_scan", f"掃描檔案失敗 {file_path}: {e}")

    def check_imports(self, content, module_name, file_path):
        """檢查匯入語句"""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('from ') or line.startswith('import '):
                try:
                    # 嘗試解析匯入語句
                    if line.startswith('from '):
                        parts = line.split()
                        if len(parts) >= 4 and parts[2] == 'import':
                            module_path = parts[1]
                            # 檢查相對匯入
                            if module_path.startswith('.'):
                                continue
                            # 檢查是否為標準庫或第三方庫
                            if '.' not in module_path and module_path not in ['os', 'sys', 'json', 'time', 'random', 'datetime', 'logging', 'tkinter', 'pathlib']:
                                # 檢查本地模組是否存在
                                module_file = self.modules_dir / f"{module_path}.py"
                                if not module_file.exists():
                                    self.log_issue("import", f"{file_path.name}:{i} 匯入模組不存在: {module_path}")

                except Exception as e:
                    self.log_issue("import_parse", f"{file_path.name}:{i} 無法解析匯入: {line}")

    def check_constants(self, content, module_name, file_path):
        """檢查常數使用"""
        # 檢查常見的常數名稱
        constants_to_check = [
            'PERSIST_DEBOUNCE_MS', 'UNIFIED_TICK_MS', 'TIME_LABEL_MS',
            'LEADERBOARD_REFRESH_MS', 'API_BASE_URL', 'API_KEY',
            'STOCK_UPDATE_TICKS', 'BTC_VOLATILITY', 'BTC_MIN_PRICE'
        ]

        for const in constants_to_check:
            if const in content:
                # 如果使用了常數但沒有從 config 匯入，記錄問題
                if 'from config import' not in content:
                    self.log_issue("constant", f"{file_path.name} 使用常數 {const} 但未從 config 匯入")
                elif const not in content:
                    self.log_issue("constant", f"{file_path.name} 使用常數 {const} 但 config 匯入中未包含")

    def check_classes(self, content, module_name, file_path):
        """檢查類別定義"""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('class '):
                try:
                    # 檢查類別名稱
                    class_def = line.split('(')[0].replace('class ', '')
                    if not class_def[0].isupper():
                        self.log_issue("class_naming", f"{file_path.name}:{i} 類別名稱應以大寫開頭: {class_def}")
                except:
                    pass

    def test_imports(self):
        """測試所有匯入"""
        print("\n🔍 測試模組匯入...")

        # 設定模組路徑
        if str(self.modules_dir) not in sys.path:
            sys.path.insert(0, str(self.modules_dir))

        # 要測試的核心模組
        core_modules = [
            'game_data',
            'bank_game',
            'config',
            'achievements',
            'events',
            'leaderboard',
            'slot_machine',
            'stock_manager',
            'ui_sections',
            'theme_manager'
        ]

        for module_name in core_modules:
            try:
                module = importlib.import_module(module_name)
                print(f"✅ {module_name} 匯入成功")
            except ImportError as e:
                self.log_issue("import_test", f"模組 {module_name} 匯入失敗: {e}")
            except Exception as e:
                self.log_issue("import_test", f"模組 {module_name} 載入錯誤: {e}")

    def test_config_constants(self):
        """測試配置常數"""
        print("\n🔍 測試配置常數...")

        try:
            from config import (
                PERSIST_DEBOUNCE_MS, UNIFIED_TICK_MS, API_BASE_URL, API_KEY,
                STOCK_UPDATE_TICKS, TIME_LABEL_MS, LEADERBOARD_REFRESH_MS,
                BTC_VOLATILITY, BTC_MIN_PRICE, CRYPTO_MINED_PER_HASHRATE, MONTH_DAYS
            )

            print("✅ 所有配置常數載入成功")

            # 檢查常數值
            if not isinstance(PERSIST_DEBOUNCE_MS, int) or PERSIST_DEBOUNCE_MS <= 0:
                self.log_issue("config_value", f"PERSIST_DEBOUNCE_MS 值無效: {PERSIST_DEBOUNCE_MS}")

            if not isinstance(UNIFIED_TICK_MS, int) or UNIFIED_TICK_MS <= 0:
                self.log_issue("config_value", f"UNIFIED_TICK_MS 值無效: {UNIFIED_TICK_MS}")

        except ImportError as e:
            self.log_issue("config_import", f"配置常數匯入失敗: {e}")
        except Exception as e:
            self.log_issue("config_test", f"配置常數測試失敗: {e}")

    def test_game_data_functionality(self):
        """測試遊戲資料功能"""
        print("\n🔍 測試遊戲資料功能...")

        try:
            from game_data import GameData

            # 測試 GameData 初始化
            data = GameData()
            print("✅ GameData 初始化成功")

            # 測試基本屬性
            if not hasattr(data, 'cash'):
                self.log_issue("game_data", "GameData 缺少 cash 屬性")

            if not hasattr(data, 'balance'):
                self.log_issue("game_data", "GameData 缺少 balance 屬性")

            # 測試儲存功能
            test_file = self.project_root / "test_save.json"
            success = data.save(str(test_file))
            if success:
                print("✅ GameData 儲存功能正常")
                if test_file.exists():
                    test_file.unlink()  # 清理測試檔案
            else:
                self.log_issue("game_data", "GameData 儲存功能失敗")

        except Exception as e:
            self.log_issue("game_data_test", f"GameData 測試失敗: {e}")
            traceback.print_exc()

    def test_bank_game_initialization(self):
        """測試 BankGame 初始化"""
        print("\n🔍 測試 BankGame 初始化...")

        try:
            import tkinter as tk
            from game_data import GameData
            from bank_game import BankGame

            # 建立隱藏的視窗進行測試
            root = tk.Tk()
            root.withdraw()  # 隱藏視窗

            data = GameData()
            game = BankGame(root, data)

            print("✅ BankGame 初始化成功")

            # 測試基本屬性
            if not hasattr(game, 'data'):
                self.log_issue("bank_game", "BankGame 缺少 data 屬性")

            if not hasattr(game, 'root'):
                self.log_issue("bank_game", "BankGame 缺少 root 屬性")

            # 清理
            root.destroy()

        except Exception as e:
            self.log_issue("bank_game_test", f"BankGame 測試失敗: {e}")
            traceback.print_exc()

    def generate_report(self):
        """產生報告"""
        print("\n" + "="*60)
        print("📋 掃描報告")
        print("="*60)

        # 問題統計
        error_count = len([i for i in self.issues if i['severity'] == 'error'])
        warning_count = len([i for i in self.issues if i['severity'] == 'warning'])

        print(f"❌ 錯誤數量: {error_count}")
        print(f"⚠️  警告數量: {warning_count}")
        print(f"✅ 已修復: {len(self.fixed)}")

        if self.issues:
            print("\n🔧 發現的問題:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['category']}: {issue['message']}")

        if self.fixed:
            print("\n✨ 已修復的問題:")
            for i, fix in enumerate(self.fixed, 1):
                print(f"  {i}. {fix}")

        print("\n" + "="*60)

    def run_full_scan(self):
        """執行完整掃描"""
        print("🚀 開始整體程式碼掃描...")
        print(f"專案根目錄: {self.project_root}")
        print(f"模組目錄: {self.modules_dir}")

        self.scan_modules()
        self.test_imports()
        self.test_config_constants()
        self.test_game_data_functionality()
        self.test_bank_game_initialization()

        self.generate_report()

        return len([i for i in self.issues if i['severity'] == 'error']) == 0

def main():
    """主函數"""
    scanner = CodeScanner()
    success = scanner.run_full_scan()

    if success:
        print("\n🎉 掃描完成！所有檢查都通過了。")
        return 0
    else:
        print(f"\n💥 掃描完成！發現 {len(scanner.issues)} 個問題需要修復。")
        return 1

if __name__ == "__main__":
    exit(main())
