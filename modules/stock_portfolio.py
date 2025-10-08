class StockPortfolio:
    """Represents a player's stock portfolio."""
    def __init__(self):
        self.stocks = {
            'TSMC': {'name': '台積電', 'industry': '科技業', 'price': 100, 'owned': 0, 'total_cost': 0, 'history': [100], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 1, 'dividend_interval': 30, 'next_dividend_day': 30},
            'HONHAI': {'name': '鴻海', 'industry': '科技業', 'price': 80, 'owned': 0, 'total_cost': 0, 'history': [80], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 1, 'dividend_interval': 30, 'next_dividend_day': 30},
            'MTK': {'name': '聯發科', 'industry': '科技業', 'price': 120, 'owned': 0, 'total_cost': 0, 'history': [120], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 1, 'dividend_interval': 30, 'next_dividend_day': 30},
            'MINING': {'name': '挖礦公司', 'industry': '一級產業', 'price': 60, 'owned': 0, 'total_cost': 0, 'history': [60], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 2, 'dividend_interval': 30, 'next_dividend_day': 30},
            'FARM': {'name': '農業公司', 'industry': '一級產業', 'price': 50, 'owned': 0, 'total_cost': 0, 'history': [50], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 1.5, 'dividend_interval': 30, 'next_dividend_day': 30},
            'FOREST': {'name': '林業公司', 'industry': '一級產業', 'price': 55, 'owned': 0, 'total_cost': 0, 'history': [55], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 1.2, 'dividend_interval': 30, 'next_dividend_day': 30},
            'RETAIL': {'name': '零售連鎖', 'industry': '服務業', 'price': 70, 'owned': 0, 'total_cost': 0, 'history': [70], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 1, 'dividend_interval': 30, 'next_dividend_day': 30},
            'RESTAURANT': {'name': '餐飲集團', 'industry': '服務業', 'price': 65, 'owned': 0, 'total_cost': 0, 'history': [65], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 0.8, 'dividend_interval': 30, 'next_dividend_day': 30},
            'TRAVEL': {'name': '旅遊公司', 'industry': '服務業', 'price': 75, 'owned': 0, 'total_cost': 0, 'history': [75], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 0.9, 'dividend_interval': 30, 'next_dividend_day': 30},
            'BTC': {'name': '比特幣', 'industry': '虛擬貨幣', 'price': 1000000, 'owned': 0, 'total_cost': 0, 'history': [1000000], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 0, 'dividend_interval': 0, 'next_dividend_day': 0}
        }
        for code, stock in self.stocks.items():
            stock['drip'] = False
        self.btc_balance = 0.0
        self.btc_miner_count = 0
        self.btc_hashrate = 0.0
        self.market_volatility = 0.01
        self.btc_mining_rate_per_kh = 0.001
        self.btc_price_volatility_sigma = 0.003
        self.transaction_history = []
        self.last_slot_win = 0
        self.dca_stocks = {}
        self.dca_funds = {}
        self.funds = {}
        self.futures_positions = []
        self.futures_realized_pnl = 0.0