"""
Life Simulator - 簡化版服務器
整合核心功能，提供簡潔易用的API介面
"""

from fastapi import FastAPI, HTTPException, Header, Query, Depends
from pydantic import BaseModel
from datetime import datetime
import os
import sys
import random
import json
import sqlite3
from typing import Dict, List, Optional, Any

# =============================================================================
# 簡化版常數定義
# =============================================================================
DB_PATH = os.getenv("DB_PATH", "app.db")
API_KEY = os.getenv("API_KEY", "dev-key")

# =============================================================================
# 簡化版FastAPI應用
# =============================================================================
app = FastAPI(
    title="Life Simulator - 簡化版",
    description="簡潔易用的生命模擬器服務器",
    version="1.0.0"
)

# =============================================================================
# 簡化版資料模型
# =============================================================================
class LoginRequest(BaseModel):
    username: str

class GameDataRequest(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    game_data: Optional[Dict[str, Any]] = None

class TradeRequest(BaseModel):
    username: str
    symbol: str
    qty: float
    action: str  # 'buy' 或 'sell'

class CasinoRequest(BaseModel):
    username: str
    game_type: str  # 'slots', 'blackjack', 'dice'
    bet_amount: float

class AchievementRequest(BaseModel):
    username: str
    save_name: Optional[str] = 'default'

# =============================================================================
# 簡化版工具函數
# =============================================================================
def get_db():
    """獲取資料庫連接"""
    return sqlite3.connect(DB_PATH)

def init_database():
    """初始化資料庫"""
    conn = get_db()
    cur = conn.cursor()

    # 用戶表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            cash REAL DEFAULT 100000,
            days INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 存檔表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_saves (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            save_name TEXT DEFAULT 'default',
            game_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 股票表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            symbol TEXT PRIMARY KEY,
            price REAL NOT NULL,
            name TEXT
        )
    """)

    # 投資組合表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            username TEXT NOT NULL,
            symbol TEXT NOT NULL,
            qty REAL NOT NULL,
            PRIMARY KEY (username, symbol)
        )
    """)

    # 成就表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            username TEXT NOT NULL,
            achievement_id TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (username, achievement_id)
        )
    """)

    # 遊戲記錄表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            game_type TEXT NOT NULL,
            result TEXT,
            winnings REAL DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# 初始化資料庫
init_database()

# =============================================================================
# 簡化版核心功能類別
# =============================================================================
class SimpleGameManager:
    """簡化版遊戲管理器"""

    def __init__(self):
        self.active_games = {}

    def save_game(self, username: str, save_name: str, game_data: Dict[str, Any]) -> bool:
        """儲存遊戲"""
        conn = get_db()
        try:
            cur = conn.cursor()
            game_data_json = json.dumps(game_data, default=str)

            # 插入或更新存檔
            cur.execute("""
                INSERT OR REPLACE INTO game_saves
                (username, save_name, game_data, updated_at)
                VALUES (?, ?, ?, ?)
            """, (username, save_name, game_data_json, datetime.now()))

            conn.commit()
            return True
        except Exception as e:
            print(f"儲存遊戲失敗: {e}")
            return False
        finally:
            conn.close()

    def load_game(self, username: str, save_name: str) -> Optional[Dict[str, Any]]:
        """載入遊戲"""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT game_data FROM game_saves
                WHERE username = ? AND save_name = ?
            """, (username, save_name))

            row = cur.fetchone()
            if row:
                return json.loads(row['game_data'])
            return None
        except Exception as e:
            print(f"載入遊戲失敗: {e}")
            return None
        finally:
            conn.close()

    def list_saves(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出存檔"""
        conn = get_db()
        try:
            cur = conn.cursor()
            if username:
                cur.execute("""
                    SELECT save_name, updated_at FROM game_saves
                    WHERE username = ? ORDER BY updated_at DESC
                """, (username,))
            else:
                cur.execute("""
                    SELECT username, save_name, updated_at FROM game_saves
                    ORDER BY updated_at DESC LIMIT 50
                """)

            saves = []
            for row in cur.fetchall():
                if username:
                    saves.append({
                        'save_name': row['save_name'],
                        'updated_at': row['updated_at']
                    })
                else:
                    saves.append({
                        'username': row['username'],
                        'save_name': row['save_name'],
                        'updated_at': row['updated_at']
                    })
            return saves
        finally:
            conn.close()


class SimpleStockManager:
    """簡化版股票管理器"""

    def __init__(self):
        self.stocks = {
            'TSMC': {'price': 100.0, 'name': '台積電'},
            'AAPL': {'price': 150.0, 'name': '蘋果'},
            'GOOGL': {'price': 2500.0, 'name': '谷歌'},
            'MSFT': {'price': 300.0, 'name': '微軟'},
            'AMZN': {'price': 3200.0, 'name': '亞馬遜'}
        }
        self._init_stocks()

    def _init_stocks(self):
        """初始化股票資料"""
        conn = get_db()
        try:
            cur = conn.cursor()
            for symbol, data in self.stocks.items():
                cur.execute("""
                    INSERT OR IGNORE INTO stocks (symbol, price, name)
                    VALUES (?, ?, ?)
                """, (symbol, data['price'], data['name']))
            conn.commit()
        finally:
            conn.close()

    def get_prices(self) -> Dict[str, float]:
        """獲取所有股票價格"""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT symbol, price FROM stocks")
            return {row['symbol']: row['price'] for row in cur.fetchall()}
        finally:
            conn.close()

    def update_prices(self):
        """隨機更新股票價格"""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT symbol, price FROM stocks")

            for row in cur.fetchall():
                symbol = row['symbol']
                current_price = row['price']
                # 隨機波動 ±5%
                change = random.uniform(-0.05, 0.05)
                new_price = max(0.1, current_price * (1 + change))

                cur.execute("""
                    UPDATE stocks SET price = ? WHERE symbol = ?
                """, (round(new_price, 2), symbol))

            conn.commit()
        finally:
            conn.close()

    def buy_stock(self, username: str, symbol: str, qty: float) -> Dict[str, Any]:
        """買入股票"""
        prices = self.get_prices()
        if symbol not in prices:
            raise HTTPException(status_code=404, detail="股票不存在")

        price = prices[symbol]
        cost = price * qty

        # 檢查用戶現金
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT cash FROM users WHERE username = ?", (username,))
            row = cur.fetchone()

            if not row or row['cash'] < cost:
                raise HTTPException(status_code=400, detail="現金不足")

            # 更新現金
            cur.execute("""
                UPDATE users SET cash = cash - ? WHERE username = ?
            """, (cost, username))

            # 更新投資組合
            cur.execute("""
                INSERT OR REPLACE INTO portfolios (username, symbol, qty)
                VALUES (?, ?, COALESCE((SELECT qty FROM portfolios WHERE username = ? AND symbol = ?), 0) + ?)
            """, (username, symbol, username, symbol, qty))

            conn.commit()

            return {
                'success': True,
                'message': f'成功購買 {qty} 股 {symbol}',
                'cost': cost
            }

        finally:
            conn.close()

    def sell_stock(self, username: str, symbol: str, qty: float) -> Dict[str, Any]:
        """賣出股票"""
        prices = self.get_prices()
        if symbol not in prices:
            raise HTTPException(status_code=404, detail="股票不存在")

        price = prices[symbol]
        proceeds = price * qty

        conn = get_db()
        try:
            cur = conn.cursor()

            # 檢查持有量
            cur.execute("""
                SELECT qty FROM portfolios
                WHERE username = ? AND symbol = ?
            """, (username, symbol))

            row = cur.fetchone()
            if not row or row['qty'] < qty:
                raise HTTPException(status_code=400, detail="持有股票不足")

            # 更新現金
            cur.execute("""
                UPDATE users SET cash = cash + ? WHERE username = ?
            """, (proceeds, username))

            # 更新投資組合
            cur.execute("""
                UPDATE portfolios SET qty = qty - ?
                WHERE username = ? AND symbol = ?
            """, (qty, username, symbol))

            # 刪除空倉位
            cur.execute("""
                DELETE FROM portfolios WHERE username = ? AND symbol = ? AND qty <= 0
            """, (username, symbol))

            conn.commit()

            return {
                'success': True,
                'message': f'成功賣出 {qty} 股 {symbol}',
                'proceeds': proceeds
            }

        finally:
            conn.close()


class SimpleCasinoManager:
    """簡化版賭場管理器"""

    def __init__(self):
        pass

    def play_slots(self, username: str, bet_amount: float) -> Dict[str, Any]:
        """玩拉霸遊戲"""
        # 簡單的拉霸邏輯
        symbols = ['🍒', '🍋', '🍊', '⭐', '💎', '7️⃣']
        reels = [random.choice(symbols) for _ in range(3)]

        # 計算中獎
        if reels[0] == reels[1] == reels[2]:
            if reels[0] == '7️⃣':
                multiplier = 10  # 大獎
            elif reels[0] == '💎':
                multiplier = 5   # 中獎
            else:
                multiplier = 3   # 小獎
            winnings = bet_amount * multiplier
        elif reels[0] == reels[1] or reels[1] == reels[2]:
            winnings = bet_amount * 1.5
        else:
            winnings = 0

        # 記錄遊戲結果
        self._record_game_result(username, 'slots', 'win' if winnings > 0 else 'lose', winnings)

        return {
            'reels': reels,
            'winnings': winnings,
            'message': f'結果: {" ".join(reels)} - 獲得 ${winnings:.0f}'
        }

    def play_dice(self, username: str, bet_amount: float, prediction: str) -> Dict[str, Any]:
        """玩骰子遊戲"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2

        # 判斷結果
        if prediction == 'over' and total > 7:
            winnings = bet_amount * 2
        elif prediction == 'under' and total < 7:
            winnings = bet_amount * 2
        elif prediction == 'seven' and total == 7:
            winnings = bet_amount * 5
        else:
            winnings = 0

        # 記錄遊戲結果
        self._record_game_result(username, 'dice', 'win' if winnings > 0 else 'lose', winnings)

        return {
            'dice': [dice1, dice2],
            'total': total,
            'winnings': winnings,
            'message': f'骰子點數: {dice1} + {dice2} = {total} - 獲得 ${winnings:.0f}'
        }

    def _record_game_result(self, username: str, game_type: str, result: str, winnings: float):
        """記錄遊戲結果"""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO game_history (username, game_type, result, winnings)
                VALUES (?, ?, ?, ?)
            """, (username, game_type, result, winnings))
            conn.commit()
        finally:
            conn.close()


class SimpleAchievementManager:
    """簡化版成就管理器"""

    def __init__(self):
        self.achievements = {
            'first_win': {'name': '首勝', 'description': '贏得第一筆獎金'},
            'high_roller': {'name': '豪客', 'description': '單筆下注超過1000'},
            'stock_master': {'name': '股票大師', 'description': '持有3種以上股票'},
            'saving_master': {'name': '儲存大師', 'description': '進行5次遊戲儲存'}
        }

    def check_achievements(self, username: str) -> List[Dict[str, Any]]:
        """檢查成就"""
        unlocked = []

        # 這裡可以實現更複雜的成就檢查邏輯
        # 目前返回空的成就列表

        return unlocked

    def get_user_achievements(self, username: str) -> List[Dict[str, Any]]:
        """獲取用戶成就"""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT achievement_id, unlocked_at FROM achievements
                WHERE username = ?
            """, (username,))

            achievements = []
            for row in cur.fetchall():
                achievement_id = row['achievement_id']
                if achievement_id in self.achievements:
                    achievements.append({
                        'id': achievement_id,
                        'name': self.achievements[achievement_id]['name'],
                        'description': self.achievements[achievement_id]['description'],
                        'unlocked_at': row['unlocked_at']
                    })

            return achievements

        finally:
            conn.close()


