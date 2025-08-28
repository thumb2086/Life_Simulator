#!/usr/bin/env python3
"""
測試腳本：驗證 bank_game.py 模組載入是否正常
"""

import sys
import os

def test_bank_game_import():
    """測試 bank_game 模組匯入"""
    try:
        # 設定模組路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, 'modules')

        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        # 匯入 bank_game 模組
        from bank_game import BankGame

        print("✅ bank_game 模組載入成功！")
        print(f"   BankGame 類別：{BankGame}")
        print("   所有常數已正確匯入")

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

if __name__ == "__main__":
    print("🔍 測試 bank_game 模組載入...")
    success = test_bank_game_import()

    if success:
        print("\n🎉 測試通過！PERSIST_DEBOUNCE_MS 錯誤已修復。")
    else:
        print("\n💥 測試失敗！請檢查錯誤訊息。")
