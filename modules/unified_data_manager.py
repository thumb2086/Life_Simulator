import os
import json
import sqlite3
import logging
from typing import Dict, Any, Optional, Union
from game_data import GameData


class UnifiedDataManager:
    """
    統一的資料管理層，支援JSON檔案和SQLite資料庫雙重存儲格式
    提供跨平台存檔遷移和統一的資料操作介面
    """

    def __init__(self, db_path: str = None, json_save_dir: str = None):
        """
        初始化統一資料管理器

        Args:
            db_path: 資料庫檔案路徑
            json_save_dir: JSON存檔目錄路徑
        """
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), '..', 'server', 'app.db')
        self.json_save_dir = json_save_dir or os.path.join(os.path.dirname(__file__), '..', 'saves')

        # 確保目錄存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.json_save_dir, exist_ok=True)

        self._init_db_schema()

    def _init_db_schema(self):
        """初始化資料庫架構"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # 遊戲存檔表 - 儲存完整的GameData對象
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_saves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT 'desktop', -- 'desktop' 或 'web'
                save_name TEXT NOT NULL,
                game_data TEXT NOT NULL, -- JSON格式的GameData
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, save_name)
            )
        """)

        # 跨平台遷移記錄
        cur.execute("""
            CREATE TABLE IF NOT EXISTS save_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_username TEXT NOT NULL,
                from_platform TEXT NOT NULL,
                from_save_name TEXT NOT NULL,
                to_username TEXT NOT NULL,
                to_platform TEXT NOT NULL,
                to_save_name TEXT NOT NULL,
                migration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_game_data(self, game_data: GameData, username: str,
                      save_name: str = 'default', platform: str = 'desktop') -> bool:
        """
        儲存遊戲資料到統一系統

        Args:
            game_data: GameData對象
            username: 使用者名稱
            save_name: 存檔名稱
            platform: 平台類型 ('desktop' 或 'web')

        Returns:
            bool: 儲存是否成功
        """
        try:
            # 序列化GameData為JSON
            data_dict = self._serialize_game_data(game_data)
            data_json = json.dumps(data_dict, ensure_ascii=False, indent=2, default=str)

            # 同時儲存到資料庫
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO game_saves
                (username, platform, save_name, game_data, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (username, platform, save_name, data_json))

            conn.commit()
            conn.close()

            # 同時儲存為JSON檔案（向後相容）
            json_path = os.path.join(self.json_save_dir, f'save_{username}_{save_name}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2, default=str)

            return True

        except Exception as e:
            logging.error(f"儲存遊戲資料失敗: {e}")
            return False

    def load_game_data(self, username: str, save_name: str = 'default',
                      platform: str = None) -> Optional[GameData]:
        """
        從統一系統載入遊戲資料

        Args:
            username: 使用者名稱
            save_name: 存檔名稱
            platform: 平台類型，None表示自動選擇最新的

        Returns:
            GameData對象或None（如果載入失敗）
        """
        try:
            # 優先從資料庫載入
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            if platform:
                cur.execute("""
                    SELECT game_data FROM game_saves
                    WHERE username=? AND save_name=? AND platform=?
                    ORDER BY updated_at DESC LIMIT 1
                """, (username, save_name, platform))
            else:
                cur.execute("""
                    SELECT game_data FROM game_saves
                    WHERE username=? AND save_name=?
                    ORDER BY updated_at DESC LIMIT 1
                """, (username, save_name))

            row = cur.fetchone()
            conn.close()

            if row:
                data_dict = json.loads(row[0])
                game_data = self._deserialize_game_data(data_dict)
                return game_data

            # 如果資料庫中沒有，嘗試從JSON檔案載入
            json_path = os.path.join(self.json_save_dir, f'save_{username}_{save_name}.json')
            if os.path.exists(json_path):
                return self._load_from_json_file(json_path)

            return None

        except Exception as e:
            logging.error(f"載入遊戲資料失敗: {e}")
            return None

    def migrate_save(self, from_username: str, from_platform: str, from_save_name: str,
                    to_username: str, to_platform: str, to_save_name: str) -> bool:
        """
        跨平台存檔遷移

        Args:
            from_*: 來源資訊
            to_*: 目標資訊

        Returns:
            bool: 遷移是否成功
        """
        try:
            # 載入來源存檔
            source_data = self.load_game_data(from_username, from_save_name, from_platform)
            if not source_data:
                logging.error("無法載入來源存檔")
                return False

            # 儲存到目標位置
            success = self.save_game_data(source_data, to_username, to_save_name, to_platform)
            if not success:
                logging.error("無法儲存到目標位置")
                return False

            # 記錄遷移
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO save_migrations
                (from_username, from_platform, from_save_name, to_username, to_platform, to_save_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (from_username, from_platform, from_save_name, to_username, to_platform, to_save_name))
            conn.commit()
            conn.close()

            logging.info(f"存檔遷移成功: {from_username}({from_platform}) -> {to_username}({to_platform})")
            return True

        except Exception as e:
            logging.error(f"存檔遷移失敗: {e}")
            return False

    def list_saves(self, username: str = None, platform: str = None) -> list:
        """
        列出存檔列表

        Args:
            username: 使用者名稱篩選
            platform: 平台篩選

        Returns:
            存檔資訊列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            query = "SELECT username, platform, save_name, created_at, updated_at FROM game_saves"
            params = []

            conditions = []
            if username:
                conditions.append("username=?")
                params.append(username)
            if platform:
                conditions.append("platform=?")
                params.append(platform)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY updated_at DESC"

            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            return [{
                'username': row[0],
                'platform': row[1],
                'save_name': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            } for row in rows]

        except Exception as e:
            logging.error(f"列出存檔失敗: {e}")
            return []

    def _serialize_game_data(self, game_data: GameData) -> Dict[str, Any]:
        """序列化GameData對象，排除無法序列化的屬性"""
        data = {}
        for key, value in game_data.__dict__.items():
            # 排除無法序列化的物件
            if key in ['achievements_manager']:
                continue
            # 將複雜物件轉換為可序列化格式
            try:
                json.dumps(value, default=str)
                data[key] = value
            except (TypeError, ValueError):
                logging.warning(f"跳過無法序列化的屬性: {key}")
                continue
        return data

    def _deserialize_game_data(self, data_dict: Dict[str, Any]) -> GameData:
        """反序列化為GameData對象"""
        game_data = GameData()
        game_data.__dict__.update(data_dict)
        return game_data

    def _load_from_json_file(self, file_path: str) -> Optional[GameData]:
        """從JSON檔案載入GameData"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            game_data = GameData()
            game_data.__dict__.update(data)
            return game_data
        except Exception as e:
            logging.error(f"從JSON檔案載入失敗: {e}")
            return None

    def export_to_json(self, username: str, save_name: str,
                      output_path: str, platform: str = None) -> bool:
        """
        將資料庫中的存檔匯出為JSON檔案

        Args:
            username: 使用者名稱
            save_name: 存檔名稱
            output_path: 輸出檔案路徑
            platform: 平台類型

        Returns:
            bool: 匯出是否成功
        """
        try:
            game_data = self.load_game_data(username, save_name, platform)
            if not game_data:
                return False

            data_dict = self._serialize_game_data(game_data)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2, default=str)
            return True

        except Exception as e:
            logging.error(f"匯出JSON失敗: {e}")
            return False

    def import_from_json(self, json_path: str, username: str,
                        save_name: str, platform: str = 'desktop') -> bool:
        """
        從JSON檔案匯入存檔到統一系統

        Args:
            json_path: JSON檔案路徑
            username: 使用者名稱
            save_name: 存檔名稱
            platform: 平台類型

        Returns:
            bool: 匯入是否成功
        """
        try:
            game_data = self._load_from_json_file(json_path)
            if not game_data:
                return False

            return self.save_game_data(game_data, username, save_name, platform)

        except Exception as e:
            logging.error(f"匯入JSON失敗: {e}")
            return False
