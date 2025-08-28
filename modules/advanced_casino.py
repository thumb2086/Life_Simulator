"""
Life Simulator - 進階賭場系統
提供多樣化的賭場遊戲和VIP會員體驗
"""

import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from game_data import GameData
from unified_data_manager import UnifiedDataManager


class CasinoGame(Enum):
    """賭場遊戲類型"""
    SLOTS = "slots"
    BLACKJACK = "blackjack"
    ROULETTE = "roulette"
    BACCARAT = "baccarat"
    DICE = "dice"
    CRAPS = "craps"
    VIDEO_POKER = "video_poker"


class RouletteBetType(Enum):
    """輪盤賭注類型"""
    STRAIGHT_UP = "straight_up"      # 單一數字
    SPLIT = "split"                  # 兩個相鄰數字
    STREET = "street"                # 三個數字一排
    CORNER = "corner"                # 四個數字方塊
    SIX_LINE = "six_line"            # 六個數字
    COLUMN = "column"                # 垂直列
    DOZEN = "dozen"                  # 1-12, 13-24, 25-36
    RED = "red"                      # 紅色
    BLACK = "black"                  # 黑色
    EVEN = "even"                    # 偶數
    ODD = "odd"                      # 奇數
    LOW = "low"                      # 1-18
    HIGH = "high"                    # 19-36


class VIPLevel(Enum):
    """VIP等級"""
    BRONZE = "bronze"        # 青銅 (0-1000)
    SILVER = "silver"        # 白銀 (1000-5000)
    GOLD = "gold"           # 黃金 (5000-25000)
    PLATINUM = "platinum"   # 白金 (25000-100000)
    DIAMOND = "diamond"     # 鑽石 (100000+)


@dataclass
class RouletteNumber:
    """輪盤數字"""
    number: int
    color: str  # red, black, green (for 0)


@dataclass
class VIPMember:
    """VIP會員"""
    username: str
    level: VIPLevel
    total_bet: float
    total_win: float
    join_date: datetime
    perks: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressiveJackpot:
    """累積獎池"""
    jackpot_id: str
    name: str
    current_amount: float
    contribution_rate: float  # 每筆賭注的貢獻百分比
    last_win_time: Optional[datetime] = None
    last_winner: Optional[str] = None
    min_bet: float = 100.0
    is_active: bool = True


@dataclass
class CasinoAchievement:
    """賭場成就"""
    achievement_id: str
    name: str
    description: str
    icon: str
    requirement_type: str  # games_played, total_win, big_win, streak
    requirement_value: Any
    reward_type: str      # cash, experience, vip_points
    reward_value: Any
    rarity: str = "common"  # common, rare, epic, legendary


