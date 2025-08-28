from fastapi import FastAPI, Header, HTTPException, Query, Depends
from pydantic import BaseModel
import os
import sqlite3
from typing import Optional, List, Dict, Any
import secrets
import random
import sys

# 整合統一成就管理器
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))
from unified_data_manager import UnifiedDataManager
from unified_stock_manager import UnifiedStockManager
from unified_achievement_manager import UnifiedAchievementManager
from multiplayer_manager import MultiplayerManager
from market_news_events import MarketNewsEventManager
from social_features import SocialFeaturesManager
from ai_investment_advisor import AIInvestmentAdvisor
from seasonal_events import SeasonalEventsManager
from mini_games import MiniGamesManager

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
API_KEY_EXPECTED = os.getenv("API_KEY", "dev-local-key")

app = FastAPI(title="Life_Simulator Server", version="1.0.0")

# 初始化統一資料管理器
data_manager = UnifiedDataManager(db_path=DB_PATH)
# 初始化統一股票管理器
stock_manager = UnifiedStockManager(db_path=DB_PATH)
# 初始化統一成就管理器
achievement_manager = UnifiedAchievementManager(db_path=DB_PATH)
# 初始化多人遊戲管理器
multiplayer_manager = MultiplayerManager(data_manager, stock_manager)
# 初始化市場新聞事件管理器
news_events_manager = MarketNewsEventManager(stock_manager, db_path=DB_PATH)
# 初始化社交功能管理器
social_manager = SocialFeaturesManager(data_manager, db_path=DB_PATH)
# 初始化AI投資顧問
ai_advisor = AIInvestmentAdvisor(stock_manager)
# 初始化季節性活動管理器
seasonal_manager = SeasonalEventsManager(data_manager, db_path=DB_PATH)
# 初始化迷你遊戲管理器
mini_games_manager = MiniGamesManager(data_manager, db_path=DB_PATH)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leaderboard (
            username TEXT PRIMARY KEY,
            asset REAL NOT NULL,
            days INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS casino (
            username TEXT PRIMARY KEY,
            casino_win INTEGER NOT NULL
        )
        """
    )
    # Users/state
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            cash REAL NOT NULL DEFAULT 100000,
            days INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    # Portfolios
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolios (
            username TEXT NOT NULL,
            symbol TEXT NOT NULL,
            qty REAL NOT NULL,
            avg_cost REAL NOT NULL,
            PRIMARY KEY (username, symbol)
        )
        """
    )
    # Stocks universe
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            symbol TEXT PRIMARY KEY,
            price REAL NOT NULL
        )
        """
    )
    # Seed some stocks if empty
    cur.execute("SELECT COUNT(*) FROM stocks")
    if (cur.fetchone()[0] or 0) == 0:
        # Match client-side game symbols so prices can be unified across server and client
        symbols = [
            ("TSMC", 100.0), ("HONHAI", 80.0), ("MTK", 120.0),
            ("MINING", 60.0), ("FARM", 50.0), ("FOREST", 55.0),
            ("RETAIL", 70.0), ("RESTAURANT", 65.0), ("TRAVEL", 75.0),
            ("BTC", 1000000.0)
        ]
        cur.executemany("INSERT INTO stocks(symbol, price) VALUES(?, ?)", symbols)
    conn.commit()
    conn.close()


init_db()


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


def require_api_key(x_api_key: Optional[str]):
    if x_api_key != API_KEY_EXPECTED:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Simple token store (in-memory). For production, use proper sessions/JWT.
TOKENS: Dict[str, str] = {}

def get_username_by_token(token: str) -> str:
    username = TOKENS.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username

def ensure_user(conn, username: str):
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", (username,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users(username, cash, days) VALUES (?, ?, ?)", (username, 100000.0, 0))
        conn.commit()

def get_prices(conn, symbols: Optional[List[str]] = None) -> Dict[str, float]:
    cur = conn.cursor()
    if symbols:
        qmarks = ",".join(["?"] * len(symbols))
        cur.execute(f"SELECT symbol, price FROM stocks WHERE symbol IN ({qmarks})", symbols)
    else:
        cur.execute("SELECT symbol, price FROM stocks")
    return {row[0]: float(row[1]) for row in cur.fetchall()}

def update_price_random_walk(price: float) -> float:
    # simple daily movement +/- up to ~3%
    drift = random.uniform(-0.03, 0.03)
    newp = max(0.01, price * (1.0 + drift))
    return round(newp, 2)


@app.post("/leaderboard/submit")
def leaderboard_submit(payload: LeaderboardSubmit, x_api_key: Optional[str] = Header(default=None)):
    require_api_key(x_api_key)
    conn = get_db()
    cur = conn.cursor()
    # Upsert latest record per user
    cur.execute(
        """
        INSERT INTO leaderboard (username, asset, days)
        VALUES (?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET asset=excluded.asset, days=excluded.days
        """,
        (payload.username, payload.asset, payload.days),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/leaderboard/top")
def leaderboard_top(username: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    if username:
        cur.execute("SELECT username, asset, days FROM leaderboard WHERE username=?", (username,))
    else:
        cur.execute("SELECT username, asset, days FROM leaderboard ORDER BY asset DESC, days ASC LIMIT 100")
    rows = cur.fetchall()
    conn.close()
    data = [{"username": r["username"], "asset": r["asset"], "days": r["days"]} for r in rows]
    return {"records": data}


@app.post("/casino/submit")
def casino_submit(payload: CasinoSubmit, x_api_key: Optional[str] = Header(default=None)):
    require_api_key(x_api_key)
    conn = get_db()
    cur = conn.cursor()
    # accumulate casino_win per user
    cur.execute("SELECT casino_win FROM casino WHERE username=?", (payload.username,))
    row = cur.fetchone()
    if row is None:
        total = max(0, int(payload.win))
        cur.execute("INSERT INTO casino (username, casino_win) VALUES (?, ?)", (payload.username, total))
    else:
        prev = int(row["casino_win"]) if row["casino_win"] is not None else 0
        total = prev + max(0, int(payload.win))
        cur.execute("UPDATE casino SET casino_win=? WHERE username=?", (total, payload.username))
    conn.commit()
    conn.close()
    return {"ok": True, "total": total}


@app.get("/casino/top")
def casino_top(username: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    if username:
        cur.execute("SELECT username, casino_win FROM casino WHERE username=?", (username,))
    else:
        cur.execute("SELECT username, casino_win FROM casino ORDER BY casino_win DESC LIMIT 100")
    rows = cur.fetchall()
    conn.close()
    data = [{"username": r["username"], "casino_win": r["casino_win"]} for r in rows]
    return {"records": data}

@app.get("/")
def root() -> Dict[str, Any]:
    return {"ok": True, "service": "Life_Simulator Server"}

@app.get("/health")
def health() -> Dict[str, Any]:
    try:
        # quick db check
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"unhealthy: {e}")

@app.get("/version")
def version() -> Dict[str, Any]:
    return {"version": app.version}


# --- Web Game APIs ---
@app.post("/auth/login")
def auth_login(payload: LoginPayload):
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="username required")
    token = secrets.token_hex(16)
    TOKENS[token] = username
    # ensure user row exists
    conn = get_db()
    ensure_user(conn, username)
    conn.close()
    return {"token": token, "username": username}


@app.get("/game/state")
def game_state(token: str):
    username = get_username_by_token(token)
    conn = get_db()
    cur = conn.cursor()
    ensure_user(conn, username)
    # user
    cur.execute("SELECT cash, days FROM users WHERE username= ?", (username,))
    row = cur.fetchone()
    cash = float(row["cash"]) if row else 0.0
    days = int(row["days"]) if row else 0
    # portfolio
    cur.execute("SELECT symbol, qty, avg_cost FROM portfolios WHERE username= ?", (username,))
    holdings = [{"symbol": r["symbol"], "qty": float(r["qty"]), "avg_cost": float(r["avg_cost"])} for r in cur.fetchall()]
    # prices
    prices = get_prices(conn)
    # net worth: cash + sum(qty * price)
    portfolio_value = 0.0
    for h in holdings:
        sym = h["symbol"]
        if sym in prices:
            portfolio_value += h["qty"] * float(prices[sym])
    net_worth = cash + portfolio_value
    conn.close()
    return {"username": username, "cash": cash, "days": days, "holdings": holdings, "prices": prices, "portfolio_value": round(portfolio_value, 2), "net_worth": round(net_worth, 2)}


@app.get("/stocks/list")
def stocks_list() -> Dict[str, Any]:
    conn = get_db()
    prices = get_prices(conn)
    conn.close()
    return {"prices": prices}


@app.post("/stocks/tick")
def stocks_tick(x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """
    Advance all stock prices on the server using a random walk.
    Protected by X-API-Key so clients can coordinate a unified market clock.
    """
    require_api_key(x_api_key)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT symbol, price FROM stocks")
    rows = cur.fetchall()
    updated: Dict[str, float] = {}
    for r in rows:
        sym = r["symbol"]
        newp = update_price_random_walk(float(r["price"]))
        cur.execute("UPDATE stocks SET price=? WHERE symbol=?", (newp, sym))
        updated[sym] = newp
    conn.commit()
    conn.close()
    return {"ok": True, "updated": updated}


@app.post("/stocks/buy")
def stocks_buy(payload: TradePayload):
    username = get_username_by_token(payload.token)
    symbol = payload.symbol.upper()
    qty = float(payload.qty)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be > 0")
    conn = get_db()
    cur = conn.cursor()
    ensure_user(conn, username)
    prices = get_prices(conn, [symbol])
    if symbol not in prices:
        conn.close()
        raise HTTPException(status_code=404, detail="symbol not found")
    price = prices[symbol]
    cost = price * qty
    cur.execute("SELECT cash FROM users WHERE username=?", (username,))
    cash = float(cur.fetchone()["cash"])
    if cash < cost:
        conn.close()
        raise HTTPException(status_code=400, detail="insufficient cash")
    # update cash
    new_cash = cash - cost
    cur.execute("UPDATE users SET cash=? WHERE username=?", (new_cash, username))
    # update holding (avg cost)
    cur.execute("SELECT qty, avg_cost FROM portfolios WHERE username=? AND symbol=?", (username, symbol))
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO portfolios(username, symbol, qty, avg_cost) VALUES(?,?,?,?)", (username, symbol, qty, price))
    else:
        prev_qty = float(row["qty"])
        prev_avg = float(row["avg_cost"])
        new_qty = prev_qty + qty
        new_avg = (prev_qty * prev_avg + qty * price) / max(1e-9, new_qty)
        cur.execute("UPDATE portfolios SET qty=?, avg_cost=? WHERE username=? AND symbol=?", (new_qty, new_avg, username, symbol))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/stocks/sell")
def stocks_sell(payload: TradePayload):
    username = get_username_by_token(payload.token)
    symbol = payload.symbol.upper()
    qty = float(payload.qty)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be > 0")
    conn = get_db()
    cur = conn.cursor()
    ensure_user(conn, username)
    prices = get_prices(conn, [symbol])
    if symbol not in prices:
        conn.close()
        raise HTTPException(status_code=404, detail="symbol not found")
    price = prices[symbol]
    cur.execute("SELECT qty, avg_cost FROM portfolios WHERE username=? AND symbol=?", (username, symbol))
    row = cur.fetchone()
    if row is None or float(row["qty"]) < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="insufficient shares")
    prev_qty = float(row["qty"])
    new_qty = prev_qty - qty
    proceeds = price * qty
    # update holding
    if new_qty <= 0:
        cur.execute("DELETE FROM portfolios WHERE username=? AND symbol=?", (username, symbol))
    else:
        cur.execute("UPDATE portfolios SET qty=? WHERE username=? AND symbol=?", (new_qty, username, symbol))
    # update cash
    cur.execute("SELECT cash FROM users WHERE username=?", (username,))
    cash = float(cur.fetchone()["cash"])
    cur.execute("UPDATE users SET cash=? WHERE username=?", (cash + proceeds, username))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/tick/advance")
def tick_advance(payload: AdvancePayload):
    username = get_username_by_token(payload.token)
    conn = get_db()
    cur = conn.cursor()
    ensure_user(conn, username)
    # advance user day
    cur.execute("SELECT days FROM users WHERE username=?", (username,))
    days = int(cur.fetchone()["days"]) + 1
    cur.execute("UPDATE users SET days=? WHERE username=?", (days, username))
    # update prices (random walk)
    cur.execute("SELECT symbol, price FROM stocks")
    rows = cur.fetchall()
    for r in rows:
        newp = update_price_random_walk(float(r["price"]))
        cur.execute("UPDATE stocks SET price=? WHERE symbol=?", (newp, r["symbol"]))
    conn.commit()
    conn.close()
    return {"ok": True, "days": days}


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


# --- 統一遊戲資料管理 API ---


# --- 統一遊戲資料管理 API ---

@app.post("/game/save")
def save_game_data(payload: GameDataPayload):
    """
    儲存遊戲資料到統一系統
    """
    try:
        # 從 payload 建立 GameData 對象
        from game_data import GameData
        game_data = GameData()
        game_data.__dict__.update(payload.game_data)

        success = data_manager.save_game_data(
            game_data,
            payload.username,
            payload.save_name,
            payload.platform
        )

        if success:
            return {"ok": True, "message": "遊戲資料儲存成功"}
        else:
            raise HTTPException(status_code=500, detail="儲存失敗")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"儲存遊戲資料失敗: {str(e)}")


@app.post("/game/load")
def load_game_data(payload: SaveLoadPayload):
    """
    從統一系統載入遊戲資料
    """
    try:
        game_data = data_manager.load_game_data(
            payload.username,
            payload.save_name,
            payload.platform
        )

        if game_data:
            return {"ok": True, "game_data": game_data.__dict__}
        else:
            raise HTTPException(status_code=404, detail="找不到存檔")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"載入遊戲資料失敗: {str(e)}")


@app.post("/game/migrate")
def migrate_save(payload: MigratePayload):
    """
    跨平台存檔遷移
    """
    try:
        success = data_manager.migrate_save(
            payload.from_username,
            payload.from_platform,
            payload.from_save_name,
            payload.to_username,
            payload.to_platform,
            payload.to_save_name
        )

        if success:
            return {"ok": True, "message": "存檔遷移成功"}
        else:
            raise HTTPException(status_code=500, detail="遷移失敗")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"存檔遷移失敗: {str(e)}")


@app.get("/game/saves")
def list_saves(username: Optional[str] = None, platform: Optional[str] = None):
    """
    列出存檔列表
    """
    try:
        saves = data_manager.list_saves(username, platform)
        return {"ok": True, "saves": saves}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出存檔失敗: {str(e)}")


@app.post("/game/export")
def export_save(username: str, save_name: str = 'default', output_path: str = None, platform: str = None):
    """
    將存檔匯出為JSON檔案
    """
    try:
        if not output_path:
            output_path = f"{username}_{save_name}_export.json"

        success = data_manager.export_to_json(username, save_name, output_path, platform)

        if success:
            return {"ok": True, "message": f"存檔已匯出至 {output_path}"}
        else:
            raise HTTPException(status_code=500, detail="匯出失敗")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出存檔失敗: {str(e)}")


@app.post("/game/import")
def import_save(json_path: str, username: str, save_name: str = 'default', platform: str = 'web'):
    """
    從JSON檔案匯入存檔
    """
    try:
        success = data_manager.import_from_json(json_path, username, save_name, platform)

        if success:
            return {"ok": True, "message": "存檔匯入成功"}
        else:
            raise HTTPException(status_code=500, detail="匯入失敗")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯入存檔失敗: {str(e)}")


# --- 統一股票管理 API ---

@app.get("/stocks/overview")
def get_market_overview():
    """
    獲取市場概覽
    """
    try:
        prices = stock_manager.sync_prices_from_database()
        overview = stock_manager.get_market_overview(prices)
        return {"ok": True, "overview": overview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取市場概覽失敗: {str(e)}")


@app.get("/stocks/industries")
def get_industries():
    """
    獲取所有行業列表
    """
    try:
        industries = stock_manager.get_all_industries()
        return {"ok": True, "industries": industries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取行業列表失敗: {str(e)}")


@app.get("/stocks/industry/{industry}")
def get_industry_stocks(industry: str):
    """
    獲取特定行業的股票
    """
    try:
        stocks = stock_manager.get_industry_stocks(industry)
        prices = stock_manager.sync_prices_from_database()
        industry_prices = {stock: prices.get(stock, 0) for stock in stocks}
        return {"ok": True, "stocks": stocks, "prices": industry_prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取行業股票失敗: {str(e)}")


@app.post("/stocks/trade/advanced")
def advanced_trade(payload: AdvancedTradePayload):
    """
    高級交易操作（支援複雜的持倉管理）
    """
    try:
        # 載入用戶遊戲資料
        game_data = data_manager.load_game_data(payload.username, 'default', 'web')
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        # 獲取當前價格
        prices = stock_manager.sync_prices_from_database()
        if payload.symbol not in prices:
            raise HTTPException(status_code=404, detail="股票代碼不存在")

        price = payload.price or prices[payload.symbol]

        # 處理交易
        if payload.action == 'buy':
            success, message, new_holdings = stock_manager.process_buy_order(
                payload.symbol, payload.qty, price, game_data.cash,
                game_data.stocks if hasattr(game_data, 'stocks') else {}
            )

            if success:
                # 更新現金和持倉
                game_data.cash -= payload.qty * price
                if not hasattr(game_data, 'stocks'):
                    game_data.stocks = {}
                game_data.stocks.update(new_holdings)

        elif payload.action == 'sell':
            holdings = game_data.stocks if hasattr(game_data, 'stocks') else {}
            if payload.symbol not in holdings:
                raise HTTPException(status_code=400, detail="沒有持有該股票")

            current_qty = holdings[payload.symbol]['owned']
            if payload.qty > current_qty:
                raise HTTPException(status_code=400, detail=".0f"".0f"f"持有股票不足，需要 {payload.qty:.0f} 股，目前持有 {current_qty:.0f} 股")

            proceeds = payload.qty * price
            game_data.cash += proceeds

            if payload.qty >= current_qty:
                del game_data.stocks[payload.symbol]
            else:
                game_data.stocks[payload.symbol]['owned'] -= payload.qty

            success, message = True, ".2f"f"成功賣出 {payload.qty:.0f} 股，獲得 ${proceeds:.2f}"

        else:
            raise HTTPException(status_code=400, detail="無效的交易動作")

        if success:
            # 儲存更新後的遊戲資料
            data_manager.save_game_data(game_data, payload.username, 'default', 'web')
            return {"ok": True, "message": message, "cash": game_data.cash}
        else:
            raise HTTPException(status_code=400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"交易失敗: {str(e)}")


@app.get("/portfolio/analysis")
def get_portfolio_analysis(username: str):
    """
    獲取投資組合分析
    """
    try:
        game_data = data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        prices = stock_manager.sync_prices_from_database()
        holdings = game_data.stocks if hasattr(game_data, 'stocks') else {}

        # 轉換持倉格式
        holdings_formatted = {}
        for symbol, stock_data in holdings.items():
            if stock_data.get('owned', 0) > 0:
                holdings_formatted[symbol] = {
                    'qty': stock_data['owned'],
                    'avg_cost': stock_data.get('total_cost', 0) / stock_data['owned'] if stock_data['owned'] > 0 else 0
                }

        portfolio_value = stock_manager.calculate_portfolio_value(holdings_formatted, prices)
        total_gain, total_loss = stock_manager.calculate_total_gain_loss(holdings_formatted, prices)

        return {
            "ok": True,
            "portfolio_value": portfolio_value,
            "total_gain": total_gain,
            "total_loss": total_loss,
            "net_worth": game_data.cash + portfolio_value,
            "holdings": holdings_formatted
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取投資組合分析失敗: {str(e)}")


@app.get("/stocks/recommendations")
def get_investment_recommendations(username: str):
    """
    獲取投資建議
    """
    try:
        game_data = data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        prices = stock_manager.sync_prices_from_database()
        holdings = game_data.stocks if hasattr(game_data, 'stocks') else {}

        # 轉換持倉格式
        holdings_formatted = {}
        for symbol, stock_data in holdings.items():
            if stock_data.get('owned', 0) > 0:
                holdings_formatted[symbol] = {
                    'qty': stock_data['owned'],
                    'avg_cost': stock_data.get('total_cost', 0) / stock_data['owned'] if stock_data['owned'] > 0 else 0
                }

        recommendations = stock_manager.get_recommendations(holdings_formatted, prices, game_data.cash)

        return {"ok": True, "recommendations": recommendations}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取投資建議失敗: {str(e)}")


@app.post("/stocks/tick/advanced")
def advanced_price_tick(x_api_key: Optional[str] = Header(default=None)):
    """
    高級價格更新（支援行業周期和市場波動）
    """
    require_api_key(x_api_key)

    try:
        # 獲取當前價格
        current_prices = stock_manager.sync_prices_from_database()

        # 使用統一股票管理器更新價格
        updated_prices = stock_manager.update_prices_random_walk(current_prices)

        # 同步回資料庫
        stock_manager.sync_prices_to_database(updated_prices)

        return {"ok": True, "updated_prices": updated_prices}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"價格更新失敗: {str(e)}")


# --- 統一成就管理 API ---

@app.post("/achievements/check")
def check_achievements(payload: AchievementCheckPayload):
    """
    檢查並更新用戶成就
    """
    try:
        game_data = data_manager.load_game_data(payload.username, payload.save_name, payload.platform)
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        newly_unlocked = achievement_manager.check_achievements(game_data, payload.username)

        return {
            "ok": True,
            "newly_unlocked": [{
                "key": a.key,
                "name": a.name,
                "description": a.description,
                "category": a.category,
                "points": a.points,
                "rarity": a.rarity
            } for a in newly_unlocked],
            "total_new": len(newly_unlocked)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查成就失敗: {str(e)}")


@app.get("/achievements/user/{username}")
def get_user_achievements(username: str):
    """
    獲取用戶成就統計
    """
    try:
        achievements_data = achievement_manager.get_user_achievements(username)
        return {"ok": True, "data": achievements_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取用戶成就失敗: {str(e)}")


@app.get("/achievements/leaderboard")
def get_achievement_leaderboard(limit: int = 100):
    """
    獲取成就排行榜
    """
    try:
        leaderboard = achievement_manager.get_achievement_leaderboard(limit)
        return {"ok": True, "leaderboard": leaderboard}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取排行榜失敗: {str(e)}")


@app.get("/achievements/categories")
def get_achievement_categories():
    """
    獲取成就分類列表
    """
    try:
        categories = achievement_manager.get_achievement_categories()
        return {"ok": True, "categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取成就分類失敗: {str(e)}")


@app.get("/achievements/category/{category}")
def get_achievements_by_category(category: str):
    """
    按分類獲取成就列表
    """
    try:
        achievements = achievement_manager.get_achievements_by_category(category)
        return {"ok": True, "achievements": achievements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取分類成就失敗: {str(e)}")


@app.get("/achievements/stats")
def get_achievement_stats():
    """
    獲取成就統計資料
    """
    try:
        stats = achievement_manager.get_achievement_stats()
        return {"ok": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取成就統計失敗: {str(e)}")


@app.post("/achievements/export")
def export_achievements(payload: AchievementExportPayload):
    """
    匯出用戶成就資料
    """
    try:
        achievements_json = achievement_manager.export_achievements(payload.username)
        return {"ok": True, "achievements_json": achievements_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出成就失敗: {str(e)}")


@app.post("/achievements/import")
def import_achievements(username: str, achievements_json: str):
    """
    匯入成就資料
    """
    try:
        achievement_manager.import_achievements(username, achievements_json)
        return {"ok": True, "message": "成就資料匯入成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯入成就失敗: {str(e)}")


# --- 多人遊戲管理 API ---

@app.post("/multiplayer/session/create")
def create_session(payload: MultiplayerSessionPayload):
    """
    建立多人遊戲會話
    """
    try:
        from multiplayer_manager import GameMode
        mode = GameMode(payload.mode) if payload.mode in ['solo', 'multiplayer', 'tournament', 'league'] else GameMode.MULTIPLAYER

        session_id = multiplayer_manager.create_session(
            host_username=payload.host_username,
            name=payload.name,
            mode=mode,
            max_players=payload.max_players,
            settings=payload.settings
        )

        return {"ok": True, "session_id": session_id, "message": "會話建立成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立會話失敗: {str(e)}")


@app.post("/multiplayer/session/join")
def join_session(payload: JoinSessionPayload):
    """
    加入多人遊戲會話
    """
    try:
        success = multiplayer_manager.join_session(payload.username, payload.session_id)

        if success:
            return {"ok": True, "message": "成功加入會話"}
        else:
            raise HTTPException(status_code=400, detail="無法加入會話")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加入會話失敗: {str(e)}")


@app.post("/multiplayer/session/leave")
def leave_session(payload: JoinSessionPayload):
    """
    離開多人遊戲會話
    """
    try:
        success = multiplayer_manager.leave_session(payload.username, payload.session_id)

        if success:
            return {"ok": True, "message": "成功離開會話"}
        else:
            raise HTTPException(status_code=400, detail="無法離開會話")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"離開會話失敗: {str(e)}")


@app.post("/multiplayer/session/start")
def start_session(session_id: str, host_username: str):
    """
    開始多人遊戲會話
    """
    try:
        success = multiplayer_manager.start_session(session_id, host_username)

        if success:
            return {"ok": True, "message": "會話已開始"}
        else:
            raise HTTPException(status_code=400, detail="無法開始會話")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"開始會話失敗: {str(e)}")


@app.post("/multiplayer/session/end")
def end_session(session_id: str, host_username: str):
    """
    結束多人遊戲會話
    """
    try:
        success = multiplayer_manager.end_session(session_id, host_username)

        if success:
            return {"ok": True, "message": "會話已結束"}
        else:
            raise HTTPException(status_code=400, detail="無法結束會話")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"結束會話失敗: {str(e)}")


@app.get("/multiplayer/sessions")
def get_active_sessions():
    """
    獲取活躍的多人遊戲會話
    """
    try:
        sessions = multiplayer_manager.get_active_sessions()
        return {"ok": True, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取會話列表失敗: {str(e)}")


@app.get("/multiplayer/session/{session_id}")
def get_session_info(session_id: str):
    """
    獲取會話詳細資訊
    """
    try:
        session_info = multiplayer_manager.get_session_info(session_id)

        if session_info:
            return {"ok": True, "session": session_info}
        else:
            raise HTTPException(status_code=404, detail="會話不存在")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取會話資訊失敗: {str(e)}")


@app.get("/multiplayer/player/{username}/sessions")
def get_player_sessions(username: str):
    """
    獲取玩家參與的會話
    """
    try:
        session_ids = multiplayer_manager.get_player_sessions(username)
        sessions = []

        for session_id in session_ids:
            session_info = multiplayer_manager.get_session_info(session_id)
            if session_info:
                sessions.append(session_info)

        return {"ok": True, "sessions": sessions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取玩家會話失敗: {str(e)}")


@app.post("/multiplayer/tournament/create")
def create_tournament(payload: TournamentPayload):
    """
    建立競賽活動
    """
    try:
        from datetime import datetime

        start_time = datetime.fromisoformat(payload.start_time)
        end_time = datetime.fromisoformat(payload.end_time)

        tournament_id = multiplayer_manager.create_tournament(
            name=payload.name,
            description=payload.description,
            start_time=start_time,
            end_time=end_time,
            prize_pool=payload.prize_pool,
            rules=payload.rules or {}
        )

        return {"ok": True, "tournament_id": tournament_id, "message": "競賽建立成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立競賽失敗: {str(e)}")


@app.post("/multiplayer/tournament/join")
def join_tournament(payload: JoinTournamentPayload):
    """
    加入競賽活動
    """
    try:
        success = multiplayer_manager.join_tournament(payload.username, payload.tournament_id)

        if success:
            return {"ok": True, "message": "成功加入競賽"}
        else:
            raise HTTPException(status_code=400, detail="無法加入競賽")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加入競賽失敗: {str(e)}")


@app.get("/multiplayer/tournaments")
def get_active_tournaments():
    """
    獲取活躍的競賽活動
    """
    try:
        tournaments = multiplayer_manager.get_active_tournaments()
        return {"ok": True, "tournaments": tournaments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取競賽列表失敗: {str(e)}")


@app.get("/multiplayer/tournament/{tournament_id}")
def get_tournament_info(tournament_id: str):
    """
    獲取競賽詳細資訊
    """
    try:
        tournament_info = multiplayer_manager.get_tournament_info(tournament_id)

        if tournament_info:
            return {"ok": True, "tournament": tournament_info}
        else:
            raise HTTPException(status_code=404, detail="競賽不存在")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取競賽資訊失敗: {str(e)}")


@app.post("/multiplayer/action/record")
def record_player_action(session_id: str, username: str, action: str, action_data: Dict[str, Any]):
    """
    記錄玩家動作
    """
    try:
        from multiplayer_manager import PlayerAction

        if action not in ['buy_stock', 'sell_stock', 'use_buff', 'complete_achievement', 'join_session', 'leave_session']:
            raise HTTPException(status_code=400, detail="無效的動作類型")

        action_enum = PlayerAction(action.upper())
        multiplayer_manager.record_player_action(session_id, username, action_enum, action_data)

        return {"ok": True, "message": "動作已記錄"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記錄動作失敗: {str(e)}")


@app.post("/multiplayer/tournament/update_leaderboard")
def update_tournament_leaderboard(tournament_id: str):
    """
    更新競賽排行榜
    """
    try:
        multiplayer_manager.update_tournament_leaderboard(tournament_id)
        return {"ok": True, "message": "排行榜已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新排行榜失敗: {str(e)}")


# --- 市場新聞和事件管理 API ---

@app.get("/news/active")
def get_active_news():
    """
    獲取活躍新聞
    """
    try:
        news_list = news_events_manager.get_active_news()
        return {"ok": True, "news": news_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取新聞失敗: {str(e)}")


@app.get("/events/active")
def get_active_events():
    """
    獲取活躍事件
    """
    try:
        events_list = news_events_manager.get_active_events()
        return {"ok": True, "events": events_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取事件失敗: {str(e)}")


@app.post("/news/generate")
def generate_news(payload: NewsGenerationPayload):
    """
    生成新聞（管理員功能）
    """
    try:
        from market_news_events import NewsCategory, NewsImpact

        # 轉換分類和影響
        category = None
        if payload.category:
            category_map = {
                'economic': NewsCategory.ECONOMIC,
                'technological': NewsCategory.TECHNOLOGICAL,
                'political': NewsCategory.POLITICAL,
                'natural': NewsCategory.NATURAL,
                'corporate': NewsCategory.CORPORATE,
                'global': NewsCategory.GLOBAL
            }
            category = category_map.get(payload.category)

        impact = None
        if payload.impact:
            impact_map = {
                'low': NewsImpact.LOW,
                'medium': NewsImpact.MEDIUM,
                'high': NewsImpact.HIGH,
                'critical': NewsImpact.CRITICAL
            }
            impact = impact_map.get(payload.impact)

        news = news_events_manager.generate_random_news(category, impact)

        return {
            "ok": True,
            "news": {
                'news_id': news.news_id,
                'title': news.title,
                'content': news.content,
                'category': news.category.value,
                'impact': news.impact.value,
                'affected_stocks': news.affected_stocks,
                'price_changes': news.price_changes,
                'created_at': news.created_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成新聞失敗: {str(e)}")


@app.post("/events/generate")
def generate_event(payload: EventGenerationPayload):
    """
    生成市場事件（管理員功能）
    """
    try:
        from market_news_events import EventType, NewsImpact

        # 轉換事件類型和嚴重程度
        event_type = None
        if payload.event_type:
            event_type_map = {
                'market_crash': EventType.MARKET_CRASH,
                'bull_market': EventType.BULL_MARKET,
                'industry_boom': EventType.INDUSTRY_BOOM,
                'regulatory_change': EventType.REGULATORY_CHANGE,
                'natural_disaster': EventType.NATURAL_DISASTER,
                'technological_breakthrough': EventType.TECHNOLOGICAL_BREAKTHROUGH,
                'merger_acquisition': EventType.MERGER_ACQUISITION,
                'dividend_announcement': EventType.DIVIDEND_ANNOUNCEMENT
            }
            event_type = event_type_map.get(payload.event_type)

        severity = None
        if payload.severity:
            severity_map = {
                'low': NewsImpact.LOW,
                'medium': NewsImpact.MEDIUM,
                'high': NewsImpact.HIGH,
                'critical': NewsImpact.CRITICAL
            }
            severity = severity_map.get(payload.severity)

        event = news_events_manager.generate_random_event(event_type, severity)

        return {
            "ok": True,
            "event": {
                'event_id': event.event_id,
                'type': event.type.value,
                'title': event.title,
                'description': event.description,
                'severity': event.severity.value,
                'affected_industries': event.affected_industries,
                'global_impact': event.global_impact,
                'created_at': event.created_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成事件失敗: {str(e)}")


@app.get("/market/sentiment")
def get_market_sentiment():
    """
    獲取市場情緒分析
    """
    try:
        sentiment = news_events_manager.get_market_sentiment()
        return {"ok": True, "sentiment": sentiment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取市場情緒失敗: {str(e)}")


@app.post("/news/auto-generate")
def trigger_auto_news_generation(x_api_key: Optional[str] = Header(default=None)):
    """
    觸發自動新聞生成（管理員功能）
    """
    require_api_key(x_api_key)

    try:
        # 生成隨機新聞
        news = news_events_manager.generate_random_news()

        return {
            "ok": True,
            "message": "自動新聞生成成功",
            "news": {
                'news_id': news.news_id,
                'title': news.title,
                'category': news.category.value,
                'impact': news.impact.value
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自動新聞生成失敗: {str(e)}")


@app.post("/events/auto-generate")
def trigger_auto_event_generation(x_api_key: Optional[str] = Header(default=None)):
    """
    觸發自動事件生成（管理員功能）
    """
    require_api_key(x_api_key)

    try:
        # 生成隨機事件
        event = news_events_manager.generate_random_event()

        return {
            "ok": True,
            "message": "自動事件生成成功",
            "event": {
                'event_id': event.event_id,
                'title': event.title,
                'type': event.type.value,
                'severity': event.severity.value
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自動事件生成失敗: {str(e)}")


@app.get("/news/categories")
def get_news_categories():
    """
    獲取新聞分類列表
    """
    try:
        from market_news_events import NewsCategory
        categories = [cat.value for cat in NewsCategory]
        return {"ok": True, "categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取新聞分類失敗: {str(e)}")


@app.get("/events/types")
def get_event_types():
    """
    獲取事件類型列表
    """
    try:
        from market_news_events import EventType
        event_types = [event.value for event in EventType]
        return {"ok": True, "event_types": event_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取事件類型失敗: {str(e)}")


@app.get("/market/impacts")
def get_impact_levels():
    """
    獲取影響程度列表
    """
    try:
        from market_news_events import NewsImpact
        impacts = [impact.value for impact in NewsImpact]
        return {"ok": True, "impacts": impacts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取影響程度失敗: {str(e)}")


# --- 社交功能管理 API ---

@app.post("/social/friends/request")
def send_friend_request(payload: FriendRequestPayload):
    """
    發送好友請求
    """
    try:
        request_id = social_manager.send_friend_request(
            payload.from_username,
            payload.to_username,
            payload.message
        )

        return {"ok": True, "request_id": request_id, "message": "好友請求已發送"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發送好友請求失敗: {str(e)}")


@app.post("/social/friends/respond")
def respond_friend_request(payload: FriendResponsePayload):
    """
    回應好友請求
    """
    try:
        success = social_manager.respond_friend_request(
            payload.request_id,
            payload.username,
            payload.accept
        )

        if success:
            action = "接受" if payload.accept else "拒絕"
            return {"ok": True, "message": f"已{action}好友請求"}
        else:
            raise HTTPException(status_code=400, detail="處理好友請求失敗")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回應好友請求失敗: {str(e)}")


@app.get("/social/friends/{username}")
def get_friends_list(username: str):
    """
    獲取好友列表
    """
    try:
        friends = social_manager.get_friends_list(username)
        return {"ok": True, "friends": friends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取好友列表失敗: {str(e)}")


@app.get("/social/friends/requests/{username}")
def get_pending_requests(username: str):
    """
    獲取待處理的好友請求
    """
    try:
        requests = social_manager.get_pending_requests(username)
        return {"ok": True, "requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取好友請求失敗: {str(e)}")


@app.post("/social/guilds/create")
def create_guild(payload: GuildCreationPayload):
    """
    建立公會
    """
    try:
        guild_id = social_manager.create_guild(
            payload.leader_username,
            payload.name,
            payload.description,
            payload.max_members
        )

        return {"ok": True, "guild_id": guild_id, "message": "公會建立成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立公會失敗: {str(e)}")


@app.post("/social/guilds/join")
def join_guild(payload: GuildJoinPayload):
    """
    加入公會
    """
    try:
        success = social_manager.join_guild(payload.username, payload.guild_id)

        if success:
            return {"ok": True, "message": "成功加入公會"}
        else:
            raise HTTPException(status_code=400, detail="無法加入公會")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加入公會失敗: {str(e)}")


@app.post("/social/guilds/leave")
def leave_guild(username: str, guild_id: str):
    """
    離開公會
    """
    try:
        success = social_manager.leave_guild(username, guild_id)

        if success:
            return {"ok": True, "message": "成功離開公會"}
        else:
            raise HTTPException(status_code=400, detail="無法離開公會")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"離開公會失敗: {str(e)}")


@app.get("/social/guilds/{guild_id}")
def get_guild_info(guild_id: str):
    """
    獲取公會資訊
    """
    try:
        guild_info = social_manager.get_guild_info(guild_id)

        if guild_info:
            return {"ok": True, "guild": guild_info}
        else:
            raise HTTPException(status_code=404, detail="公會不存在")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取公會資訊失敗: {str(e)}")


@app.get("/social/guilds/user/{username}")
def get_user_guild(username: str):
    """
    獲取用戶的公會
    """
    try:
        guild_id = social_manager.get_user_guild(username)

        if guild_id:
            guild_info = social_manager.get_guild_info(guild_id)
            return {"ok": True, "guild": guild_info}
        else:
            return {"ok": True, "guild": None, "message": "用戶未加入任何公會"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取用戶公會失敗: {str(e)}")


@app.post("/social/messages/send")
def send_message(payload: MessagePayload):
    """
    發送訊息
    """
    try:
        message_id = social_manager.send_message(
            payload.from_username,
            payload.to_username,
            payload.content,
            payload.message_type
        )

        return {"ok": True, "message_id": message_id, "message": "訊息已發送"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發送訊息失敗: {str(e)}")


@app.get("/social/messages/{username}")
def get_messages(username: str, unread_only: bool = False):
    """
    獲取用戶訊息
    """
    try:
        messages = social_manager.get_messages(username, unread_only)
        return {"ok": True, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取訊息失敗: {str(e)}")


@app.post("/social/messages/mark-read")
def mark_message_read(username: str, message_id: str):
    """
    標記訊息為已讀
    """
    try:
        success = social_manager.mark_message_read(username, message_id)

        if success:
            return {"ok": True, "message": "訊息已標記為已讀"}
        else:
            raise HTTPException(status_code=400, detail="標記訊息失敗")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"標記訊息失敗: {str(e)}")


@app.post("/social/leaderboards/create")
def create_leaderboard(payload: LeaderboardCreationPayload):
    """
    建立排行榜
    """
    try:
        leaderboard_id = social_manager.create_leaderboard(
            payload.name,
            payload.type,
            payload.period
        )

        return {"ok": True, "leaderboard_id": leaderboard_id, "message": "排行榜建立成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立排行榜失敗: {str(e)}")


@app.post("/social/leaderboards/{leaderboard_id}/update")
def update_leaderboard(leaderboard_id: str):
    """
    更新排行榜
    """
    try:
        social_manager.update_leaderboard(leaderboard_id)
        return {"ok": True, "message": "排行榜已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新排行榜失敗: {str(e)}")


@app.get("/social/leaderboards/{leaderboard_id}")
def get_leaderboard(leaderboard_id: str):
    """
    獲取排行榜
    """
    try:
        if leaderboard_id not in social_manager.leaderboards:
            raise HTTPException(status_code=404, detail="排行榜不存在")

        leaderboard = social_manager.leaderboards[leaderboard_id]
        return {
            "ok": True,
            "leaderboard": {
                'leaderboard_id': leaderboard.leaderboard_id,
                'name': leaderboard.name,
                'type': leaderboard.type,
                'period': leaderboard.period,
                'entries': leaderboard.entries,
                'last_updated': leaderboard.last_updated.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取排行榜失敗: {str(e)}")


@app.post("/social/guilds/{guild_id}/message")
def send_guild_message(guild_id: str, from_username: str, content: str):
    """
    發送公會訊息
    """
    try:
        social_manager.send_guild_message(guild_id, from_username, content)
        return {"ok": True, "message": "公會訊息已發送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發送公會訊息失敗: {str(e)}")


# --- AI投資顧問 API ---

@app.post("/ai/portfolio/analyze")
def analyze_portfolio(payload: PortfolioAnalysisPayload):
    """
    AI投資組合分析
    """
    try:
        game_data = data_manager.load_game_data(payload.username, payload.save_name, payload.platform)
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        analysis = ai_advisor.analyze_portfolio(payload.username, game_data)

        return {
            "ok": True,
            "analysis": {
                'analysis_id': analysis.analysis_id,
                'total_value': analysis.total_value,
                'total_cost': analysis.total_cost,
                'unrealized_gain_loss': analysis.unrealized_gain_loss,
                'gain_loss_percentage': analysis.gain_loss_percentage,
                'diversification_score': analysis.diversification_score,
                'risk_score': analysis.risk_score,
                'sector_allocation': analysis.sector_allocation,
                'top_performers': analysis.top_performers,
                'underperformers': analysis.underperformers,
                'recommendations': analysis.recommendations,
                'analyzed_at': analysis.analyzed_at.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"投資組合分析失敗: {str(e)}")


@app.post("/ai/investment/recommend")
def get_investment_recommendation(payload: InvestmentRecommendationPayload):
    """
    獲取AI投資建議
    """
    try:
        game_data = data_manager.load_game_data(payload.username, payload.save_name, payload.platform)
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        recommendation = ai_advisor.generate_investment_recommendation(payload.username, game_data)

        return {
            "ok": True,
            "recommendation": {
                'recommendation_id': recommendation.recommendation_id,
                'strategy': recommendation.strategy.value,
                'risk_tolerance': recommendation.risk_tolerance.value,
                'recommended_stocks': recommendation.recommended_stocks,
                'expected_return': recommendation.expected_return,
                'expected_risk': recommendation.expected_risk,
                'confidence_score': recommendation.confidence_score,
                'reasoning': recommendation.reasoning,
                'created_at': recommendation.created_at.isoformat(),
                'valid_until': recommendation.valid_until.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成投資建議失敗: {str(e)}")


@app.get("/ai/market/insights")
def get_market_insights():
    """
    獲取AI市場洞察
    """
    try:
        insights = ai_advisor.get_market_insights()

        return {"ok": True, "insights": insights}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取市場洞察失敗: {str(e)}")


@app.get("/ai/stock/analyze/{symbol}")
def analyze_stock(symbol: str):
    """
    AI股票分析
    """
    try:
        # 技術分析
        technical = ai_advisor.technical_analyzer.analyze_stock_trend(symbol)
        rsi = ai_advisor.technical_analyzer.calculate_rsi(symbol)
        ma20 = ai_advisor.technical_analyzer.calculate_moving_average(symbol, 20)
        support, resistance = ai_advisor.technical_analyzer.detect_support_resistance(symbol)

        # 基本面分析
        fundamentals = ai_advisor.fundamental_analyzer.analyze_fundamentals(symbol)
        intrinsic_value = ai_advisor.fundamental_analyzer.calculate_intrinsic_value(symbol)

        # 價格預測
        prediction = ai_advisor.market_predictor.predict_stock_price(symbol, 7)

        # 綜合評分
        current_price = ai_advisor.stock_manager.sync_prices_from_database().get(symbol, 0)
        undervalued = current_price < intrinsic_value * 0.9 if intrinsic_value > 0 else False

        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'technical_analysis': {
                'trend': technical['trend'],
                'strength': technical['strength'],
                'rsi': rsi,
                'ma20': ma20,
                'support': support,
                'resistance': resistance
            },
            'fundamental_analysis': fundamentals,
            'valuation': {
                'intrinsic_value': intrinsic_value,
                'undervalued': undervalued,
                'margin_of_safety': (intrinsic_value - current_price) / current_price if current_price > 0 else 0
            },
            'prediction': {
                'predicted_price': prediction.predicted_value,
                'confidence': prediction.confidence,
                'time_horizon': prediction.time_horizon,
                'factors': prediction.factors
            },
            'overall_rating': 'BUY' if undervalued and technical['trend'] == 'bullish' else
                           'HOLD' if fundamentals['rating'] == 'HOLD' else 'SELL',
            'confidence': min(technical['strength'], prediction.confidence)
        }

        return {"ok": True, "analysis": analysis}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"股票分析失敗: {str(e)}")


@app.get("/ai/risk/assess/{username}")
def assess_risk_tolerance(username: str):
    """
    AI風險承受度評估
    """
    try:
        game_data = data_manager.load_game_data(username, 'default', 'web')
        if not game_data:
            raise HTTPException(status_code=404, detail="找不到用戶存檔")

        risk_tolerance = ai_advisor.assess_risk_tolerance(game_data)

        # 生成風險評估報告
        age_in_game = game_data.days // 365
        assessment = {
            'risk_tolerance': risk_tolerance.value,
            'assessment_factors': {
                'game_age_years': age_in_game,
                'current_balance': getattr(game_data, 'cash', 0),
                'portfolio_diversification': len([s for s in getattr(game_data, 'stocks', {}).values() if s.get('owned', 0) > 0]),
                'investment_experience': age_in_game * 0.1  # 簡化計算
            },
            'recommended_allocation': {
                'stocks': 0.6 if risk_tolerance == ai_advisor.technical_analyzer.stock_manager.__class__.__name__ == 'Aggressive' else
                        0.4 if risk_tolerance == ai_advisor.technical_analyzer.stock_manager.__class__.__name__ == 'Moderate' else 0.2,
                'bonds': 0.3 if risk_tolerance.value == 'moderate' else
                        0.5 if risk_tolerance.value == 'conservative' else 0.1,
                'cash': 0.1 if risk_tolerance.value == 'conservative' else
                       0.2 if risk_tolerance.value == 'moderate' else 0.1
            },
            'risk_warnings': [
                "市場波動可能影響投資報酬" if risk_tolerance.value == 'conservative' else
                "請注意風險管理" if risk_tolerance.value == 'moderate' else
                "高風險投資需要謹慎決策"
            ],
            'suggested_strategies': [
                '價值投資' if risk_tolerance.value == 'conservative' else
                '平衡投資' if risk_tolerance.value == 'moderate' else
                '成長投資'
            ]
        }

        return {"ok": True, "assessment": assessment}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"風險評估失敗: {str(e)}")


@app.get("/ai/market/predict/{symbol}")
def predict_stock_price(symbol: str, days_ahead: int = 7):
    """
    AI股票價格預測
    """
    try:
        prediction = ai_advisor.market_predictor.predict_stock_price(symbol, days_ahead)
        current_price = ai_advisor.stock_manager.sync_prices_from_database().get(symbol, 0)

        prediction_data = {
            'prediction_id': prediction.prediction_id,
            'symbol': symbol,
            'current_price': current_price,
            'predicted_price': prediction.predicted_value,
            'price_change': prediction.predicted_value - current_price,
            'price_change_percent': ((prediction.predicted_value - current_price) / current_price * 100) if current_price > 0 else 0,
            'confidence': prediction.confidence,
            'time_horizon': prediction.time_horizon,
            'factors': prediction.factors,
            'created_at': prediction.created_at.isoformat(),
            'prediction_type': 'bullish' if prediction.predicted_value > current_price else 'bearish'
        }

        return {"ok": True, "prediction": prediction_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"價格預測失敗: {str(e)}")


@app.get("/ai/market/outlook")
def get_market_outlook():
    """
    AI市場展望
    """
    try:
        outlook = ai_advisor.market_predictor.generate_market_outlook()

        # 獲取市場指數
        prices = ai_advisor.stock_manager.sync_prices_from_database()
        market_average = sum(prices.values()) / len(prices) if prices else 0

        outlook_data = {
            'market_condition': outlook['condition'],
            'confidence': outlook['confidence'],
            'key_drivers': outlook['key_drivers'],
            'sector_outlook': outlook['sector_outlook'],
            'risk_assessment': outlook['risk_assessment'],
            'time_horizon': outlook['time_horizon'],
            'market_average': market_average,
            'market_volatility': ai_advisor.technical_analyzer.stock_manager.sync_prices_from_database()  # 簡化計算
        }

        return {"ok": True, "outlook": outlook_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取市場展望失敗: {str(e)}")


# --- 季節性活動和挑戰管理 API ---

@app.get("/seasonal/events")
def get_seasonal_events(season: Optional[str] = None):
    """
    獲取季節性活動
    """
    try:
        from seasonal_events import Season

        season_enum = None
        if season:
            season_map = {
                'spring': Season.SPRING,
                'summer': Season.SUMMER,
                'autumn': Season.AUTUMN,
                'winter': Season.WINTER
            }
            season_enum = season_map.get(season)

        events = seasonal_manager.get_seasonal_events(season_enum)
        return {"ok": True, "events": events}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取季節性活動失敗: {str(e)}")


@app.get("/seasonal/current")
def get_current_season():
    """
    獲取當前季節
    """
    try:
        current_season = seasonal_manager.get_current_season()
        return {"ok": True, "current_season": current_season.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取當前季節失敗: {str(e)}")


@app.get("/challenges/available")
def get_available_challenges(username: str):
    """
    獲取可用挑戰
    """
    try:
        challenges = seasonal_manager.get_available_challenges(username)
        return {"ok": True, "challenges": challenges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取可用挑戰失敗: {str(e)}")


@app.post("/challenges/start")
def start_challenge(payload: ChallengeStartPayload):
    """
    開始挑戰
    """
    try:
        success = seasonal_manager.start_challenge(payload.username, payload.challenge_id)

        if success:
            return {"ok": True, "message": "挑戰已開始"}
        else:
            raise HTTPException(status_code=400, detail="無法開始挑戰")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"開始挑戰失敗: {str(e)}")


@app.post("/events/progress")
def update_event_progress(payload: EventProgressPayload):
    """
    更新活動進度
    """
    try:
        success = seasonal_manager.update_player_progress(
            payload.username,
            payload.event_id,
            payload.progress_data
        )

        if success:
            return {"ok": True, "message": "進度已更新"}
        else:
            raise HTTPException(status_code=400, detail="更新進度失敗")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新活動進度失敗: {str(e)}")


@app.get("/events/progress/{username}/{event_id}")
def get_event_progress(username: str, event_id: str):
    """
    獲取活動進度
    """
    try:
        progress = seasonal_manager.get_player_event_progress(username, event_id)

        if progress:
            return {"ok": True, "progress": progress}
        else:
            return {"ok": True, "progress": None, "message": "尚未參與此活動"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取活動進度失敗: {str(e)}")


@app.post("/events/claim-rewards")
def claim_event_rewards(username: str, event_id: str):
    """
    領取活動獎勵
    """
    try:
        success = seasonal_manager.claim_rewards(username, event_id)

        if success:
            return {"ok": True, "message": "獎勵已領取"}
        else:
            raise HTTPException(status_code=400, detail="無法領取獎勵")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"領取獎勵失敗: {str(e)}")


@app.get("/events/statistics/{event_id}")
def get_event_statistics(event_id: str):
    """
    獲取活動統計
    """
    try:
        stats = seasonal_manager.get_event_statistics(event_id)
        return {"ok": True, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取活動統計失敗: {str(e)}")


@app.post("/seasonal/generate-event")
def generate_random_event(season: Optional[str] = None):
    """
    生成隨機季節性活動（管理員功能）
    """
    try:
        from seasonal_events import Season

        season_enum = None
        if season:
            season_map = {
                'spring': Season.SPRING,
                'summer': Season.SUMMER,
                'autumn': Season.AUTUMN,
                'winter': Season.WINTER
            }
            season_enum = season_map.get(season)

        event = seasonal_manager.generate_random_event(season_enum)

        return {
            "ok": True,
            "message": "隨機活動已生成",
            "event": {
                'event_id': event.event_id,
                'name': event.name,
                'description': event.description,
                'season': event.season.value,
                'event_type': event.event_type.value,
                'start_date': event.start_date.isoformat(),
                'end_date': event.end_date.isoformat(),
                'rewards': event.rewards,
                'objectives': event.objectives
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成隨機活動失敗: {str(e)}")


@app.get("/seasonal/calendar")
def get_seasonal_calendar():
    """
    獲取季節性活動日曆
    """
    try:
        calendar = {}

        from seasonal_events import Season
        for season in Season:
            events = seasonal_manager.get_seasonal_events(season)
            calendar[season.value] = events

        return {"ok": True, "calendar": calendar}

        raise HTTPException(status_code=500, detail=f"獲取活動日曆失敗: {str(e)}")


# --- 迷你遊戲和副業管理 API ---

@app.post("/minigames/casino/play")
def play_casino_game(payload: CasinoGamePayload):
    """
    玩賭場遊戲
    """
    try:
        if payload.game_type == "slots":
            result = mini_games_manager.play_slots(payload.username, payload.bet_amount)
        else:
            raise HTTPException(status_code=400, detail="不支援的遊戲類型")

        return {
            "ok": True,
            "game_result": {
                'game_id': result.game_id,
                'score': result.score,
                'winnings': result.winnings,
                'experience_gained': result.experience_gained,
                'metadata': result.metadata
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"遊戲執行失敗: {str(e)}")


@app.post("/minigames/blackjack/action")
def blackjack_action(payload: BlackjackActionPayload):
    """
    21點遊戲動作
    """
    try:
        result = mini_games_manager.play_blackjack(
            payload.username,
            payload.bet_amount,
            payload.action
        )

        return {"ok": True, "game_result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"21點遊戲失敗: {str(e)}")


@app.get("/minigames/trivia/question")
def get_trivia_question(difficulty: Optional[str] = None, category: Optional[str] = None):
    """
    獲取知識問答題目
    """
    try:
        from mini_games import Difficulty

        diff_enum = None
        if difficulty:
            diff_map = {
                'easy': Difficulty.EASY,
                'medium': Difficulty.MEDIUM,
                'hard': Difficulty.HARD,
                'expert': Difficulty.EXPERT
            }
            diff_enum = diff_map.get(difficulty)

        question = mini_games_manager.get_trivia_question(diff_enum, category)

        return {
            "ok": True,
            "question": {
                'question_id': question.question_id,
                'question': question.question,
                'options': question.options,
                'difficulty': question.difficulty.value,
                'category': question.category,
                'points': question.points
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取題目失敗: {str(e)}")


@app.post("/minigames/trivia/answer")
def answer_trivia_question(payload: TriviaAnswerPayload):
    """
    回答知識問答題目
    """
    try:
        result = mini_games_manager.answer_trivia_question(
            payload.username,
            payload.question_id,
            payload.answer
        )

        return {"ok": True, "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答題目失敗: {str(e)}")


@app.get("/minigames/side-hustles")
def get_available_side_hustles(username: str):
    """
    獲取可用副業活動
    """
    try:
        hustles = mini_games_manager.get_available_side_hustles(username)
        return {"ok": True, "hustles": hustles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取副業失敗: {str(e)}")


@app.post("/minigames/side-hustles/perform")
def perform_side_hustle(payload: SideHustlePayload):
    """
    執行副業活動
    """
    try:
        result = mini_games_manager.perform_side_hustle(payload.username, payload.hustle_id)

        if result['success']:
            return {"ok": True, "result": result}
        else:
            return {"ok": False, "message": result['message']}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"執行副業失敗: {str(e)}")


@app.get("/minigames/daily-challenge/{username}")
def get_daily_challenge(username: str):
    """
    獲取每日挑戰
    """
    try:
        challenge = mini_games_manager.get_daily_challenge(username)
        return {"ok": True, "challenge": challenge}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取每日挑戰失敗: {str(e)}")


@app.post("/minigames/daily-challenge/progress")
def update_daily_challenge_progress(username: str, progress: int):
    """
    更新每日挑戰進度
    """
    try:
        mini_games_manager.update_daily_challenge_progress(username, progress)
        return {"ok": True, "message": "進度已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新進度失敗: {str(e)}")


@app.get("/minigames/stats/{username}")
def get_player_game_stats(username: str):
    """
    獲取玩家遊戲統計
    """
    try:
        stats = mini_games_manager.get_player_stats(username)
        return {"ok": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


@app.get("/minigames/leaderboard")
def get_game_leaderboard(game_type: str = "casino", limit: int = 10):
    """
    獲取遊戲排行榜
    """
    try:
        from mini_games import MiniGameType

        type_map = {
            'casino': MiniGameType.CASINO,
            'puzzle': MiniGameType.PUZZLE,
            'trivia': MiniGameType.TRIVIA,
            'prediction': MiniGameType.PREDICTION,
            'side_hustle': MiniGameType.SIDE_HUSTLE
        }

        game_type_enum = type_map.get(game_type, MiniGameType.CASINO)
        leaderboard = mini_games_manager.get_game_leaderboard(game_type_enum, limit)

        return {"ok": True, "leaderboard": leaderboard}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取排行榜失敗: {str(e)}")


@app.get("/minigames/types")
def get_mini_game_types():
    """
    獲取迷你遊戲類型列表
    """
    try:
        from mini_games import MiniGameType, CasinoGame, Difficulty

        game_types = [game_type.value for game_type in MiniGameType]
        casino_games = [game.value for game in CasinoGame]
        difficulties = [diff.value for diff in Difficulty]

        return {
            "ok": True,
            "game_types": game_types,
            "casino_games": casino_games,
            "difficulties": difficulties
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取遊戲類型失敗: {str(e)}")


if __name__ == "__main__":
    # Allow running the server directly with: python server/main.py
    import uvicorn
    print("Starting Life_Simulator Server on http://127.0.0.1:8000 (reload disabled in __main__)...")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
