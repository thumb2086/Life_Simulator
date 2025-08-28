import asyncio
import json
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from game_data import GameData
from unified_data_manager import UnifiedDataManager
from unified_stock_manager import UnifiedStockManager


class GameMode(Enum):
    """遊戲模式"""
    SOLO = "solo"
    MULTIPLAYER = "multiplayer"
    TOURNAMENT = "tournament"
    LEAGUE = "league"


class SessionStatus(Enum):
    """遊戲會話狀態"""
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


class PlayerAction(Enum):
    """玩家動作類型"""
    BUY_STOCK = "buy_stock"
    SELL_STOCK = "sell_stock"
    USE_BUFF = "use_buff"
    COMPLETE_ACHIEVEMENT = "complete_achievement"
    JOIN_SESSION = "join_session"
    LEAVE_SESSION = "leave_session"


@dataclass
class MultiplayerSession:
    """多人遊戲會話"""
    session_id: str
    name: str
    host_username: str
    mode: GameMode
    status: SessionStatus
    max_players: int
    current_players: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    settings: Dict[str, Any]
    shared_market: Dict[str, float]  # 共享市場價格
    leaderboard: List[Dict[str, Any]]
    events: List[Dict[str, Any]]  # 會話事件記錄


@dataclass
class Tournament:
    """競賽活動"""
    tournament_id: str
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    prize_pool: float
    participants: List[str]
    rules: Dict[str, Any]
    status: str
    leaderboard: List[Dict[str, Any]]


