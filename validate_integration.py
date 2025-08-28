#!/usr/bin/env python3
"""
簡化整合驗證腳本
逐步驗證統一系統的核心功能
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

def test_basic_setup():
    """測試基本設定"""
    print("1. 測試基本檔案存在性...")

    # 檢查必要檔案是否存在
    required_files = [
        'modules/game_data.py',
        'modules/unified_data_manager.py',
        'modules/unified_stock_manager.py',
        'modules/unified_achievement_manager.py',
        'server/main.py'
    ]

    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} - 不存在")
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ 缺少檔案: {missing_files}")
        return False

    print("✅ 基本檔案檢查通過")
    return True

def test_database_schema():
    """測試資料庫架構"""
    print("\n2. 測試資料庫架構...")

    db_path = os.path.join(os.path.dirname(__file__), 'server', 'test_app.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 檢查必要表格
        required_tables = [
            'game_saves',
            'achievement_unlocks',
            'achievement_stats',
            'stocks',
            'leaderboard'
        ]

        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cur.fetchall()]

        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                print(f"   ✓ {table} 表格存在")
            else:
                print(f"   ✗ {table} 表格不存在")
                missing_tables.append(table)

        conn.close()

        if missing_tables:
            print(f"❌ 缺少表格: {missing_tables}")
            return False

        print("✅ 資料庫架構檢查通過")
        return True

    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
        return False

def test_directory_structure():
    """測試目錄結構"""
    print("\n3. 測試目錄結構...")

    required_dirs = [
        'modules',
        'server',
        'saves',
        'data'
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = os.path.join(os.path.dirname(__file__), dir_name)
        if os.path.exists(dir_path):
            print(f"   ✓ {dir_name}/ 目錄存在")
        else:
            print(f"   ✗ {dir_name}/ 目錄不存在")
            missing_dirs.append(dir_name)

    if missing_dirs:
        print(f"❌ 缺少目錄: {missing_dirs}")
        return False

    print("✅ 目錄結構檢查通過")
    return True

def test_json_data_integrity():
    """測試JSON資料完整性"""
    print("\n4. 測試現有存檔資料...")

    saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
    if not os.path.exists(saves_dir):
        print("   ✗ saves/ 目錄不存在")
        return False

    save_files = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
    if not save_files:
        print("   ⚠ 沒有找到存檔檔案")
        return True  # 不算失敗，只是沒有資料

    valid_saves = 0
    for save_file in save_files:
        file_path = os.path.join(saves_dir, save_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 檢查基本欄位
            required_fields = ['cash', 'days', 'stocks']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                print(f"   ✗ {save_file} 缺少欄位: {missing_fields}")
            else:
                valid_saves += 1
                print(f"   ✓ {save_file} 資料完整")

        except Exception as e:
            print(f"   ✗ {save_file} 讀取失敗: {e}")

    if valid_saves > 0:
        print(f"✅ 找到 {valid_saves} 個有效存檔")
        return True
    else:
        print("❌ 沒有有效存檔")
        return False

def test_server_api_structure():
    """測試伺服器API結構"""
    print("\n5. 測試伺服器API結構...")

    server_main = os.path.join(os.path.dirname(__file__), 'server', 'main.py')

    try:
        with open(server_main, 'r', encoding='utf-8') as f:
            content = f.read()

        # 檢查關鍵API端點
        required_endpoints = [
            '/game/save',
            '/game/load',
            '/stocks/overview',
            '/achievements/check',
            '/achievements/user'
        ]

        found_endpoints = []
        for endpoint in required_endpoints:
            if endpoint in content:
                found_endpoints.append(endpoint)
                print(f"   ✓ {endpoint} 端點存在")
            else:
                print(f"   ✗ {endpoint} 端點不存在")

        if len(found_endpoints) == len(required_endpoints):
            print("✅ 伺服器API結構檢查通過")
            return True
        else:
            print(f"❌ 缺少 {len(required_endpoints) - len(found_endpoints)} 個API端點")
            return False

    except Exception as e:
        print(f"❌ 伺服器檔案檢查失敗: {e}")
        return False

def test_module_imports():
    """測試模組匯入"""
    print("\n6. 測試模組匯入能力...")

    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    sys.path.insert(0, modules_dir)

    test_modules = [
        'game_data',
        'unified_data_manager',
        'unified_stock_manager',
        'unified_achievement_manager'
    ]

    importable_modules = []
    for module in test_modules:
        try:
            module_path = os.path.join(modules_dir, f'{module}.py')
            if os.path.exists(module_path):
                # 嘗試匯入模組
                spec = __import__(module)
                importable_modules.append(module)
                print(f"   ✓ {module} 模組可匯入")
            else:
                print(f"   ✗ {module}.py 檔案不存在")

        except Exception as e:
            print(f"   ✗ {module} 模組匯入失敗: {str(e)[:50]}...")

    if len(importable_modules) == len(test_modules):
        print("✅ 模組匯入檢查通過")
        return True
    else:
        print(f"❌ {len(test_modules) - len(importable_modules)} 個模組無法匯入")
        return False

def generate_integration_report(results):
    """生成整合報告"""
    print("\n" + "="*60)
    print("📊 整合驗證報告")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    print(f"總測試項目: {total_tests}")
    print(f"通過項目: {passed_tests}")
    print(f"失敗項目: {total_tests - passed_tests}")
    print(".1f")

    if passed_tests == total_tests:
        print("🎉 所有驗證通過！系統整合成功！")
        status = "SUCCESS"
    else:
        print("⚠️  發現問題，需要檢查")
        status = "ISSUES_FOUND"

    # 詳細結果
    print("\n詳細測試結果:")
    for test_name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {test_name}")

    # 儲存報告
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'results': results,
        'summary': {
            'total': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
    }

    report_path = os.path.join(os.path.dirname(__file__), 'integration_validation_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📝 報告已儲存至: {report_path}")

    return status == "SUCCESS"

def main():
    """主驗證函數"""
    print("🚀 開始執行統一系統整合驗證...")
    print("這將驗證所有整合組件的基本功能")

    # 執行所有測試
    test_functions = [
        ('基本檔案檢查', test_basic_setup),
        ('資料庫架構檢查', test_database_schema),
        ('目錄結構檢查', test_directory_structure),
        ('JSON資料完整性檢查', test_json_data_integrity),
        ('伺服器API結構檢查', test_server_api_structure),
        ('模組匯入檢查', test_module_imports)
    ]

    results = {}
    for test_name, test_func in test_functions:
        print(f"\n🔍 執行: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 測試執行失敗: {e}")
            results[test_name] = False

    # 生成報告
    success = generate_integration_report(results)

    return success

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 整合驗證完成 - 系統準備就緒！")
            sys.exit(0)
        else:
            print("\n❌ 整合驗證完成 - 發現問題需要修復")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 驗證過程發生錯誤: {e}")
        sys.exit(1)
