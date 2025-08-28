#!/usr/bin/env python3
"""
簡化整合驗證腳本 - 無特殊字符版本
逐步驗證統一系統的核心功能
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

def log(message):
    """簡單日誌輸出"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_basic_setup():
    """測試基本設定"""
    log("1. 測試基本檔案存在性...")

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
            log(f"   OK: {file_path}")
        else:
            log(f"   FAIL: {file_path} - 不存在")
            missing_files.append(file_path)

    if missing_files:
        log(f"FAIL: 缺少檔案: {missing_files}")
        return False

    log("PASS: 基本檔案檢查通過")
    return True

def test_directory_structure():
    """測試目錄結構"""
    log("2. 測試目錄結構...")

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
            log(f"   OK: {dir_name}/ 目錄存在")
        else:
            log(f"   FAIL: {dir_name}/ 目錄不存在")
            missing_dirs.append(dir_name)

    if missing_dirs:
        log(f"FAIL: 缺少目錄: {missing_dirs}")
        return False

    log("PASS: 目錄結構檢查通過")
    return True

def test_json_data_integrity():
    """測試JSON資料完整性"""
    log("3. 測試現有存檔資料...")

    saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
    if not os.path.exists(saves_dir):
        log("FAIL: saves/ 目錄不存在")
        return False

    save_files = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
    if not save_files:
        log("WARN: 沒有找到存檔檔案")
        return True

    valid_saves = 0
    for save_file in save_files:
        file_path = os.path.join(saves_dir, save_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            required_fields = ['cash', 'days', 'stocks']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                log(f"   FAIL: {save_file} 缺少欄位: {missing_fields}")
            else:
                valid_saves += 1
                log(f"   OK: {save_file} 資料完整")

        except Exception as e:
            log(f"   FAIL: {save_file} 讀取失敗: {str(e)[:50]}")

    if valid_saves > 0:
        log(f"PASS: 找到 {valid_saves} 個有效存檔")
        return True
    else:
        log("FAIL: 沒有有效存檔")
        return False

def test_server_api_structure():
    """測試伺服器API結構"""
    log("4. 測試伺服器API結構...")

    server_main = os.path.join(os.path.dirname(__file__), 'server', 'main.py')

    try:
        with open(server_main, 'r', encoding='utf-8') as f:
            content = f.read()

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
                log(f"   OK: {endpoint} 端點存在")
            else:
                log(f"   FAIL: {endpoint} 端點不存在")

        if len(found_endpoints) == len(required_endpoints):
            log("PASS: 伺服器API結構檢查通過")
            return True
        else:
            log(f"FAIL: 缺少 {len(required_endpoints) - len(found_endpoints)} 個API端點")
            return False

    except Exception as e:
        log(f"FAIL: 伺服器檔案檢查失敗: {e}")
        return False

def test_module_structure():
    """測試模組檔案結構"""
    log("5. 測試模組檔案結構...")

    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    test_modules = [
        'game_data.py',
        'unified_data_manager.py',
        'unified_stock_manager.py',
        'unified_achievement_manager.py'
    ]

    missing_modules = []
    for module_file in test_modules:
        module_path = os.path.join(modules_dir, module_file)
        if os.path.exists(module_path):
            # 檢查檔案大小
            size = os.path.getsize(module_path)
            if size > 100:  # 至少100字節
                log(f"   OK: {module_file} ({size} bytes)")
            else:
                log(f"   FAIL: {module_file} 檔案過小 ({size} bytes)")
                missing_modules.append(module_file)
        else:
            log(f"   FAIL: {module_file} 不存在")
            missing_modules.append(module_file)

    if missing_modules:
        log(f"FAIL: 模組檔案問題: {missing_modules}")
        return False

    log("PASS: 模組檔案結構檢查通過")
    return True

def generate_report(results):
    """生成整合報告"""
    log("="*50)
    log("INTEGRATION VALIDATION REPORT")
    log("="*50)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    log(f"Total Tests: {total_tests}")
    log(f"Passed: {passed_tests}")
    log(f"Failed: {total_tests - passed_tests}")
    log(".1f")

    if passed_tests == total_tests:
        log("SUCCESS: All validations passed!")
        status = "SUCCESS"
    else:
        log("ISSUES: Some tests failed")
        status = "ISSUES_FOUND"

    log("Detailed Results:")
    for test_name, result in results.items():
        icon = "PASS" if result else "FAIL"
        log(f"  {icon}: {test_name}")

    # Save report
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

    log(f"Report saved to: {report_path}")

    return status == "SUCCESS"

def main():
    """主驗證函數"""
    log("Starting integration validation...")

    test_functions = [
        ('Basic File Check', test_basic_setup),
        ('Directory Structure', test_directory_structure),
        ('JSON Data Integrity', test_json_data_integrity),
        ('Server API Structure', test_server_api_structure),
        ('Module Structure', test_module_structure)
    ]

    results = {}
    for test_name, test_func in test_functions:
        log(f"Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            log(f"Test execution failed: {e}")
            results[test_name] = False

    success = generate_report(results)

    return success

if __name__ == "__main__":
    try:
        success = main()
        if success:
            log("VALIDATION COMPLETE - System ready!")
            sys.exit(0)
        else:
            log("VALIDATION COMPLETE - Issues found")
            sys.exit(1)
    except Exception as e:
        log(f"Validation process error: {e}")
        sys.exit(1)
