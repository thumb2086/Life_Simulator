# --- leaderboard.py (修改後) ---

import json
import os
import logging

class Leaderboard:
    def __init__(self, filename='leaderboard.json'):
        self.filename = filename
        self.records = self.load()

    def add_record(self, username, asset, days):
        # 先移除同帳號舊紀錄，只保留最新一筆
        self.records = [r for r in self.records if r['username'] != username]
        self.records.append({'username': username, 'asset': asset, 'days': days})
        self.save()

    def get_top(self, username=None):
        if username:
            filtered = [r for r in self.records if r['username'] == username]
        else:
            filtered = self.records
        return sorted(filtered, key=lambda r: (-r['asset'], r['days']))[:100]

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def load(self):
        if os.path.exists(self.filename):
            try:
                # 檢查檔案大小，如果為 0 則視為空檔案
                if os.path.getsize(self.filename) > 0:
                    with open(self.filename, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    return [] # 檔案存在但為空，返回空列表
            except json.JSONDecodeError:
                # 處理檔案內容為無效 JSON 的情況 (例如只有空格或部分內容)
                logging.warning(f"警告: {self.filename} 檔案內容無效，將重置為空列表。")
                return []
            except Exception as e:
                # 處理其他可能的讀取錯誤
                logging.error(f"讀取 {self.filename} 時發生未知錯誤: {e}")
                return []
        return [] # 檔案不存在，返回空列表

class CasinoLeaderboard(Leaderboard):
    def __init__(self, filename='slot_casino.json'):
        super().__init__(filename)
    def add_casino_record(self, username, win):
        # 累加玩家賭場總贏金
        found = False
        for r in self.records:
            if r['username'] == username:
                r['casino_win'] = r.get('casino_win', 0) + win
                found = True
                break
        if not found:
            self.records.append({'username': username, 'casino_win': win})
        self.save()
    def get_top_casino(self, username=None):
        if username:
            filtered = [r for r in self.records if r['username'] == username]
        else:
            filtered = self.records
        return sorted(filtered, key=lambda r: -r.get('casino_win', 0))[:100]