# =============================================================================
# 簡化版管理器實例
# =============================================================================
game_manager = SimpleGameManager()
stock_manager = SimpleStockManager()
casino_manager = SimpleCasinoManager()
achievement_manager = SimpleAchievementManager()

# =============================================================================
# 簡化版API端點
# =============================================================================

# 基礎端點
@app.get("/")
async def root():
    """服務器根端點"""
    return {
        "message": "Life Simulator 簡化版服務器",
        "version": app.version,
        "features": ["遊戲存檔", "股票交易", "賭場遊戲", "成就系統"]
    }

@app.get("/health")
async def health():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 用戶認證
@app.post("/login")
async def login(request: LoginRequest):
    """用戶登入"""
    conn = get_db()
    try:
        cur = conn.cursor()
        # 確保用戶存在
        cur.execute("""
            INSERT OR IGNORE INTO users (username, cash, days)
            VALUES (?, 100000, 0)
        """, (request.username,))

        conn.commit()

        return {
            "success": True,
            "username": request.username,
            "message": "登入成功"
        }
    finally:
        conn.close()

# 遊戲資料
@app.post("/game/save")
async def save_game(request: GameDataRequest):
    """儲存遊戲"""
    if not request.game_data:
        raise HTTPException(status_code=400, detail="需要遊戲資料")

    success = game_manager.save_game(request.username, request.save_name, request.game_data)

    if success:
        return {"success": True, "message": "遊戲已儲存"}
    else:
        raise HTTPException(status_code=500, detail="儲存失敗")

