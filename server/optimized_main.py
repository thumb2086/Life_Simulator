"""
Life Simulator Server - 統一遊戲平台服務器
支援桌面和Web雙平台遊戲體驗，提供完整的遊戲功能API
"""

# =============================================================================
# 標準庫匯入
# =============================================================================
import os
import sys
import random
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# =============================================================================
# 第三方庫匯入
# =============================================================================
from fastapi import FastAPI, HTTPException, Header, Query, Depends
from pydantic import BaseModel

# =============================================================================
# 專案模組匯入
# =============================================================================
# 確保可以匯入 modules/ 內的檔案
MODULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'modules')
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

from unified_data_manager import UnifiedDataManager
from unified_stock_manager import UnifiedStockManager
from unified_achievement_manager import UnifiedAchievementManager
from multiplayer_manager import MultiplayerManager
from market_news_events import MarketNewsEventManager
from social_features import SocialFeaturesManager
from ai_investment_advisor import AIInvestmentAdvisor
from seasonal_events import SeasonalEventsManager
from mini_games import MiniGamesManager

# =============================================================================
# 常數定義
# =============================================================================
DEFAULT_DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
DEFAULT_API_KEY = os.getenv("API_KEY", "dev-local-key")

# 股票初始化資料
STOCK_SEED_DATA = [
    ("TSMC", 100.0), ("HONHAI", 80.0), ("MTK", 120.0),
    ("MINING", 60.0), ("FARM", 50.0), ("FOREST", 55.0),
    ("RETAIL", 70.0), ("RESTAURANT", 65.0), ("TRAVEL", 75.0),
    ("BTC", 1000000.0)
]

# =============================================================================
# FastAPI 應用初始化
# =============================================================================
app = FastAPI(
    title="Life Simulator Server",
    description="統一遊戲平台服務器，支援桌面和Web雙平台遊戲體驗",
    version="2.0.0"
)

# =============================================================================
# 服務器組件初始化
# =============================================================================
# 統一資料管理器
data_manager = UnifiedDataManager(db_path=DEFAULT_DB_PATH)
# 統一股票管理器
stock_manager = UnifiedStockManager(db_path=DEFAULT_DB_PATH)
# 統一成就管理器
achievement_manager = UnifiedAchievementManager(db_path=DEFAULT_DB_PATH)
# 多人遊戲管理器
multiplayer_manager = MultiplayerManager(data_manager, stock_manager)
# 市場新聞事件管理器
news_events_manager = MarketNewsEventManager(stock_manager, db_path=DEFAULT_DB_PATH)
# 社交功能管理器
social_manager = SocialFeaturesManager(data_manager, db_path=DEFAULT_DB_PATH)
# AI投資顧問
ai_advisor = AIInvestmentAdvisor(stock_manager)
# 季節性活動管理器
seasonal_manager = SeasonalEventsManager(data_manager, db_path=DEFAULT_DB_PATH)
# 迷你遊戲管理器
mini_games_manager = MiniGamesManager(data_manager, db_path=DEFAULT_DB_PATH)

# =============================================================================
# 工具函數
# =============================================================================
def get_database_connection() -> sqlite3.Connection:
    """獲取資料庫連接"""
    return sqlite3.connect(DEFAULT_DB_PATH)


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """驗證API金鑰"""
    if x_api_key != DEFAULT_API_KEY:
        raise HTTPException(status_code=401, detail="無效的API金鑰")


def get_username_by_token(token: str) -> str:
    """通過token獲取用戶名"""
    username = TOKENS.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="無效的token")
    return username


def ensure_user_exists(conn: sqlite3.Connection, username: str) -> None:
    """確保用戶存在於資料庫中"""
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", (username,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users(username, cash, days) VALUES (?, ?, ?)",
                   (username, 100000.0, 0))
        conn.commit()


def get_stock_prices(conn: sqlite3.Connection,
                    symbols: Optional[List[str]] = None) -> Dict[str, float]:
    """獲取股票價格"""
    cur = conn.cursor()
    if symbols:
        qmarks = ",".join(["?"] * len(symbols))
        cur.execute(f"SELECT symbol, price FROM stocks WHERE symbol IN ({qmarks})", symbols)
    else:
        cur.execute("SELECT symbol, price FROM stocks")
    return {row[0]: float(row[1]) for row in cur.fetchall()}


def update_price_with_random_walk(price: float, volatility: float = 0.03) -> float:
    """使用隨機漫步更新價格"""
    drift = random.uniform(-volatility, volatility)
    new_price = max(0.01, price * (1.0 + drift))
    return round(new_price, 2)


