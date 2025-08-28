import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

from game_data import GameData
from unified_stock_manager import UnifiedStockManager


class RiskTolerance(Enum):
    """風險承受度"""
    CONSERVATIVE = "conservative"  # 保守型
    MODERATE = "moderate"         # 穩健型
    AGGRESSIVE = "aggressive"     # 進取型


class InvestmentStrategy(Enum):
    """投資策略"""
    BUY_AND_HOLD = "buy_and_hold"     # 買入持有
    VALUE_INVESTING = "value_investing" # 價值投資
    GROWTH_INVESTING = "growth_investing" # 成長投資
    DIVIDEND_INVESTING = "dividend_investing" # 股息投資
    MOMENTUM_TRADING = "momentum_trading" # 動量交易
    MEAN_REVERSION = "mean_reversion" # 均值回歸


class MarketCondition(Enum):
    """市場狀況"""
    BULL_MARKET = "bull_market"     # 多頭市場
    BEAR_MARKET = "bear_market"     # 空頭市場
    SIDEWAYS = "sideways"          # 橫盤整理
    VOLATILE = "volatile"          # 高波動


@dataclass
class InvestmentRecommendation:
    """投資建議"""
    recommendation_id: str
    username: str
    strategy: InvestmentStrategy
    risk_tolerance: RiskTolerance
    recommended_stocks: List[Dict[str, Any]]
    expected_return: float  # 預期年化報酬率
    expected_risk: float    # 預期風險
    confidence_score: float # 信心分數 (0-1)
    reasoning: str
    created_at: datetime
    valid_until: datetime


@dataclass
class PortfolioAnalysis:
    """投資組合分析"""
    analysis_id: str
    username: str
    total_value: float
    total_cost: float
    unrealized_gain_loss: float
    gain_loss_percentage: float
    diversification_score: float  # 多元化分數 (0-1)
    risk_score: float            # 風險分數 (0-1)
    sector_allocation: Dict[str, float]  # 行業配置
    top_performers: List[Dict[str, Any]]
    underperformers: List[Dict[str, Any]]
    recommendations: List[str]
    analyzed_at: datetime


@dataclass
class MarketPrediction:
    """市場預測"""
    prediction_id: str
    asset_type: str  # stock, index, commodity
    asset_symbol: str
    prediction_type: str  # price, trend, volatility
    predicted_value: float
    confidence: float
    time_horizon: str  # short_term, medium_term, long_term
    factors: List[str]
    created_at: datetime