@app.post("/game/load")
async def load_game(request: GameDataRequest):
    """載入遊戲"""
    game_data = game_manager.load_game(request.username, request.save_name)

    if game_data:
        return {"success": True, "game_data": game_data}
    else:
        raise HTTPException(status_code=404, detail="找不到存檔")

@app.get("/game/saves")
async def list_saves(username: Optional[str] = None):
    """列出存檔"""
    saves = game_manager.list_saves(username)
    return {"saves": saves}

# 股票系統
@app.get("/stocks")
async def get_stocks():
    """獲取股票價格"""
    prices = stock_manager.get_prices()
    return {"stocks": prices}

@app.post("/stocks/trade")
async def trade_stock(request: TradeRequest):
    """股票交易"""
    if request.action == 'buy':
        result = stock_manager.buy_stock(request.username, request.symbol, request.qty)
    elif request.action == 'sell':
        result = stock_manager.sell_stock(request.username, request.symbol, request.qty)
    else:
        raise HTTPException(status_code=400, detail="無效的交易動作")

    return result

@app.post("/stocks/update")
async def update_stock_prices():
    """更新股票價格"""
    stock_manager.update_prices()
    return {"success": True, "message": "股票價格已更新"}

# 賭場系統
@app.post("/casino/slots")
async def play_slots(request: CasinoRequest):
    """玩拉霸遊戲"""
    result = casino_manager.play_slots(request.username, request.bet_amount)
    return result

