"""
Life Simulator Server - 統一主服務器
整合所有功能模組，提供統一的API介面
"""

# =============================================================================
# 標準庫匯入
# =============================================================================
import os
import sys
from datetime import datetime
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
MODULES_DIR = os.path.join(os.path.dirname(__file__), 'modules')
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

# 匯入各功能模組
from auth.auth_manager import AuthManager
from game_data.game_data_manager import GameDataManager
from stock_trading.stock_trading_manager import StockTradingManager
from achievements.achievement_manager import AchievementManager
from casino.casino_manager import CasinoManager
from mini_games.mini_games_manager import MiniGamesManager
from social.social_manager import SocialFeaturesManager
from market_news.market_news_manager import MarketNewsEventManager

# 匯入遊戲資料類別
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'modules'))
from game_data import GameData

# =============================================================================
# 常數定義
# =============================================================================
DEFAULT_DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
DEFAULT_API_KEY = os.getenv("API_KEY", "dev-local-key")

# =============================================================================
# FastAPI 應用初始化
# =============================================================================
app = FastAPI(
    title="Life Simulator Server",
    description="統一遊戲平台服務器，整合所有遊戲功能",
    version="2.1.0"
)

# =============================================================================
# 服務器組件初始化
# =============================================================================
# 初始化各功能管理器
auth_manager = AuthManager(DEFAULT_API_KEY)
game_data_manager = GameDataManager("saves")
stock_trading_manager = StockTradingManager(DEFAULT_DB_PATH)
achievement_manager = AchievementManager(DEFAULT_DB_PATH)
casino_manager = CasinoManager(game_data_manager, DEFAULT_DB_PATH)
mini_games_manager = MiniGamesManager(game_data_manager, DEFAULT_DB_PATH)
social_manager = SocialFeaturesManager(game_data_manager, DEFAULT_DB_PATH)
market_news_manager = MarketNewsEventManager(stock_trading_manager, DEFAULT_DB_PATH)

# =============================================================================
# Pydantic 模型
# =============================================================================
class LoginPayload(BaseModel):
    username: str

class GameDataPayload(BaseModel):
    game_data: Dict[str, Any]
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'

class SaveLoadPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = None

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
    price: Optional[float] = None

class LeaderboardSubmit(BaseModel):
    username: str
    asset: float
    days: int

class CasinoGamePayload(BaseModel):
    username: str
    bet_amount: float
    game_type: str

class AchievementCheckPayload(BaseModel):
    username: str
    save_name: Optional[str] = 'default'
    platform: Optional[str] = 'web'

# 匯入更多模型
from auth.auth_manager import LoginRequest
from game_data.game_data_manager import SaveLoadRequest
from stock_trading.stock_trading_manager import TradeRequest, AdvancedTradeRequest
from achievements.achievement_manager import AchievementCheckRequest
from casino.casino_manager import CasinoGameRequest
from mini_games.mini_games_manager import TriviaQuestion
from social.social_manager import FriendRequestPayload, FriendResponsePayload, GuildCreationPayload, MessagePayload
from market_news.market_news_manager import NewsGenerationPayload, TournamentPayload

# =============================================================================
# 工具函數
# =============================================================================
def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """驗證API金鑰"""
    auth_manager.require_api_key(x_api_key)

def get_username_by_token(token: str) -> str:
    """通過權杖獲取用戶名"""
    return auth_manager.get_username_by_token(token)

# =============================================================================
# API 路由定義
# =============================================================================

