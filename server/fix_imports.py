import os
import re

def fix_relative_imports(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(directory, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替換相對導入為絕對導入
            content = content.replace('from .', 'from modules.')
            content = re.sub(r'from ([a-zA-Z_][a-zA-Z0-9_]*) import', r'from modules.\1 import', content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Updated {filename}")

if __name__ == '__main__':
    modules_dir = os.path.join(os.path.dirname(__file__), '..', 'modules')
    fix_relative_imports(modules_dir)
    print("All files updated")