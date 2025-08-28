import os
import json
import logging


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
        
        # 初始化消耗品每日購買計數
        if hasattr(self, 'consumables'):
            for item_id in self.consumables:
                self.consumables[item_id]['daily_bought'] = 0
        
        # 初始化活躍 Buff
        self.active_buffs = []
        
        # 設定預設難度
        self.current_difficulty = 'normal'
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
        # 每檔股票新增 DRIP（股息再投資）開關，預設 False
        for code, stock in self.stocks.items():
            stock['drip'] = False
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
        # --- Player attributes ---
        # 基礎屬性（0~100）：快樂與體力
        self.happiness = 50
        self.stamina = 50
        # 擴充屬性（0~100）：智力、勤奮、魅力、經驗（0~1000 可擴展，但先以 0~100 顯示）、今日運氣
        self.intelligence = 50
        self.diligence = 50
        self.charisma = 50
        self.experience = 0
        # 今日運氣（0~100）與最後生成日，用於每日重擲
        self.luck_today = 50
        self.last_luck_day = -1
        if is_reborn:
            self.reborn_count += 1
        # --- Activities 規則與狀態（冷卻與每日上限）---
        # activity_rules: 每個活動的每日上限與冷卻天數
        self.activity_rules = {
            'study': {'daily_max': 3, 'cooldown_days': 1},
            'workout': {'daily_max': 3, 'cooldown_days': 1},
            'social': {'daily_max': 3, 'cooldown_days': 1},
            'meditate': {'daily_max': 3, 'cooldown_days': 1},
        }
        # activity_state: 當日剩餘次數與冷卻剩餘天數
        self.activity_state = {
            k: {'remaining': v['daily_max'], 'cd_left': 0}
            for k, v in self.activity_rules.items()
        }
        # --- Work Mode (上班模式) 預設欄位 ---
        # 當前工作：name, level, salary_per_day, tax_rate, next_promotion_day
        self.job = None
        # 任職公司與公司目錄（影響薪資倍率）
        self.current_company = '一般公司'
        self.companies_catalog = {
            '一般公司': {'salary_multiplier': 1.00},
            '宇宙科技': {'salary_multiplier': 1.10},
            '幸福生活': {'salary_multiplier': 0.95},
        }
        # 收入歷史：[{day, type:'salary', gross, tax, net}]
        self.income_history = []
        # 學歷系統：等級、倍率、升級花費
        self.education_level = '高中'
        self.education_levels = ['高中', '大學', '碩士', '博士']
        self.education_multipliers = {
            '高中': 1.00,
            '大學': 1.10,
            '碩士': 1.25,
            '博士': 1.40,
        }
        # 升級至該目標學歷的費用
        self.education_upgrade_cost = {
            '大學': 1000.0,
            '碩士': 3000.0,
            '博士': 8000.0,
        }
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
        
        # 消耗品定義：名稱、價格、效果、持續時間(天)、每日限購、描述
        self.consumables = {
            'energy_drink': {
                'name': '能量飲料',
                'price': 50,
                'effects': [
                    {'type': 'stamina', 'value': 20, 'duration': 0},  # 立即恢復體力
                    {'type': 'buff', 'stat': 'productivity', 'value': 0.2, 'duration': 24}  # 臨時提升生產力
                ],
                'daily_limit': 5,
                'daily_bought': 0,
                'description': '立即恢復20體力，並在24小時內提升20%生產力'
            },
            'study_kit': {
                'name': '學習套組',
                'price': 100,
                'effects': [
                    {'type': 'buff', 'stat': 'intelligence', 'value': 0.3, 'duration': 72},
                    {'type': 'buff', 'stat': 'study_efficiency', 'value': 0.5, 'duration': 72}
                ],
                'daily_limit': 3,
                'daily_bought': 0,
                'description': '72小時內提升30%智力成長與50%學習效率'
            },
            'social_card': {
                'name': '社交卡',
                'price': 80,
                'effects': [
                    {'type': 'buff', 'stat': 'charisma', 'value': 0.4, 'duration': 48},
                    {'type': 'buff', 'stat': 'luck', 'value': 0.3, 'duration': 24}
                ],
                'daily_limit': 3,
                'daily_bought': 0,
                'description': '48小時內提升40%魅力，24小時內提升30%運氣'
            }
        }
        
        # 玩家庫存：儲存擁有的消耗品 {item_id: quantity}
        self.inventory = {item_id: 0 for item_id in self.consumables}
        
        # 活躍的 Buff 效果
        self.active_buffs = []
        
        # 難度模式設定
        self.difficulty_levels = {
            'easy': {
                'salary_multiplier': 1.2,
                'expense_multiplier': 0.8,
                'stock_volatility': 0.8,
                'event_frequency': 0.8,
                'event_severity': 0.8,
                'activity_benefit': 1.2,
                'activity_cooldown': 0.8
            },
            'normal': {
                'salary_multiplier': 1.0,
                'expense_multiplier': 1.0,
                'stock_volatility': 1.0,
                'event_frequency': 1.0,
                'event_severity': 1.0,
                'activity_benefit': 1.0,
                'activity_cooldown': 1.0
            },
            'hard': {
                'salary_multiplier': 0.8,
                'expense_multiplier': 1.2,
                'stock_volatility': 1.2,
                'event_frequency': 1.2,
                'event_severity': 1.2,
                'activity_benefit': 0.8,
                'activity_cooldown': 1.2
            }
        }
        self.current_difficulty = 'normal'
        # --- Auto-Invest (DCA) 設定 ---
        # 股票定投：{code: {amount_cash: float, interval_days: int, next_day: int}}
        self.dca_stocks = {}
        # 基金定投：{fname: {amount_cash: float, interval_days: int, next_day: int}}
        self.dca_funds = {}
        # --- Entrepreneurship (創業) ---
        # 簡單的創業結構：[{name, level, revenue_per_day, cost_per_day, next_upgrade_cost}]
        self.businesses = []
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
                logging.error(f"存檔失敗：{e}")


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
            
            # 確保消耗品相關欄位存在
            if not hasattr(self, 'consumables'):
                # 這裡的初始值會由 reset() 方法設置
                self.consumables = {}
                
            if not hasattr(self, 'inventory'):
                self.inventory = {}
                
            if not hasattr(self, 'active_buffs'):
                self.active_buffs = []
                
            if not hasattr(self, 'difficulty_levels'):
                self.difficulty_levels = {
                    'easy': {'salary_multiplier': 1.2, 'expense_multiplier': 0.8},
                    'normal': {'salary_multiplier': 1.0, 'expense_multiplier': 1.0},
                    'hard': {'salary_multiplier': 0.8, 'expense_multiplier': 1.2}
                }
                
            if not hasattr(self, 'current_difficulty'):
                self.current_difficulty = 'normal'
                if 'buy_points' not in stock:
                    stock['buy_points'] = []
                if 'sell_points' not in stock:
                    stock['sell_points'] = []
                if 'drip' not in stock:
                    stock['drip'] = False

            # 補齊新加入的 btc 參數
            if not hasattr(self, 'btc_mining_rate_per_kh'):
                self.btc_mining_rate_per_kh = 0.001
            if not hasattr(self, 'btc_price_volatility_sigma'):
                self.btc_price_volatility_sigma = 0.003

            # --- 補齊 Work Mode 欄位 ---
            if not hasattr(self, 'job'):
                self.job = None
            # 公司選擇與目錄
            if not hasattr(self, 'companies_catalog'):
                self.companies_catalog = {
                    '一般公司': {'salary_multiplier': 1.00},
                    '宇宙科技': {'salary_multiplier': 1.10},
                    '幸福生活': {'salary_multiplier': 0.95},
                }
            if not hasattr(self, 'current_company'):
                self.current_company = '一般公司'
            if not hasattr(self, 'income_history'):
                self.income_history = []
            # --- 補齊 Player attributes ---
            if not hasattr(self, 'happiness'):
                self.happiness = 50
            if not hasattr(self, 'stamina'):
                self.stamina = 50
            # --- 新增擴充屬性：預設值補齊 ---
            if not hasattr(self, 'intelligence'):
                self.intelligence = 50
            if not hasattr(self, 'diligence'):
                self.diligence = 50
            if not hasattr(self, 'charisma'):
                self.charisma = 50
            if not hasattr(self, 'experience'):
                self.experience = 0
            if not hasattr(self, 'luck_today'):
                self.luck_today = 50
            if not hasattr(self, 'last_luck_day'):
                self.last_luck_day = -1
            # --- 補齊 Education ---
            if not hasattr(self, 'education_level'):
                self.education_level = '高中'
            if not hasattr(self, 'education_levels'):
                self.education_levels = ['高中', '大學', '碩士', '博士']
            if not hasattr(self, 'education_multipliers'):
                self.education_multipliers = {
                    '高中': 1.00,
                    '大學': 1.10,
                    '碩士': 1.25,
                    '博士': 1.40,
                }
            if not hasattr(self, 'education_upgrade_cost'):
                self.education_upgrade_cost = {
                    '大學': 1000.0,
                    '碩士': 3000.0,
                    '博士': 8000.0,
                }
            if not hasattr(self, 'jobs_catalog'):
                self.jobs_catalog = {
                    '實習生': {'base_salary_per_day': 50.0, 'tax_rate': 0.05},
                    '工程師': {'base_salary_per_day': 120.0, 'tax_rate': 0.10},
                    '資深工程師': {'base_salary_per_day': 200.0, 'tax_rate': 0.12},
                    '經理': {'base_salary_per_day': 300.0, 'tax_rate': 0.15},
                }
            # --- 補齊 Activities 欄位 ---
            if not hasattr(self, 'activity_rules') or not isinstance(getattr(self, 'activity_rules', None), dict):
                self.activity_rules = {
                    'study': {'daily_max': 3, 'cooldown_days': 1},
                    'workout': {'daily_max': 3, 'cooldown_days': 1},
                    'social': {'daily_max': 3, 'cooldown_days': 1},
                    'meditate': {'daily_max': 3, 'cooldown_days': 1},
                }
            # 狀態若不存在或格式錯誤則重建
            if not hasattr(self, 'activity_state') or not isinstance(getattr(self, 'activity_state', None), dict):
                self.activity_state = {}
            # 同步 rules 與 state 的鍵與預設值
            for k, rule in self.activity_rules.items():
                st = self.activity_state.get(k)
                if not isinstance(st, dict):
                    st = {}
                if 'remaining' not in st:
                    st['remaining'] = int(rule.get('daily_max', 3))
                if 'cd_left' not in st:
                    st['cd_left'] = 0
                self.activity_state[k] = st
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

            # --- 補齊 Auto-Invest / Entrepreneurship 欄位 ---
            if not hasattr(self, 'dca_stocks'):
                self.dca_stocks = {}
            if not hasattr(self, 'dca_funds'):
                self.dca_funds = {}
            if not hasattr(self, 'businesses'):
                self.businesses = []

            if hasattr(self, 'achievements_manager'):
                self.achievements_manager.__init__(self, self.achievements_unlocked) # 重新初始化成就管理器
        except Exception as e:
            if show_error:
                show_error(f"讀檔失敗：{e}")
            else:
                logging.error(f"讀檔失敗：{e}")

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

    def total_assets(self):
        return self.balance + self.cash - self.loan
        
    def can_afford(self, amount):
        """檢查現金是否足夠支付指定金額"""
        return self.cash >= amount
        
    def add_item(self, item_id, quantity=1):
        """添加物品到庫存"""
        if item_id in self.inventory:
            self.inventory[item_id] += quantity
        else:
            self.inventory[item_id] = quantity
        return self.inventory[item_id]
        
    def remove_item(self, item_id, quantity=1):
        """從庫存中移除物品"""
        if item_id not in self.inventory or self.inventory[item_id] < quantity:
            return False
        self.inventory[item_id] -= quantity
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True
        
    def has_item(self, item_id, quantity=1):
        """檢查是否擁有足夠數量的物品"""
        return item_id in self.inventory and self.inventory[item_id] >= quantity
        
    def buy_consumable(self, item_id, quantity=1):
        """購買消耗品"""
        if item_id not in self.consumables:
            return False, "無效的物品ID"
            
        item = self.consumables[item_id]
        total_cost = item['price'] * quantity
        
        # 檢查金錢是否足夠
        if not self.can_afford(total_cost):
            return False, "現金不足"
            
        # 檢查每日限購
        if item['daily_bought'] + quantity > item['daily_limit']:
            return False, f"已達每日限購數量 (今日還可購買 {item['daily_limit'] - item['daily_bought']} 個)"
            
        # 扣錢並增加物品
        self.cash -= total_cost
        self.add_item(item_id, quantity)
        item['daily_bought'] += quantity
        
        return True, f"成功購買 {quantity} 個 {item['name']}"
        
    def use_consumable(self, item_id):
        """使用消耗品"""
        if not self.has_item(item_id):
            return False, "物品不存在或數量不足"
            
        if item_id not in self.consumables:
            return False, "無效的物品ID"
            
        item = self.consumables[item_id]
        
        # 應用效果
        results = []
        for effect in item.get('effects', []):
            if effect['type'] == 'stamina':
                self.stamina = min(100, self.stamina + effect['value'])
                results.append(f"體力 +{effect['value']}")
            elif effect['type'] == 'buff':
                self.add_buff(
                    stat=effect['stat'],
                    value=effect['value'],
                    duration=effect['duration']
                )
                results.append(f"{effect['stat']} +{int(effect['value']*100)}% ({effect['duration']}小時)")
        
        # 從庫存中移除
        self.remove_item(item_id)
        
        return True, f"使用 {item['name']} 成功！\n效果: {', '.join(results)}"
        
    def add_buff(self, stat, value, duration, description=""):
        """添加一個buff效果"""
        self.active_buffs.append({
            'stat': stat,
            'value': value,
            'duration': duration * 60,  # 轉換為分鐘
            'applied_at': 0,  # 會在 unified_timer 中更新
            'description': description
        })
        
    def get_buff_value(self, stat):
        """獲取指定屬性的buff加成總和"""
        total = 0.0
        for buff in self.active_buffs:
            if buff['stat'] == stat:
                total += buff['value']
        return total
        
    def update_buffs(self, minutes_passed=1):
        """更新buff持續時間，返回過期的buff列表"""
        if not hasattr(self, 'active_buffs'):
            self.active_buffs = []
            return []
            
        expired = []
        remaining = []
        
        for buff in self.active_buffs:
            buff['duration'] = max(0, buff['duration'] - minutes_passed)
            if buff['duration'] <= 0:
                expired.append(buff)
            else:
                remaining.append(buff)
                
        self.active_buffs = remaining
        return expired

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
    
    def get_difficulty_multiplier(self, key):
        """獲取當前難度的倍率"""
        if not hasattr(self, 'difficulty_levels') or not hasattr(self, 'current_difficulty'):
            return 1.0
        level = self.difficulty_levels.get(self.current_difficulty, {})
        return level.get(key, 1.0)