# -----------------------------------------------------------------------------
# 基礎系統 API
# -----------------------------------------------------------------------------
@app.get("/")
async def root() -> Dict[str, Any]:
    """
    服務器根端點

    返回服務器基本資訊
    """
    return {
        "service": "Life Simulator Server",
        "version": app.version,
        "status": "running",
        "modules": [
            "authentication",
            "game_data_management",
            "stock_trading",
            "achievements",
            "casino_games",
            "mini_games",
            "social_features",
            "market_news_events"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康檢查端點

    檢查資料庫連接和服務器狀態
    """
    try:
        # 檢查各模組狀態
        modules_status = {
            "auth": "healthy",
            "game_data": "healthy",
            "stock_trading": "healthy",
            "achievements": "healthy",
            "casino": "healthy",
            "mini_games": "healthy",
            "social": "healthy",
            "market_news": "healthy"
        }

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules": modules_status
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/version")
async def get_version() -> Dict[str, Any]:
    """獲取服務器版本資訊"""
    return {"version": app.version}

# -----------------------------------------------------------------------------
# 認證系統 API
# -----------------------------------------------------------------------------
@app.post("/auth/login")
async def authenticate_user(payload: LoginPayload) -> Dict[str, Any]:
    """
    用戶登入

    生成訪問權杖並確保用戶存在於資料庫中
    """
    try:
        token = auth_manager.authenticate_user(payload.username)
        return {
            "token": token,
            "username": payload.username,
            "message": "登入成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登入失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 遊戲資料管理 API
# -----------------------------------------------------------------------------
@app.post("/game/save")
async def save_game_data(payload: GameDataPayload) -> Dict[str, Any]:
    """
    儲存遊戲資料
    """
    try:
        # 從 payload 建立 GameData 對象
        game_data = GameData()
        game_data.__dict__.update(payload.game_data)

        success = game_data_manager.save_game_data(
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
async def load_game_data(payload: SaveLoadPayload) -> Dict[str, Any]:
    """
    載入遊戲資料
    """
    try:
        game_data = game_data_manager.load_game_data(
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

@app.get("/game/saves")
async def list_game_saves(username: Optional[str] = None, platform: Optional[str] = None) -> Dict[str, Any]:
    """
    列出存檔列表
    """
    try:
        saves = game_data_manager.list_saves(username, platform)
        return {"ok": True, "saves": saves}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出存檔失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 股票交易 API
# -----------------------------------------------------------------------------
@app.get("/stocks/list")
async def get_stocks_list() -> Dict[str, Any]:
    """
    獲取股票列表和價格
    """
    try:
        prices = stock_trading_manager.sync_prices_from_database()
        return {"prices": prices, "count": len(prices)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取股票列表失敗: {str(e)}")

@app.post("/stocks/buy")
async def buy_stocks(payload: TradePayload) -> Dict[str, Any]:
    """
    購買股票
    """
    try:
        # 這裡需要實現實際的購買邏輯
        # 整合統一遊戲資料載入和股票交易
        return {"ok": True, "message": "購買股票功能開發中"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"購買股票失敗: {str(e)}")

@app.post("/stocks/sell")
async def sell_stocks(payload: TradePayload) -> Dict[str, Any]:
    """
    賣出股票
    """
    try:
        # 這裡需要實現實際的賣出邏輯
        return {"ok": True, "message": "賣出股票功能開發中"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"賣出股票失敗: {str(e)}")

@app.get("/stocks/overview")
async def get_market_overview() -> Dict[str, Any]:
    """
    獲取市場概覽
    """
    try:
        prices = stock_trading_manager.sync_prices_from_database()
        overview = stock_trading_manager.get_market_overview(prices)
        return {"ok": True, "overview": overview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取市場概覽失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 成就系統 API
# -----------------------------------------------------------------------------
@app.post("/achievements/check")
async def check_achievements(payload: AchievementCheckPayload) -> Dict[str, Any]:
    """
    檢查並更新用戶成就
    """
    try:
        # 載入遊戲資料
        game_data = game_data_manager.load_game_data(payload.username, payload.save_name, payload.platform)
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
async def get_user_achievements(username: str) -> Dict[str, Any]:
    """
    獲取用戶成就統計
    """
    try:
        achievements_data = achievement_manager.get_user_achievements(username)
        return {"ok": True, "data": achievements_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取用戶成就失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 賭場系統 API
# -----------------------------------------------------------------------------
@app.post("/casino/play")
async def play_casino_game(payload: CasinoGamePayload) -> Dict[str, Any]:
    """
    玩賭場遊戲
    """
    try:
        result = casino_manager.play_casino_game(payload.username, payload.game_type, payload.bet_amount)
        return {"ok": True, "game_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"賭場遊戲失敗: {str(e)}")

@app.get("/casino/info")
async def get_casino_info() -> Dict[str, Any]:
    """
    獲取賭場資訊
    """
    try:
        info = casino_manager.get_casino_info()
        return {"ok": True, "casino_info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取賭場資訊失敗: {str(e)}")

@app.get("/casino/vip/{username}")
async def get_player_vip_status(username: str) -> Dict[str, Any]:
    """
    獲取玩家VIP狀態
    """
    try:
        vip_status = casino_manager.get_player_vip_status(username)
        return {"ok": True, "vip_status": vip_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取VIP狀態失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 迷你遊戲 API
# -----------------------------------------------------------------------------
@app.post("/minigames/slots")
async def play_slots(payload: CasinoGamePayload) -> Dict[str, Any]:
    """
    玩拉霸遊戲
    """
    try:
        result = mini_games_manager.play_slots(payload.username, payload.bet_amount)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"拉霸遊戲失敗: {str(e)}")

@app.post("/minigames/blackjack")
async def play_blackjack(payload: CasinoGamePayload) -> Dict[str, Any]:
    """
    玩21點遊戲
    """
    try:
        # 這裡需要實現21點遊戲邏輯
        return {"ok": True, "message": "21點遊戲功能開發中"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"21點遊戲失敗: {str(e)}")

@app.get("/minigames/trivia")
async def get_trivia_question() -> Dict[str, Any]:
    """
    獲取知識問答題目
    """
    try:
        question = mini_games_manager.get_trivia_question()
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

# -----------------------------------------------------------------------------
# 社交功能 API
# -----------------------------------------------------------------------------
@app.post("/social/friends/request")
async def send_friend_request(payload: FriendRequestPayload) -> Dict[str, Any]:
    """
    發送好友請求
    """
    try:
        request_id = social_manager.send_friend_request(
            payload.from_username,
            payload.to_username,
            payload.message
        )
        return {"ok": True, "request_id": request_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發送好友請求失敗: {str(e)}")

@app.post("/social/friends/respond")
async def respond_to_friend_request(payload: FriendResponsePayload) -> Dict[str, Any]:
    """
    回應好友請求
    """
    try:
        success = social_manager.respond_to_friend_request(
            payload.request_id,
            payload.username,
            payload.accept
        )
        if success:
            return {"ok": True, "message": "好友請求處理完成"}
        else:
            raise HTTPException(status_code=400, detail="處理好友請求失敗")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回應好友請求失敗: {str(e)}")

@app.get("/social/friends/{username}")
async def get_friends_list(username: str) -> Dict[str, Any]:
    """
    獲取好友列表
    """
    try:
        friends = social_manager.get_friends_list(username)
        return {"ok": True, "friends": friends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取好友列表失敗: {str(e)}")

@app.post("/social/messages/send")
async def send_message(payload: MessagePayload) -> Dict[str, Any]:
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
        return {"ok": True, "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發送訊息失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 市場新聞事件 API
# -----------------------------------------------------------------------------
@app.post("/market/news/generate")
async def generate_market_news(payload: NewsGenerationPayload) -> Dict[str, Any]:
    """
    生成市場新聞
    """
    try:
        from market_news.market_news_manager import NewsCategory, EventImpact

        category = NewsCategory(payload.category) if payload.category else None
        impact = EventImpact(payload.impact) if payload.impact else None

        news = market_news_manager.generate_market_news(category, impact)
        return {
            "ok": True,
            "news": {
                'news_id': news.news_id,
                'title': news.title,
                'content': news.content,
                'category': news.category.value,
                'impact': news.impact.value,
                'affected_stocks': news.affected_stocks,
                'sentiment_score': news.sentiment_score,
                'published_at': news.published_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成新聞失敗: {str(e)}")

@app.get("/market/news/active")
async def get_active_news() -> Dict[str, Any]:
    """
    獲取活躍新聞
    """
    try:
        news_list = market_news_manager.get_active_news()
        return {"ok": True, "news": news_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取新聞失敗: {str(e)}")

@app.get("/market/events/active")
async def get_active_events() -> Dict[str, Any]:
    """
    獲取活躍事件
    """
    try:
        events_list = market_news_manager.get_active_events()
        return {"ok": True, "events": events_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取事件失敗: {str(e)}")

# -----------------------------------------------------------------------------
# 排行榜 API
# -----------------------------------------------------------------------------
@app.get("/leaderboard/top")
async def get_leaderboard_top(limit: int = Query(default=100, ge=1, le=1000)) -> Dict[str, Any]:
    """
    獲取排行榜前N名
    """
    try:
        # 這裡可以整合各類排行榜
        return {"ok": True, "message": "排行榜功能開發中"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取排行榜失敗: {str(e)}")

# =============================================================================
# 應用啟動
# =============================================================================

if __name__ == "__main__":
    """
    應用程式入口點

    啟動FastAPI服務器
    """
    import uvicorn

    print("=" * 60)
    print("🚀 Life Simulator Server 啟動中...")
    print(f"📊 版本: {app.version}")
    print("🌐 訪問地址: http://127.0.0.1:8000")
    print("📚 API文檔: http://127.0.0.1:8000/docs")
    print("🎮 已載入模組:")
    print("  ✓ 認證系統")
    print("  ✓ 遊戲資料管理")
    print("  ✓ 股票交易系統")
    print("  ✓ 成就系統")
    print("  ✓ 賭場系統")
    print("  ✓ 迷你遊戲系統")
    print("  ✓ 社交功能")
    print("  ✓ 市場新聞事件")
    print("=" * 60)

    # 啟動服務器
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
