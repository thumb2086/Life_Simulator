from fastapi import FastAPI, Header, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sqlite3
from typing import Optional, List, Dict, Any
import secrets
import random

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
API_KEY_EXPECTED = os.getenv("API_KEY", "dev-local-key")

app = FastAPI(title="Life_Simulator Server", version="1.0.0")


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
        symbols = [
            ("AAPL", 180.0), ("MSFT", 420.0), ("GOOG", 140.0),
            ("TSLA", 250.0), ("NVDA", 900.0), ("AMZN", 170.0)
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

# Static web frontend (PWA)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.isdir(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root() -> RedirectResponse:
    # Redirect to leaderboard page by default
    return RedirectResponse(url="/static/leaderboard.html")


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
    cur.execute("SELECT cash, days FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    cash = float(row["cash"]) if row else 0.0
    days = int(row["days"]) if row else 0
    # portfolio
    cur.execute("SELECT symbol, qty, avg_cost FROM portfolios WHERE username=?", (username,))
    holdings = [{"symbol": r["symbol"], "qty": float(r["qty"]), "avg_cost": float(r["avg_cost"])} for r in cur.fetchall()]
    # prices
    prices = get_prices(conn)
    conn.close()
    return {"username": username, "cash": cash, "days": days, "holdings": holdings, "prices": prices}


@app.get("/stocks/list")
def stocks_list() -> Dict[str, Any]:
    conn = get_db()
    prices = get_prices(conn)
    conn.close()
    return {"prices": prices}


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
