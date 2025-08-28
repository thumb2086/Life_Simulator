#!/usr/bin/env python3
"""
簡單掃描腳本 - 檢查基本模組和常數
"""

import sys
import os
from pathlib import Path

def scan_project():
    """掃描專案"""
    # 找到專案根目錄
    script_dir = Path(__file__).parent
    modules_dir = script_dir / "modules"

    print(f"Project root: {script_dir}")
    print(f"Modules dir: {modules_dir}")

    # 檢查模組目錄是否存在
    if not modules_dir.exists():
        print("ERROR: modules directory not found")
        return False

    # 檢查關鍵檔案
    key_files = [
        "config.py",
        "game_data.py",
        "bank_game.py",
        "achievements.py",
        "events.py"
    ]

    missing_files = []
    for file in key_files:
        if not (modules_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"ERROR: Missing files: {missing_files}")
        return False

    print("All key files found")

    # 設定模組路徑
    sys.path.insert(0, str(modules_dir))

    # 測試匯入
    tests = [
        ("config", "PERSIST_DEBOUNCE_MS, UNIFIED_TICK_MS, TIME_LABEL_MS"),
        ("game_data", "GameData"),
        ("bank_game", "BankGame"),
        ("achievements", "AchievementsManager"),
        ("events", "EventManager")
    ]

    failed_tests = []

    for module_name, test_items in tests:
        try:
            module = __import__(module_name)
            print(f"PASS: {module_name} imported successfully")

            # 測試特定項目
            if test_items == "GameData":
                gd = module.GameData()
                print(f"PASS: {test_items} instantiated")
            elif test_items == "BankGame":
                print(f"PASS: {test_items} class found")
            elif "PERSIST_DEBOUNCE_MS" in test_items:
                const_val = getattr(module, 'PERSIST_DEBOUNCE_MS', None)
                if const_val is not None:
                    print(f"PASS: Constants loaded - PERSIST_DEBOUNCE_MS = {const_val}")
                else:
                    print(f"FAIL: Constants not found in {module_name}")
                    failed_tests.append(f"{module_name} constants")

        except Exception as e:
            print(f"FAIL: {module_name} - {e}")
            failed_tests.append(module_name)

    # 總結
    if failed_tests:
        print(f"\nFAILED TESTS: {len(failed_tests)}")
        for test in failed_tests:
            print(f"  - {test}")
        return False
    else:
        print("\nALL TESTS PASSED!")
        return True

if __name__ == "__main__":
    success = scan_project()
    sys.exit(0 if success else 1)
