import random
import logging
from typing import Dict, List, Tuple, Optional, Any
from game_data import GameData


class UnifiedStockManager:
    """
    統一股票管理系統，整合桌面版和Web版的股票功能
    支援複雜的股票數據結構和跨平台操作
    """

    def __init__(self, db_path: str = None):
        """
        初始化統一股票管理器

        Args:
            db_path: 資料庫路徑，用於Web版價格同步
        """
        self.db_path = db_path
        self._init_stock_universe()

    def _init_stock_universe(self):
        """初始化股票宇宙，與桌面版保持一致"""
        self.stock_universe = {
            'TSMC': {'name': '台積電', 'industry': '科技業', 'initial_price': 100.0},
            'HONHAI': {'name': '鴻海', 'industry': '科技業', 'initial_price': 80.0},
            'MTK': {'name': '聯發科', 'industry': '科技業', 'initial_price': 120.0},
            'MINING': {'name': '挖礦公司', 'industry': '一級產業', 'initial_price': 60.0},
            'FARM': {'name': '農業公司', 'industry': '一級產業', 'initial_price': 50.0},
            'FOREST': {'name': '林業公司', 'industry': '一級產業', 'initial_price': 55.0},
            'RETAIL': {'name': '零售連鎖', 'industry': '服務業', 'initial_price': 70.0},
            'RESTAURANT': {'name': '餐飲集團', 'industry': '服務業', 'initial_price': 65.0},
            'TRAVEL': {'name': '旅遊公司', 'industry': '服務業', 'initial_price': 75.0},
            'BTC': {'name': '比特幣', 'industry': '虛擬貨幣', 'initial_price': 1000000.0}
        }

    def sync_prices_from_database(self) -> Dict[str, float]:
        """
        從資料庫同步價格（用於Web版）

        Returns:
            股票代碼到價格的映射
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT symbol, price FROM stocks")
            rows = cur.fetchall()
            conn.close()

            prices = {row[0]: float(row[1]) for row in rows}
            return prices
        except Exception as e:
            logging.warning(f"無法從資料庫同步價格: {e}")
            return self._get_default_prices()

    def sync_prices_to_database(self, prices: Dict[str, float]):
        """
        將價格同步到資料庫（用於Web版）

        Args:
            prices: 股票代碼到價格的映射
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            for symbol, price in prices.items():
                cur.execute(
                    "UPDATE stocks SET price=? WHERE symbol=?",
                    (price, symbol)
                )

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"無法同步價格到資料庫: {e}")

    def _get_default_prices(self) -> Dict[str, float]:
        """獲取預設價格"""
        return {symbol: data['initial_price'] for symbol, data in self.stock_universe.items()}

    def update_prices_random_walk(self, prices: Dict[str, float],
                                volatility: float = 0.01) -> Dict[str, float]:
        """
        使用隨機漫步更新價格

        Args:
            prices: 當前價格
            volatility: 波動率

        Returns:
            更新後的價格
        """
        updated_prices = {}

        for symbol, current_price in prices.items():
            # 基本隨機漫步
            drift = random.uniform(-volatility, volatility)
            new_price = max(0.01, current_price * (1.0 + drift))
            updated_prices[symbol] = round(new_price, 2)

            # 比特幣特殊處理 - 更高波動率
            if symbol == 'BTC':
                btc_drift = random.uniform(-0.03, 0.03)
                btc_price = max(0.01, current_price * (1.0 + btc_drift))
                updated_prices[symbol] = round(btc_price, 2)

        return updated_prices

    def get_industry_stocks(self, industry: str) -> List[str]:
        """
        獲取特定行業的股票列表

        Args:
            industry: 行業名稱

        Returns:
            股票代碼列表
        """
        return [symbol for symbol, data in self.stock_universe.items()
                if data['industry'] == industry]

    def get_all_industries(self) -> List[str]:
        """獲取所有行業列表"""
        return list(set(data['industry'] for data in self.stock_universe.values()))

    def calculate_portfolio_value(self, holdings: Dict[str, Dict[str, Any]],
                                prices: Dict[str, float]) -> float:
        """
        計算投資組合價值

        Args:
            holdings: 持倉資料 {symbol: {'qty': float, 'avg_cost': float}}
            prices: 當前價格

        Returns:
            總價值
        """
        total_value = 0.0
        for symbol, holding in holdings.items():
            if symbol in prices:
                total_value += holding['qty'] * prices[symbol]
        return total_value

    def calculate_total_gain_loss(self, holdings: Dict[str, Dict[str, Any]],
                                prices: Dict[str, float]) -> Tuple[float, float]:
        """
        計算總收益和損失

        Args:
            holdings: 持倉資料
            prices: 當前價格

        Returns:
            (總收益, 總損失)
        """
        total_gain = 0.0
        total_loss = 0.0

        for symbol, holding in holdings.items():
            if symbol in prices:
                current_value = holding['qty'] * prices[symbol]
                cost_basis = holding['qty'] * holding['avg_cost']
                gain_loss = current_value - cost_basis

                if gain_loss > 0:
                    total_gain += gain_loss
                else:
                    total_loss += abs(gain_loss)

        return total_gain, total_loss

    def get_market_overview(self, prices: Dict[str, float]) -> Dict[str, Any]:
        """
        獲取市場概覽

        Args:
            prices: 當前價格

        Returns:
            市場統計資料
        """
        if not prices:
            return {}

        price_values = list(prices.values())
        industries = {}

        # 按行業統計
        for symbol, price in prices.items():
            industry = self.stock_universe.get(symbol, {}).get('industry', '未知')
            if industry not in industries:
                industries[industry] = []
            industries[industry].append(price)

        industry_avg = {}
        for industry, industry_prices in industries.items():
            industry_avg[industry] = sum(industry_prices) / len(industry_prices)

        return {
            'total_stocks': len(prices),
            'market_avg': sum(price_values) / len(price_values),
            'highest': max(price_values),
            'lowest': min(price_values),
            'industry_avg': industry_avg,
            'gainers': sorted(prices.items(), key=lambda x: x[1], reverse=True)[:5],
            'losers': sorted(prices.items(), key=lambda x: x[1])[:5]
        }

    def validate_trade(self, symbol: str, qty: float, price: float,
                      cash: float, action: str) -> Tuple[bool, str]:
        """
        驗證交易是否有效

        Args:
            symbol: 股票代碼
            qty: 數量
            price: 價格
            cash: 可用現金
            action: 'buy' 或 'sell'

        Returns:
            (是否有效, 錯誤訊息)
        """
        if qty <= 0:
            return False, "數量必須大於0"

        if symbol not in self.stock_universe:
            return False, "無效的股票代碼"

        total_cost = qty * price

        if action == 'buy':
            if total_cost > cash:
                return False, ".2f"".2f"f"現金不足，需要 ${total_cost:.2f}，目前有 ${cash:.2f}"
        elif action == 'sell':
            # 賣出驗證在持有量檢查時進行
            pass
        else:
            return False, "無效的交易動作"

        return True, ""

    def process_buy_order(self, symbol: str, qty: float, price: float,
                         cash: float, holdings: Dict[str, Dict[str, Any]]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        處理買入訂單

        Args:
            symbol: 股票代碼
            qty: 購買數量
            price: 購買價格
            cash: 可用現金
            holdings: 當前持倉

        Returns:
            (成功與否, 訊息, 更新後持倉)
        """
        is_valid, error_msg = self.validate_trade(symbol, qty, price, cash, 'buy')
        if not is_valid:
            return False, error_msg, holdings

        total_cost = qty * price
        new_holdings = holdings.copy()

        if symbol in new_holdings:
            # 計算新的平均成本
            current_qty = new_holdings[symbol]['qty']
            current_cost = new_holdings[symbol]['avg_cost']
            new_qty = current_qty + qty
            new_avg_cost = (current_qty * current_cost + qty * price) / new_qty

            new_holdings[symbol] = {
                'qty': new_qty,
                'avg_cost': new_avg_cost
            }
        else:
            new_holdings[symbol] = {
                'qty': qty,
                'avg_cost': price
            }

        return True, ".2f", new_holdings

    def process_sell_order(self, symbol: str, qty: float, price: float,
                          holdings: Dict[str, Dict[str, Any]]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        處理賣出訂單

        Args:
            symbol: 股票代碼
            qty: 賣出數量
            price: 賣出價格
            holdings: 當前持倉

        Returns:
            (成功與否, 訊息, 更新後持倉)
        """
        if symbol not in holdings:
            return False, "沒有持有該股票", holdings

        current_qty = holdings[symbol]['qty']
        if qty > current_qty:
            return False, ".0f"".0f"f"持有股票不足，需要 {qty:.0f} 股，目前持有 {current_qty:.0f} 股", holdings

        new_holdings = holdings.copy()
        proceeds = qty * price

        if qty >= current_qty:
            # 全部賣出
            del new_holdings[symbol]
        else:
            # 部分賣出
            new_holdings[symbol] = {
                'qty': current_qty - qty,
                'avg_cost': holdings[symbol]['avg_cost']  # 平均成本保持不變
            }

        return True, ".2f", new_holdings

    def get_recommendations(self, holdings: Dict[str, Dict[str, Any]],
                          prices: Dict[str, float], cash: float) -> List[Dict[str, Any]]:
        """
        獲取投資建議

        Args:
            holdings: 當前持倉
            prices: 當前價格
            cash: 可用現金

        Returns:
            建議列表
        """
        recommendations = []

        # 簡單的建議邏輯
        total_value = self.calculate_portfolio_value(holdings, prices)
        total_portfolio = total_value + cash

        if total_portfolio < 10000:
            recommendations.append({
                'type': 'buy',
                'symbol': 'TSMC',
                'reason': '建議從穩定科技股開始投資'
            })

        # 檢查是否有過度集中的持倉
        if holdings:
            max_holding = max(holding['qty'] * prices.get(symbol, 0)
                            for symbol, holding in holdings.items())
            if max_holding > total_value * 0.5:
                recommendations.append({
                    'type': 'diversify',
                    'reason': '建議分散投資，降低風險'
                })

        return recommendations
