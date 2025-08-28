import random
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class InvestmentPortfolioManager:
    """投資組合管理器，提供風險評估和投資策略"""

    def __init__(self, game: 'BankGame'):
        self.game = game

    def get_portfolio_summary(self):
        """獲取投資組合總結"""
        portfolio = {
            'stocks': {},
            'funds': {},
            'crypto': {},
            'total_value': 0,
            'total_cost': 0,
            'total_return': 0,
            'diversity_score': 0
        }

        # 統計股票投資
        stock_value = 0
        stock_cost = 0
        for code, stock in self.game.data.stocks.items():
            if stock['owned'] > 0:
                current_value = stock['price'] * stock['owned']
                stock_value += current_value
                stock_cost += stock['total_cost']
                portfolio['stocks'][code] = {
                    'name': stock['name'],
                    'shares': stock['owned'],
                    'current_price': stock['price'],
                    'current_value': current_value,
                    'total_cost': stock['total_cost'],
                    'return_rate': (current_value - stock['total_cost']) / stock['total_cost'] if stock['total_cost'] > 0 else 0
                }

        # 統計基金投資
        fund_value = 0
        fund_cost = 0
        for fname, fund in self.game.data.funds.items():
            if fund['units'] > 0:
                current_value = fund['nav'] * fund['units']
                fund_value += current_value
                fund_cost += fund['total_cost']
                portfolio['funds'][fname] = {
                    'units': fund['units'],
                    'nav': fund['nav'],
                    'current_value': current_value,
                    'total_cost': fund['total_cost'],
                    'return_rate': (current_value - fund['total_cost']) / fund['total_cost'] if fund['total_cost'] > 0 else 0
                }

        # 統計加密貨幣投資
        crypto_value = self.game.data.btc_balance * self.game.data.stocks['BTC']['price']
        crypto_cost = sum(cost for cost in [getattr(self.game.data, 'btc_purchase_cost', 0)] if cost > 0)
        if self.game.data.btc_balance > 0:
            portfolio['crypto']['BTC'] = {
                'amount': self.game.data.btc_balance,
                'current_price': self.game.data.stocks['BTC']['price'],
                'current_value': crypto_value,
                'total_cost': crypto_cost,
                'return_rate': (crypto_value - crypto_cost) / crypto_cost if crypto_cost > 0 else 0
            }

        # 計算總計
        portfolio['total_value'] = stock_value + fund_value + crypto_value
        portfolio['total_cost'] = stock_cost + fund_cost + crypto_cost
        portfolio['total_return'] = portfolio['total_value'] - portfolio['total_cost']
        portfolio['return_rate'] = (portfolio['total_return'] / portfolio['total_cost']) if portfolio['total_cost'] > 0 else 0

        # 計算多元化分數
        asset_types = []
        if portfolio['stocks']:
            asset_types.append('stocks')
        if portfolio['funds']:
            asset_types.append('funds')
        if portfolio['crypto']:
            asset_types.append('crypto')

        stock_count = len(portfolio['stocks'])
        portfolio['diversity_score'] = min(100, (len(asset_types) * 20) + (stock_count * 5))

        return portfolio

    def assess_portfolio_risk(self):
        """評估投資組合風險"""
        portfolio = self.get_portfolio_summary()

        risk_metrics = {
            'volatility': 0,
            'concentration_risk': 0,
            'sector_risk': 0,
            'liquidity_risk': 0,
            'overall_risk': 0,
            'risk_level': '低風險'
        }

        # 計算波動性風險
        if portfolio['stocks']:
            volatilities = []
            for stock_data in portfolio['stocks'].values():
                # 估計波動性（基於價格變化）
                if len(self.game.data.stocks[stock_data['name']]['history']) > 10:
                    history = self.game.data.stocks[stock_data['name']]['history'][-10:]
                    returns = [history[i+1]/history[i] - 1 for i in range(len(history)-1)]
                    volatility = np.std(returns) * np.sqrt(252) if returns else 0
                    volatilities.append(volatility)

            risk_metrics['volatility'] = np.mean(volatilities) if volatilities else 0

        # 計算集中風險
        if portfolio['stocks']:
            max_allocation = max(stock['current_value'] for stock in portfolio['stocks'].values())
            risk_metrics['concentration_risk'] = (max_allocation / portfolio['total_value']) * 100

        # 計算行業風險
        sector_allocation = {}
        for stock_data in portfolio['stocks'].values():
            stock_info = next((s for s in self.game.data.stocks.values() if s['name'] == stock_data['name']), None)
            if stock_info:
                sector = stock_info.get('industry', '其他')
                if sector not in sector_allocation:
                    sector_allocation[sector] = 0
                sector_allocation[sector] += stock_data['current_value']

        if sector_allocation:
            max_sector_allocation = max(sector_allocation.values())
            risk_metrics['sector_risk'] = (max_sector_allocation / portfolio['total_value']) * 100

        # 計算流動性風險
        illiquid_assets = crypto_value = self.game.data.btc_balance * self.game.data.stocks['BTC']['price']
        risk_metrics['liquidity_risk'] = (illiquid_assets / portfolio['total_value']) * 100 if portfolio['total_value'] > 0 else 0

        # 計算整體風險
        risk_score = (
            risk_metrics['volatility'] * 0.3 +
            risk_metrics['concentration_risk'] * 0.3 +
            risk_metrics['sector_risk'] * 0.2 +
            risk_metrics['liquidity_risk'] * 0.2
        )

        risk_metrics['overall_risk'] = risk_score

        # 確定風險等級
        if risk_score < 20:
            risk_metrics['risk_level'] = '低風險'
        elif risk_score < 40:
            risk_metrics['risk_level'] = '中等風險'
        elif risk_score < 60:
            risk_metrics['risk_level'] = '高風險'
        else:
            risk_metrics['risk_level'] = '極高風險'

        return risk_metrics

    def get_investment_recommendations(self):
        """獲取投資建議"""
        portfolio = self.get_portfolio_summary()
        risk_metrics = self.assess_portfolio_risk()

        recommendations = []

        # 多元化建議
        if portfolio['diversity_score'] < 50:
            recommendations.append({
                'type': 'diversification',
                'priority': 'high',
                'title': '提升投資多元化',
                'description': '您的投資組合過於集中，建議分散投資到不同類型的資產',
                'action': '考慮投資基金或不同行業的股票'
            })

        # 風險控制建議
        if risk_metrics['concentration_risk'] > 30:
            recommendations.append({
                'type': 'risk_management',
                'priority': 'high',
                'title': '降低集中風險',
                'priority': 'high',
                'description': f'單一資產占比過高 ({risk_metrics["concentration_risk"]:.1f}%)',
                'action': '減少高占比資產的持有量'
            })

        # 行業分散建議
        if risk_metrics['sector_risk'] > 40:
            recommendations.append({
                'type': 'sector_diversification',
                'priority': 'medium',
                'title': '分散行業投資',
                'description': f'單一行業占比過高 ({risk_metrics["sector_risk"]:.1f}%)',
                'action': '投資其他行業的股票或基金'
            })

        # 收益優化建議
        if portfolio['return_rate'] < 0.05 and self.game.data.days > 30:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': '優化投資組合',
                'description': f'投資回報率偏低 ({portfolio["return_rate"]:.1%})',
                'action': '考慮調整投資策略或尋找更高收益的機會'
            })

        # 流動性建議
        if risk_metrics['liquidity_risk'] > 50:
            recommendations.append({
                'type': 'liquidity',
                'priority': 'low',
                'title': '改善流動性',
                'description': f'非流動性資產占比過高 ({risk_metrics["liquidity_risk"]:.1f}%)',
                'action': '考慮轉換部分資產為更易變現的形式'
            })

        return recommendations

    def analyze_market_trends(self):
        """分析市場趨勢"""
        trends = {
            'market_sentiment': 'neutral',
            'hot_sectors': [],
            'cold_sectors': [],
            'volatility_forecast': 'normal',
            'recommendations': []
        }

        # 分析市場情緒
        market_return = 0
        for stock in self.game.data.stocks.values():
            if len(stock['history']) >= 2:
                recent_return = (stock['price'] - stock['history'][-2]) / stock['history'][-2]
                market_return += recent_return

        avg_market_return = market_return / len(self.game.data.stocks)
        if avg_market_return > 0.05:
            trends['market_sentiment'] = 'bullish'
        elif avg_market_return < -0.05:
            trends['market_sentiment'] = 'bearish'

        # 分析熱門行業
        sector_performance = {}
        for stock in self.game.data.stocks.values():
            sector = stock.get('industry', '其他')
            if sector not in sector_performance:
                sector_performance[sector] = []

            if len(stock['history']) >= 5:
                recent_performance = (stock['price'] - stock['history'][-5]) / stock['history'][-5]
                sector_performance[sector].append(recent_performance)

        for sector, performances in sector_performance.items():
            if performances:
                avg_performance = sum(performances) / len(performances)
                if avg_performance > 0.03:
                    trends['hot_sectors'].append(sector)
                elif avg_performance < -0.03:
                    trends['cold_sectors'].append(sector)

        # 預測波動性
        recent_volatility = []
        for stock in self.game.data.stocks.values():
            if len(stock['history']) >= 10:
                prices = stock['history'][-10:]
                returns = [prices[i+1]/prices[i] - 1 for i in range(len(prices)-1)]
                if returns:
                    volatility = np.std(returns)
                    recent_volatility.append(volatility)

        if recent_volatility:
            avg_volatility = sum(recent_volatility) / len(recent_volatility)
            if avg_volatility > 0.03:
                trends['volatility_forecast'] = 'high'
            elif avg_volatility < 0.01:
                trends['volatility_forecast'] = 'low'

        # 生成建議
        if trends['market_sentiment'] == 'bullish':
            trends['recommendations'].append('市場情緒樂觀，適合積極投資')
        elif trends['market_sentiment'] == 'bearish':
            trends['recommendations'].append('市場情緒悲觀，建議謹慎投資')

        if trends['hot_sectors']:
            trends['recommendations'].append(f'熱門行業：{", ".join(trends["hot_sectors"])}')

        if trends['volatility_forecast'] == 'high':
            trends['recommendations'].append('市場波動較大，注意風險控制')

        return trends

    def generate_investment_strategy(self):
        """生成投資策略建議"""
        portfolio = self.get_portfolio_summary()
        risk_metrics = self.assess_portfolio_risk()
        market_trends = self.analyze_market_trends()

        strategy = {
            'risk_profile': risk_metrics['risk_level'],
            'time_horizon': self._estimate_time_horizon(),
            'recommended_allocation': {},
            'strategy_type': '',
            'specific_actions': []
        }

        # 確定策略類型
        if risk_metrics['risk_level'] == '低風險':
            strategy['strategy_type'] = '保守型'
            strategy['recommended_allocation'] = {
                'stocks': 40,
                'funds': 40,
                'cash': 20
            }
        elif risk_metrics['risk_level'] == '中等風險':
            strategy['strategy_type'] = '平衡型'
            strategy['recommended_allocation'] = {
                'stocks': 50,
                'funds': 30,
                'crypto': 10,
                'cash': 10
            }
        elif risk_metrics['risk_level'] == '高風險':
            strategy['strategy_type'] = '積極型'
            strategy['recommended_allocation'] = {
                'stocks': 60,
                'crypto': 20,
                'funds': 15,
                'cash': 5
            }
        else:
            strategy['strategy_type'] = '極端型'
            strategy['recommended_allocation'] = {
                'crypto': 50,
                'stocks': 40,
                'funds': 10
            }

        # 生成具體行動建議
        if portfolio['diversity_score'] < 60:
            strategy['specific_actions'].append('增加投資多元化，考慮投資指數基金')

        if market_trends['hot_sectors']:
            strategy['specific_actions'].append(f'關注熱門行業：{", ".join(market_trends["hot_sectors"])}')

        if risk_metrics['concentration_risk'] > 40:
            strategy['specific_actions'].append('降低單一資產集中度')

        if portfolio['return_rate'] < 0 and self.game.data.days > 60:
            strategy['specific_actions'].append('評估投資策略，可能需要調整投資組合')

        return strategy

    def _estimate_time_horizon(self):
        """估計投資時間視野"""
        days = self.game.data.days
        if days < 90:
            return '短期 (3個月內)'
        elif days < 365:
            return '中期 (1年內)'
        elif days < 1095:
            return '長期 (2-3年)'
        else:
            return '超長期 (3年以上)'

    def calculate_optimal_portfolio(self, target_return=None, max_risk=None):
        """計算最優投資組合（簡化版馬可維茨模型）"""
        available_assets = []

        # 收集可用資產
        for code, stock in self.game.data.stocks.items():
            if len(stock['history']) >= 30:
                returns = []
                for i in range(1, min(30, len(stock['history']))):
                    ret = (stock['history'][-i] - stock['history'][-i-1]) / stock['history'][-i-1]
                    returns.append(ret)

                if returns:
                    asset = {
                        'code': code,
                        'name': stock['name'],
                        'expected_return': sum(returns) / len(returns),
                        'risk': np.std(returns),
                        'price': stock['price']
                    }
                    available_assets.append(asset)

        if len(available_assets) < 2:
            return None

        # 簡化最優化（實際應用需要更複雜的算法）
        optimal_portfolio = {}

        # 根據風險偏好分配
        if max_risk is None:
            max_risk = 0.1  # 預設最大風險

        # 選擇風險最低的資產作為基礎
        sorted_assets = sorted(available_assets, key=lambda x: x['risk'])

        total_weight = 0
        for i, asset in enumerate(sorted_assets[:5]):  # 選擇前5個最低風險資產
            if asset['risk'] <= max_risk:
                weight = 1 / (i + 1)  # 簡單權重分配
                optimal_portfolio[asset['code']] = {
                    'name': asset['name'],
                    'weight': weight,
                    'expected_return': asset['expected_return'],
                    'risk': asset['risk']
                }
                total_weight += weight

        # 正規化權重
        for code in optimal_portfolio:
            optimal_portfolio[code]['weight'] /= total_weight

        return optimal_portfolio
