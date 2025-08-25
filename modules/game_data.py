import os
import json


class GameData:
    def __init__(self):
        self.reborn_count = 0
        self.reset()

    def reset(self, is_reborn=False):
        self.balance = 0
        self.cash = 1000
        self.loan = 0
        self.deposit_interest_rate = 0.01
        self.loan_interest_rate = 0.005
        # 多檔股票資料
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
        self.btc_balance = 0.0
        self.btc_miner_count = 0
        self.btc_hashrate = 0.0
        self.market_volatility = 0.01 # 普通股票波動率
        
        # 新增比特幣相關可調整參數
        self.btc_mining_rate_per_kh = 0.001 # 每 1 kh 算力每回合產出的比特幣數量
        self.btc_price_volatility_sigma = 0.003 # 比特幣價格波動率 (高斯分佈的標準差)

        self.transaction_history = []
        self.last_slot_win = 0
        self.achievements_unlocked = []
        self.days = 0
        if is_reborn:
            self.reborn_count += 1
        # --- Work Mode (上班模式) 預設欄位 ---
        # 當前工作：name, level, salary_per_day, tax_rate, next_promotion_day
        self.job = None
        # 收入歷史：[{day, type:'salary', gross, tax, net}]
        self.income_history = []
        # 職業目錄（可於 UI 選擇），金額單位：遊戲幣/日
        self.jobs_catalog = {
            '實習生': {'base_salary_per_day': 50.0, 'tax_rate': 0.05},
            '工程師': {'base_salary_per_day': 120.0, 'tax_rate': 0.10},
            '資深工程師': {'base_salary_per_day': 200.0, 'tax_rate': 0.12},
            '經理': {'base_salary_per_day': 300.0, 'tax_rate': 0.15},
        }
        # --- Expenses (支出) 預設欄位 ---
        # 支出列表：[{name, amount, frequency:'daily'|'weekly'|'monthly', next_due_day:int}]
        self.expenses = []
        # 支出歷史：[{day, name, amount}]
        self.expense_history = []
        # 是否已加入預設固定支出（公用事業與基本訂閱）
        self.expense_defaults_added = False
        # 商店：可購買的項目與玩家物品清單（嘗試外部讀取 data/store_catalog.json）
        self.store_catalog = self._load_store_catalog_external()
        self.inventory = []
        # --- Funds/ETF 預設欄位 ---
        # 可供交易的基金目錄：每檔包含股票權重（以股票代碼為鍵，權重總和為1），與手續費率（單邊）
        self.funds_catalog = {
            '台灣科技ETF': {
                'weights': {'TSMC': 0.5, 'HONHAI': 0.3, 'MTK': 0.2},
                'fee_rate': 0.002
            },
            '服務業綜合ETF': {
                'weights': {'RETAIL': 0.34, 'RESTAURANT': 0.33, 'TRAVEL': 0.33},
                'fee_rate': 0.002
            },
            '一級產業ETF': {
                'weights': {'MINING': 0.34, 'FARM': 0.33, 'FOREST': 0.33},
                'fee_rate': 0.002
            },
        }
        # 持有的基金資訊：每檔包含 nav、units（持有單位）、total_cost、history（nav 歷史）、base_prices（初始化時的股票基準價）
        self.funds = {}
        for fname, finfo in self.funds_catalog.items():
            base_prices = {code: self.stocks[code]['price'] for code in finfo['weights'].keys() if code in self.stocks}
            self.funds[fname] = {
                'nav': 100.0,
                'units': 0.0,
                'total_cost': 0.0,
                'history': [100.0],
                'base_prices': base_prices,
            }

    def save(self, file_path, show_error=None):
        try:
            if hasattr(self, 'achievements_manager'):
                self.achievements_unlocked = self.achievements_manager.export_unlocked_keys()
            data = {k: v for k, v in self.__dict__.items() if k != 'achievements_manager'}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if show_error:
                show_error(f"存檔失敗：{e}")
            else:
                print(f"存檔失敗：{e}")


    def load(self, file_path, show_error=None):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.__dict__.update(data)
            # 自動補齊新版欄位
            if not hasattr(self, 'reborn_count'):
                self.reborn_count = 0
            if not hasattr(self, 'btc_balance'):
                self.btc_balance = 0.0
            if not hasattr(self, 'btc_miner_count'):
                self.btc_miner_count = 0
            if not hasattr(self, 'btc_hashrate'):
                self.btc_hashrate = 0.0
            if 'BTC' not in self.stocks:
                self.stocks['BTC'] = {'name': '比特幣', 'industry': '虛擬貨幣', 'price': 1000000, 'owned': 0, 'total_cost': 0, 'history': [1000000], 'buy_points': [], 'sell_points': [], 'dividend_per_share': 0, 'dividend_interval': 0, 'next_dividend_day': 0}
            
            # BUG FIX: industry_map 將服務業公司的產業別錯誤地設為其名稱，已修正。
            industry_map = {
                'TSMC': '科技業', 'HONHAI': '科技業', 'MTK': '科技業',
                'MINING': '一級產業', 'FARM': '一級產業', 'FOREST': '一級產業',
                'RETAIL': '服務業', 'RESTAURANT': '服務業', 'TRAVEL': '服務業',
            }
            for code, stock in self.stocks.items():
                if 'industry' not in stock:
                    stock['industry'] = industry_map.get(code, '未知')
                if 'dividend_per_share' not in stock:
                    stock['dividend_per_share'] = 1
                if 'dividend_interval' not in stock:
                    stock['dividend_interval'] = 30
                if 'next_dividend_day' not in stock:
                    stock['next_dividend_day'] = 30
                # 確保舊存檔也有 buy_points 和 sell_points
                if 'buy_points' not in stock:
                    stock['buy_points'] = []
                if 'sell_points' not in stock:
                    stock['sell_points'] = []

            # 補齊新加入的 btc 參數
            if not hasattr(self, 'btc_mining_rate_per_kh'):
                self.btc_mining_rate_per_kh = 0.001
            if not hasattr(self, 'btc_price_volatility_sigma'):
                self.btc_price_volatility_sigma = 0.003

            # --- 補齊 Work Mode 欄位 ---
            if not hasattr(self, 'job'):
                self.job = None
            if not hasattr(self, 'income_history'):
                self.income_history = []
            if not hasattr(self, 'jobs_catalog'):
                self.jobs_catalog = {
                    '實習生': {'base_salary_per_day': 50.0, 'tax_rate': 0.05},
                    '工程師': {'base_salary_per_day': 120.0, 'tax_rate': 0.10},
                    '資深工程師': {'base_salary_per_day': 200.0, 'tax_rate': 0.12},
                    '經理': {'base_salary_per_day': 300.0, 'tax_rate': 0.15},
                }
            # --- 補齊 Expenses 欄位 ---
            if not hasattr(self, 'expenses'):
                self.expenses = []
            if not hasattr(self, 'expense_history'):
                self.expense_history = []
            if not hasattr(self, 'expense_defaults_added'):
                self.expense_defaults_added = False
            # --- 補齊 商店 與 物品欄 ---
            if not hasattr(self, 'store_catalog'):
                self.store_catalog = self._load_store_catalog_external()
            if not hasattr(self, 'inventory'):
                self.inventory = []
            # --- 補齊 Funds/ETF 欄位 ---
            if not hasattr(self, 'funds_catalog'):
                self.funds_catalog = {
                    '台灣科技ETF': {
                        'weights': {'TSMC': 0.5, 'HONHAI': 0.3, 'MTK': 0.2},
                        'fee_rate': 0.002
                    },
                    '服務業綜合ETF': {
                        'weights': {'RETAIL': 0.34, 'RESTAURANT': 0.33, 'TRAVEL': 0.33},
                        'fee_rate': 0.002
                    },
                    '一級產業ETF': {
                        'weights': {'MINING': 0.34, 'FARM': 0.33, 'FOREST': 0.33},
                        'fee_rate': 0.002
                    },
                }
            if not hasattr(self, 'funds'):
                self.funds = {}
            # 補齊每檔基金必要欄位
            for fname, finfo in self.funds_catalog.items():
                if fname not in self.funds:
                    self.funds[fname] = {}
                f = self.funds[fname]
                if 'nav' not in f:
                    f['nav'] = 100.0
                if 'units' not in f:
                    f['units'] = 0.0
                if 'total_cost' not in f:
                    f['total_cost'] = 0.0
                if 'history' not in f or not isinstance(f.get('history'), list):
                    f['history'] = [f.get('nav', 100.0)]
                # 基準價格若不存在，以當前股價建立，避免除以零
                if 'base_prices' not in f or not f.get('base_prices'):
                    f['base_prices'] = {code: self.stocks[code]['price'] for code in finfo['weights'].keys() if code in self.stocks}

            if hasattr(self, 'achievements_manager'):
                self.achievements_manager.__init__(self, self.achievements_unlocked) # 重新初始化成就管理器
        except Exception as e:
            if show_error:
                show_error(f"讀檔失敗：{e}")
            else:
                print(f"讀檔失敗：{e}")

    def _load_store_catalog_external(self):
        # 從專案根目錄的 data/store_catalog.json 載入，失敗則回退到內建預設
        try:
            # modules/ 在上一層建立 data/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, 'data')
            os.makedirs(data_path, exist_ok=True)
            catalog_path = os.path.join(data_path, 'store_catalog.json')
            if os.path.exists(catalog_path):
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    cat = json.load(f)
                if isinstance(cat, dict) and 'subscriptions' in cat and 'goods' in cat:
                    return cat
        except Exception:
            pass
        # 內建預設
        return {
            'subscriptions': {
                'Netflix 訂閱': {'price': 0.0, 'type': 'subscription', 'amount': 15.0, 'frequency': 'monthly'},
                'Spotify 訂閱': {'price': 0.0, 'type': 'subscription', 'amount': 10.0, 'frequency': 'monthly'},
                '健身房會員': {'price': 0.0, 'type': 'subscription', 'amount': 30.0, 'frequency': 'monthly'},
            },
            'goods': {
                '筆電': {'price': 800.0, 'type': 'goods'},
                '自行車': {'price': 150.0, 'type': 'goods'},
            }
        }

    def is_valid(self):
        return self.balance is not None and self.cash is not None

    def total_assets(self):
        # 計算普通股票的市值
        stock_value = sum(s['price'] * s['owned'] for s in self.stocks.values() if s['name'] != '比特幣')

        # 計算比特幣的市值
        btc_price = self.stocks['BTC']['price']
        btc_market_value = self.btc_balance * btc_price

        # 總資產 = 銀行存款 + 現金 + 普通股票市值 + 比特幣市值 - 貸款
        return self.balance + self.cash + stock_value + btc_market_value - self.loan
    
    @property
    def loan_limit(self):
        # 貸款上限為資產5倍（不含貸款本身）
        assets = self.balance + self.cash + \
                 sum(s['price'] * s['owned'] for s in self.stocks.values() if s['name'] != '比特幣') + \
                 (self.btc_balance * self.stocks['BTC']['price'])
        return assets * 5