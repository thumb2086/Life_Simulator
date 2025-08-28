import json
import logging
from typing import Dict, List, Any, Optional, Callable
from game_data import GameData


class UnifiedAchievement:
    """
    統一成就類別，支援跨平台成就追蹤
    """

    def __init__(self, key: str, name: str, description: str,
                 condition: Callable, category: str, points: int = 10,
                 rarity: str = 'common', prerequisites: List[str] = None):
        self.key = key
        self.name = name
        self.description = description
        self.condition = condition
        self.category = category
        self.points = points
        self.rarity = rarity  # 'common', 'rare', 'epic', 'legendary'
        self.prerequisites = prerequisites or []
        self.unlocked = False
        self.unlock_time = None
        self.progress = 0.0  # 0.0 to 1.0 for progress tracking


class UnifiedAchievementManager:
    """
    統一成就管理系統，整合桌面版和Web版的成就功能
    支援進度追蹤、跨平台同步和排行榜整合
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.achievements = self._init_achievements()
        self._init_db_schema()

    def _init_db_schema(self):
        """初始化成就相關的資料庫結構"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 成就解鎖記錄
            cur.execute("""
                CREATE TABLE IF NOT EXISTS achievement_unlocks (
                    username TEXT NOT NULL,
                    achievement_key TEXT NOT NULL,
                    unlock_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    platform TEXT DEFAULT 'web',
                    PRIMARY KEY (username, achievement_key)
                )
            """)

            # 成就統計
            cur.execute("""
                CREATE TABLE IF NOT EXISTS achievement_stats (
                    achievement_key TEXT PRIMARY KEY,
                    total_unlocks INTEGER DEFAULT 0,
                    last_unlock TIMESTAMP,
                    rarity TEXT DEFAULT 'common'
                )
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"初始化成就資料庫失敗: {e}")

    def _init_achievements(self) -> List[UnifiedAchievement]:
        """初始化所有成就定義"""
        return [
            # 基礎股票成就
            UnifiedAchievement(
                'first_stock', '第一次買股票', '成功購買任一股票',
                lambda gd: any(s.get('owned', 0) > 0 for s in gd.stocks.values()),
                '股票', 10, 'common'
            ),
            UnifiedAchievement(
                'stock_portfolio_5', '投資組合擴張', '擁有5種不同股票',
                lambda gd: sum(1 for s in gd.stocks.values() if s.get('owned', 0) > 0) >= 5,
                '股票', 25, 'common'
            ),
            UnifiedAchievement(
                'stock_millionaire', '股票百萬富翁', '股票投資總價值超過$100萬',
                lambda gd: sum(s.get('price', 0) * s.get('owned', 0) for s in gd.stocks.values() if s.get('name', '') != '比特幣') >= 1000000,
                '股票', 100, 'rare'
            ),

            # 比特幣成就
            UnifiedAchievement(
                'btc_first', '加密貨幣新手', '首次購買比特幣',
                lambda gd: gd.btc_balance > 0,
                '加密貨幣', 15, 'common'
            ),
            UnifiedAchievement(
                'btc_whale', '比特幣鯨魚', '擁有價值超過$10萬的比特幣',
                lambda gd: gd.btc_balance * gd.stocks.get('BTC', {}).get('price', 0) >= 100000,
                '加密貨幣', 75, 'epic'
            ),

            # 理財成就
            UnifiedAchievement(
                'rich', '資產破萬', '總資產達到 $10,000',
                lambda gd: self._calculate_total_assets(gd) >= 10000,
                '理財', 10, 'common'
            ),
            UnifiedAchievement(
                'millionaire', '百萬富翁', '總資產達到 $1,000,000',
                lambda gd: self._calculate_total_assets(gd) >= 1000000,
                '理財', 100, 'rare'
            ),
            UnifiedAchievement(
                'billionaire', '億萬富翁', '總資產達到 $100,000,000',
                lambda gd: self._calculate_total_assets(gd) >= 100000000,
                '理財', 500, 'legendary'
            ),

            # 工作成就
            UnifiedAchievement(
                'first_job', '初入職場', '獲得第一份工作',
                lambda gd: gd.job is not None,
                '職業', 10, 'common'
            ),
            UnifiedAchievement(
                'executive', '企業高管', '成為經理或更高職位',
                lambda gd: gd.job and gd.job.get('name', '') in ['資深工程師', '經理'],
                '職業', 50, 'rare'
            ),

            # 教育成就
            UnifiedAchievement(
                'graduate', '大學畢業', '學歷達到大學',
                lambda gd: gd.education_level in ['大學', '碩士', '博士'],
                '教育', 20, 'common'
            ),
            UnifiedAchievement(
                'phd', '博士學位', '學歷達到博士',
                lambda gd: gd.education_level == '博士',
                '教育', 75, 'epic'
            ),

            # 屬性成就
            UnifiedAchievement(
                'happy_life', '幸福人生', '快樂度達到90以上',
                lambda gd: gd.happiness >= 90,
                '屬性', 25, 'common'
            ),
            UnifiedAchievement(
                'well_balanced', '均衡發展', '所有屬性都達到70以上',
                lambda gd: all(getattr(gd, attr, 0) >= 70 for attr in ['happiness', 'stamina', 'intelligence', 'diligence', 'charisma']),
                '屬性', 50, 'rare'
            ),

            # 活動成就
            UnifiedAchievement(
                'studious', '勤學好問', '完成讀書活動50次',
                lambda gd: getattr(gd, 'activity_study_count', 0) >= 50,
                '活動', 30, 'common'
            ),
            UnifiedAchievement(
                'zen_master', '禪定大師', '完成冥想活動50次',
                lambda gd: getattr(gd, 'activity_meditate_count', 0) >= 50,
                '活動', 30, 'common'
            ),

            # 遊戲進度成就
            UnifiedAchievement(
                'survivor', '生存者', '遊戲進行超過100天',
                lambda gd: gd.days >= 100,
                '進度', 25, 'common'
            ),
            UnifiedAchievement(
                'veteran', '老兵', '遊戲進行超過365天',
                lambda gd: gd.days >= 365,
                '進度', 75, 'rare'
            ),
            UnifiedAchievement(
                'rebirth', '重生者', '進行第一次重生',
                lambda gd: gd.reborn_count >= 1,
                '進度', 50, 'rare'
            ),

            # 特殊成就
            UnifiedAchievement(
                'jackpot', '頭獎得主', '單筆交易獲利超過$10萬',
                lambda gd: getattr(gd, 'max_single_profit', 0) >= 100000,
                '特殊', 100, 'epic'
            ),
            UnifiedAchievement(
                'trading_master', '交易大師', '累積交易次數超過1000次',
                lambda gd: len(gd.transaction_history) >= 1000,
                '特殊', 75, 'epic'
            )
        ]

    def _calculate_total_assets(self, game_data: GameData) -> float:
        """計算總資產（向後相容舊版GameData）"""
        if hasattr(game_data, 'total_assets') and callable(game_data.total_assets):
            return game_data.total_assets()

        # 手動計算總資產
        cash = getattr(game_data, 'cash', 0)
        loan = getattr(game_data, 'loan', 0)
        stock_value = sum(
            s.get('price', 0) * s.get('owned', 0)
            for s in getattr(game_data, 'stocks', {}).values()
        )

        return cash - loan + stock_value

    def check_achievements(self, game_data: GameData, username: str = None) -> List[UnifiedAchievement]:
        """
        檢查成就解鎖狀態

        Args:
            game_data: 遊戲資料對象
            username: 使用者名稱（用於資料庫記錄）

        Returns:
            新解鎖的成就列表
        """
        newly_unlocked = []

        for achievement in self.achievements:
            if achievement.unlocked:
                continue

            try:
                if achievement.condition(game_data):
                    achievement.unlocked = True
                    achievement.unlock_time = None  # 會在資料庫中記錄時間
                    newly_unlocked.append(achievement)

                    # 記錄到資料庫
                    if username and self.db_path:
                        self._record_achievement_unlock(username, achievement.key)

            except Exception as e:
                logging.warning(f"檢查成就 {achievement.key} 失敗: {e}")

        return newly_unlocked

    def _record_achievement_unlock(self, username: str, achievement_key: str):
        """記錄成就解鎖到資料庫"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR IGNORE INTO achievement_unlocks
                (username, achievement_key, platform)
                VALUES (?, ?, 'web')
            """, (username, achievement_key))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"記錄成就解鎖失敗: {e}")

    def get_user_achievements(self, username: str) -> Dict[str, Any]:
        """
        獲取用戶成就統計

        Args:
            username: 使用者名稱

        Returns:
            成就統計資料
        """
        if not self.db_path:
            return {}

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 獲取用戶解鎖的成就
            cur.execute("""
                SELECT achievement_key, unlock_time
                FROM achievement_unlocks
                WHERE username=?
                ORDER BY unlock_time DESC
            """, (username,))

            user_achievements = {}
            total_points = 0

            for row in cur.fetchall():
                key, unlock_time = row
                achievement = next((a for a in self.achievements if a.key == key), None)
                if achievement:
                    user_achievements[key] = {
                        'name': achievement.name,
                        'description': achievement.description,
                        'category': achievement.category,
                        'points': achievement.points,
                        'rarity': achievement.rarity,
                        'unlock_time': unlock_time
                    }
                    total_points += achievement.points

            # 計算完成率
            total_achievements = len(self.achievements)
            unlocked_count = len(user_achievements)
            completion_rate = (unlocked_count / total_achievements) * 100 if total_achievements > 0 else 0

            conn.close()

            return {
                'achievements': user_achievements,
                'total_points': total_points,
                'unlocked_count': unlocked_count,
                'total_count': total_achievements,
                'completion_rate': round(completion_rate, 2)
            }

        except Exception as e:
            logging.warning(f"獲取用戶成就失敗: {e}")
            return {}

    def get_achievement_leaderboard(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        獲取成就排行榜

        Args:
            limit: 返回的記錄數量限制

        Returns:
            排行榜資料
        """
        if not self.db_path:
            return []

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT username, COUNT(*) as achievement_count, SUM(?) as total_points
                FROM achievement_unlocks au
                JOIN achievements a ON au.achievement_key = a.key
                GROUP BY username
                ORDER BY total_points DESC, achievement_count DESC
                LIMIT ?
            """, (limit,))

            leaderboard = []
            for row in cur.fetchall():
                leaderboard.append({
                    'username': row[0],
                    'achievement_count': row[1],
                    'total_points': row[2] or 0
                })

            conn.close()
            return leaderboard

        except Exception as e:
            logging.warning(f"獲取成就排行榜失敗: {e}")
            return []

    def get_achievement_stats(self) -> Dict[str, Any]:
        """
        獲取成就統計資料

        Returns:
            全域成就統計
        """
        stats = {
            'total_achievements': len(self.achievements),
            'categories': {},
            'rarities': {},
            'most_unlocked': []
        }

        # 按分類統計
        for achievement in self.achievements:
            category = achievement.category
            rarity = achievement.rarity

            if category not in stats['categories']:
                stats['categories'][category] = 0
            stats['categories'][category] += 1

            if rarity not in stats['rarities']:
                stats['rarities'][rarity] = 0
            stats['rarities'][rarity] += 1

        return stats

    def export_achievements(self, username: str) -> str:
        """
        匯出用戶成就資料為JSON

        Args:
            username: 使用者名稱

        Returns:
            JSON格式的成就資料
        """
        achievements_data = self.get_user_achievements(username)
        return json.dumps(achievements_data, ensure_ascii=False, indent=2, default=str)

    def import_achievements(self, username: str, achievements_json: str):
        """
        從JSON匯入成就資料

        Args:
            username: 使用者名稱
            achievements_json: JSON格式的成就資料
        """
        try:
            data = json.loads(achievements_json)
            achievements = data.get('achievements', {})

            for key in achievements.keys():
                self._record_achievement_unlock(username, key)

        except Exception as e:
            logging.warning(f"匯入成就資料失敗: {e}")

    def get_achievement_categories(self) -> List[str]:
        """獲取所有成就分類"""
        return list(set(a.category for a in self.achievements))

    def get_achievements_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        按分類獲取成就列表

        Args:
            category: 成就分類

        Returns:
            該分類的成就列表
        """
        return [{
            'key': a.key,
            'name': a.name,
            'description': a.description,
            'points': a.points,
            'rarity': a.rarity,
            'prerequisites': a.prerequisites
        } for a in self.achievements if a.category == category]
