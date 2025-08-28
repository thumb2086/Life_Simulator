"""
Life Simulator Server - 股票交易模組
處理股票買賣、市場數據和投資組合管理
"""

import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from fastapi import HTTPException
from pydantic import BaseModel


class TradeRequest(BaseModel):
    """交易請求模型"""
    username: str
    symbol: str
    qty: float
    action: str  # 'buy' 或 'sell'


class AdvancedTradeRequest(BaseModel):
    """高級交易請求模型"""
    username: str
    symbol: str
    qty: float
    action: str
    price: Optional[float] = None


class StockTradingManager:
    """
    股票交易管理器
    負責股票買賣、市場數據和投資組合管理
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_stock_database()

    def _init_stock_database(self):
        """初始化股票資料庫"""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 股票表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    price REAL NOT NULL,
                    name TEXT,
                    industry TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 用戶投資組合表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    username TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    qty REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (username, symbol)
                )
            """)

            # 交易記錄表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    qty REAL NOT NULL,
                    price REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

        finally:
            conn.close()

    def _get_db_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def sync_prices_from_database(self) -> Dict[str, float]:
        """
        從資料庫同步價格

        Returns:
            股票價格字典
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT symbol, price FROM stocks")
            rows = cur.fetchall()

            prices = {}
            for row in rows:
                prices[row['symbol']] = float(row['price'])

            return prices

        finally:
            conn.close()

    def sync_prices_to_database(self, prices: Dict[str, float]):
        """
        同步價格到資料庫

        Args:
            prices: 股票價格字典
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            for symbol, price in prices.items():
                cur.execute("""
                    INSERT OR REPLACE INTO stocks (symbol, price, last_updated)
                    VALUES (?, ?, ?)
                """, (symbol, price, datetime.now()))

            conn.commit()

        finally:
            conn.close()

    def get_market_overview(self, prices: Dict[str, float]) -> Dict[str, Any]:
        """
        獲取市場概覽

        Args:
            prices: 當前價格字典

        Returns:
            市場統計資料
        """
        if not prices:
            return {}

        prices_list = list(prices.values())
        total_market_cap = sum(prices_list)

        return {
            'total_stocks': len(prices),
            'total_market_cap': total_market_cap,
            'average_price': sum(prices_list) / len(prices_list),
            'highest_price': max(prices_list),
            'lowest_price': min(prices_list),
            'price_range': max(prices_list) - min(prices_list)
        }

    def get_all_industries(self) -> List[str]:
        """
        獲取所有行業列表

        Returns:
            行業列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT industry FROM stocks WHERE industry IS NOT NULL")
            rows = cur.fetchall()

            return [row['industry'] for row in rows]

        finally:
            conn.close()

    def get_industry_stocks(self, industry: str) -> List[str]:
        """
        獲取特定行業的股票

        Args:
            industry: 行業名稱

        Returns:
            股票代碼列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT symbol FROM stocks WHERE industry = ?", (industry,))
            rows = cur.fetchall()

            return [row['symbol'] for row in rows]

        finally:
            conn.close()

    def calculate_portfolio_value(self, holdings: Dict[str, Dict[str, Any]], prices: Dict[str, float]) -> float:
        """
        計算投資組合價值

        Args:
            holdings: 持有股票字典
            prices: 當前價格字典

        Returns:
            投資組合總價值
        """
        total_value = 0.0

        for symbol, stock_data in holdings.items():
            qty = stock_data.get('qty', 0)
            if symbol in prices and qty > 0:
                total_value += qty * prices[symbol]

        return total_value

    def calculate_total_gain_loss(self, holdings: Dict[str, Dict[str, Any]], prices: Dict[str, float]) -> Tuple[float, float]:
        """
        計算總收益和損失

        Args:
            holdings: 持有股票字典
            prices: 當前價格字典

        Returns:
            (總收益, 總損失)
        """
        total_gain = 0.0
        total_loss = 0.0

        for symbol, stock_data in holdings.items():
            qty = stock_data.get('qty', 0)
            avg_cost = stock_data.get('avg_cost', 0)

            if symbol in prices and qty > 0:
                current_value = qty * prices[symbol]
                cost_basis = qty * avg_cost

                difference = current_value - cost_basis
                if difference > 0:
                    total_gain += difference
                else:
                    total_loss += abs(difference)

        return total_gain, total_loss

    def process_buy_order(self, symbol: str, qty: float, price: float, cash_available: float,
                         current_holdings: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        處理買入訂單

        Args:
            symbol: 股票代碼
            qty: 數量
            price: 價格
            cash_available: 可用現金
            current_holdings: 當前持有股票

        Returns:
            (成功, 訊息, 更新後持有股票)
        """
        cost = price * qty

        # 檢查現金是否足夠
        if cash_available < cost:
            return False, f"現金不足，需要 ${cost:.2f}，目前有 ${cash_available:.2f}", current_holdings

        # 更新持有股票
        updated_holdings = current_holdings.copy()

        if symbol in updated_holdings:
            # 計算新的平均成本
            current_qty = updated_holdings[symbol]['owned']
            current_avg_cost = updated_holdings[symbol]['total_cost'] / current_qty

            new_qty = current_qty + qty
            new_avg_cost = (current_qty * current_avg_cost + cost) / new_qty

            updated_holdings[symbol]['owned'] = new_qty
            updated_holdings[symbol]['total_cost'] = new_qty * new_avg_cost
        else:
            # 新建持有記錄
            updated_holdings[symbol] = {
                'owned': qty,
                'total_cost': cost
            }

        return True, f"成功購買 {qty} 股 {symbol}", updated_holdings

    def get_recommendations(self, holdings: Dict[str, Dict[str, Any]], prices: Dict[str, float],
                          available_cash: float) -> List[Dict[str, Any]]:
        """
        獲取投資建議

        Args:
            holdings: 當前持有股票
            prices: 當前價格
            available_cash: 可用現金

        Returns:
            投資建議列表
        """
        recommendations = []

        # 簡單的推薦邏輯
        portfolio_value = self.calculate_portfolio_value(holdings, prices)
        total_investment = portfolio_value + available_cash

        # 建議分散投資
        if len(holdings) < 3 and available_cash > 1000:
            recommendations.append({
                'type': 'diversification',
                'action': 'buy',
                'symbol': 'TSMC',  # 建議買入台積電
                'reason': '建議分散投資組合，增加持股種類',
                'suggested_amount': min(available_cash * 0.2, 2000)
            })

        # 建議止損
        for symbol, stock_data in holdings.items():
            qty = stock_data.get('qty', 0)
            avg_cost = stock_data.get('avg_cost', 0)

            if symbol in prices and qty > 0:
                current_price = prices[symbol]
                loss_percentage = (avg_cost - current_price) / avg_cost

                if loss_percentage > 0.1:  # 損失超過10%
                    recommendations.append({
                        'type': 'stop_loss',
                        'action': 'sell',
                        'symbol': symbol,
                        'reason': f'建議止損，當前損失 {loss_percentage:.1%}',
                        'suggested_qty': qty * 0.5  # 賣出一半
                    })

        return recommendations

    def update_prices_random_walk(self, current_prices: Dict[str, float], volatility: float = 0.03) -> Dict[str, float]:
        """
        使用隨機漫步更新價格

        Args:
            current_prices: 當前價格字典
            volatility: 波動率

        Returns:
            更新後的價格字典
        """
        updated_prices = {}

        for symbol, price in current_prices.items():
            # 隨機價格變動
            change = random.uniform(-volatility, volatility)
            new_price = max(0.01, price * (1 + change))
            updated_prices[symbol] = round(new_price, 2)

        return updated_prices

    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        獲取股票歷史價格

        Args:
            symbol: 股票代碼
            days: 歷史天數

        Returns:
            歷史價格列表
        """
        # 這個方法需要更複雜的實現來存儲歷史價格
        # 目前返回模擬數據
        import random
        from datetime import timedelta

        history = []
        base_price = 100.0  # 基準價格

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            price_change = random.uniform(-0.05, 0.05)
            price = base_price * (1 + price_change)
            base_price = price  # 更新基準價格

            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(price, 2),
                'change': round(price_change * 100, 2)
            })

        return history[::-1]  # 反轉順序，最舊到最新

    def get_portfolio_analysis(self, username: str) -> Dict[str, Any]:
        """
        獲取投資組合分析

        Args:
            username: 用戶名

        Returns:
            投資組合分析報告
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 獲取用戶投資組合
            cur.execute("""
                SELECT symbol, qty, avg_cost
                FROM portfolios
                WHERE username = ?
            """, (username,))

            holdings = {}
            for row in cur.fetchall():
                holdings[row['symbol']] = {
                    'qty': float(row['qty']),
                    'avg_cost': float(row['avg_cost'])
                }

            # 獲取當前價格
            prices = self.sync_prices_from_database()

            # 計算分析數據
            portfolio_value = self.calculate_portfolio_value(holdings, prices)
            total_gain, total_loss = self.calculate_total_gain_loss(holdings, prices)

            # 計算投資組合組成
            portfolio_composition = {}
            for symbol, data in holdings.items():
                if symbol in prices:
                    value = data['qty'] * prices[symbol]
                    portfolio_composition[symbol] = {
                        'quantity': data['qty'],
                        'current_price': prices[symbol],
                        'value': value,
                        'percentage': (value / portfolio_value * 100) if portfolio_value > 0 else 0
                    }

            return {
                'portfolio_value': portfolio_value,
                'total_gain': total_gain,
                'total_loss': total_loss,
                'net_gain_loss': total_gain - total_loss,
                'holdings_count': len(holdings),
                'portfolio_composition': portfolio_composition,
                'analysis_date': datetime.now().isoformat()
            }

        finally:
            conn.close()

    def get_market_trends(self) -> Dict[str, Any]:
        """
        獲取市場趨勢分析

        Returns:
            市場趨勢數據
        """
        prices = self.sync_prices_from_database()

        if not prices:
            return {}

        # 計算趨勢指標
        prices_list = list(prices.values())
        avg_price = sum(prices_list) / len(prices_list)

        # 分類股票表現
        outperforming = []
        underperforming = []

        for symbol, price in prices.items():
            performance = (price - avg_price) / avg_price
            if performance > 0.05:  # 優於平均5%以上
                outperforming.append(symbol)
            elif performance < -0.05:  # 低於平均5%以上
                underperforming.append(symbol)

        return {
            'market_average': avg_price,
            'total_stocks': len(prices),
            'outperforming_stocks': outperforming,
            'underperforming_stocks': underperforming,
            'market_sentiment': 'bullish' if len(outperforming) > len(underperforming) else 'bearish',
            'analysis_timestamp': datetime.now().isoformat()
        }
