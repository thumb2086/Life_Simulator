"""
Life Simulator Server - 成就系統模組
處理成就解鎖、統計和排行榜
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from fastapi import HTTPException
from pydantic import BaseModel

from game_data import GameData


@dataclass
class Achievement:
    """成就定義"""
    key: str
    name: str
    description: str
    category: str
    points: int
    rarity: str
    requirements: Dict[str, Any]
    rewards: Dict[str, Any]


class AchievementCheckRequest(BaseModel):
    """成就檢查請求模型"""
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'


class AchievementExportRequest(BaseModel):
    """成就匯出請求模型"""
    username: str


class AchievementManager:
    """
    成就管理器
    負責成就系統的管理、檢查和統計
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_achievement_database()
        self._load_achievements()

    def _init_achievement_database(self):
        """初始化成就資料庫"""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 用戶成就表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    username TEXT NOT NULL,
                    achievement_key TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    progress REAL DEFAULT 1.0,
                    PRIMARY KEY (username, achievement_key)
                )
            """)

            # 成就統計表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS achievement_stats (
                    achievement_key TEXT PRIMARY KEY,
                    total_unlocked INTEGER DEFAULT 0,
                    last_unlocked TIMESTAMP,
                    rarity_score REAL DEFAULT 0
                )
            """)

            conn.commit()

        finally:
            conn.close()

    def _get_db_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_achievements(self):
        """載入成就定義"""
        self.achievements = {
            # 財富成就
            'first_million': Achievement(
                key='first_million',
                name='百萬富翁',
                description='資產首次超過100萬',
                category='wealth',
                points=100,
                rarity='common',
                requirements={'total_asset': 1000000},
                rewards={'cash': 10000, 'experience': 500}
            ),

            'millionaire': Achievement(
                key='millionaire',
                name='千萬富翁',
                description='資產超過1000萬',
                category='wealth',
                points=500,
                rarity='rare',
                requirements={'total_asset': 10000000},
                rewards={'cash': 50000, 'experience': 1000}
            ),

            'billionaire': Achievement(
                key='billionaire',
                name='億萬富翁',
                description='資產超過1億',
                category='wealth',
                points=1000,
                rarity='epic',
                requirements={'total_asset': 100000000},
                rewards={'cash': 100000, 'experience': 5000, 'title': '億萬富翁'}
            ),

            # 投資成就
            'first_trade': Achievement(
                key='first_trade',
                name='初次交易',
                description='完成第一筆股票交易',
                category='trading',
                points=50,
                rarity='common',
                requirements={'total_trades': 1},
                rewards={'experience': 100}
            ),

            'trading_master': Achievement(
                key='trading_master',
                name='交易大師',
                description='完成100筆交易',
                category='trading',
                points=300,
                rarity='rare',
                requirements={'total_trades': 100},
                rewards={'cash': 25000, 'experience': 750}
            ),

            'portfolio_manager': Achievement(
                key='portfolio_manager',
                name='投資組合經理',
                description='持有5種不同股票',
                category='trading',
                points=200,
                rarity='rare',
                requirements={'unique_stocks': 5},
                rewards={'experience': 500}
            ),

            # 遊戲成就
            'first_save': Achievement(
                key='first_save',
                name='儲存大師',
                description='第一次儲存遊戲',
                category='gameplay',
                points=25,
                rarity='common',
                requirements={'save_count': 1},
                rewards={'experience': 50}
            ),

            'long_term_player': Achievement(
                key='long_term_player',
                name='長期玩家',
                description='遊戲時間超過100天',
                category='gameplay',
                points=150,
                rarity='uncommon',
                requirements={'days_played': 100},
                rewards={'cash': 10000, 'experience': 300}
            ),

            # 社交成就
            'social_butterfly': Achievement(
                key='social_butterfly',
                name='社交高手',
                description='擁有10個好友',
                category='social',
                points=200,
                rarity='rare',
                requirements={'friend_count': 10},
                rewards={'experience': 400, 'social_points': 100}
            ),

            'guild_master': Achievement(
                key='guild_master',
                name='公會大師',
                description='創建自己的公會',
                category='social',
                points=250,
                rarity='rare',
                requirements={'guild_created': True},
                rewards={'cash': 20000, 'experience': 600}
            ),

            # 賭場成就
            'casino_newbie': Achievement(
                key='casino_newbie',
                name='賭場新手',
                description='首次在賭場獲勝',
                category='casino',
                points=75,
                rarity='common',
                requirements={'casino_wins': 1},
                rewards={'experience': 150}
            ),

            'high_roller': Achievement(
                key='high_roller',
                name='豪客',
                description='單筆賭注超過10,000',
                category='casino',
                points=400,
                rarity='epic',
                requirements={'max_bet': 10000},
                rewards={'cash': 30000, 'experience': 800, 'vip_points': 500}
            ),

            # 特殊成就
            'perfect_game': Achievement(
                key='perfect_game',
                name='完美遊戲',
                description='在21點中獲得21點',
                category='casino',
                points=150,
                rarity='uncommon',
                requirements={'blackjack_21': True},
                rewards={'cash': 15000, 'experience': 300}
            ),

            'jackpot_winner': Achievement(
                key='jackpot_winner',
                name='大獎得主',
                description='贏得累積獎池',
                category='casino',
                points=1000,
                rarity='legendary',
                requirements={'jackpot_win': True},
                rewards={'cash': 100000, 'experience': 2000, 'title': '幸運之星'}
            )
        }

    def check_achievements(self, game_data: GameData, username: str) -> List[Achievement]:
        """
        檢查並解鎖成就

        Args:
            game_data: 遊戲資料
            username: 用戶名

        Returns:
            新解鎖的成就列表
        """
        newly_unlocked = []

        # 獲取已解鎖的成就
        unlocked_keys = self.get_unlocked_achievement_keys(username)

        # 檢查每個成就
        for achievement in self.achievements.values():
            if achievement.key in unlocked_keys:
                continue  # 已解鎖

            if self._check_achievement_requirements(achievement, game_data, username):
                # 解鎖成就
                self._unlock_achievement(username, achievement)
                newly_unlocked.append(achievement)

        return newly_unlocked

    def _check_achievement_requirements(self, achievement: Achievement, game_data: GameData, username: str) -> bool:
        """
        檢查成就要求是否滿足

        Args:
            achievement: 成就對象
            game_data: 遊戲資料
            username: 用戶名

        Returns:
            是否滿足要求
        """
        requirements = achievement.requirements

        for req_key, req_value in requirements.items():
            if req_key == 'total_asset':
                current_value = getattr(game_data, 'cash', 0) + getattr(game_data, 'portfolio_value', 0)
            elif req_key == 'total_trades':
                current_value = getattr(game_data, 'total_trades', 0)
            elif req_key == 'unique_stocks':
                stocks = getattr(game_data, 'stocks', {})
                current_value = len([s for s in stocks.values() if s.get('owned', 0) > 0])
            elif req_key == 'save_count':
                current_value = 1  # 每次檢查都算一次
            elif req_key == 'days_played':
                current_value = getattr(game_data, 'days', 0)
            elif req_key == 'friend_count':
                current_value = getattr(game_data, 'friend_count', 0)
            elif req_key == 'guild_created':
                current_value = getattr(game_data, 'guild_created', False)
            elif req_key == 'casino_wins':
                current_value = getattr(game_data, 'casino_wins', 0)
            elif req_key == 'max_bet':
                current_value = getattr(game_data, 'max_casino_bet', 0)
            elif req_key == 'blackjack_21':
                current_value = getattr(game_data, 'blackjack_perfect', False)
            elif req_key == 'jackpot_win':
                current_value = getattr(game_data, 'jackpot_wins', 0) > 0
            else:
                continue

            if isinstance(req_value, bool):
                if current_value != req_value:
                    return False
            elif isinstance(req_value, (int, float)):
                if current_value < req_value:
                    return False
            else:
                if current_value != req_value:
                    return False

        return True

    def _unlock_achievement(self, username: str, achievement: Achievement):
        """
        解鎖成就

        Args:
            username: 用戶名
            achievement: 成就對象
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 插入用戶成就記錄
            cur.execute("""
                INSERT OR REPLACE INTO user_achievements
                (username, achievement_key, unlocked_at, progress)
                VALUES (?, ?, ?, ?)
            """, (username, achievement.key, datetime.now(), 1.0))

            # 更新成就統計
            cur.execute("""
                INSERT OR REPLACE INTO achievement_stats
                (achievement_key, total_unlocked, last_unlocked, rarity_score)
                VALUES (
                    ?,
                    COALESCE((SELECT total_unlocked FROM achievement_stats WHERE achievement_key = ?), 0) + 1,
                    ?,
                    ?
                )
            """, (achievement.key, achievement.key, datetime.now(), self._get_rarity_score(achievement.rarity)))

            conn.commit()

        finally:
            conn.close()

    def _get_rarity_score(self, rarity: str) -> float:
        """獲取稀有度分數"""
        rarity_scores = {
            'common': 1.0,
            'uncommon': 1.5,
            'rare': 2.0,
            'epic': 3.0,
            'legendary': 5.0
        }
        return rarity_scores.get(rarity, 1.0)

    def get_unlocked_achievement_keys(self, username: str) -> List[str]:
        """
        獲取用戶已解鎖的成就鍵

        Args:
            username: 用戶名

        Returns:
            成就鍵列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT achievement_key FROM user_achievements
                WHERE username = ?
            """, (username,))

            return [row['achievement_key'] for row in cur.fetchall()]

        finally:
            conn.close()

    def get_user_achievements(self, username: str) -> Dict[str, Any]:
        """
        獲取用戶成就統計

        Args:
            username: 用戶名

        Returns:
            用戶成就統計資料
        """
        unlocked_keys = self.get_unlocked_achievement_keys(username)

        unlocked_achievements = []
        for key in unlocked_keys:
            if key in self.achievements:
                achievement = self.achievements[key]
                unlocked_achievements.append({
                    'key': achievement.key,
                    'name': achievement.name,
                    'description': achievement.description,
                    'category': achievement.category,
                    'points': achievement.points,
                    'rarity': achievement.rarity,
                    'unlocked_at': self._get_unlock_time(username, key)
                })

        # 按分類統計
        category_stats = {}
        for achievement in unlocked_achievements:
            category = achievement['category']
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1

        # 計算總分和稀有度統計
        total_points = sum(a['points'] for a in unlocked_achievements)
        rarity_counts = {}
        for achievement in unlocked_achievements:
            rarity = achievement['rarity']
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

        return {
            'total_achievements': len(unlocked_achievements),
            'total_points': total_points,
            'category_breakdown': category_stats,
            'rarity_breakdown': rarity_counts,
            'achievements': unlocked_achievements
        }

    def _get_unlock_time(self, username: str, achievement_key: str) -> str:
        """獲取成就解鎖時間"""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT unlocked_at FROM user_achievements
                WHERE username = ? AND achievement_key = ?
            """, (username, achievement_key))

            row = cur.fetchone()
            return row['unlocked_at'] if row else datetime.now().isoformat()

        finally:
            conn.close()

    def get_achievement_leaderboard(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        獲取成就排行榜

        Args:
            limit: 返回記錄數量限制

        Returns:
            排行榜數據
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 計算每個用戶的成就點數總和
            cur.execute("""
                SELECT
                    ua.username,
                    SUM(a.points) as total_points,
                    COUNT(*) as achievement_count,
                    MAX(ua.unlocked_at) as last_unlocked
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_key = a.key
                GROUP BY ua.username
                ORDER BY total_points DESC, achievement_count DESC
                LIMIT ?
            """, (limit,))

            leaderboard = []
            for row in cur.fetchall():
                leaderboard.append({
                    'username': row['username'],
                    'total_points': row['total_points'] or 0,
                    'achievement_count': row['achievement_count'] or 0,
                    'last_unlocked': row['last_unlocked']
                })

            return leaderboard

        finally:
            conn.close()

    def get_achievement_categories(self) -> List[str]:
        """
        獲取成就分類列表

        Returns:
            分類列表
        """
        categories = set()
        for achievement in self.achievements.values():
            categories.add(achievement.category)

        return sorted(list(categories))

    def get_achievements_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        按分類獲取成就列表

        Args:
            category: 分類名稱

        Returns:
            成就列表
        """
        category_achievements = []
        for achievement in self.achievements.values():
            if achievement.category == category:
                category_achievements.append({
                    'key': achievement.key,
                    'name': achievement.name,
                    'description': achievement.description,
                    'points': achievement.points,
                    'rarity': achievement.rarity,
                    'requirements': achievement.requirements,
                    'rewards': achievement.rewards
                })

        return category_achievements

    def get_achievement_stats(self) -> Dict[str, Any]:
        """
        獲取成就統計資料

        Returns:
            全域成就統計
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 總成就統計
            cur.execute("SELECT COUNT(*) as total_users FROM (SELECT DISTINCT username FROM user_achievements)")
            total_users = cur.fetchone()['total_users']

            cur.execute("SELECT COUNT(*) as total_achievements FROM user_achievements")
            total_achievements = cur.fetchone()['total_achievements']

            # 最受歡迎的成就
            cur.execute("""
                SELECT achievement_key, COUNT(*) as unlock_count
                FROM user_achievements
                GROUP BY achievement_key
                ORDER BY unlock_count DESC
                LIMIT 5
            """)

            popular_achievements = []
            for row in cur.fetchall():
                achievement_key = row['achievement_key']
                if achievement_key in self.achievements:
                    achievement = self.achievements[achievement_key]
                    popular_achievements.append({
                        'achievement': achievement.name,
                        'unlock_count': row['unlock_count'],
                        'rarity': achievement.rarity
                    })

            return {
                'total_users': total_users,
                'total_achievements_unlocked': total_achievements,
                'average_achievements_per_user': total_achievements / total_users if total_users > 0 else 0,
                'popular_achievements': popular_achievements,
                'total_achievement_types': len(self.achievements)
            }

        finally:
            conn.close()

    def export_achievements(self, username: str) -> str:
        """
        匯出用戶成就資料

        Args:
            username: 用戶名

        Returns:
            JSON格式的成就資料
        """
        import json

        achievements_data = self.get_user_achievements(username)

        export_data = {
            'username': username,
            'export_date': datetime.now().isoformat(),
            'achievements_data': achievements_data
        }

        return json.dumps(export_data, ensure_ascii=False, indent=2)

    def import_achievements(self, username: str, achievements_json: str):
        """
        匯入成就資料

        Args:
            username: 用戶名
            achievements_json: 成就資料JSON
        """
        import json

        try:
            import_data = json.loads(achievements_json)

            if 'achievements_data' not in import_data:
                return

            achievements_data = import_data['achievements_data']

            # 這裡可以實現匯入邏輯
            # 實際實現會比較複雜，需要處理重複和驗證

        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="無效的成就資料格式")

    def get_recent_achievements(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        獲取最近解鎖的成就

        Args:
            limit: 返回記錄數量限制

        Returns:
            最近成就列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT ua.username, ua.achievement_key, ua.unlocked_at,
                       a.name, a.category, a.points, a.rarity
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_key = a.key
                ORDER BY ua.unlocked_at DESC
                LIMIT ?
            """, (limit,))

            recent_achievements = []
            for row in cur.fetchall():
                recent_achievements.append({
                    'username': row['username'],
                    'achievement_name': row['name'],
                    'achievement_key': row['achievement_key'],
                    'category': row['category'],
                    'points': row['points'],
                    'rarity': row['rarity'],
                    'unlocked_at': row['unlocked_at']
                })

            return recent_achievements

        finally:
            conn.close()