@app.post("/casino/dice")
async def play_dice(request: CasinoRequest):
    """玩骰子遊戲"""
    prediction = getattr(request, 'prediction', 'seven')
    result = casino_manager.play_dice(request.username, request.bet_amount, prediction)
    return result

# 成就系統
@app.post("/achievements/check")
async def check_achievements(request: AchievementRequest):
    """檢查成就"""
    achievements = achievement_manager.check_achievements(request.username)
    return {"new_achievements": achievements}

@app.get("/achievements/{username}")
async def get_user_achievements(username: str):
    """獲取用戶成就"""
    achievements = achievement_manager.get_user_achievements(username)
    return {"achievements": achievements}

# 統計資訊
@app.get("/stats/{username}")
async def get_user_stats(username: str):
    """獲取用戶統計"""
    conn = get_db()
    try:
        cur = conn.cursor()

        # 用戶基本資訊
        cur.execute("""
            SELECT cash, days FROM users WHERE username = ?
        """, (username,))
        user_row = cur.fetchone()

        if not user_row:
            raise HTTPException(status_code=404, detail="用戶不存在")

        # 投資組合
        cur.execute("""
            SELECT symbol, qty FROM portfolios WHERE username = ?
        """, (username,))
        portfolio = {row['symbol']: row['qty'] for row in cur.fetchall()}

        # 遊戲歷史
        cur.execute("""
            SELECT game_type, COUNT(*) as count, SUM(winnings) as total_winnings
            FROM game_history
            WHERE username = ?
            GROUP BY game_type
        """, (username,))
        game_stats = {}
        for row in cur.fetchall():
            game_stats[row['game_type']] = {
                'games_played': row['count'],
                'total_winnings': row['total_winnings'] or 0
            }

        return {
            "user_info": {
                "username": username,
                "cash": user_row['cash'],
                "days": user_row['days']
            },
            "portfolio": portfolio,
            "game_stats": game_stats
        }

    finally:
        conn.close()


# =============================================================================
# 應用啟動
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    print("🚀 Life Simulator 簡化版服務器啟動中...")
    print(f"📊 版本: {app.version}")
    print("🌐 訪問地址: http://127.0.0.1:8000")
    print("📚 API文檔: http://127.0.0.1:8000/docs")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
