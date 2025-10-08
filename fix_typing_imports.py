import os
import re

def fix_typing_imports(directory):
    """修正所有 Python 檔案中的 typing 模組導入"""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 修正 typing 導入
                content = re.sub(
                    r'from modules\.typing import ([\w\s,]+)',
                    r'from typing import \1',
                    content
                )
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"檢查並修正: {file_path}")

if __name__ == '__main__':
    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    server_dir = os.path.join(os.path.dirname(__file__), 'server')
    
    print("開始修正 typing 模組導入...")
    fix_typing_imports(modules_dir)
    fix_typing_imports(server_dir)
    print("完成！")