import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from modules.game_data import GameData
from modules.unified_data_manager import UnifiedDataManager
from modules.advanced_casino import AdvancedCasinoManager


class MiniGameType(Enum):
    """迷你遊戲類型"""
    CASINO = "casino"           # 賭場遊戲
    PUZZLE = "puzzle"           # 益智遊戲
    TRIVIA = "trivia"           # 知識問答
    PREDICTION = "prediction"   # 預測遊戲
    SIDE_HUSTLE = "side_hustle" # 副業活動


class CasinoGame(Enum):
    """賭場遊戲類型"""
    SLOTS = "slots"
    BLACKJACK = "blackjack"
    ROULETTE = "roulette"
    DICE = "dice"
    BACCARAT = "baccarat"


class Difficulty(Enum):
    """遊戲難度"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class MiniGameResult:
    """迷你遊戲結果"""
    game_id: str
    player_username: str
    game_type: MiniGameType
    score: int
    winnings: float
    experience_gained: int
    completed_at: datetime
    metadata: Dict[str, Any]  # 遊戲特定資料


@dataclass
class SideHustle:
    """副業活動"""
    hustle_id: str
    name: str
    description: str
    base_income: float
    duration_hours: int
    energy_cost: int
    skill_requirements: Dict[str, int]
    success_rate: float
    risk_level: str
    category: str


@dataclass
class CasinoGameState:
    """賭場遊戲狀態"""
    game_id: str
    player_username: str
    game_type: CasinoGame
    bet_amount: float
    game_data: Dict[str, Any]
    start_time: datetime
    status: str  # active, completed, cancelled


@dataclass
class TriviaQuestion:
    """知識問答題目"""
    question_id: str
    question: str
    options: List[str]
    correct_answer: int
    difficulty: Difficulty
    category: str
    points: int


class MiniGamesManager:
    """
    迷你遊戲和副業管理系統
    提供各種娛樂性和收益性活動
    """

    def __init__(self, data_manager: UnifiedDataManager, db_path: str = None):
        self.data_manager = data_manager
        self.db_path = db_path

        # 遊戲狀態
        self.active_games: Dict[str, CasinoGameState] = {}
        self.daily_challenges: Dict[str, Dict[str, Any]] = {}
        self.trivia_questions: List[TriviaQuestion] = []

        # 初始化進階賭場管理器
        self.advanced_casino = AdvancedCasinoManager(data_manager, db_path)

        # 初始化資料庫結構
        self._init_mini_games_db_schema()

        # 載入遊戲資料
        self._load_side_hustles()
        self._load_trivia_questions()

    def _init_mini_games_db_schema(self):
        """初始化迷你遊戲資料庫結構"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 遊戲結果表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mini_game_results (
                    game_id TEXT NOT NULL,
                    player_username TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    score INTEGER DEFAULT 0,
                    winnings REAL DEFAULT 0.0,
                    experience_gained INTEGER DEFAULT 0,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    PRIMARY KEY (game_id, player_username)
                )
            """)

            # 副業活動表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS side_hustles (
                    hustle_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    base_income REAL NOT NULL,
                    duration_hours INTEGER NOT NULL,
                    energy_cost INTEGER NOT NULL,
                    skill_requirements TEXT,
                    success_rate REAL NOT NULL,
                    risk_level TEXT DEFAULT 'low',
                    category TEXT DEFAULT 'general'
                )
            """)

            # 每日挑戰表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS daily_challenges (
                    username TEXT NOT NULL,
                    challenge_date DATE NOT NULL,
                    challenge_type TEXT NOT NULL,
                    target INTEGER NOT NULL,
                    current_progress INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    reward_claimed BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (username, challenge_date, challenge_type)
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"初始化迷你遊戲資料庫失敗: {e}")

    def _load_side_hustles(self):
        """載入副業活動"""
        self.side_hustles = {
            'freelance_writing': SideHustle(
                hustle_id='freelance_writing',
                name='自由寫作',
                description='為雜誌和網站撰寫文章',
                base_income=500.0,
                duration_hours=4,
                energy_cost=20,
                skill_requirements={'intelligence': 3},
                success_rate=0.7,
                risk_level='low',
                category='creative'
            ),

            'online_tutoring': SideHustle(
                hustle_id='online_tutoring',
                name='線上家教',
                description='教授學生各科目知識',
                base_income=800.0,
                duration_hours=2,
                energy_cost=15,
                skill_requirements={'intelligence': 5},
                success_rate=0.8,
                risk_level='low',
                category='education'
            ),

            'graphic_design': SideHustle(
                hustle_id='graphic_design',
                name='平面設計',
                description='設計海報和廣告素材',
                base_income=1200.0,
                duration_hours=6,
                energy_cost=30,
                skill_requirements={'intelligence': 4, 'diligence': 3},
                success_rate=0.6,
                risk_level='low',
                category='creative'
            ),

            'delivery_driver': SideHustle(
                hustle_id='delivery_driver',
                name='外送員',
                description='配送食物和包裹',
                base_income=300.0,
                duration_hours=3,
                energy_cost=25,
                skill_requirements={'stamina': 3},
                success_rate=0.9,
                risk_level='medium',
                category='physical'
            ),

            'stock_trading': SideHustle(
                hustle_id='stock_trading',
                name='股票交易',
                description='進行短期股票交易',
                base_income=1000.0,
                duration_hours=2,
                energy_cost=10,
                skill_requirements={'intelligence': 6},
                success_rate=0.5,
                risk_level='high',
                category='financial'
            ),

            'social_media_manager': SideHustle(
                hustle_id='social_media_manager',
                name='社群媒體管理',
                description='管理企業社群帳號',
                base_income=700.0,
                duration_hours=3,
                energy_cost=15,
                skill_requirements={'charisma': 4},
                success_rate=0.75,
                risk_level='low',
                category='marketing'
            ),

            'app_development': SideHustle(
                hustle_id='app_development',
                name='應用程式開發',
                description='開發手機應用程式',
                base_income=2500.0,
                duration_hours=8,
                energy_cost=40,
                skill_requirements={'intelligence': 7, 'diligence': 5},
                success_rate=0.4,
                risk_level='medium',
                category='technology'
            ),

            'photography': SideHustle(
                hustle_id='photography',
                name='商業攝影',
                description='為活動和產品拍攝照片',
                base_income=900.0,
                duration_hours=4,
                energy_cost=20,
                skill_requirements={'diligence': 4},
                success_rate=0.65,
                risk_level='low',
                category='creative'
            )
        }

    def _load_trivia_questions(self):
        """載入知識問答題目"""
        self.trivia_questions = [
            TriviaQuestion(
                question_id='finance_001',
                question='什麼是股票股息？',
                options=['公司利潤', '股票價格', '公司分紅', '市場指數'],
                correct_answer=2,
                difficulty=Difficulty.EASY,
                category='finance',
                points=10
            ),

            TriviaQuestion(
                question_id='finance_002',
                question='什麼是通貨膨脹？',
                options=['貨幣升值', '物價上漲', '利率上升', 'GDP增長'],
                correct_answer=1,
                difficulty=Difficulty.EASY,
                category='finance',
                points=10
            ),

            TriviaQuestion(
                question_id='finance_003',
                question='什麼是多元化投資？',
                options=['只投資股票', '只投資債券', '分散投資不同資產', '只投資房地產'],
                correct_answer=2,
                difficulty=Difficulty.MEDIUM,
                category='finance',
                points=15
            ),

            TriviaQuestion(
                question_id='finance_004',
                question='什麼是複利？',
                options=['簡單利息', '利息滾利息', '銀行存款', '股票分紅'],
                correct_answer=1,
                difficulty=Difficulty.MEDIUM,
                category='finance',
                points=15
            ),

            TriviaQuestion(
                question_id='business_001',
                question='什麼是創業公司？',
                options=['大公司', '新成立公司', '上市公司', '國營企業'],
                correct_answer=1,
                difficulty=Difficulty.EASY,
                category='business',
                points=10
            ),

            TriviaQuestion(
                question_id='business_002',
                question='什麼是供應鏈？',
                options=['銷售網路', '生產流程', '產品從生產到消費的過程', '市場分析'],
                correct_answer=2,
                difficulty=Difficulty.MEDIUM,
                category='business',
                points=15
            ),

            TriviaQuestion(
                question_id='tech_001',
                question='什麼是人工智慧？',
                options=['機器人', '電腦模擬人類智慧', '網路技術', '手機應用'],
                correct_answer=1,
                difficulty=Difficulty.MEDIUM,
                category='technology',
                points=15
            ),

            TriviaQuestion(
                question_id='tech_002',
                question='什麼是區塊鏈？',
                options=['新型手機', '分散式帳本技術', '網路瀏覽器', '作業系統'],
                correct_answer=1,
                difficulty=Difficulty.HARD,
                category='technology',
                points=20
            )
        ]

    # ===== 進階賭場遊戲 =====

    def play_advanced_casino(self, username: str, game_type: str, bet_amount: float, **kwargs) -> Dict[str, Any]:
        """
        玩進階賭場遊戲

        Args:
            username: 玩家用戶名
            game_type: 遊戲類型 (roulette, baccarat, dice)
            bet_amount: 下注金額
            **kwargs: 遊戲特定參數

        Returns:
            遊戲結果
        """
        try:
            if game_type == "roulette":
                bet_type = kwargs.get('bet_type')
                bet_value = kwargs.get('bet_value')
                result = self.advanced_casino.play_roulette(username, bet_amount, bet_type, bet_value)
            elif game_type == "baccarat":
                bet_type = kwargs.get('bet_type')
                result = self.advanced_casino.play_baccarat(username, bet_amount, bet_type)
            elif game_type == "dice":
                dice_game_type = kwargs.get('dice_game_type')
                prediction = kwargs.get('prediction')
                result = self.advanced_casino.play_dice_game(username, bet_amount, dice_game_type, prediction)
            else:
                return {"error": "不支援的遊戲類型"}

            return result

        except Exception as e:
            logging.error(f"進階賭場遊戲失敗: {e}")
            return {"error": str(e)}

    def get_casino_info(self) -> Dict[str, Any]:
        """獲取賭場資訊"""
        return {
            "jackpots": self.advanced_casino.get_progressive_jackpots(),
            "games_available": ["slots", "blackjack", "roulette", "baccarat", "dice"],
            "vip_levels": ["bronze", "silver", "gold", "platinum", "diamond"]
        }

    def get_player_vip_status(self, username: str) -> Dict[str, Any]:
        """獲取玩家VIP狀態"""
        vip_level = self.advanced_casino.get_vip_level(username)
        perks = self.advanced_casino.get_vip_perks(vip_level)
        stats = self.advanced_casino.get_casino_stats(username)

        return {
            "vip_level": vip_level.value,
            "perks": perks,
            "stats": stats
        }

    # ===== 增強版拉霸遊戲 =====

    def play_enhanced_slots(self, username: str, bet_amount: float) -> MiniGameResult:
        """
        玩增強版拉霸遊戲（支援累積獎池）

        Args:
            username: 玩家用戶名
            bet_amount: 下注金額

        Returns:
            遊戲結果
        """
        game_id = f"enhanced_slots_{int(datetime.now().timestamp())}_{username}"

        # 增強版拉霸邏輯
        symbols = ['🍒', '🍋', '🍊', '⭐', '💎', '7️⃣', '🎰', '💰']
        reels = [random.choice(symbols) for _ in range(5)]  # 5個滾輪

        # 計算中獎
        unique_symbols = set(reels)
        max_count = max(reels.count(symbol) for symbol in unique_symbols)

        # 貢獻獎池
        self.advanced_casino.contribute_to_jackpot(bet_amount, "slots")

        # 計算獎金
        if max_count >= 5:  # 五個相同
            if reels[0] == '7️⃣':
                # 觸發大獎池
                jackpot_prize = self.advanced_casino.trigger_jackpot("mega_jackpot", username)
                winnings = jackpot_prize
                multiplier = jackpot_prize / bet_amount
            else:
                multiplier = 100.0  # 普通大獎
                winnings = bet_amount * multiplier
        elif max_count >= 4:  # 四個相同
            multiplier = 20.0
            winnings = bet_amount * multiplier
        elif max_count >= 3:  # 三個相同
            if reels.count(reels[0]) >= 3:
                multiplier = 10.0
            else:
                multiplier = 5.0
            winnings = bet_amount * multiplier
        elif max_count >= 2:  # 兩個相同
            multiplier = 2.0
            winnings = bet_amount * multiplier
        else:
            winnings = 0
            multiplier = 0

        # 儲存遊戲結果
        result = MiniGameResult(
            game_id=game_id,
            player_username=username,
            game_type=MiniGameType.CASINO,
            score=int(winnings // 10),
            winnings=winnings,
            experience_gained=int(winnings // 100),
            completed_at=datetime.now(),
            metadata={
                'game': 'enhanced_slots',
                'reels': reels,
                'bet_amount': bet_amount,
                'multiplier': multiplier,
                'jackpot_contribution': bet_amount * 0.01
            }
        )

        self._save_game_result(result)
        return result
        """
        玩拉霸遊戲

        Args:
            username: 玩家用戶名
            bet_amount: 下注金額

        Returns:
            遊戲結果
        """
        game_id = f"slots_{int(datetime.now().timestamp())}_{username}"

        # 簡化的拉霸邏輯
        symbols = ['🍒', '🍋', '🍊', '⭐', '💎', '7️⃣']
        reels = [random.choice(symbols) for _ in range(3)]

        # 計算中獎
        if reels[0] == reels[1] == reels[2]:
            if reels[0] == '7️⃣':
                multiplier = 10  # 大獎
            elif reels[0] == '💎':
                multiplier = 5   # 小獎
            else:
                multiplier = 3   # 普通獎
            winnings = bet_amount * multiplier
            score = 100
        elif reels[0] == reels[1] or reels[1] == reels[2]:
            winnings = bet_amount * 1.5
            score = 50
        else:
            winnings = 0
            score = 10

        # 儲存遊戲結果
        result = MiniGameResult(
            game_id=game_id,
            player_username=username,
            game_type=MiniGameType.CASINO,
            score=score,
            winnings=winnings,
            experience_gained=score // 10,
            completed_at=datetime.now(),
            metadata={
                'game': 'slots',
                'reels': reels,
                'bet_amount': bet_amount
            }
        )

        self._save_game_result(result)
        return result

    def play_blackjack(self, username: str, bet_amount: float, action: str) -> Dict[str, Any]:
        """
        玩21點遊戲

        Args:
            username: 玩家用戶名
            bet_amount: 下注金額
            action: 動作 (hit, stand, double, surrender)

        Returns:
            遊戲狀態和結果
        """
        game_id = f"blackjack_{int(datetime.now().timestamp())}_{username}"

        # 檢查是否已有進行中的遊戲
        if username in self.active_games:
            game_state = self.active_games[username]
        else:
            # 新遊戲
            player_cards = [self._draw_card(), self._draw_card()]
            dealer_cards = [self._draw_card(), self._draw_card()]

            game_state = CasinoGameState(
                game_id=game_id,
                player_username=username,
                game_type=CasinoGame.BLACKJACK,
                bet_amount=bet_amount,
                game_data={
                    'player_cards': player_cards,
                    'dealer_cards': dealer_cards,
                    'player_score': self._calculate_blackjack_score(player_cards),
                    'dealer_score': self._calculate_blackjack_score([dealer_cards[0]]),  # 只顯示第一張
                    'game_status': 'playing'
                },
                start_time=datetime.now(),
                status='active'
            )
            self.active_games[username] = game_state

        # 處理玩家動作
        if action == 'hit':
            new_card = self._draw_card()
            game_state.game_data['player_cards'].append(new_card)
            game_state.game_data['player_score'] = self._calculate_blackjack_score(game_state.game_data['player_cards'])

            # 檢查是否爆牌
            if game_state.game_data['player_score'] > 21:
                game_state.game_data['game_status'] = 'bust'
                game_state.status = 'completed'
                winnings = 0
            else:
                return {
                    'status': 'continue',
                    'game_data': game_state.game_data,
                    'message': f'抽到 {new_card}，目前點數：{game_state.game_data["player_score"]}'
                }

        elif action == 'stand':
            # 莊家回合
            dealer_cards = game_state.game_data['dealer_cards']
            dealer_score = self._calculate_blackjack_score(dealer_cards)

            while dealer_score < 17:
                new_card = self._draw_card()
                dealer_cards.append(new_card)
                dealer_score = self._calculate_blackjack_score(dealer_cards)

            game_state.game_data['dealer_score'] = dealer_score
            game_state.game_data['dealer_cards'] = dealer_cards

            player_score = game_state.game_data['player_score']

            # 判斷勝負
            if dealer_score > 21 or player_score > dealer_score:
                winnings = bet_amount * 2
                result = 'win'
            elif player_score == dealer_score:
                winnings = bet_amount
                result = 'push'
            else:
                winnings = 0
                result = 'lose'

            game_state.game_data['game_status'] = result
            game_state.status = 'completed'

        elif action == 'double':
            if len(game_state.game_data['player_cards']) == 2:
                bet_amount *= 2
                game_state.bet_amount = bet_amount

                new_card = self._draw_card()
                game_state.game_data['player_cards'].append(new_card)
                game_state.game_data['player_score'] = self._calculate_blackjack_score(game_state.game_data['player_cards'])

                # 自動站立
                return self.play_blackjack(username, bet_amount, 'stand')

        # 儲存結果
        if game_state.status == 'completed':
            result = MiniGameResult(
                game_id=game_id,
                player_username=username,
                game_type=MiniGameType.CASINO,
                score=100 if result == 'win' else 50 if result == 'push' else 10,
                winnings=winnings,
                experience_gained=10,
                completed_at=datetime.now(),
                metadata={
                    'game': 'blackjack',
                    'bet_amount': bet_amount,
                    'result': result,
                    'final_data': game_state.game_data
                }
            )
            self._save_game_result(result)
            del self.active_games[username]

        return {
            'status': 'completed',
            'result': result,
            'winnings': winnings,
            'game_data': game_state.game_data
        }

    def _draw_card(self) -> str:
        """抽一張牌"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        return f"{random.choice(ranks)}{random.choice(suits)}"

    def _calculate_blackjack_score(self, cards: List[str]) -> int:
        """計算21點分數"""
        score = 0
        aces = 0

        for card in cards:
            rank = card[:-1]  # 移除花色

            if rank in ['J', 'Q', 'K']:
                score += 10
            elif rank == 'A':
                score += 11
                aces += 1
            else:
                score += int(rank)

        # 處理A牌
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1

        return score

    # ===== 知識問答遊戲 =====

    def get_trivia_question(self, difficulty: Difficulty = None, category: str = None) -> TriviaQuestion:
        """
        獲取知識問答題目

        Args:
            difficulty: 難度等級
            category: 題目分類

        Returns:
            隨機題目
        """
        candidates = self.trivia_questions

        if difficulty:
            candidates = [q for q in candidates if q.difficulty == difficulty]

        if category:
            candidates = [q for q in candidates if q.category == category]

        if candidates:
            return random.choice(candidates)
        else:
            # 返回通用題目
            return self.trivia_questions[0]

    def answer_trivia_question(self, username: str, question_id: str, answer: int) -> Dict[str, Any]:
        """
        回答知識問答題目

        Args:
            username: 玩家用戶名
            question_id: 題目ID
            answer: 答案選項 (0-3)

        Returns:
            回答結果
        """
        question = next((q for q in self.trivia_questions if q.question_id == question_id), None)

        if not question:
            return {'correct': False, 'message': '題目不存在'}

        correct = answer == question.correct_answer
        points = question.points if correct else 0
        experience = points // 2

        # 儲存結果
        result = MiniGameResult(
            game_id=f"trivia_{int(datetime.now().timestamp())}_{username}",
            player_username=username,
            game_type=MiniGameType.TRIVIA,
            score=points,
            winnings=0,  # 問答不給錢
            experience_gained=experience,
            completed_at=datetime.now(),
            metadata={
                'question_id': question_id,
                'correct_answer': question.correct_answer,
                'player_answer': answer,
                'category': question.category,
                'difficulty': question.difficulty.value
            }
        )

        self._save_game_result(result)

        return {
            'correct': correct,
            'points': points,
            'experience': experience,
            'correct_answer': question.correct_answer,
            'message': '答對了！' if correct else '答錯了，再接再厲！'
        }

    # ===== 副業活動 =====

    def get_available_side_hustles(self, username: str) -> List[Dict[str, Any]]:
        """
        獲取可用副業活動

        Args:
            username: 玩家用戶名

        Returns:
            可用副業列表
        """
        game_data = self.data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            return []

        available_hustles = []

        for hustle_id, hustle in self.side_hustles.items():
            # 檢查技能要求
            skill_met = True
            for skill, required_level in hustle.skill_requirements.items():
                current_level = getattr(game_data, skill, 0)
                if current_level < required_level:
                    skill_met = False
                    break

            # 檢查體力
            energy_ok = getattr(game_data, 'stamina', 0) >= hustle.energy_cost

            if skill_met and energy_ok:
                available_hustles.append({
                    'hustle_id': hustle.hustle_id,
                    'name': hustle.name,
                    'description': hustle.description,
                    'base_income': hustle.base_income,
                    'duration_hours': hustle.duration_hours,
                    'energy_cost': hustle.energy_cost,
                    'skill_requirements': hustle.skill_requirements,
                    'success_rate': hustle.success_rate,
                    'risk_level': hustle.risk_level,
                    'category': hustle.category
                })

        return available_hustles

    def perform_side_hustle(self, username: str, hustle_id: str) -> Dict[str, Any]:
        """
        執行副業活動

        Args:
            username: 玩家用戶名
            hustle_id: 副業ID

        Returns:
            執行結果
        """
        if hustle_id not in self.side_hustles:
            return {'success': False, 'message': '副業不存在'}

        hustle = self.side_hustles[hustle_id]
        game_data = self.data_manager.load_game_data(username, 'default', 'web')

        if not game_data:
            return {'success': False, 'message': '無法載入遊戲資料'}

        # 檢查體力
        if getattr(game_data, 'stamina', 0) < hustle.energy_cost:
            return {'success': False, 'message': '體力不足'}

        # 模擬執行結果
        success = random.random() < hustle.success_rate

        if success:
            # 計算收入（加入隨機變化）
            income_variation = random.uniform(0.8, 1.2)
            actual_income = hustle.base_income * income_variation

            # 計算經驗值
            experience_gained = int(hustle.duration_hours * 5)

            # 更新遊戲資料
            game_data.cash += actual_income
            game_data.stamina -= hustle.energy_cost
            game_data.experience += experience_gained

            # 儲存結果
            result = MiniGameResult(
                game_id=f"hustle_{int(datetime.now().timestamp())}_{username}",
                player_username=username,
                game_type=MiniGameType.SIDE_HUSTLE,
                score=int(actual_income // 10),
                winnings=actual_income,
                experience_gained=experience_gained,
                completed_at=datetime.now(),
                metadata={
                    'hustle_id': hustle_id,
                    'hustle_name': hustle.name,
                    'duration': hustle.duration_hours,
                    'energy_cost': hustle.energy_cost
                }
            )
            self._save_game_result(result)

            # 儲存遊戲資料
            self.data_manager.save_game_data(game_data, username, 'default', 'web')

            return {
                'success': True,
                'income': actual_income,
                'experience': experience_gained,
                'message': f'成功完成 {hustle.name}，獲得 ${actual_income:.0f} 和 {experience_gained} 經驗值！'
            }
        else:
            # 失敗情況
            game_data.stamina -= hustle.energy_cost // 2  # 失敗只消耗一半體力
            self.data_manager.save_game_data(game_data, username, 'default', 'web')

            return {
                'success': False,
                'message': f'{hustle.name} 失敗了，但獲得了一些經驗。'
            }

    # ===== 每日挑戰 =====

    def get_daily_challenge(self, username: str) -> Dict[str, Any]:
        """
        獲取今日挑戰

        Args:
            username: 玩家用戶名

        Returns:
            今日挑戰
        """
        today = datetime.now().date()
        challenge_key = f"{username}_{today}"

        if challenge_key not in self.daily_challenges:
            # 生成新挑戰
            challenge = self._generate_daily_challenge()
            self.daily_challenges[challenge_key] = challenge

        return self.daily_challenges[challenge_key]

    def _generate_daily_challenge(self) -> Dict[str, Any]:
        """生成每日挑戰"""
        challenge_types = [
            {
                'type': 'invest',
                'description': '進行投資交易',
                'target': random.randint(3, 8),
                'reward': {'cash': 200, 'experience': 50}
            },
            {
                'type': 'study',
                'description': '學習新知識',
                'target': random.randint(2, 5),
                'reward': {'experience': 75}
            },
            {
                'type': 'social',
                'description': '參與社交活動',
                'target': random.randint(1, 3),
                'reward': {'social_points': 25}
            },
            {
                'type': 'earn',
                'description': '賺取額外收入',
                'target': random.randint(500, 2000),
                'reward': {'cash': 100}
            }
        ]

        return random.choice(challenge_types)

    def update_daily_challenge_progress(self, username: str, progress: int):
        """
        更新每日挑戰進度

        Args:
            username: 玩家用戶名
            progress: 進度值
        """
        today = datetime.now().date()
        challenge_key = f"{username}_{today}"

        if challenge_key in self.daily_challenges:
            challenge = self.daily_challenges[challenge_key]
            challenge['current_progress'] = min(progress, challenge['target'])

    # ===== 工具方法 =====

    def _save_game_result(self, result: MiniGameResult):
        """儲存遊戲結果"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO mini_game_results
                (game_id, player_username, game_type, score, winnings, experience_gained, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.game_id,
                result.player_username,
                result.game_type.value,
                result.score,
                result.winnings,
                result.experience_gained,
                result.completed_at.isoformat(),
                json.dumps(result.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"儲存遊戲結果失敗: {e}")

    def get_player_stats(self, username: str) -> Dict[str, Any]:
        """獲取玩家遊戲統計"""
        if not self.db_path:
            return {}

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 獲取遊戲統計
            cur.execute("""
                SELECT game_type, COUNT(*) as games_played,
                       SUM(winnings) as total_winnings,
                       AVG(score) as avg_score,
                       SUM(experience_gained) as total_experience
                FROM mini_game_results
                WHERE player_username = ?
                GROUP BY game_type
            """, (username,))

            stats = {}
            for row in cur.fetchall():
                game_type, games, winnings, avg_score, experience = row
                stats[game_type] = {
                    'games_played': games,
                    'total_winnings': winnings or 0,
                    'avg_score': avg_score or 0,
                    'total_experience': experience or 0
                }

            conn.close()
            return stats

        except Exception as e:
            logging.warning(f"獲取玩家統計失敗: {e}")
            return {}

    def get_game_leaderboard(self, game_type: MiniGameType, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取遊戲排行榜"""
        if not self.db_path:
            return []

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT player_username,
                       COUNT(*) as games_played,
                       SUM(winnings) as total_winnings,
                       AVG(score) as avg_score,
                       MAX(score) as best_score
                FROM mini_game_results
                WHERE game_type = ?
                GROUP BY player_username
                ORDER BY total_winnings DESC
                LIMIT ?
            """, (game_type.value, limit))

            leaderboard = []
            for row in cur.fetchall():
                username, games, winnings, avg_score, best_score = row
                leaderboard.append({
                    'username': username,
                    'games_played': games,
                    'total_winnings': winnings or 0,
                    'avg_score': avg_score or 0,
                    'best_score': best_score or 0
                })

            conn.close()
            return leaderboard

        except Exception as e:
            logging.warning(f"獲取排行榜失敗: {e}")
            return []
