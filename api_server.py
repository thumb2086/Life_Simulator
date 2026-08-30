"""
Life Simulator - FastAPI Backend
Extracts game logic from tkinter BankGame into REST API for web frontend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
import random
import math

from game_data import GameData
from health_manager import HealthManager
from housing_manager import HousingManager
from education_manager import EducationManager
from social_manager import SocialManager

app = FastAPI(title="Life Simulator API", version="1.0.0")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Game State (single session) ──────────────────────────────────────
data = GameData()
health_mgr = HealthManager(data)
housing_mgr = HousingManager(data)
edu_mgr = EducationManager(data)
social_mgr = SocialManager(data)
tick_count = 0

SAVE_DIR = os.path.join(os.path.dirname(__file__), "saves")
os.makedirs(SAVE_DIR, exist_ok=True)


def _get_full_state() -> dict:
    """Snapshot the entire game state as a JSON-safe dict."""
    stocks_serialized = {}
    for code, s in data.stocks.items():
        stocks_serialized[code] = {
            "name": s["name"],
            "industry": s["industry"],
            "price": round(s["price"], 2),
            "owned": s["owned"],
            "dividend_per_share": s.get("dividend_per_share", 0),
            "dividend_interval": s.get("dividend_interval", 30),
            "history": s["history"][-60:],  # last 60 data points for chart
        }

    return {
        "days": data.days,
        "cash": round(data.cash, 2),
        "balance": round(data.balance, 2),
        "loan": round(data.loan, 2),
        "total_assets": round(data.total_assets(), 2),
        "stocks": stocks_serialized,
        "btc_balance": round(data.btc_balance, 6),
        "btc_hashrate": round(getattr(data, "btc_hashrate", 0), 2),
        "btc_miner_count": getattr(data, "btc_miner_count", 0),
        "job": data.job,
        "health": data.health,
        "housing": data.housing,
        "education": data.education,
        "social": data.social,
        "achievements": getattr(data, "achievements_unlocked", []),
        "recent_events": getattr(data, "_recent_events", []),
    }


# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/api/state")
def get_state():
    return _get_full_state()


@app.get("/api/status")
def status():
    return {"status": "ok", "days": data.days, "cash": round(data.cash, 2)}


# ── Day Advance ──────────────────────────────────────────────────────
class AdvanceResult(BaseModel):
    message: str = ""
    events: list = []


@app.post("/api/advance")
def advance_day():
    """Advance the game by one tick (~1 day). Mirrors unified_timer 30s block."""
    global tick_count
    tick_count += 1
    events = []

    # Stock price fluctuation
    for stock in data.stocks.values():
        change = random.gauss(0, data.market_volatility)
        stock["price"] = max(10, round(stock["price"] * (1 + change), 2))
        stock["history"].append(stock["price"])

    # Every 5 ticks: just stocks (already done above)
    # Every 1 tick for web: do the full daily cycle
    # Interest
    if data.balance > 0:
        interest = data.balance * data.deposit_interest_rate
        data.balance += interest
        events.append(f"存款利息 +${interest:.2f}")

    if data.loan > 0:
        interest = data.loan * data.loan_interest_rate
        data.loan += interest
        if data.cash >= interest:
            data.cash -= interest
        else:
            diff = interest - data.cash
            data.cash = 0
            data.balance = max(0, data.balance - diff)
        events.append(f"貸款利息 -${interest:.2f}")

    # Salary
    if data.job:
        gross = float(data.job.get("salary_per_day", 0))
        tax_rate = float(data.job.get("tax_rate", 0))
        tax = max(0, round(gross * tax_rate, 2))
        net = round(gross - tax, 2)
        if net > 0:
            data.cash += net
            data.income_history.append({"day": data.days + 1, "type": "salary",
                                        "gross": gross, "tax": tax, "net": net})
            events.append(f"薪資 +${net:.2f}")

    # Expenses
    today = data.days + 1
    freq_days = {"daily": 1, "weekly": 7, "monthly": 30}
    for exp in list(getattr(data, "expenses", [])):
        due = int(exp.get("next_due_day", today))
        if due <= today:
            amount = float(exp.get("amount", 0))
            paid = min(amount, data.cash)
            data.cash -= paid
            remaining = amount - paid
            if remaining > 0:
                paid_from_balance = min(remaining, data.balance)
                data.balance -= paid_from_balance
                paid += paid_from_balance
            data.expense_history.append({"day": today, "name": exp.get("name", "支出"), "amount": paid})
            exp["next_due_day"] = today + freq_days.get(exp.get("frequency", "daily"), 1)
            events.append(f"支出 {exp.get('name', '')} -${paid:.2f}")

    data.days += 1

    # Life systems daily
    for mgr in [health_mgr, housing_mgr, edu_mgr, social_mgr]:
        msg = mgr.process_daily()
        if msg:
            events.append(msg)

    # Dividends
    for code, stock in data.stocks.items():
        if data.days >= stock.get("next_dividend_day", 30):
            if stock["owned"] > 0 and stock.get("dividend_per_share", 0) > 0:
                dividend = stock["owned"] * stock["dividend_per_share"]
                data.cash += dividend
                events.append(f"{stock['name']} 配息 +${dividend:.2f}")
            stock["next_dividend_day"] = data.days + stock.get("dividend_interval", 30)

    # BTC price fluctuation
    btc = data.stocks["BTC"]
    btc_change = random.gauss(0, 0.03)
    btc["price"] = max(10000, round(btc["price"] * (1 + btc_change)))
    btc["history"].append(btc["price"])

    # BTC mining
    hashrate = getattr(data, "btc_hashrate", 0)
    if hashrate > 0:
        mined = hashrate * 0.01
        data.btc_balance += mined
        events.append(f"BTC 挖礦 +{mined:.4f}")

    data._recent_events = events[-10:]
    return {"day": data.days, "events": events, "state": _get_full_state()}


# ── Banking ──────────────────────────────────────────────────────────
class AmountReq(BaseModel):
    amount: float

@app.post("/api/bank/deposit")
def bank_deposit(req: AmountReq):
    if req.amount <= 0:
        raise HTTPException(400, "金額必須大於 0")
    if req.amount > data.cash:
        raise HTTPException(400, "現金不足")
    data.cash -= req.amount
    data.balance += req.amount
    return {"message": f"存入 ${req.amount:.2f}", "state": _get_full_state()}

@app.post("/api/bank/withdraw")
def bank_withdraw(req: AmountReq):
    if req.amount <= 0:
        raise HTTPException(400, "金額必須大於 0")
    if req.amount > data.balance:
        raise HTTPException(400, "存款不足")
    data.balance -= req.amount
    data.cash += req.amount
    return {"message": f"領出 ${req.amount:.2f}", "state": _get_full_state()}

@app.post("/api/bank/loan")
def bank_loan(req: AmountReq):
    if req.amount <= 0:
        raise HTTPException(400, "金額必須大於 0")
    if req.amount > data.loan_limit:
        raise HTTPException(400, f"超過貸款上限 ${data.loan_limit:.2f}")
    data.loan += req.amount
    data.cash += req.amount
    return {"message": f"貸款 +${req.amount:.2f}", "state": _get_full_state()}

@app.post("/api/bank/repay")
def bank_repay(req: AmountReq):
    if req.amount <= 0:
        raise HTTPException(400, "金額必須大於 0")
    total = data.cash + data.balance
    repay_amount = min(req.amount, data.loan, total)
    # First use cash, then balance
    cash_used = min(repay_amount, data.cash)
    data.cash -= cash_used
    balance_used = repay_amount - cash_used
    data.balance -= balance_used
    data.loan -= repay_amount
    return {"message": f"償還 ${repay_amount:.2f}", "state": _get_full_state()}


# ── Stock Trading ────────────────────────────────────────────────────
class StockTradeReq(BaseModel):
    code: str
    shares: int

@app.post("/api/stock/buy")
def stock_buy(req: StockTradeReq):
    stock = data.stocks.get(req.code)
    if not stock:
        raise HTTPException(400, "未知股票代碼")
    if req.shares <= 0:
        raise HTTPException(400, "股數必須大於 0")
    cost = stock["price"] * req.shares
    if cost > data.cash:
        raise HTTPException(400, f"現金不足 (需要 ${cost:.2f})")
    data.cash -= cost
    stock["owned"] += req.shares
    stock["total_cost"] += cost
    return {"message": f"買入 {stock['name']} {req.shares} 股", "state": _get_full_state()}

@app.post("/api/stock/sell")
def stock_sell(req: StockTradeReq):
    stock = data.stocks.get(req.code)
    if not stock:
        raise HTTPException(400, "未知股票代碼")
    if req.shares <= 0:
        raise HTTPException(400, "股數必須大於 0")
    if req.shares > stock["owned"]:
        raise HTTPException(400, "持股不足")
    revenue = stock["price"] * req.shares
    stock["owned"] -= req.shares
    stock["total_cost"] -= stock["total_cost"] * (req.shares / max(stock["owned"] + req.shares, 1))
    data.cash += revenue
    return {"message": f"賣出 {stock['name']} {req.shares} 股 +${revenue:.2f}", "state": _get_full_state()}


# ── BTC ──────────────────────────────────────────────────────────────
class BtcBuyReq(BaseModel):
    usd_amount: float

@app.post("/api/btc/buy")
def btc_buy(req: BtcBuyReq):
    btc_price = data.stocks["BTC"]["price"]
    if req.usd_amount <= 0:
        raise HTTPException(400, "金額必須大於 0")
    if req.usd_amount > data.cash:
        raise HTTPException(400, "現金不足")
    btc_amount = req.usd_amount / btc_price
    data.cash -= req.usd_amount
    data.btc_balance += btc_amount
    return {"message": f"買入 {btc_amount:.6f} BTC", "state": _get_full_state()}

@app.post("/api/btc/sell")
def btc_sell(req: BtcBuyReq):
    btc_price = data.stocks["BTC"]["price"]
    btc_amount = req.usd_amount / btc_price
    if btc_amount > data.btc_balance:
        raise HTTPException(400, "BTC 餘額不足")
    data.btc_balance -= btc_amount
    data.cash += req.usd_amount
    return {"message": f"賣出 {btc_amount:.6f} BTC", "state": _get_full_state()}

class MinerReq(BaseModel):
    count: int = 1

@app.post("/api/btc/miner")
def btc_buy_miner(req: MinerReq):
    price = 50000
    total = price * req.count
    if total > data.cash:
        raise HTTPException(400, "現金不足")
    data.cash -= total
    data.btc_miner_count = getattr(data, "btc_miner_count", 0) + req.count
    data.btc_hashrate = getattr(data, "btc_hashrate", 0) + req.count * 100
    return {"message": f"購入 {req.count} 台礦機", "state": _get_full_state()}


# ── Health ───────────────────────────────────────────────────────────
@app.post("/api/health/eat")
def health_eat(quality: int = 2):
    msg = health_mgr.eat_meal(quality)
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/health/exercise")
def health_exercise():
    msg = health_mgr.exercise()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/health/rest")
def health_rest():
    msg = health_mgr.rest()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/health/meditate")
def health_meditate():
    msg = health_mgr.meditate()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/health/gym")
def health_gym(level: int = 1):
    msg = health_mgr.join_gym(level)
    return {"message": msg, "state": _get_full_state()}


# ── Housing ──────────────────────────────────────────────────────────
@app.post("/api/housing/rent")
def housing_rent():
    msg = housing_mgr.rent_property()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/housing/buy")
def housing_buy(property_type: str = "小套房"):
    msg = housing_mgr.buy_property(property_type)
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/housing/sell")
def housing_sell():
    msg = housing_mgr.sell_property()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/housing/facility")
def housing_facility(name: str = "冷氣"):
    msg = housing_mgr.install_facility(name)
    return {"message": msg, "state": _get_full_state()}


# ── Education ────────────────────────────────────────────────────────
@app.post("/api/edu/study")
def edu_study(skill: str = "程式", level: str = "基礎"):
    msg = edu_mgr.learn_skill(skill, level)
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/edu/degree")
def edu_degree(degree: str = "大學"):
    msg = edu_mgr.study_degree(degree)
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/edu/cert")
def edu_cert(cert: str = "PMP"):
    msg = edu_mgr.get_certification(cert)
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/edu/job")
def edu_job(job_title: str = "工程師"):
    msg = edu_mgr.apply_job(job_title)
    return {"message": msg, "state": _get_full_state()}


# ── Social ───────────────────────────────────────────────────────────
@app.post("/api/social/event")
def social_event():
    msg = social_mgr.attend_event()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/social/network")
def social_network():
    msg = social_mgr.network()
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/social/gift")
def social_gift(target: str = "朋友"):
    msg = social_mgr.give_gift(target)
    return {"message": msg, "state": _get_full_state()}

@app.post("/api/social/volunteer")
def social_volunteer():
    msg = social_mgr.attend_event("volunteer")
    return {"message": msg, "state": _get_full_state()}


# ── Save / Load ──────────────────────────────────────────────────────
class SaveReq(BaseModel):
    slot: str = "web_save"

@app.post("/api/save")
def save_game(req: SaveReq):
    path = os.path.join(SAVE_DIR, f"{req.slot}.json")
    data.save(path)
    return {"message": f"已儲存到 {req.slot}", "path": path}

@app.post("/api/load")
def load_game(req: SaveReq):
    path = os.path.join(SAVE_DIR, f"{req.slot}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "存檔不存在")
    data.load(path)
    # Re-init managers with loaded data
    health_mgr.__init__(data)
    housing_mgr.__init__(data)
    edu_mgr.__init__(data)
    social_mgr.__init__(data)
    return {"message": f"已載入 {req.slot}", "state": _get_full_state()}

@app.get("/api/saves")
def list_saves():
    files = [f.replace(".json", "") for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    return {"saves": files}


# ── Serve Phaser frontend ────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "web")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    # Serve static files (game.js, CSS, etc.) from web/
    from starlette.responses import FileResponse as StarletteFileResponse
    import mimetypes

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/game")
    def serve_game():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{filename:path}")
    def serve_static(filename: str):
        filepath = os.path.join(FRONTEND_DIR, filename)
        if os.path.isfile(filepath):
            return FileResponse(filepath)
        raise HTTPException(404, "Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