class AITechnicalAnalyzer:
    """AI技術分析器"""

    def __init__(self, stock_manager: UnifiedStockManager):
        self.stock_manager = stock_manager

    def analyze_stock_trend(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """分析股票趨勢"""
        # 簡化版：基於隨機波動模擬趨勢分析
        trend = random.choice(['bullish', 'bearish', 'neutral'])
        strength = random.uniform(0.1, 0.9)

        return {
            'symbol': symbol,
            'trend': trend,
            'strength': strength,
            'momentum': random.uniform(-0.5, 0.5),
            'volatility': random.uniform(0.01, 0.05),
            'support_level': random.uniform(50, 150),
            'resistance_level': random.uniform(150, 250)
        }

    def calculate_rsi(self, symbol: str) -> float:
        """計算RSI指標"""
        return random.uniform(20, 80)

    def calculate_moving_average(self, symbol: str, period: int) -> float:
        """計算移動平均線"""
        current_price = self.stock_manager.sync_prices_from_database().get(symbol, 100)
        return current_price * random.uniform(0.9, 1.1)

    def detect_support_resistance(self, symbol: str) -> Tuple[float, float]:
        """檢測支撐和阻力位"""
        current_price = self.stock_manager.sync_prices_from_database().get(symbol, 100)
        support = current_price * random.uniform(0.8, 0.95)
        resistance = current_price * random.uniform(1.05, 1.2)
        return support, resistance


class AIFundamentalAnalyzer:
    """AI基本面分析器"""

    def __init__(self, stock_manager: UnifiedStockManager):
        self.stock_manager = stock_manager

    def analyze_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """分析基本面"""
        return {
            'symbol': symbol,
            'pe_ratio': random.uniform(10, 30),
            'pb_ratio': random.uniform(0.5, 3.0),
            'dividend_yield': random.uniform(0, 0.05),
            'revenue_growth': random.uniform(-0.1, 0.2),
            'earnings_growth': random.uniform(-0.1, 0.25),
            'debt_to_equity': random.uniform(0.1, 1.5),
            'roe': random.uniform(0.05, 0.25),
            'rating': random.choice(['BUY', 'HOLD', 'SELL'])
        }

    def calculate_intrinsic_value(self, symbol: str) -> float:
        """計算內在價值"""
        current_price = self.stock_manager.sync_prices_from_database().get(symbol, 100)
        return current_price * random.uniform(0.8, 1.3)


class AIMarketPredictor:
    """AI市場預測器"""

    def __init__(self, stock_manager: UnifiedStockManager):
        self.stock_manager = stock_manager

    def predict_market_condition(self) -> MarketCondition:
        """預測市場狀況"""
        return random.choice(list(MarketCondition))

    def predict_stock_price(self, symbol: str, days_ahead: int) -> MarketPrediction:
        """預測股票價格"""
        current_price = self.stock_manager.sync_prices_from_database().get(symbol, 100)
        predicted_price = current_price * random.uniform(0.9, 1.1)

        prediction_id = f"pred_{int(datetime.now().timestamp())}_{symbol}"

        return MarketPrediction(
            prediction_id=prediction_id,
            asset_type="stock",
            asset_symbol=symbol,
            prediction_type="price",
            predicted_value=predicted_price,
            confidence=random.uniform(0.4, 0.8),
            time_horizon="short_term" if days_ahead <= 7 else "medium_term",
            factors=["technical_analysis", "market_sentiment", "sector_performance"],
            created_at=datetime.now()
        )

    def generate_market_outlook(self) -> Dict[str, Any]:
        """生成市場展望"""
        condition = self.predict_market_condition()

        outlook = {
            'condition': condition.value,
            'confidence': random.uniform(0.5, 0.8),
            'key_drivers': random.sample([
                "經濟數據", "央行政策", "地緣政治", "企業獲利",
                "利率環境", "通貨膨脹", "就業市場", "國際貿易"
            ], 3),
            'sector_outlook': {
                '科技業': random.choice(['正面', '中性', '負面']),
                '金融業': random.choice(['正面', '中性', '負面']),
                '消費業': random.choice(['正面', '中性', '負面']),
                '工業': random.choice(['正面', '中性', '負面'])
            },
            'risk_assessment': random.choice(['低風險', '中風險', '高風險']),
            'time_horizon': random.choice(['短期', '中期', '長期'])
        }

        return outlook


class AIInvestmentAdvisor:
    """
    AI投資顧問系統
    提供智能投資建議和策略分析
    """

    def __init__(self, stock_manager: UnifiedStockManager):
        self.stock_manager = stock_manager
        self.technical_analyzer = AITechnicalAnalyzer(stock_manager)
        self.fundamental_analyzer = AIFundamentalAnalyzer(stock_manager)
        self.market_predictor = AIMarketPredictor(stock_manager)

    def assess_risk_tolerance(self, game_data: GameData) -> RiskTolerance:
        """評估風險承受度"""
        # 基於遊戲資料分析風險承受度
        age_in_game = game_data.days // 365  # 遊戲中的年齡

        # 簡單的風險評估邏輯
        if age_in_game < 2:
            return RiskTolerance.CONSERVATIVE
        elif age_in_game < 5:
            return RiskTolerance.MODERATE
        else:
            return RiskTolerance.AGGRESSIVE

    def analyze_portfolio(self, username: str, game_data: GameData) -> PortfolioAnalysis:
        """分析投資組合"""
        analysis_id = f"analysis_{int(datetime.now().timestamp())}_{username}"

        # 計算投資組合數據
        holdings = game_data.stocks if hasattr(game_data, 'stocks') else {}
        prices = self.stock_manager.sync_prices_from_database()

        total_value = 0
        total_cost = 0
        sector_allocation = {}

        for symbol, stock_data in holdings.items():
            if stock_data.get('owned', 0) > 0:
                quantity = stock_data['owned']
                current_price = prices.get(symbol, 0)
                avg_cost = stock_data.get('total_cost', 0) / quantity if quantity > 0 else 0

                total_value += quantity * current_price
                total_cost += quantity * avg_cost

                # 分類行業
                industry = self.stock_manager.stock_universe.get(symbol, {}).get('industry', '其他')
                if industry not in sector_allocation:
                    sector_allocation[industry] = 0
                sector_allocation[industry] += quantity * current_price

        # 計算未實現損益
        unrealized_gain_loss = total_value - total_cost
        gain_loss_percentage = (unrealized_gain_loss / total_cost * 100) if total_cost > 0 else 0

        # 計算多元化分數
        stock_count = sum(1 for stock in holdings.values() if stock.get('owned', 0) > 0)
        diversification_score = min(stock_count / 10, 1.0)  # 最多10檔股票得滿分

        # 計算風險分數（基於波動率）
        risk_score = random.uniform(0.1, 0.8)  # 簡化版

        # 行業配置百分比
        total_portfolio_value = sum(sector_allocation.values())
        if total_portfolio_value > 0:
            sector_allocation = {k: v/total_portfolio_value for k, v in sector_allocation.items()}

        # 找出表現最佳和最差的股票
        stock_performance = []
        for symbol, stock_data in holdings.items():
            if stock_data.get('owned', 0) > 0:
                quantity = stock_data['owned']
                current_price = prices.get(symbol, 0)
                avg_cost = stock_data.get('total_cost', 0) / quantity if quantity > 0 else 0

                if avg_cost > 0:
                    performance = (current_price - avg_cost) / avg_cost * 100
                    stock_performance.append({
                        'symbol': symbol,
                        'performance': performance,
                        'current_value': quantity * current_price
                    })

        stock_performance.sort(key=lambda x: x['performance'], reverse=True)
        top_performers = stock_performance[:3] if len(stock_performance) >= 3 else stock_performance
        underperformers = stock_performance[-3:] if len(stock_performance) >= 3 else []

        # 生成建議
        recommendations = self._generate_portfolio_recommendations(
            diversification_score, risk_score, stock_performance
        )

        return PortfolioAnalysis(
            analysis_id=analysis_id,
            username=username,
            total_value=total_value,
            total_cost=total_cost,
            unrealized_gain_loss=unrealized_gain_loss,
            gain_loss_percentage=gain_loss_percentage,
            diversification_score=diversification_score,
            risk_score=risk_score,
            sector_allocation=sector_allocation,
            top_performers=top_performers,
            underperformers=underperformers,
            recommendations=recommendations,
            analyzed_at=datetime.now()
        )

    def generate_investment_recommendation(self, username: str, game_data: GameData) -> InvestmentRecommendation:
        """生成投資建議"""
        recommendation_id = f"rec_{int(datetime.now().timestamp())}_{username}"

        # 評估風險承受度
        risk_tolerance = self.assess_risk_tolerance(game_data)

        # 確定投資策略
        strategy = self._determine_optimal_strategy(game_data, risk_tolerance)

        # 基於策略生成股票建議
        recommended_stocks = self._generate_stock_recommendations(strategy, risk_tolerance, game_data)

        # 計算預期報酬和風險
        expected_return, expected_risk = self._calculate_expected_performance(recommended_stocks, strategy)

        # 生成理由
        reasoning = self._generate_recommendation_reasoning(strategy, risk_tolerance, recommended_stocks)

        # 信心分數
        confidence_score = random.uniform(0.6, 0.9)

        return InvestmentRecommendation(
            recommendation_id=recommendation_id,
            username=username,
            strategy=strategy,
            risk_tolerance=risk_tolerance,
            recommended_stocks=recommended_stocks,
            expected_return=expected_return,
            expected_risk=expected_risk,
            confidence_score=confidence_score,
            reasoning=reasoning,
            created_at=datetime.now(),
            valid_until=datetime.now() + timedelta(days=7)
        )

    def get_market_insights(self) -> Dict[str, Any]:
        """獲取市場洞察"""
        market_outlook = self.market_predictor.generate_market_outlook()

        # 生成熱門股票
        prices = self.stock_manager.sync_prices_from_database()
        popular_stocks = random.sample(list(prices.keys()), min(5, len(prices)))

        hot_stocks = []
        for symbol in popular_stocks:
            analysis = self.technical_analyzer.analyze_stock_trend(symbol)
            fundamentals = self.fundamental_analyzer.analyze_fundamentals(symbol)

            hot_stocks.append({
                'symbol': symbol,
                'name': self.stock_manager.stock_universe.get(symbol, {}).get('name', symbol),
                'current_price': prices[symbol],
                'trend': analysis['trend'],
                'rating': fundamentals['rating'],
                'pe_ratio': fundamentals['pe_ratio'],
                'dividend_yield': fundamentals['dividend_yield']
            })

        return {
            'market_outlook': market_outlook,
            'hot_stocks': hot_stocks,
            'sector_performance': market_outlook['sector_outlook'],
            'investment_opportunities': self._identify_opportunities(),
            'risk_warnings': self._generate_risk_warnings()
        }

    def _determine_optimal_strategy(self, game_data: GameData, risk_tolerance: RiskTolerance) -> InvestmentStrategy:
        """確定最佳投資策略"""
        # 基於風險承受度和遊戲狀態確定策略
        if risk_tolerance == RiskTolerance.CONSERVATIVE:
            return InvestmentStrategy.DIVIDEND_INVESTING
        elif risk_tolerance == RiskTolerance.MODERATE:
            return InvestmentStrategy.VALUE_INVESTING
        else:
            return InvestmentStrategy.GROWTH_INVESTING

    def _generate_stock_recommendations(self, strategy: InvestmentStrategy,
                                      risk_tolerance: RiskTolerance,
                                      game_data: GameData) -> List[Dict[str, Any]]:
        """生成股票建議"""
        stocks = []
        available_stocks = list(self.stock_manager.stock_universe.keys())

        # 根據策略篩選股票
        if strategy == InvestmentStrategy.DIVIDEND_INVESTING:
            # 高股息股票
            for symbol in available_stocks[:3]:
                fundamentals = self.fundamental_analyzer.analyze_fundamentals(symbol)
                stocks.append({
                    'symbol': symbol,
                    'name': self.stock_manager.stock_universe[symbol]['name'],
                    'allocation': random.uniform(0.2, 0.4),
                    'reason': f"高股息收益率 {fundamentals['dividend_yield']:.1%}",
                    'confidence': random.uniform(0.7, 0.9)
                })

        elif strategy == InvestmentStrategy.VALUE_INVESTING:
            # 價值型股票
            for symbol in available_stocks[3:6]:
                fundamentals = self.fundamental_analyzer.analyze_fundamentals(symbol)
                stocks.append({
                    'symbol': symbol,
                    'name': self.stock_manager.stock_universe[symbol]['name'],
                    'allocation': random.uniform(0.15, 0.3),
                    'reason': f"低估值，PB比率 {fundamentals['pb_ratio']:.2f}",
                    'confidence': random.uniform(0.6, 0.85)
                })

        else:  # Growth Investing
            # 成長型股票
            for symbol in available_stocks[6:9]:
                fundamentals = self.fundamental_analyzer.analyze_fundamentals(symbol)
                stocks.append({
                    'symbol': symbol,
                    'name': self.stock_manager.stock_universe[symbol]['name'],
                    'allocation': random.uniform(0.1, 0.25),
                    'reason': f"高成長潛力，營收成長 {fundamentals['revenue_growth']:.1%}",
                    'confidence': random.uniform(0.5, 0.8)
                })

        return stocks

    def _calculate_expected_performance(self, stocks: List[Dict[str, Any]],
                                      strategy: InvestmentStrategy) -> Tuple[float, float]:
        """計算預期表現"""
        # 簡化的預期報酬和風險計算
        base_return = {
            InvestmentStrategy.DIVIDEND_INVESTING: 0.06,
            InvestmentStrategy.VALUE_INVESTING: 0.08,
            InvestmentStrategy.GROWTH_INVESTING: 0.12
        }.get(strategy, 0.08)

        base_risk = {
            InvestmentStrategy.DIVIDEND_INVESTING: 0.08,
            InvestmentStrategy.VALUE_INVESTING: 0.12,
            InvestmentStrategy.GROWTH_INVESTING: 0.18
        }.get(strategy, 0.12)

        # 加入隨機變化
        expected_return = base_return * random.uniform(0.8, 1.2)
        expected_risk = base_risk * random.uniform(0.9, 1.1)

        return expected_return, expected_risk

    def _generate_recommendation_reasoning(self, strategy: InvestmentStrategy,
                                         risk_tolerance: RiskTolerance,
                                         stocks: List[Dict[str, Any]]) -> str:
        """生成建議理由"""
        strategy_name = {
            InvestmentStrategy.DIVIDEND_INVESTING: "股息投資",
            InvestmentStrategy.VALUE_INVESTING: "價值投資",
            InvestmentStrategy.GROWTH_INVESTING: "成長投資"
        }.get(strategy, "綜合投資")

        risk_name = {
            RiskTolerance.CONSERVATIVE: "保守",
            RiskTolerance.MODERATE: "穩健",
            RiskTolerance.AGGRESSIVE: "進取"
        }.get(risk_tolerance, "平衡")

        stock_names = [stock['name'] for stock in stocks[:3]]

        return f"基於您的{risk_name}風險偏好，建議採用{strategy_name}策略。主要投資標的包括{', '.join(stock_names)}。這個組合在控制風險的同時提供合理的報酬潛力。"

    def _generate_portfolio_recommendations(self, diversification_score: float,
                                          risk_score: float,
                                          stock_performance: List[Dict[str, Any]]) -> List[str]:
        """生成投資組合建議"""
        recommendations = []

        if diversification_score < 0.5:
            recommendations.append("建議增加持股多元化，至少持有5檔不同股票")

        if risk_score > 0.7:
            recommendations.append("投資組合風險較高，建議增加防禦性股票")

        # 表現相關建議
        if stock_performance:
            best_performer = max(stock_performance, key=lambda x: x['performance'])
            worst_performer = min(stock_performance, key=lambda x: x['performance'])

            if best_performer['performance'] > 20:
                recommendations.append(f"考慮增加 {best_performer['symbol']} 的持股比例")

            if worst_performer['performance'] < -20:
                recommendations.append(f"評估是否減持表現不佳的 {worst_performer['symbol']}")

        return recommendations

    def _identify_opportunities(self) -> List[Dict[str, Any]]:
        """識別投資機會"""
        opportunities = []

        # 基於技術分析識別機會
        prices = self.stock_manager.sync_prices_from_database()
        for symbol in random.sample(list(prices.keys()), 3):
            analysis = self.technical_analyzer.analyze_stock_trend(symbol)

            if analysis['trend'] == 'bullish' and analysis['strength'] > 0.7:
                opportunities.append({
                    'type': 'technical_breakout',
                    'symbol': symbol,
                    'description': f"{symbol} 呈現強勢上漲趨勢",
                    'confidence': analysis['strength']
                })

        return opportunities

    def _generate_risk_warnings(self) -> List[str]:
        """生成風險警告"""
        warnings = [
            "市場波動性增加，建議關注風險控制",
            "部分行業面臨供應鏈壓力",
            "利率環境可能影響投資報酬"
        ]

        return random.sample(warnings, random.randint(1, 3))
