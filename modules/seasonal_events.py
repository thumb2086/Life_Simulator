import random
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from game_data import GameData
from unified_data_manager import UnifiedDataManager


class Season(Enum):
    """季節"""
    SPRING = "spring"  # 春季
    SUMMER = "summer"  # 夏季
    AUTUMN = "autumn"  # 秋季
    WINTER = "winter"  # 冬季


class EventType(Enum):
    """活動類型"""
    FESTIVAL = "festival"      # 節慶活動
    CHALLENGE = "challenge"    # 挑戰活動
    QUEST = "quest"           # 任務活動
    BONUS = "bonus"           # 獎勵活動
    SPECIAL = "special"       # 特殊活動


class ChallengeDifficulty(Enum):
    """挑戰難度"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class SeasonalEvent:
    """季節性活動"""
    event_id: str
    name: str
    description: str
    season: Season
    event_type: EventType
    start_date: date
    end_date: date
    rewards: Dict[str, Any]
    requirements: Dict[str, Any]
    objectives: List[Dict[str, Any]]
    is_active: bool = False
    participants: Set[str] = None

    def __post_init__(self):
        if self.participants is None:
            self.participants = set()


@dataclass
class Challenge:
    """挑戰活動"""
    challenge_id: str
    title: str
    description: str
    difficulty: ChallengeDifficulty
    duration_days: int
    objectives: List[Dict[str, Any]]
    rewards: Dict[str, Any]
    prerequisites: Dict[str, Any]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_completed: bool = False


@dataclass
class PlayerProgress:
    """玩家活動進度"""
    username: str
    event_id: str
    objectives_progress: Dict[str, Any]
    start_time: datetime
    last_update: datetime
    is_completed: bool = False
    rewards_claimed: bool = False


class SeasonalEventsManager:
    """
    季節性活動和挑戰管理系統
    提供動態活動和挑戰，提升遊戲的可重玩性
    """

    def __init__(self, data_manager: UnifiedDataManager, db_path: str = None):
        self.data_manager = data_manager
        self.db_path = db_path
        self.events: Dict[str, SeasonalEvent] = {}
        self.challenges: Dict[str, Challenge] = {}
        self.player_progress: Dict[str, Dict[str, PlayerProgress]] = {}  # username -> event_id -> progress

        # 初始化資料庫結構
        self._init_seasonal_db_schema()

        # 載入預設活動和挑戰
        self._load_default_events()
        self._load_default_challenges()

    def _init_seasonal_db_schema(self):
        """初始化季節性活動資料庫結構"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 季節性活動表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS seasonal_events (
                    event_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    season TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    rewards TEXT,
                    requirements TEXT,
                    objectives TEXT,
                    is_active BOOLEAN DEFAULT FALSE
                )
            """)

            # 挑戰活動表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    challenge_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    difficulty TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    objectives TEXT,
                    rewards TEXT,
                    prerequisites TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    is_completed BOOLEAN DEFAULT FALSE
                )
            """)

            # 玩家進度表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS player_progress (
                    username TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    objectives_progress TEXT,
                    start_time TEXT NOT NULL,
                    last_update TEXT NOT NULL,
                    is_completed BOOLEAN DEFAULT FALSE,
                    rewards_claimed BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (username, event_id)
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"初始化季節性活動資料庫失敗: {e}")

    def _load_default_events(self):
        """載入預設季節性活動"""
        current_year = datetime.now().year

        default_events = [
            # 春季活動
            SeasonalEvent(
                event_id="spring_festival_2024",
                name="春季投資節",
                description="春季是投資的好時機，參與活動獲得額外投資機會！",
                season=Season.SPRING,
                event_type=EventType.FESTIVAL,
                start_date=date(current_year, 3, 1),
                end_date=date(current_year, 3, 31),
                rewards={
                    'cash_bonus': 5000,
                    'experience_bonus': 100,
                    'special_item': 'spring_investment_pack'
                },
                requirements={'min_level': 1},
                objectives=[
                    {'type': 'invest', 'target': 10000, 'description': '投資至少$10,000'},
                    {'type': 'diversify', 'target': 3, 'description': '持有至少3種不同股票'},
                    {'type': 'trade', 'target': 5, 'description': '完成至少5筆交易'}
                ]
            ),

            # 夏季活動
            SeasonalEvent(
                event_id="summer_challenge_2024",
                name="夏季成長挑戰",
                description="夏季是成長的季節，挑戰自己成為更好的投資者！",
                season=Season.SUMMER,
                event_type=EventType.CHALLENGE,
                start_date=date(current_year, 6, 1),
                end_date=date(current_year, 8, 31),
                rewards={
                    'skill_points': 50,
                    'achievement_unlock': 'summer_investor',
                    'cash_bonus': 10000
                },
                requirements={'min_days': 30},
                objectives=[
                    {'type': 'profit', 'target': 0.1, 'description': '實現10%投資報酬率'},
                    {'type': 'study', 'target': 10, 'description': '完成10次學習活動'},
                    {'type': 'social', 'target': 5, 'description': '參與5次社交活動'}
                ]
            ),

            # 秋季活動
            SeasonalEvent(
                event_id="autumn_harvest_2024",
                name="秋季豐收慶典",
                description="秋季豐收季節，慶祝您的投資成果！",
                season=Season.AUTUMN,
                event_type=EventType.BONUS,
                start_date=date(current_year, 9, 1),
                end_date=date(current_year, 11, 30),
                rewards={
                    'multiplier': 1.5,  # 所有收益1.5倍
                    'special_dividend': 0.05,  # 額外股息
                    'bonus_days': 7  # 額外遊戲天數
                },
                requirements={'min_portfolio_value': 50000},
                objectives=[
                    {'type': 'portfolio_growth', 'target': 0.2, 'description': '投資組合成長20%'},
                    {'type': 'dividend_income', 'target': 1000, 'description': '獲得$1000股息收入'},
                    {'type': 'share_achievement', 'target': 3, 'description': '分享3個成就'}
                ]
            ),

            # 冬季活動
            SeasonalEvent(
                event_id="winter_festival_2024",
                name="冬季投資馬拉松",
                description="寒冷的冬季，正是累積財富的最佳時機！",
                season=Season.WINTER,
                event_type=EventType.QUEST,
                start_date=date(current_year, 12, 1),
                end_date=date(current_year, 12, 31),
                rewards={
                    'year_end_bonus': 20000,
                    'special_title': 'winter_warrior',
                    'guild_points': 100
                },
                requirements={'min_games_played': 10},
                objectives=[
                    {'type': 'survive_winter', 'target': 30, 'description': '在冬季存活30天'},
                    {'type': 'winter_profit', 'target': 0.15, 'description': '實現15%冬季收益'},
                    {'type': 'complete_challenges', 'target': 3, 'description': '完成3個冬季挑戰'}
                ]
            )
        ]

        for event in default_events:
            self.events[event.event_id] = event

    def _load_default_challenges(self):
        """載入預設挑戰活動"""
        default_challenges = [
            Challenge(
                challenge_id="millionaire_challenge",
                title="百萬富翁挑戰",
                description="從零開始，成為百萬富翁！",
                difficulty=ChallengeDifficulty.HARD,
                duration_days=90,
                objectives=[
                    {'type': 'net_worth', 'target': 1000000, 'description': '達到$1,000,000淨資產'},
                    {'type': 'diversification', 'target': 8, 'description': '持有至少8種不同股票'},
                    {'type': 'monthly_income', 'target': 5000, 'description': '每月收入至少$5,000'}
                ],
                rewards={
                    'cash': 50000,
                    'achievement': 'millionaire_challenge_completed',
                    'title': 'challenge_master'
                },
                prerequisites={'min_days': 30}
            ),

            Challenge(
                challenge_id="speed_trader",
                title="閃電交易員",
                description="在有限時間內完成大量交易！",
                difficulty=ChallengeDifficulty.MEDIUM,
                duration_days=7,
                objectives=[
                    {'type': 'trades_completed', 'target': 50, 'description': '完成50筆交易'},
                    {'type': 'profit_target', 'target': 0.05, 'description': '實現5%收益'},
                    {'type': 'no_losses', 'target': 0, 'description': '不允許任何虧損交易'}
                ],
                rewards={
                    'cash': 10000,
                    'experience': 200,
                    'title': 'speed_trader'
                },
                prerequisites={'min_level': 5}
            ),

            Challenge(
                challenge_id="value_investor",
                title="價值投資大師",
                description="運用價值投資策略獲得優異報酬！",
                difficulty=ChallengeDifficulty.EXPERT,
                duration_days=60,
                objectives=[
                    {'type': 'undervalued_stocks', 'target': 5, 'description': '持有5檔被低估的股票'},
                    {'type': 'long_term_hold', 'target': 30, 'description': '平均持股時間超過30天'},
                    {'type': 'value_return', 'target': 0.25, 'description': '實現25%價值投資報酬'}
                ],
                rewards={
                    'cash': 25000,
                    'skill_book': 'advanced_value_investing',
                    'achievement': 'value_investor_master'
                },
                prerequisites={'min_days': 60, 'min_portfolio': 100000}
            ),

            Challenge(
                challenge_id="social_butterfly",
                title="社交高手",
                description="建立廣泛的社交網路！",
                difficulty=ChallengeDifficulty.EASY,
                duration_days=30,
                objectives=[
                    {'type': 'friends_made', 'target': 10, 'description': '結交10位好友'},
                    {'type': 'guild_joined', 'target': 1, 'description': '加入一個公會'},
                    {'type': 'social_events', 'target': 15, 'description': '參與15次社交活動'}
                ],
                rewards={
                    'social_points': 100,
                    'friend_bonus': 0.1,  # 好友收益加成
                    'title': 'social_butterfly'
                },
                prerequisites={'min_days': 10}
            )
        ]

        for challenge in default_challenges:
            self.challenges[challenge.challenge_id] = challenge

    def get_current_season(self) -> Season:
        """獲取當前季節"""
        current_month = datetime.now().month

        if 3 <= current_month <= 5:
            return Season.SPRING
        elif 6 <= current_month <= 8:
            return Season.SUMMER
        elif 9 <= current_month <= 11:
            return Season.AUTUMN
        else:
            return Season.WINTER

    def get_seasonal_events(self, season: Optional[Season] = None) -> List[Dict[str, Any]]:
        """獲取季節性活動"""
        if season is None:
            season = self.get_current_season()

        current_date = date.today()

        seasonal_events = []
        for event_id, event in self.events.items():
            if event.season == season and event.start_date <= current_date <= event.end_date:
                event.is_active = True
                seasonal_events.append({
                    'event_id': event.event_id,
                    'name': event.name,
                    'description': event.description,
                    'season': event.season.value,
                    'event_type': event.event_type.value,
                    'start_date': event.start_date.isoformat(),
                    'end_date': event.end_date.isoformat(),
                    'rewards': event.rewards,
                    'requirements': event.requirements,
                    'objectives': event.objectives,
                    'participants_count': len(event.participants),
                    'is_active': event.is_active
                })

        return seasonal_events

    def get_available_challenges(self, username: str) -> List[Dict[str, Any]]:
        """獲取可用挑戰"""
        game_data = self.data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            return []

        available_challenges = []
        for challenge_id, challenge in self.challenges.items():
            # 檢查先決條件
            if self._check_challenge_prerequisites(challenge, game_data):
                available_challenges.append({
                    'challenge_id': challenge.challenge_id,
                    'title': challenge.title,
                    'description': challenge.description,
                    'difficulty': challenge.difficulty.value,
                    'duration_days': challenge.duration_days,
                    'objectives': challenge.objectives,
                    'rewards': challenge.rewards,
                    'prerequisites': challenge.prerequisites
                })

        return available_challenges

    def start_challenge(self, username: str, challenge_id: str) -> bool:
        """開始挑戰"""
        if challenge_id not in self.challenges:
            return False

        challenge = self.challenges[challenge_id]

        # 檢查是否已經開始
        if username in self.player_progress and challenge_id in self.player_progress[username]:
            return False

        # 檢查先決條件
        game_data = self.data_manager.load_game_data(username, 'default', 'web')
        if not game_data or not self._check_challenge_prerequisites(challenge, game_data):
            return False

        # 建立進度記錄
        progress = PlayerProgress(
            username=username,
            event_id=challenge_id,
            objectives_progress={obj['type']: 0 for obj in challenge.objectives},
            start_time=datetime.now(),
            last_update=datetime.now()
        )

        if username not in self.player_progress:
            self.player_progress[username] = {}
        self.player_progress[username][challenge_id] = progress

        # 設定挑戰時間
        challenge.start_time = datetime.now()
        challenge.end_time = datetime.now() + timedelta(days=challenge.duration_days)

        logging.info(f"玩家 {username} 開始挑戰: {challenge.title}")
        return True

    def update_player_progress(self, username: str, event_id: str, progress_data: Dict[str, Any]):
        """更新玩家進度"""
        if (username not in self.player_progress or
            event_id not in self.player_progress[username]):
            return False

        progress = self.player_progress[username][event_id]
        progress.objectives_progress.update(progress_data)
        progress.last_update = datetime.now()

        # 檢查是否完成
        if self._check_progress_completion(progress, event_id):
            progress.is_completed = True
            self._award_completion_rewards(username, event_id)
            logging.info(f"玩家 {username} 完成活動/挑戰: {event_id}")

        return True

    def _check_challenge_prerequisites(self, challenge: Challenge, game_data: GameData) -> bool:
        """檢查挑戰先決條件"""
        prereqs = challenge.prerequisites

        # 檢查遊戲天數
        if 'min_days' in prereqs and game_data.days < prereqs['min_days']:
            return False

        # 檢查等級（簡化為天數）
        if 'min_level' in prereqs and (game_data.days // 10) < prereqs['min_level']:
            return False

        # 檢查投資組合價值
        if 'min_portfolio' in prereqs:
            portfolio_value = getattr(game_data, 'cash', 0)
            if hasattr(game_data, 'stocks'):
                # 簡化計算
                portfolio_value += sum(
                    stock.get('owned', 0) * stock.get('price', 0)
                    for stock in game_data.stocks.values()
                )
            if portfolio_value < prereqs['min_portfolio']:
                return False

        return True

    def _check_progress_completion(self, progress: PlayerProgress, event_id: str) -> bool:
        """檢查進度是否完成"""
        # 獲取目標
        objectives = []
        if event_id in self.events:
            objectives = self.events[event_id].objectives
        elif event_id in self.challenges:
            objectives = self.challenges[event_id].objectives

        # 檢查每個目標是否達成
        for objective in objectives:
            obj_type = objective['type']
            target = objective['target']
            current = progress.objectives_progress.get(obj_type, 0)

            if current < target:
                return False

        return True

    def _award_completion_rewards(self, username: str, event_id: str):
        """頒發完成獎勵"""
        rewards = {}
        if event_id in self.events:
            rewards = self.events[event_id].rewards
        elif event_id in self.challenges:
            rewards = self.challenges[event_id].rewards

        # 在實際實現中，這裡會更新遊戲資料並給予獎勵
        logging.info(f"給予玩家 {username} 完成獎勵: {rewards}")

    def get_player_event_progress(self, username: str, event_id: str) -> Optional[Dict[str, Any]]:
        """獲取玩家活動進度"""
        if (username not in self.player_progress or
            event_id not in self.player_progress[username]):
            return None

        progress = self.player_progress[username][event_id]

        return {
            'username': progress.username,
            'event_id': progress.event_id,
            'objectives_progress': progress.objectives_progress,
            'start_time': progress.start_time.isoformat(),
            'last_update': progress.last_update.isoformat(),
            'is_completed': progress.is_completed,
            'rewards_claimed': progress.rewards_claimed
        }

    def claim_rewards(self, username: str, event_id: str) -> bool:
        """領取獎勵"""
        if (username not in self.player_progress or
            event_id not in self.player_progress[username]):
            return False

        progress = self.player_progress[username][event_id]

        if not progress.is_completed or progress.rewards_claimed:
            return False

        # 標記已領取獎勵
        progress.rewards_claimed = True

        # 實際領取獎勵的邏輯在這裡實現
        logging.info(f"玩家 {username} 領取活動 {event_id} 的獎勵")
        return True

    def get_event_statistics(self, event_id: str) -> Dict[str, Any]:
        """獲取活動統計"""
        if event_id not in self.events:
            return {}

        event = self.events[event_id]

        # 計算參與者統計
        total_participants = len(event.participants)
        completed_count = sum(
            1 for username, progress_dict in self.player_progress.items()
            if event_id in progress_dict and progress_dict[event_id].is_completed
        )

        return {
            'event_id': event_id,
            'name': event.name,
            'total_participants': total_participants,
            'completed_count': completed_count,
            'completion_rate': (completed_count / total_participants * 100) if total_participants > 0 else 0,
            'is_active': event.is_active
        }

    def generate_random_event(self, season: Optional[Season] = None) -> SeasonalEvent:
        """生成隨機季節性活動"""
        if season is None:
            season = self.get_current_season()

        event_types = [EventType.FESTIVAL, EventType.CHALLENGE, EventType.BONUS, EventType.SPECIAL]

        # 根據季節調整事件類型權重
        if season == Season.SPRING:
            weights = [0.4, 0.3, 0.2, 0.1]  # 春季偏向節慶
        elif season == Season.SUMMER:
            weights = [0.2, 0.4, 0.2, 0.2]  # 夏季偏向挑戰
        elif season == Season.AUTUMN:
            weights = [0.3, 0.2, 0.4, 0.1]  # 秋季偏向獎勵
        else:  # WINTER
            weights = [0.2, 0.3, 0.2, 0.3]  # 冬季偏向特殊活動

        event_type = random.choices(event_types, weights=weights)[0]

        # 生成事件名稱和描述
        if event_type == EventType.FESTIVAL:
            names = ["投資嘉年華", "理財博覽會", "股東大會", "投資者日"]
            descriptions = ["歡慶投資盛會，參與就有機會獲得豐厚獎勵！"]
        elif event_type == EventType.CHALLENGE:
            names = ["投資挑戰賽", "理財競賽", "股海爭霸", "財富積累賽"]
            descriptions = ["挑戰自我極限，成為頂尖投資者！"]
        elif event_type == EventType.BONUS:
            names = ["雙倍收益日", "幸運抽獎", "額外股息", "投資紅包"]
            descriptions = ["好運連連，投資收益加倍！"]
        else:  # SPECIAL
            names = ["神秘活動", "限時任務", "隱藏挑戰", "特別邀請賽"]
            descriptions = ["神秘事件即將展開，準備迎接挑戰吧！"]

        name = random.choice(names)
        description = random.choice(descriptions)

        # 生成獎勵
        rewards = self._generate_random_rewards(event_type)

        # 生成目標
        objectives = self._generate_random_objectives(event_type)

        # 設定時間
        current_date = date.today()
        start_date = current_date + timedelta(days=random.randint(1, 7))
        duration = random.randint(7, 21)
        end_date = start_date + timedelta(days=duration)

        event_id = f"random_{season.value}_{int(datetime.now().timestamp())}"

        event = SeasonalEvent(
            event_id=event_id,
            name=name,
            description=description,
            season=season,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            rewards=rewards,
            requirements={'min_level': random.randint(1, 5)},
            objectives=objectives
        )

        self.events[event_id] = event
        return event

    def _generate_random_rewards(self, event_type: EventType) -> Dict[str, Any]:
        """生成隨機獎勵"""
        if event_type == EventType.FESTIVAL:
            return {
                'cash_bonus': random.randint(1000, 10000),
                'experience_bonus': random.randint(50, 200),
                'special_item': random.choice(['festival_pack', 'investment_boost', 'luck_charm'])
            }
        elif event_type == EventType.CHALLENGE:
            return {
                'cash': random.randint(5000, 20000),
                'skill_points': random.randint(25, 100),
                'achievement_unlock': f'challenge_{random.randint(1, 100)}'
            }
        elif event_type == EventType.BONUS:
            return {
                'multiplier': round(random.uniform(1.2, 2.0), 1),
                'bonus_days': random.randint(3, 10),
                'special_dividend': round(random.uniform(0.01, 0.05), 3)
            }
        else:  # SPECIAL
            return {
                'mystery_box': random.choice(['gold', 'diamond', 'legendary']),
                'exclusive_title': f'special_{random.randint(1, 100)}',
                'guild_reputation': random.randint(50, 200)
            }

    def _generate_random_objectives(self, event_type: EventType) -> List[Dict[str, Any]]:
        """生成隨機目標"""
        objectives = []

        if event_type == EventType.FESTIVAL:
            objectives.append({
                'type': 'invest',
                'target': random.randint(5000, 20000),
                'description': f'投資至少${random.randint(5000, 20000)}'
            })
            objectives.append({
                'type': 'trade',
                'target': random.randint(3, 10),
                'description': f'完成至少{random.randint(3, 10)}筆交易'
            })

        elif event_type == EventType.CHALLENGE:
            objectives.append({
                'type': 'profit',
                'target': round(random.uniform(0.05, 0.20), 2),
                'description': f'實現{random.uniform(0.05, 0.20):.1%}投資報酬'
            })
            objectives.append({
                'type': 'activity',
                'target': random.randint(5, 15),
                'description': f'完成{random.randint(5, 15)}次遊戲活動'
            })

        elif event_type == EventType.BONUS:
            objectives.append({
                'type': 'participate',
                'target': random.randint(1, 5),
                'description': f'參與{random.randint(1, 5)}次活動'
            })

        else:  # SPECIAL
            objectives.append({
                'type': 'mystery',
                'target': random.randint(1, 3),
                'description': f'完成{random.randint(1, 3)}個神秘任務'
            })

        return objectives
