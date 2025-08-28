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

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
API_KEY_EXPECTED = os.getenv("API_KEY", "dev-local-key")

app = FastAPI(title="Life_Simulator Server", version="1.0.0")

# 初始化統一資料管理器
data_manager = UnifiedDataManager(db_path=DB_PATH)
# 初始化統一股票管理器
stock_manager = UnifiedStockManager(db_path=DB_PATH)
# 初始化統一成就管理器
achievement_manager = UnifiedAchievementManager(db_path=DB_PATH)


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


if __name__ == "__main__":
    # Allow running the server directly with: python server/main.py
    import uvicorn
    print("Starting Life_Simulator Server on http://127.0.0.1:8000 (reload disabled in __main__)...")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
