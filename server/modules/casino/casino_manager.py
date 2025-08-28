"""
Life Simulator Server - 賭場模組
整合進階賭場系統，提供完整的賭場體驗
"""

from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from pydantic import BaseModel

from modules.advanced_casino import AdvancedCasinoManager


class CasinoGameRequest(BaseModel):
    """賭場遊戲請求模型"""
    username: str
    game_type: str  # slots, blackjack, roulette, baccarat, dice, enhanced_slots
    bet_amount: float
    kwargs: Any  # 遊戲特定參數


class CasinoManager:
    """
    賭場管理器
    整合所有賭場功能，提供統一的賭場介面
    """

    def __init__(self, data_manager, db_path: str):
        self.data_manager = data_manager
        self.advanced_casino = AdvancedCasinoManager(data_manager, db_path)

    def play_casino_game(self, username: str, game_type: str, bet_amount: float, **kwargs) -> Dict[str, Any]:
        """
        玩賭場遊戲

        Args:
            username: 玩家用戶名
            game_type: 遊戲類型
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
                raise HTTPException(status_code=400, detail="不支援的賭場遊戲類型")

            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"賭場遊戲失敗: {str(e)}")

    def get_casino_info(self) -> Dict[str, Any]:
        """
        獲取賭場資訊

        Returns:
            賭場資訊
        """
        return self.advanced_casino.get_progressive_jackpots()

    def get_player_vip_status(self, username: str) -> Dict[str, Any]:
        """
        獲取玩家VIP狀態

        Args:
            username: 用戶名

        Returns:
            VIP狀態資訊
        """
        vip_level = self.advanced_casino.get_vip_level(username)
        perks = self.advanced_casino.get_vip_perks(vip_level)
        stats = self.advanced_casino.get_casino_stats(username)

        return {
            "vip_level": vip_level.value,
            "perks": perks,
            "stats": stats
        }

    def get_casino_stats(self, username: str) -> Dict[str, Any]:
        """
        獲取玩家賭場統計

        Args:
            username: 用戶名

        Returns:
            賭場統計資料
        """
        return self.advanced_casino.get_casino_stats(username)

    def get_progressive_jackpots(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取累積獎池資訊

        Returns:
            獎池資訊
        """
        return self.advanced_casino.get_progressive_jackpots()

    def get_casino_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取賭場排行榜

        Args:
            limit: 返回記錄數量限制

        Returns:
            排行榜數據
        """
        # 這裡需要實現排行榜邏輯
        # 目前返回空的排行榜
        return []

    def get_available_games(self) -> Dict[str, Any]:
        """
        獲取可用的賭場遊戲

        Returns:
            遊戲列表
        """
        return {
            "slots": {
                "name": "拉霸機",
                "description": "經典三滾輪拉霸遊戲",
                "min_bet": 10,
                "max_bet": 1000,
                "rtp": 0.95  # Return to Player
            },
            "enhanced_slots": {
                "name": "豪華拉霸機",
                "description": "五滾輪豪華拉霸，支援累積獎池",
                "min_bet": 50,
                "max_bet": 5000,
                "rtp": 0.92,
                "features": ["progressive_jackpot", "bonus_rounds"]
            },
            "blackjack": {
                "name": "21點",
                "description": "經典21點遊戲",
                "min_bet": 25,
                "max_bet": 2500,
                "rtp": 0.995
            },
            "roulette": {
                "name": "俄羅斯輪盤",
                "description": "歐洲式輪盤遊戲",
                "min_bet": 10,
                "max_bet": 1000,
                "rtp": 0.973
            },
            "baccarat": {
                "name": "百家樂",
                "description": "經典百家樂遊戲",
                "min_bet": 100,
                "max_bet": 10000,
                "rtp": 0.988
            },
            "dice": {
                "name": "骰子遊戲",
                "description": "多種骰子遊戲選擇",
                "min_bet": 5,
                "max_bet": 500,
                "rtp": 0.98
            }
        }

    def calculate_house_edge(self, game_type: str) -> float:
        """
        計算莊家優勢

        Args:
            game_type: 遊戲類型

        Returns:
            莊家優勢百分比
        """
        house_edges = {
            "slots": 0.05,          # 5%
            "enhanced_slots": 0.08, # 8%
            "blackjack": 0.005,     # 0.5%
            "roulette": 0.027,      # 2.7%
            "baccarat": 0.012,      # 1.2%
            "dice": 0.02           # 2%
        }

        return house_edges.get(game_type, 0.05)

    def get_game_rules(self, game_type: str) -> Dict[str, Any]:
        """
        獲取遊戲規則

        Args:
            game_type: 遊戲類型

        Returns:
            遊戲規則說明
        """
        rules = {
            "slots": {
                "objective": "匹配相同的符號獲得獎金",
                "symbols": ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"],
                "payouts": {
                    "3_same": "2-100x",
                    "4_same": "5-200x",
                    "5_same": "10-1000x"
                }
            },
            "blackjack": {
                "objective": "點數接近21點但不超過",
                "card_values": {
                    "2-10": "面值",
                    "J,Q,K": "10點",
                    "A": "1或11點"
                },
                "rules": [
                    "莊家必須在17點或以上停牌",
                    "21點自動獲勝",
                    "超過21點爆牌"
                ]
            },
            "roulette": {
                "objective": "預測輪盤停下的數字或顏色",
                "wheel": "歐洲輪盤：0-36 + 綠色0",
                "bets": [
                    "單一數字 (35:1)",
                    "分隔 (17:1)",
                    "街注 (11:1)",
                    "角注 (8:1)",
                    "紅黑 (1:1)",
                    "單雙 (1:1)"
                ]
            },
            "baccarat": {
                "objective": "預測莊家或閒家獲勝",
                "card_values": "A=1, 2-9=面值, 10,J,Q,K=0",
                "rules": [
                    "前兩張牌點數相加取個位數",
                    "第三張牌規則取決於前兩張點數",
                    "最接近9點獲勝"
                ]
            },
            "dice": {
                "seven_eleven": {
                    "objective": "預測擲出7或11",
                    "payout": "1:1",
                    "house_edge": "16.67%"
                },
                "craps": {
                    "objective": "預測點數",
                    "payout": "5:1",
                    "house_edge": "16.67%"
                }
            }
        }

        return rules.get(game_type, {})

    def get_casino_tips(self) -> List[str]:
        """
        獲取賭場遊戲技巧

        Returns:
            遊戲技巧列表
        """
        return [
            "💰 設定預算：永遠不要賭你輸不起的錢",
            "🎯 了解規則：熟悉每種遊戲的規則和賠率",
            "📊 管理資金：使用資金管理策略",
            "⏰ 設定時間：不要玩太久，適時休息",
            "🎲 享受樂趣：賭博應該是娛樂，不是賺錢的方式",
            "🏆 知道何時停手：設定獲勝和損失限額",
            "📈 學習RTP：選擇回報率高的遊戲",
            "🎮 從小額開始：熟悉遊戲再增加賭注"
        ]

    def get_responsible_gaming_info(self) -> Dict[str, Any]:
        """
        獲取負責任遊戲資訊

        Returns:
            負責任遊戲資訊
        """
        return {
            "hotline": "賭博問題求助熱線：0800-000-000",
            "resources": [
                "認識賭博問題",
                "自我評估工具",
                "專業諮詢服務",
                "支援團體"
            ],
            "tips": [
                "定期檢查自己的賭博習慣",
                "如果感到失控，立即尋求幫助",
                "設定存款限額",
                "不要為了輸錢而繼續賭博",
                "平衡娛樂與現實生活"
            ],
            "warning_signs": [
                "賭博花費超過預算",
                "為了賭博而借錢",
                "隱瞞賭博行為",
                "影響工作或人際關係",
                "無法控制賭博衝動"
            ]
        }
