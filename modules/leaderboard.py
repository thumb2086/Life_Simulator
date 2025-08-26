# --- leaderboard.py (修改後) ---

import json
import os
import logging
from typing import List, Dict, Optional

try:
    import requests  # optional; used for server API if available
except Exception:  # pragma: no cover
    requests = None

try:
    from config import API_BASE_URL, API_KEY
except Exception:
    API_BASE_URL, API_KEY = None, None

class Leaderboard:
    def __init__(self, filename='leaderboard.json'):
        self.filename = filename
        # 若使用伺服器，初始化本地快取為空；離線時仍可讀取本地檔
        if API_BASE_URL:
            self.records = []
        else:
            self.records = self.load()

    def add_record(self, username, asset, days):
        # 優先呼叫遠端 API
        if API_BASE_URL and requests is not None:
            try:
                url = f"{API_BASE_URL.rstrip('/')}/leaderboard/submit"
                headers = {"X-API-Key": API_KEY or ""}
                payload = {"username": username, "asset": float(asset), "days": int(days)}
                requests.post(url, json=payload, headers=headers, timeout=5).raise_for_status()
                return
            except Exception as e:
                logging.warning(f"Leaderboard API submit failed, fallback to local file: {e}")
        # 本地檔案回退
        self.records = [r for r in self.records if r['username'] != username]
        self.records.append({'username': username, 'asset': asset, 'days': days})
        self.save()

    def get_top(self, username: Optional[str] = None):
        # 優先呼叫遠端 API
        if API_BASE_URL and requests is not None:
            try:
                url = f"{API_BASE_URL.rstrip('/')}/leaderboard/top"
                params = {"username": username} if username else None
                resp = requests.get(url, params=params, timeout=5)
                resp.raise_for_status()
                data = resp.json().get('records', [])
                # 與原回傳格式一致：list[dict]
                return data[:100]
            except Exception as e:
                logging.warning(f"Leaderboard API get_top failed, fallback to local file: {e}")
        # 本地檔案回退
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
        # 優先呼叫遠端 API
        if API_BASE_URL and requests is not None:
            try:
                url = f"{API_BASE_URL.rstrip('/')}/casino/submit"
                headers = {"X-API-Key": API_KEY or ""}
                payload = {"username": username, "win": int(max(0, win))}
                requests.post(url, json=payload, headers=headers, timeout=5).raise_for_status()
                return
            except Exception as e:
                logging.warning(f"Casino API submit failed, fallback to local file: {e}")
        # 本地檔案回退：累加玩家賭場總贏金
        found = False
        for r in self.records:
            if r['username'] == username:
                r['casino_win'] = r.get('casino_win', 0) + max(0, win)
                found = True
                break
        if not found:
            self.records.append({'username': username, 'casino_win': max(0, win)})
        self.save()
    def get_top_casino(self, username=None):
        # 優先呼叫遠端 API
        if API_BASE_URL and requests is not None:
            try:
                url = f"{API_BASE_URL.rstrip('/')}/casino/top"
                params = {"username": username} if username else None
                resp = requests.get(url, params=params, timeout=5)
                resp.raise_for_status()
                data = resp.json().get('records', [])
                return data[:100]
            except Exception as e:
                logging.warning(f"Casino API get_top failed, fallback to local file: {e}")
        # 本地檔案回退
        if username:
            filtered = [r for r in self.records if r['username'] == username]
        else:
            filtered = self.records
        return sorted(filtered, key=lambda r: -r.get('casino_win', 0))[:100]