class AdvancedCasinoManager:
    """
    進階賭場管理系統
    提供完整的賭場體驗，包括多樣化遊戲、VIP系統和累積獎池
    """

    def __init__(self, data_manager: UnifiedDataManager, db_path: str = None):
        self.data_manager = data_manager
        self.db_path = db_path

        # 賭場遊戲狀態
        self.active_games: Dict[str, Dict[str, Any]] = {}
        self.vip_members: Dict[str, VIPMember] = {}
        self.progressive_jackpots: Dict[str, ProgressiveJackpot] = {}

        # 初始化賭場系統
        self._init_casino_db_schema()
        self._load_casino_data()
        self._initialize_jackpots()
        self._load_casino_achievements()

    def _init_casino_db_schema(self):
        """初始化賭場資料庫結構"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # VIP會員表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vip_members (
                    username TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    total_bet REAL NOT NULL DEFAULT 0,
                    total_win REAL NOT NULL DEFAULT 0,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    perks TEXT
                )
            """)

            # 累積獎池表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS progressive_jackpots (
                    jackpot_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    current_amount REAL NOT NULL DEFAULT 0,
                    contribution_rate REAL NOT NULL DEFAULT 0.01,
                    last_win_time TIMESTAMP,
                    last_winner TEXT,
                    min_bet REAL NOT NULL DEFAULT 100.0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)

            # 賭場成就表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS casino_achievements (
                    username TEXT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (username, achievement_id)
                )
            """)

            # 賭場統計表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS casino_stats (
                    username TEXT PRIMARY KEY,
                    total_games INTEGER NOT NULL DEFAULT 0,
                    total_bet REAL NOT NULL DEFAULT 0,
                    total_win REAL NOT NULL DEFAULT 0,
                    best_win REAL NOT NULL DEFAULT 0,
                    win_streak INTEGER NOT NULL DEFAULT 0,
                    lose_streak INTEGER NOT NULL DEFAULT 0,
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"初始化賭場資料庫失敗: {e}")

    def _load_casino_data(self):
        """載入賭場資料"""
        # 初始化輪盤數字
        self.roulette_wheel = self._create_roulette_wheel()

        # 載入VIP會員
        self._load_vip_members()

        # 載入累積獎池
        self._load_progressive_jackpots()

    def _create_roulette_wheel(self) -> List[RouletteNumber]:
        """建立輪盤輪盤"""
        # 歐洲輪盤：0-36，紅黑交替
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

        wheel = []
        for i in range(37):  # 0-36
            if i == 0:
                wheel.append(RouletteNumber(i, "green"))
            elif i in red_numbers:
                wheel.append(RouletteNumber(i, "red"))
            else:
                wheel.append(RouletteNumber(i, "black"))

        return wheel

    def _load_vip_members(self):
        """載入VIP會員資料"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT * FROM vip_members")
            for row in cur.fetchall():
                username, level, total_bet, total_win, join_date, perks = row
                self.vip_members[username] = VIPMember(
                    username=username,
                    level=VIPLevel(level),
                    total_bet=total_bet,
                    total_win=total_win,
                    join_date=datetime.fromisoformat(join_date),
                    perks=json.loads(perks) if perks else {}
                )

            conn.close()

        except Exception as e:
            logging.warning(f"載入VIP會員資料失敗: {e}")

    def _load_progressive_jackpots(self):
        """載入累積獎池資料"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT * FROM progressive_jackpots")
            for row in cur.fetchall():
                jackpot_id, name, current_amount, contribution_rate, last_win_time, last_winner, min_bet, is_active = row

                self.progressive_jackpots[jackpot_id] = ProgressiveJackpot(
                    jackpot_id=jackpot_id,
                    name=name,
                    current_amount=current_amount,
                    contribution_rate=contribution_rate,
                    last_win_time=datetime.fromisoformat(last_win_time) if last_win_time else None,
                    last_winner=last_winner,
                    min_bet=min_bet,
                    is_active=bool(is_active)
                )

            conn.close()

        except Exception as e:
            logging.warning(f"載入累積獎池資料失敗: {e}")

    def _initialize_jackpots(self):
        """初始化預設累積獎池"""
        default_jackpots = {
            "mega_jackpot": ProgressiveJackpot(
                jackpot_id="mega_jackpot",
                name="超級大獎",
                current_amount=100000.0,
                contribution_rate=0.005,
                min_bet=500.0
            ),
            "slots_jackpot": ProgressiveJackpot(
                jackpot_id="slots_jackpot",
                name="拉霸大獎",
                current_amount=50000.0,
                contribution_rate=0.01,
                min_bet=100.0
            ),
            "blackjack_jackpot": ProgressiveJackpot(
                jackpot_id="blackjack_jackpot",
                name="21點大獎",
                current_amount=25000.0,
                contribution_rate=0.008,
                min_bet=200.0
            )
        }

        # 只在不存在時建立
        for jackpot_id, jackpot in default_jackpots.items():
            if jackpot_id not in self.progressive_jackpots:
                self.progressive_jackpots[jackpot_id] = jackpot
                self._save_progressive_jackpot(jackpot)

    def _load_casino_achievements(self):
        """載入賭場成就定義"""
        self.casino_achievements = {
            "first_win": CasinoAchievement(
                achievement_id="first_win",
                name="首勝",
                description="贏得第一筆賭場獎金",
                icon="🎉",
                requirement_type="total_win",
                requirement_value=1,
                reward_type="experience",
                reward_value=100,
                rarity="common"
            ),
            "high_roller": CasinoAchievement(
                achievement_id="high_roller",
                name="豪客",
                description="單筆下注超過10,000元",
                icon="💰",
                requirement_type="big_win",
                requirement_value=10000,
                reward_type="cash",
                reward_value=1000,
                rarity="rare"
            ),
            "jackpot_winner": CasinoAchievement(
                achievement_id="jackpot_winner",
                name="大獎得主",
                description="贏得累積獎池",
                icon="🏆",
                requirement_type="jackpot_win",
                requirement_value=1,
                reward_type="vip_points",
                reward_value=1000,
                rarity="legendary"
            ),
            "win_streak_10": CasinoAchievement(
                achievement_id="win_streak_10",
                name="連勝王者",
                description="連續贏得10場遊戲",
                icon="🔥",
                requirement_type="streak",
                requirement_value=10,
                reward_type="cash",
                reward_value=500,
                rarity="epic"
            ),
            "vip_member": CasinoAchievement(
                achievement_id="vip_member",
                name="VIP會員",
                description="成為VIP會員",
                icon="👑",
                requirement_type="vip_level",
                requirement_value="bronze",
                reward_type="experience",
                reward_value=500,
                rarity="rare"
            )
        }

    # ===== VIP系統 =====

    def get_vip_level(self, username: str) -> VIPLevel:
        """
        獲取用戶VIP等級

        Args:
            username: 用戶名

        Returns:
            VIP等級
        """
        if username in self.vip_members:
            return self.vip_members[username].level

        # 計算VIP等級
        game_data = self.data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            return VIPLevel.BRONZE

        total_bet = getattr(game_data, 'total_casino_bet', 0)
        return self._calculate_vip_level(total_bet)

    def _calculate_vip_level(self, total_bet: float) -> VIPLevel:
        """根據總下注金額計算VIP等級"""
        if total_bet >= 100000:
            return VIPLevel.DIAMOND
        elif total_bet >= 25000:
            return VIPLevel.PLATINUM
        elif total_bet >= 5000:
            return VIPLevel.GOLD
        elif total_bet >= 1000:
            return VIPLevel.SILVER
        else:
            return VIPLevel.BRONZE

    def get_vip_perks(self, vip_level: VIPLevel) -> Dict[str, Any]:
        """獲取VIP特權"""
        perks = {
            VIPLevel.BRONZE: {
                "bonus_rate": 0.01,
                "max_bet_multiplier": 1.0,
                "experience_bonus": 0.05
            },
            VIPLevel.SILVER: {
                "bonus_rate": 0.02,
                "max_bet_multiplier": 1.5,
                "experience_bonus": 0.10,
                "weekly_bonus": 100
            },
            VIPLevel.GOLD: {
                "bonus_rate": 0.03,
                "max_bet_multiplier": 2.0,
                "experience_bonus": 0.15,
                "weekly_bonus": 500,
                "exclusive_games": True
            },
            VIPLevel.PLATINUM: {
                "bonus_rate": 0.05,
                "max_bet_multiplier": 3.0,
                "experience_bonus": 0.20,
                "weekly_bonus": 1000,
                "exclusive_games": True,
                "personal_manager": True
            },
            VIPLevel.DIAMOND: {
                "bonus_rate": 0.08,
                "max_bet_multiplier": 5.0,
                "experience_bonus": 0.25,
                "weekly_bonus": 5000,
                "exclusive_games": True,
                "personal_manager": True,
                "custom_games": True
            }
        }
        return perks.get(vip_level, perks[VIPLevel.BRONZE])

    # ===== 累積獎池系統 =====

    def contribute_to_jackpot(self, bet_amount: float, game_type: str) -> Dict[str, float]:
        """
        向累積獎池貢獻

        Args:
            bet_amount: 下注金額
            game_type: 遊戲類型

        Returns:
            各獎池的貢獻金額
        """
        contributions = {}

        for jackpot_id, jackpot in self.progressive_jackpots.items():
            if not jackpot.is_active:
                continue

            contribution = bet_amount * jackpot.contribution_rate
            jackpot.current_amount += contribution
            contributions[jackpot_id] = contribution

            # 儲存更新
            self._save_progressive_jackpot(jackpot)

        return contributions

    def trigger_jackpot(self, jackpot_id: str, winner_username: str) -> float:
        """
        觸發累積獎池

        Args:
            jackpot_id: 獎池ID
            winner_username: 得獎者用戶名

        Returns:
            獎池金額
        """
        if jackpot_id not in self.progressive_jackpots:
            return 0.0

        jackpot = self.progressive_jackpots[jackpot_id]
        prize_amount = jackpot.current_amount

        # 重置獎池
        jackpot.current_amount = 1000.0  # 基礎金額
        jackpot.last_win_time = datetime.now()
        jackpot.last_winner = winner_username

        # 儲存更新
        self._save_progressive_jackpot(jackpot)

        return prize_amount

    def _save_progressive_jackpot(self, jackpot: ProgressiveJackpot):
        """儲存累積獎池資料"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO progressive_jackpots
                (jackpot_id, name, current_amount, contribution_rate, last_win_time, last_winner, min_bet, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                jackpot.jackpot_id,
                jackpot.name,
                jackpot.current_amount,
                jackpot.contribution_rate,
                jackpot.last_win_time.isoformat() if jackpot.last_win_time else None,
                jackpot.last_winner,
                jackpot.min_bet,
                jackpot.is_active
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"儲存累積獎池失敗: {e}")

    # ===== 俄羅斯輪盤遊戲 =====

    def play_roulette(self, username: str, bet_amount: float, bet_type: RouletteBetType, bet_value: Any = None) -> Dict[str, Any]:
        """
        玩俄羅斯輪盤

        Args:
            username: 玩家用戶名
            bet_amount: 下注金額
            bet_type: 賭注類型
            bet_value: 賭注值（根據類型而定）

        Returns:
            遊戲結果
        """
        # 旋轉輪盤
        winning_number = random.choice(self.roulette_wheel)

        # 計算中獎
        payout_multiplier = self._calculate_roulette_payout(bet_type, bet_value, winning_number)

        if payout_multiplier > 0:
            winnings = bet_amount * payout_multiplier
            result = "win"
        else:
            winnings = 0
            result = "lose"

        # 更新統計
        self._update_player_stats(username, bet_amount, winnings)

        # 貢獻獎池
        self.contribute_to_jackpot(bet_amount, "roulette")

        # 檢查成就
        self._check_casino_achievements(username, bet_amount, winnings)

        return {
            "winning_number": winning_number.number,
            "winning_color": winning_number.color,
            "result": result,
            "winnings": winnings,
            "payout_multiplier": payout_multiplier,
            "bet_details": {
                "type": bet_type.value,
                "value": bet_value,
                "amount": bet_amount
            }
        }

    def _calculate_roulette_payout(self, bet_type: RouletteBetType, bet_value: Any, winning_number: RouletteNumber) -> float:
        """計算輪盤賭注的賠率"""
        payouts = {
            RouletteBetType.STRAIGHT_UP: 35.0,    # 單一數字：35:1
            RouletteBetType.SPLIT: 17.0,          # 分割：17:1
            RouletteBetType.STREET: 11.0,         # 街注：11:1
            RouletteBetType.CORNER: 8.0,          # 角注：8:1
            RouletteBetType.SIX_LINE: 5.0,        # 六線：5:1
            RouletteBetType.COLUMN: 2.0,          # 列：2:1
            RouletteBetType.DOZEN: 2.0,           # 一打：2:1
            RouletteBetType.RED: 1.0,             # 紅/黑：1:1
            RouletteBetType.BLACK: 1.0,
            RouletteBetType.EVEN: 1.0,            # 偶/奇：1:1
            RouletteBetType.ODD: 1.0,
            RouletteBetType.LOW: 1.0,             # 低/高：1:1
            RouletteBetType.HIGH: 1.0
        }

        if bet_type == RouletteBetType.STRAIGHT_UP:
            return payouts[bet_type] if bet_value == winning_number.number else 0.0
        elif bet_type == RouletteBetType.RED:
            return payouts[bet_type] if winning_number.color == "red" else 0.0
        elif bet_type == RouletteBetType.BLACK:
            return payouts[bet_type] if winning_number.color == "black" else 0.0
        elif bet_type == RouletteBetType.EVEN:
            return payouts[bet_type] if winning_number.number > 0 and winning_number.number % 2 == 0 else 0.0
        elif bet_type == RouletteBetType.ODD:
            return payouts[bet_type] if winning_number.number > 0 and winning_number.number % 2 == 1 else 0.0
        elif bet_type == RouletteBetType.LOW:
            return payouts[bet_type] if 1 <= winning_number.number <= 18 else 0.0
        elif bet_type == RouletteBetType.HIGH:
            return payouts[bet_type] if 19 <= winning_number.number <= 36 else 0.0
        elif bet_type == RouletteBetType.DOZEN:
            if bet_value == 1:
                return payouts[bet_type] if 1 <= winning_number.number <= 12 else 0.0
            elif bet_value == 2:
                return payouts[bet_type] if 13 <= winning_number.number <= 24 else 0.0
            elif bet_value == 3:
                return payouts[bet_type] if 25 <= winning_number.number <= 36 else 0.0
        elif bet_type == RouletteBetType.COLUMN:
            # 簡化實現
            return payouts[bet_type] if random.random() < 0.33 else 0.0

        return 0.0

    # ===== 百家樂遊戲 =====

    def play_baccarat(self, username: str, bet_amount: float, bet_type: str) -> Dict[str, Any]:
        """
        玩百家樂

        Args:
            username: 玩家用戶名
            bet_amount: 下注金額
            bet_type: 賭注類型 (player, banker, tie)

        Returns:
            遊戲結果
        """
        # 發牌
        player_cards = [self._draw_baccarat_card(), self._draw_baccarat_card()]
        banker_cards = [self._draw_baccarat_card(), self._draw_baccarat_card()]

        player_score = self._calculate_baccarat_score(player_cards)
        banker_score = self._calculate_baccarat_score(banker_cards)

        # 決定是否補牌（簡化規則）
        if player_score <= 5:
            player_cards.append(self._draw_baccarat_card())
            player_score = self._calculate_baccarat_score(player_cards)

        if banker_score <= 5:
            banker_cards.append(self._draw_baccarat_card())
            banker_score = self._calculate_baccarat_score(banker_cards)

        # 判斷勝負
        if player_score > banker_score:
            winner = "player"
        elif banker_score > player_score:
            winner = "banker"
        else:
            winner = "tie"

        # 計算賠率
        if winner == bet_type:
            if bet_type == "tie":
                payout_multiplier = 8.0  # 和局通常8:1
            elif bet_type == "banker":
                payout_multiplier = 0.95  # 莊家通常0.95:1（扣除佣金）
            else:
                payout_multiplier = 1.0   # 閒家1:1
            winnings = bet_amount * payout_multiplier
            result = "win"
        else:
            winnings = 0
            result = "lose"

        # 更新統計
        self._update_player_stats(username, bet_amount, winnings)

        # 貢獻獎池
        self.contribute_to_jackpot(bet_amount, "baccarat")

        return {
            "result": result,
            "winner": winner,
            "winnings": winnings,
            "player_cards": [str(card) for card in player_cards],
            "banker_cards": [str(card) for card in banker_cards],
            "player_score": player_score,
            "banker_score": banker_score,
            "bet_details": {
                "type": bet_type,
                "amount": bet_amount
            }
        }

    def _draw_baccarat_card(self) -> str:
        """抽一張百家樂牌"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        return f"{random.choice(ranks)}{random.choice(suits)}"

    def _calculate_baccarat_score(self, cards: List[str]) -> int:
        """計算百家樂點數"""
        score = 0
        for card in cards:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                score += 0
            elif rank == 'A':
                score += 1
            else:
                score += int(rank)

        return score % 10  # 百家樂只取個位數

    # ===== 骰子遊戲 =====

    def play_dice_game(self, username: str, bet_amount: float, game_type: str, prediction: Any = None) -> Dict[str, Any]:
        """
        玩骰子遊戲

        Args:
            username: 玩家用戶名
            bet_amount: 下注金額
            game_type: 遊戲類型 (seven_eleven, craps, etc.)
            prediction: 預測結果

        Returns:
            遊戲結果
        """
        # 擲骰子
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2

        # 根據遊戲類型判斷勝負
        if game_type == "seven_eleven":
            # 7或11贏，2,3,12輸，其他重擲
            if total in [7, 11]:
                result = "win"
                payout_multiplier = 1.0
            elif total in [2, 3, 12]:
                result = "lose"
                payout_multiplier = 0.0
            else:
                result = "push"  # 平局
                payout_multiplier = 0.0

        elif game_type == "craps":
            # Craps規則
            if prediction == total:
                result = "win"
                payout_multiplier = 5.0  # 猜中點數賠率較高
            else:
                result = "lose"
                payout_multiplier = 0.0

        elif game_type == "over_under":
            # 大小預測
            if (prediction == "over" and total > 7) or (prediction == "under" and total < 7):
                result = "win"
                payout_multiplier = 1.0
            elif total == 7:
                result = "push"
                payout_multiplier = 0.0
            else:
                result = "lose"
                payout_multiplier = 0.0

        else:
            result = "lose"
            payout_multiplier = 0.0

        winnings = bet_amount * payout_multiplier if result == "win" else 0

        # 更新統計
        self._update_player_stats(username, bet_amount, winnings)

        # 貢獻獎池
        self.contribute_to_jackpot(bet_amount, "dice")

        return {
            "result": result,
            "dice": [dice1, dice2],
            "total": total,
            "winnings": winnings,
            "payout_multiplier": payout_multiplier,
            "game_details": {
                "type": game_type,
                "prediction": prediction,
                "amount": bet_amount
            }
        }

    # ===== 工具方法 =====

    def _update_player_stats(self, username: str, bet_amount: float, winnings: float):
        """更新玩家統計資料"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 獲取現有統計
            cur.execute("SELECT * FROM casino_stats WHERE username = ?", (username,))
            row = cur.fetchone()

            if row:
                username, total_games, total_bet, total_win, best_win, win_streak, lose_streak, last_played = row

                # 更新統計
                new_total_games = total_games + 1
                new_total_bet = total_bet + bet_amount
                new_total_win = total_win + winnings
                new_best_win = max(best_win, winnings)

                # 更新連勝/連敗
                if winnings > 0:
                    new_win_streak = win_streak + 1
                    new_lose_streak = 0
                else:
                    new_win_streak = 0
                    new_lose_streak = lose_streak + 1

            else:
                # 新玩家
                new_total_games = 1
                new_total_bet = bet_amount
                new_total_win = winnings
                new_best_win = winnings
                new_win_streak = 1 if winnings > 0 else 0
                new_lose_streak = 0 if winnings > 0 else 1

            # 儲存更新
            cur.execute("""
                INSERT OR REPLACE INTO casino_stats
                (username, total_games, total_bet, total_win, best_win, win_streak, lose_streak, last_played)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, new_total_games, new_total_bet, new_total_win,
                new_best_win, new_win_streak, new_lose_streak, datetime.now()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"更新玩家統計失敗: {e}")

    def _check_casino_achievements(self, username: str, bet_amount: float, winnings: float):
        """檢查賭場成就"""
        # 此處實現成就檢查邏輯
        pass

    def get_casino_stats(self, username: str) -> Dict[str, Any]:
        """獲取玩家賭場統計"""
        if not self.db_path:
            return {}

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT * FROM casino_stats WHERE username = ?", (username,))
            row = cur.fetchone()

            if row:
                username, total_games, total_bet, total_win, best_win, win_streak, lose_streak, last_played = row
                return {
                    "total_games": total_games,
                    "total_bet": total_bet,
                    "total_win": total_win,
                    "best_win": best_win,
                    "win_streak": win_streak,
                    "lose_streak": lose_streak,
                    "win_rate": total_win / total_bet if total_bet > 0 else 0,
                    "last_played": last_played
                }
            else:
                return {}

        except Exception as e:
            logging.warning(f"獲取賭場統計失敗: {e}")
            return {}
        finally:
            if 'conn' in locals():
                conn.close()

    def get_progressive_jackpots(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有累積獎池資訊"""
        return {
            jackpot_id: {
                "name": jackpot.name,
                "current_amount": jackpot.current_amount,
                "min_bet": jackpot.min_bet,
                "last_winner": jackpot.last_winner,
                "last_win_time": jackpot.last_win_time.isoformat() if jackpot.last_win_time else None
            }
            for jackpot_id, jackpot in self.progressive_jackpots.items()
            if jackpot.is_active
        }
