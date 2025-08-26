from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
import os
import sqlite3
from typing import Optional, List, Dict, Any

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
API_KEY_EXPECTED = os.getenv("API_KEY", "dev-local-key")

app = FastAPI(title="Stock Game Server", version="1.0.0")


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


def require_api_key(x_api_key: Optional[str]):
    if x_api_key != API_KEY_EXPECTED:
        raise HTTPException(status_code=401, detail="Invalid API key")


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