class MultiplayerManager:
    """
    多人遊戲管理系統
    支援即時多人遊戲、競賽活動和社交功能
    """

    def __init__(self, data_manager: UnifiedDataManager, stock_manager: UnifiedStockManager):
        self.data_manager = data_manager
        self.stock_manager = stock_manager
        self.sessions: Dict[str, MultiplayerSession] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.active_connections: Dict[str, Set[str]] = {}  # username -> session_ids
        self.event_handlers: Dict[str, callable] = {}
        self.market_sync_timer = None

        # 啟動市場同步
        self._start_market_sync()

    def _start_market_sync(self):
        """啟動共享市場價格同步"""
        def sync_market():
            while True:
                try:
                    self._sync_shared_markets()
                    time.sleep(5)  # 每5秒同步一次
                except Exception as e:
                    logging.error(f"市場同步失敗: {e}")
                    time.sleep(10)

        self.market_sync_timer = threading.Thread(target=sync_market, daemon=True)
        self.market_sync_timer.start()

    def _sync_shared_markets(self):
        """同步所有活躍會話的共享市場"""
        for session_id, session in self.sessions.items():
            if session.status == SessionStatus.ACTIVE:
                # 獲取當前市場價格
                current_prices = self.stock_manager.sync_prices_from_database()

                # 應用會話特定的市場波動
                session_market = self._apply_session_market_effects(current_prices, session)

                # 更新會話市場
                session.shared_market.update(session_market)

                # 通知所有玩家市場更新
                self._broadcast_market_update(session_id, session_market)

    def _apply_session_market_effects(self, prices: Dict[str, float], session: MultiplayerSession) -> Dict[str, float]:
        """應用會話特定的市場效果"""
        modified_prices = prices.copy()

        # 根據會話設定應用特殊效果
        if session.settings.get('market_volatility_multiplier', 1.0) != 1.0:
            multiplier = session.settings['market_volatility_multiplier']
            for symbol in modified_prices:
                # 增加額外的隨機波動
                volatility = random.uniform(-0.02 * multiplier, 0.02 * multiplier)
                modified_prices[symbol] *= (1 + volatility)

        # 應用行業特定效果
        industry_effects = session.settings.get('industry_effects', {})
        for industry, effect in industry_effects.items():
            industry_stocks = self.stock_manager.get_industry_stocks(industry)
            for symbol in industry_stocks:
                if symbol in modified_prices:
                    modified_prices[symbol] *= (1 + effect)

        return modified_prices

    def create_session(self, host_username: str, name: str, mode: GameMode = GameMode.MULTIPLAYER,
                      max_players: int = 8, settings: Dict[str, Any] = None) -> str:
        """
        建立新的多人遊戲會話

        Args:
            host_username: 主持人用戶名
            name: 會話名稱
            mode: 遊戲模式
            max_players: 最大玩家數
            settings: 會話設定

        Returns:
            會話ID
        """
        session_id = f"session_{int(time.time())}_{random.randint(1000, 9999)}"

        # 獲取初始市場價格
        initial_prices = self.stock_manager.sync_prices_from_database()

        session = MultiplayerSession(
            session_id=session_id,
            name=name,
            host_username=host_username,
            mode=mode,
            status=SessionStatus.WAITING,
            max_players=max_players,
            current_players=[host_username],
            start_time=datetime.now(),
            end_time=None,
            settings=settings or {},
            shared_market=initial_prices,
            leaderboard=[],
            events=[{
                'type': 'session_created',
                'timestamp': datetime.now().isoformat(),
                'data': {'host': host_username, 'name': name}
            }]
        )

        self.sessions[session_id] = session

        # 記錄主持人加入連接
        if host_username not in self.active_connections:
            self.active_connections[host_username] = set()
        self.active_connections[host_username].add(session_id)

        logging.info(f"建立新會話: {session_id} by {host_username}")
        return session_id

    def join_session(self, username: str, session_id: str) -> bool:
        """
        加入遊戲會話

        Args:
            username: 用戶名
            session_id: 會話ID

        Returns:
            是否成功加入
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        if len(session.current_players) >= session.max_players:
            return False

        if username in session.current_players:
            return False

        session.current_players.append(username)

        # 記錄玩家加入事件
        session.events.append({
            'type': 'player_joined',
            'timestamp': datetime.now().isoformat(),
            'data': {'username': username}
        })

        # 記錄連接
        if username not in self.active_connections:
            self.active_connections[username] = set()
        self.active_connections[username].add(session_id)

        # 通知所有玩家
        self._broadcast_event(session_id, 'player_joined', {'username': username})

        logging.info(f"玩家 {username} 加入會話 {session_id}")
        return True

    def leave_session(self, username: str, session_id: str) -> bool:
        """
        離開遊戲會話

        Args:
            username: 用戶名
            session_id: 會話ID

        Returns:
            是否成功離開
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        if username not in session.current_players:
            return False

        session.current_players.remove(username)

        # 記錄玩家離開事件
        session.events.append({
            'type': 'player_left',
            'timestamp': datetime.now().isoformat(),
            'data': {'username': username}
        })

        # 如果主持人離開，結束會話
        if username == session.host_username and session.current_players:
            new_host = session.current_players[0]
            session.host_username = new_host
            session.events.append({
                'type': 'host_changed',
                'timestamp': datetime.now().isoformat(),
                'data': {'new_host': new_host}
            })

        # 如果沒有玩家了，結束會話
        if not session.current_players:
            session.status = SessionStatus.FINISHED
            session.end_time = datetime.now()

        # 清理連接記錄
        if username in self.active_connections:
            self.active_connections[username].discard(session_id)
            if not self.active_connections[username]:
                del self.active_connections[username]

        # 通知其他玩家
        self._broadcast_event(session_id, 'player_left', {'username': username})

        logging.info(f"玩家 {username} 離開會話 {session_id}")
        return True

    def start_session(self, session_id: str, host_username: str) -> bool:
        """
        開始遊戲會話

        Args:
            session_id: 會話ID
            host_username: 主持人用戶名

        Returns:
            是否成功開始
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        if session.host_username != host_username:
            return False

        if session.status != SessionStatus.WAITING:
            return False

        session.status = SessionStatus.ACTIVE
        session.start_time = datetime.now()

        # 初始化排行榜
        for username in session.current_players:
            session.leaderboard.append({
                'username': username,
                'net_worth': 0.0,
                'rank': 0,
                'last_update': datetime.now().isoformat()
            })

        session.events.append({
            'type': 'session_started',
            'timestamp': datetime.now().isoformat(),
            'data': {'player_count': len(session.current_players)}
        })

        # 通知所有玩家
        self._broadcast_event(session_id, 'session_started', {
            'shared_market': session.shared_market,
            'leaderboard': session.leaderboard
        })

        logging.info(f"會話 {session_id} 已開始")
        return True

    def end_session(self, session_id: str, host_username: str) -> bool:
        """
        結束遊戲會話

        Args:
            session_id: 會話ID
            host_username: 主持人用戶名

        Returns:
            是否成功結束
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        if session.host_username != host_username:
            return False

        session.status = SessionStatus.FINISHED
        session.end_time = datetime.now()

        # 計算最終排行榜
        self._update_leaderboard(session_id)

        session.events.append({
            'type': 'session_ended',
            'timestamp': datetime.now().isoformat(),
            'data': {'final_leaderboard': session.leaderboard}
        })

        # 通知所有玩家
        self._broadcast_event(session_id, 'session_ended', {
            'final_leaderboard': session.leaderboard
        })

        logging.info(f"會話 {session_id} 已結束")
        return True

    def _update_leaderboard(self, session_id: str):
        """更新會話排行榜"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        for i, entry in enumerate(session.leaderboard):
            username = entry['username']

            # 載入玩家遊戲資料
            game_data = self.data_manager.load_game_data(username, 'default', 'web')
            if game_data:
                # 計算淨資產
                holdings = game_data.stocks if hasattr(game_data, 'stocks') else {}
                holdings_formatted = {}
                for symbol, stock_data in holdings.items():
                    if stock_data.get('owned', 0) > 0:
                        holdings_formatted[symbol] = {
                            'qty': stock_data['owned'],
                            'avg_cost': stock_data.get('total_cost', 0) / stock_data['owned'] if stock_data['owned'] > 0 else 0
                        }

                portfolio_value = self.stock_manager.calculate_portfolio_value(
                    holdings_formatted, session.shared_market
                )
                net_worth = game_data.cash + portfolio_value

                entry['net_worth'] = net_worth
                entry['last_update'] = datetime.now().isoformat()

        # 重新排序排行榜
        session.leaderboard.sort(key=lambda x: x['net_worth'], reverse=True)

        # 更新排名
        for i, entry in enumerate(session.leaderboard):
            entry['rank'] = i + 1

    def record_player_action(self, session_id: str, username: str, action: PlayerAction,
                           action_data: Dict[str, Any]):
        """
        記錄玩家動作

        Args:
            session_id: 會話ID
            username: 用戶名
            action: 動作類型
            action_data: 動作資料
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        # 記錄動作事件
        session.events.append({
            'type': 'player_action',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'username': username,
                'action': action.value,
                'action_data': action_data
            }
        })

        # 處理特殊動作
        if action == PlayerAction.COMPLETE_ACHIEVEMENT:
            # 通知其他玩家成就解鎖
            self._broadcast_event(session_id, 'achievement_unlocked', {
                'username': username,
                'achievement': action_data
            })

        # 更新排行榜
        if action in [PlayerAction.BUY_STOCK, PlayerAction.SELL_STOCK]:
            self._update_leaderboard(session_id)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取會話資訊"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            'session_id': session.session_id,
            'name': session.name,
            'host_username': session.host_username,
            'mode': session.mode.value,
            'status': session.status.value,
            'max_players': session.max_players,
            'current_players': session.current_players,
            'start_time': session.start_time.isoformat(),
            'settings': session.settings,
            'shared_market': session.shared_market,
            'leaderboard': session.leaderboard
        }

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """獲取活躍會話列表"""
        active_sessions = []
        for session_id, session in self.sessions.items():
            if session.status in [SessionStatus.WAITING, SessionStatus.ACTIVE]:
                active_sessions.append(self.get_session_info(session_id))

        return active_sessions

    def get_player_sessions(self, username: str) -> List[str]:
        """獲取玩家參與的會話"""
        return list(self.active_connections.get(username, set()))

    def _broadcast_event(self, session_id: str, event_type: str, event_data: Dict[str, Any]):
        """廣播事件給會話中的所有玩家"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        # 在實際實現中，這裡會通過WebSocket或其他即時通信方式廣播
        # 目前先記錄事件
        logging.info(f"廣播事件 {event_type} 給會話 {session_id} 的玩家: {session.current_players}")

    def _broadcast_market_update(self, session_id: str, market_data: Dict[str, float]):
        """廣播市場更新"""
        self._broadcast_event(session_id, 'market_update', {'prices': market_data})

    def create_tournament(self, name: str, description: str, start_time: datetime,
                         end_time: datetime, prize_pool: float, rules: Dict[str, Any]) -> str:
        """
        建立競賽活動

        Args:
            name: 競賽名稱
            description: 描述
            start_time: 開始時間
            end_time: 結束時間
            prize_pool: 獎池
            rules: 競賽規則

        Returns:
            競賽ID
        """
        tournament_id = f"tournament_{int(time.time())}_{random.randint(1000, 9999)}"

        tournament = Tournament(
            tournament_id=tournament_id,
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            prize_pool=prize_pool,
            participants=[],
            rules=rules,
            status='upcoming',
            leaderboard=[]
        )

        self.tournaments[tournament_id] = tournament
        logging.info(f"建立競賽: {tournament_id}")
        return tournament_id

    def join_tournament(self, username: str, tournament_id: str) -> bool:
        """
        加入競賽

        Args:
            username: 用戶名
            tournament_id: 競賽ID

        Returns:
            是否成功加入
        """
        if tournament_id not in self.tournaments:
            return False

        tournament = self.tournaments[tournament_id]

        if username in tournament.participants:
            return False

        if datetime.now() >= tournament.start_time:
            return False  # 競賽已開始

        tournament.participants.append(username)
        logging.info(f"玩家 {username} 加入競賽 {tournament_id}")
        return True

    def get_tournament_info(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """獲取競賽資訊"""
        if tournament_id not in self.tournaments:
            return None

        tournament = self.tournaments[tournament_id]
        return {
            'tournament_id': tournament.tournament_id,
            'name': tournament.name,
            'description': tournament.description,
            'start_time': tournament.start_time.isoformat(),
            'end_time': tournament.end_time.isoformat(),
            'prize_pool': tournament.prize_pool,
            'participants': tournament.participants,
            'rules': tournament.rules,
            'status': tournament.status,
            'leaderboard': tournament.leaderboard
        }

    def get_active_tournaments(self) -> List[Dict[str, Any]]:
        """獲取活躍競賽列表"""
        now = datetime.now()
        active_tournaments = []

        for tournament_id, tournament in self.tournaments.items():
            if tournament.start_time <= now <= tournament.end_time:
                active_tournaments.append(self.get_tournament_info(tournament_id))

        return active_tournaments

    def update_tournament_leaderboard(self, tournament_id: str):
        """更新競賽排行榜"""
        if tournament_id not in self.tournaments:
            return

        tournament = self.tournaments[tournament_id]

        leaderboard = []
        for username in tournament.participants:
            # 根據競賽規則計算分數
            score = self._calculate_tournament_score(username, tournament.rules)
            leaderboard.append({
                'username': username,
                'score': score,
                'rank': 0
            })

        # 排序排行榜
        leaderboard.sort(key=lambda x: x['score'], reverse=True)

        # 更新排名
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1

        tournament.leaderboard = leaderboard

    def _calculate_tournament_score(self, username: str, rules: Dict[str, Any]) -> float:
        """計算競賽分數"""
        # 載入玩家遊戲資料
        game_data = self.data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            return 0.0

        score = 0.0

        # 根據規則計算分數
        if rules.get('score_net_worth', True):
            # 淨資產分數
            holdings = game_data.stocks if hasattr(game_data, 'stocks') else {}
            holdings_formatted = {}
            for symbol, stock_data in holdings.items():
                if stock_data.get('owned', 0) > 0:
                    holdings_formatted[symbol] = {
                        'qty': stock_data['owned'],
                        'avg_cost': stock_data.get('total_cost', 0) / stock_data['owned'] if stock_data['owned'] > 0 else 0
                    }

            prices = self.stock_manager.sync_prices_from_database()
            portfolio_value = self.stock_manager.calculate_portfolio_value(holdings_formatted, prices)
            score += game_data.cash + portfolio_value

        if rules.get('score_achievements', False):
            # 成就分數
            achievements_data = self.data_manager.achievement_manager.get_user_achievements(username)
            score += achievements_data.get('total_points', 0) * rules.get('achievement_multiplier', 1.0)

        return score
