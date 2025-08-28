"""
Life Simulator Server - 遊戲資料管理模組
處理遊戲存檔、載入、遷移和數據管理
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from pydantic import BaseModel

from game_data import GameData


class SaveLoadRequest(BaseModel):
    """存檔載入請求模型"""
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = None


class MigrateRequest(BaseModel):
    """存檔遷移請求模型"""
    from_username: str
    from_platform: str
    from_save_name: str
    to_username: str
    to_platform: str
    to_save_name: str


class GameDataManager:
    """
    遊戲資料管理器
    負責遊戲存檔、載入、遷移和管理
    """

    def __init__(self, save_directory: str = "saves"):
        self.save_directory = save_directory
        self._ensure_save_directory_exists()

    def _ensure_save_directory_exists(self):
        """確保存檔目錄存在"""
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def _get_save_path(self, username: str, save_name: str, platform: str = 'web') -> str:
        """獲取存檔檔案路徑"""
        return os.path.join(self.save_directory, f"{username}_{save_name}_{platform}.json")

    def save_game_data(self, game_data: GameData, username: str, save_name: str, platform: str) -> bool:
        """
        儲存遊戲資料

        Args:
            game_data: 遊戲資料對象
            username: 用戶名
            save_name: 存檔名稱
            platform: 平台類型

        Returns:
            儲存是否成功
        """
        try:
            save_path = self._get_save_path(username, save_name, platform)

            # 將遊戲資料轉換為字典並添加元資料
            save_data = {
                'metadata': {
                    'username': username,
                    'save_name': save_name,
                    'platform': platform,
                    'saved_at': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'game_data': game_data.__dict__ if hasattr(game_data, '__dict__') else game_data
            }

            # 儲存到檔案
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)

            return True

        except Exception as e:
            print(f"儲存遊戲資料失敗: {e}")
            return False

    def load_game_data(self, username: str, save_name: str, platform: str) -> Optional[GameData]:
        """
        載入遊戲資料

        Args:
            username: 用戶名
            save_name: 存檔名稱
            platform: 平台類型

        Returns:
            GameData對象或None
        """
        try:
            save_path = self._get_save_path(username, save_name, platform)

            if not os.path.exists(save_path):
                return None

            # 從檔案載入資料
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # 建立GameData對象
            game_data = GameData()
            if 'game_data' in save_data:
                game_data.__dict__.update(save_data['game_data'])

            return game_data

        except Exception as e:
            print(f"載入遊戲資料失敗: {e}")
            return None

    def migrate_save(self, from_username: str, from_platform: str, from_save_name: str,
                    to_username: str, to_platform: str, to_save_name: str) -> bool:
        """
        遷移存檔

        Args:
            from_username: 來源用戶名
            from_platform: 來源平台
            from_save_name: 來源存檔名稱
            to_username: 目標用戶名
            to_platform: 目標平台
            to_save_name: 目標存檔名稱

        Returns:
            遷移是否成功
        """
        try:
            # 載入來源存檔
            source_data = self.load_game_data(from_username, from_save_name, from_platform)
            if not source_data:
                return False

            # 儲存到目標位置
            success = self.save_game_data(source_data, to_username, to_save_name, to_platform)

            if success:
                # 可選：刪除來源檔案
                source_path = self._get_save_path(from_username, from_save_name, from_platform)
                if os.path.exists(source_path):
                    os.remove(source_path)

            return success

        except Exception as e:
            print(f"遷移存檔失敗: {e}")
            return False

    def list_saves(self, username: Optional[str] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出存檔列表

        Args:
            username: 用戶名篩選
            platform: 平台篩選

        Returns:
            存檔列表
        """
        try:
            saves = []

            if not os.path.exists(self.save_directory):
                return saves

            for filename in os.listdir(self.save_directory):
                if not filename.endswith('.json'):
                    continue

                try:
                    # 解析檔案名: username_save_name_platform.json
                    parts = filename[:-5].split('_')  # 移除.json並分割
                    if len(parts) >= 3:
                        file_username = parts[0]
                        file_save_name = '_'.join(parts[1:-1])
                        file_platform = parts[-1]

                        # 應用篩選條件
                        if username and file_username != username:
                            continue
                        if platform and file_platform != platform:
                            continue

                        # 獲取檔案資訊
                        filepath = os.path.join(self.save_directory, filename)
                        stat = os.stat(filepath)

                        saves.append({
                            'username': file_username,
                            'save_name': file_save_name,
                            'platform': file_platform,
                            'filename': filename,
                            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'size': stat.st_size
                        })

                except Exception as e:
                    print(f"解析存檔檔案失敗 {filename}: {e}")
                    continue

            # 按修改時間排序
            saves.sort(key=lambda x: x['modified_time'], reverse=True)

            return saves

        except Exception as e:
            print(f"列出存檔失敗: {e}")
            return []

    def export_to_json(self, username: str, save_name: str, output_path: str, platform: str = 'web') -> bool:
        """
        匯出存檔為JSON檔案

        Args:
            username: 用戶名
            save_name: 存檔名稱
            output_path: 輸出檔案路徑
            platform: 平台類型

        Returns:
            匯出是否成功
        """
        try:
            game_data = self.load_game_data(username, save_name, platform)
            if not game_data:
                return False

            save_data = {
                'metadata': {
                    'username': username,
                    'save_name': save_name,
                    'platform': platform,
                    'exported_at': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'game_data': game_data.__dict__ if hasattr(game_data, '__dict__') else game_data
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)

            return True

        except Exception as e:
            print(f"匯出存檔失敗: {e}")
            return False

    def import_from_json(self, json_path: str, username: str, save_name: str, platform: str = 'web') -> bool:
        """
        從JSON檔案匯入存檔

        Args:
            json_path: JSON檔案路徑
            username: 用戶名
            save_name: 存檔名稱
            platform: 平台類型

        Returns:
            匯入是否成功
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if 'game_data' not in import_data:
                return False

            # 建立GameData對象
            game_data = GameData()
            game_data.__dict__.update(import_data['game_data'])

            # 儲存到系統
            return self.save_game_data(game_data, username, save_name, platform)

        except Exception as e:
            print(f"匯入存檔失敗: {e}")
            return False

    def delete_save(self, username: str, save_name: str, platform: str) -> bool:
        """
        刪除存檔

        Args:
            username: 用戶名
            save_name: 存檔名稱
            platform: 平台類型

        Returns:
            刪除是否成功
        """
        try:
            save_path = self._get_save_path(username, save_name, platform)

            if os.path.exists(save_path):
                os.remove(save_path)
                return True

            return False

        except Exception as e:
            print(f"刪除存檔失敗: {e}")
            return False

    def get_save_info(self, username: str, save_name: str, platform: str) -> Optional[Dict[str, Any]]:
        """
        獲取存檔資訊

        Args:
            username: 用戶名
            save_name: 存檔名稱
            platform: 平台類型

        Returns:
            存檔資訊或None
        """
        try:
            save_path = self._get_save_path(username, save_name, platform)

            if not os.path.exists(save_path):
                return None

            # 獲取檔案統計資訊
            stat = os.stat(save_path)

            # 讀取元資料
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})

            return {
                'username': username,
                'save_name': save_name,
                'platform': platform,
                'file_path': save_path,
                'size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'metadata': metadata
            }

        except Exception as e:
            print(f"獲取存檔資訊失敗: {e}")
            return None
