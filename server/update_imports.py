import os
import re

def update_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新所有匯入語句
    content = content.replace('from seasonal_events import', 'from modules.seasonal_events import')
    content = content.replace('from mini_games import', 'from modules.mini_games import')
    content = content.replace('from market_news_events import', 'from modules.market_news_events import')
    content = content.replace('from multiplayer_manager import', 'from modules.multiplayer_manager import')
    content = content.replace('from game_data import', 'from modules.game_data import')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    file_path = os.path.join(os.path.dirname(__file__), 'main.py')
    update_imports(file_path)
    print("更新完成")