# =============================================================================
# 資料庫初始化
# =============================================================================
def initialize_database() -> None:
    """初始化資料庫結構"""
    conn = get_database_connection()
    cur = conn.cursor()

    # 排行榜表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            username TEXT PRIMARY KEY,
            asset REAL NOT NULL,
            days INTEGER NOT NULL
        )
    """)

    # 賭場表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS casino (
            username TEXT PRIMARY KEY,
            casino_win INTEGER NOT NULL
        )
    """)

    # 用戶表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            cash REAL NOT NULL DEFAULT 100000,
            days INTEGER NOT NULL DEFAULT 0
        )
    """)

    # 投資組合表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            username TEXT NOT NULL,
            symbol TEXT NOT NULL,
            qty REAL NOT NULL,
            avg_cost REAL NOT NULL,
            PRIMARY KEY (username, symbol)
        )
    """)

    # 股票表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            symbol TEXT PRIMARY KEY,
            price REAL NOT NULL
        )
    """)

    # 初始化股票資料
    cur.execute("SELECT COUNT(*) FROM stocks")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO stocks(symbol, price) VALUES(?, ?)", STOCK_SEED_DATA)

    conn.commit()
    conn.close()


# 初始化資料庫
initialize_database()

# =============================================================================
# 記憶體存儲
# =============================================================================
TOKENS: Dict[str, str] = {}


# =============================================================================
# Pydantic 模型
# =============================================================================
class LeaderboardSubmit(BaseModel):
    username: str
    asset: float
    days: int


class CasinoSubmit(BaseModel):
    username: str
    win: int


class LoginPayload(BaseModel):
    username: str


class TradePayload(BaseModel):
    token: str
    symbol: str
    qty: float


class AdvancePayload(BaseModel):
    token: str


class GameDataPayload(BaseModel):
    game_data: Dict[str, Any]
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'


class SaveLoadPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = None


class MigratePayload(BaseModel):
    from_username: str
    from_platform: str
    from_save_name: str
    to_username: str
    to_platform: str
    to_save_name: str


class TradePayload(BaseModel):
    username: str
    symbol: str
    qty: float
    action: str  # 'buy' 或 'sell'


class AdvancedTradePayload(BaseModel):
    username: str
    symbol: str
    qty: float
    action: str
    price: Optional[float] = None  # 如果不提供則使用當前價格


class PortfolioPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = None


class AchievementCheckPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'


class AchievementExportPayload(BaseModel):
    username: str


class MultiplayerSessionPayload(BaseModel):
    host_username: str
    name: str
    mode: str = 'multiplayer'
    max_players: int = 8
    settings: Optional[Dict[str, Any]] = None


class JoinSessionPayload(BaseModel):
    username: str
    session_id: str


class TournamentPayload(BaseModel):
    name: str
    description: str
    start_time: str  # ISO format
    end_time: str    # ISO format
    prize_pool: float
    rules: Optional[Dict[str, Any]] = None


class JoinTournamentPayload(BaseModel):
    username: str
    tournament_id: str


class NewsGenerationPayload(BaseModel):
    category: Optional[str] = None  # economic, technological, political, natural, corporate, global
    impact: Optional[str] = None    # low, medium, high, critical


class EventGenerationPayload(BaseModel):
    event_type: Optional[str] = None  # market_crash, bull_market, industry_boom, etc.
    severity: Optional[str] = None     # low, medium, high, critical


class FriendRequestPayload(BaseModel):
    from_username: str
    to_username: str
    message: Optional[str] = ""


class FriendResponsePayload(BaseModel):
    request_id: str
    username: str
    accept: bool


class GuildCreationPayload(BaseModel):
    leader_username: str
    name: str
    description: Optional[str] = ""
    max_members: Optional[int] = 50


class GuildJoinPayload(BaseModel):
    username: str
    guild_id: str


class MessagePayload(BaseModel):
    from_username: str
    to_username: str
    content: str
    message_type: Optional[str] = "friend"


class LeaderboardCreationPayload(BaseModel):
    name: str
    type: str  # wealth, achievements, trading, social
    period: Optional[str] = "all_time"


class PortfolioAnalysisPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'


class InvestmentRecommendationPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'


class EventProgressPayload(BaseModel):
    username: str
    event_id: str
    progress_data: Dict[str, Any]


class ChallengeStartPayload(BaseModel):
    username: str
    challenge_id: str


class SideHustlePayload(BaseModel):
    username: str
    hustle_id: str


class CasinoGamePayload(BaseModel):
    username: str
    bet_amount: float
    game_type: str  # slots, blackjack, roulette, dice, baccarat


class BlackjackActionPayload(BaseModel):
    username: str
    bet_amount: float
    action: str  # hit, stand, double, surrender


class TriviaAnswerPayload(BaseModel):
    username: str
    question_id: str
    answer: int  # 0-3
