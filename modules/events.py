import random
import tkinter.messagebox as messagebox

class GameEvent:
    def __init__(self, name, description, effect_func, effect_desc=""):
        self.name = name
        self.description = description
        self.effect_func = effect_func
        self.effect_desc = effect_desc

class EventManager:
    def __init__(self, game):
        self.game = game
        self.events = self._init_events()

    def _init_events(self):
        industries = list({v['industry'] for v in self.game.data.stocks.values()})
        stocks = list(self.game.data.stocks.keys())
        events = [
            GameEvent('利多新聞', '某科技股利多，隨機一檔科技業股票大漲！', self.positive_news, '隨機一檔科技業股票價格上漲 10%~30%'),
            GameEvent('利空新聞', '市場恐慌，隨機一檔股票大跌！', self.negative_news, '隨機一檔股票價格下跌 10%~30%'),
            GameEvent('黑天鵝事件', '突發黑天鵝，所有股票下跌，貸款利率上升！', self.black_swan, '所有股票價格下跌 20%~40%，貸款利率+0.2%'),
            GameEvent('銀行優惠', '銀行推出存款優惠，存款利率暫時提升！', self.deposit_bonus, '存款利率+1%'),
            GameEvent('利率調降', '央行調降利率，存款利率下降！', self.deposit_rate_down, '存款利率-0.5%（最低0.1%）'),
            GameEvent('現金紅包', '獲得現金紅包，現金增加！', self.cash_bonus, '現金隨機增加 $200~$1000'),
            GameEvent('意外支出', '突發意外支出，現金減少！', self.cash_penalty, '現金隨機減少 $50~$300'),
            GameEvent('貸款減免', '銀行減免部分貸款，貸款減少！', self.loan_reduction, '貸款減少 $100~$500'),
            GameEvent('貸款催繳', '銀行催繳貸款，必須立即還款！', self.loan_penalty, '現金與貸款同時減少 $100~$500（若現金足夠）'),
            GameEvent('科技突破', '科技公司突破創新，所有科技業股票上漲！', self.tech_boom, '所有科技業股票價格上漲 5%~20%'),
            GameEvent('產業危機', '產業危機，隨機一個產業所有股票下跌！', self.industry_crisis, '隨機一個產業所有股票價格下跌 5%~20%'),
            GameEvent('產業利多', '隨機一個產業獲得利多，該產業所有股票大漲！', self.industry_boom, '隨機一個產業所有股票價格上漲 15%~30%'),
            GameEvent('產業利空', '隨機一個產業遭遇利空，該產業所有股票大跌！', self.industry_bust, '隨機一個產業所有股票價格下跌 10%~30%'),
            GameEvent('公司利多', '隨機一家公司獲得利多，該公司股價大漲！', self.company_boom, '隨機一家公司股價上漲 20%~50%'),
            GameEvent('公司利空', '隨機一家公司遭遇利空，該公司股價大跌！', self.company_bust, '隨機一家公司股價下跌 15%~40%'),
            GameEvent('通膨來襲', '通膨來襲，所有股票價格上漲，現金購買力下降！', self.inflation, '所有股票價格上漲 5%~15%，現金-2%'),
            GameEvent('通縮來襲', '通縮來襲，所有股票價格下跌，現金購買力上升！', self.deflation, '所有股票價格下跌 5%~15%，現金+2%'),
            GameEvent('突發稅金', '政府徵收突發稅金，現金減少！', self.tax_event, '現金減少 $100~$500'),
            GameEvent('投資講座', '參加投資講座，可能有正負效果！', self.investment_seminar, '現金隨機增加 $200~$800 或減少 $100~$400'),
        ]
        return events

    def trigger_random_event(self):
        event = random.choice(self.events)
        effect_result = event.effect_func()
        msg = f"隨機事件：{event.name} - {event.description}"
        if effect_result:
            msg += f"｜影響：{effect_result}"
        self.game.log_transaction(msg)
        return msg

    def positive_news(self):
        # 隨機一檔科技業股票大漲
        tech_stocks = [k for k, v in self.game.data.stocks.items() if v['industry'] == '科技業']
        if not tech_stocks:
            return None
        code = random.choice(tech_stocks)
        stock = self.game.data.stocks[code]
        percent = random.randint(10, 30)
        stock['price'] *= (1 + percent / 100)
        stock['price'] = round(stock['price'], 2)
        stock['history'].append(stock['price'])
        return f"{stock['name']}價格上漲 {percent}%"

    def negative_news(self):
        stock = random.choice(list(self.game.data.stocks.values()))
        stock['price'] *= random.uniform(0.7, 0.9)

    def black_swan(self):
        for stock in self.game.data.stocks.values():
            stock['price'] *= random.uniform(0.6, 0.8)
        self.game.data.loan_interest_rate += 0.002

    def deposit_bonus(self):
        self.game.data.deposit_interest_rate += 0.01
        return f"存款利率提升至 {self.game.data.deposit_interest_rate*100:.2f}%"

    def deposit_rate_down(self):
        self.game.data.deposit_interest_rate = max(0.001, self.game.data.deposit_interest_rate - 0.005)

    def cash_bonus(self):
        amount = random.randint(200, 1000)
        self.game.data.cash += amount
        return f"現金增加 ${amount}"

    def cash_penalty(self):
        self.game.data.cash = max(0, self.game.data.cash - random.randint(50, 300))

    def loan_reduction(self):
        amount = random.randint(100, 500)
        self.game.data.loan = max(0, self.game.data.loan - amount)
        return f"貸款減少 ${amount}"

    def loan_penalty(self):
        penalty = min(self.game.data.loan, random.randint(100, 500))
        if self.game.data.cash >= penalty:
            self.game.data.cash -= penalty
            self.game.data.loan -= penalty
        # 若現金不足則不處理

    def tech_boom(self):
        # 所有科技業股票上漲
        up_list = []
        for k, v in self.game.data.stocks.items():
            if v['industry'] == '科技業':
                percent = random.randint(5, 20)
                v['price'] *= (1 + percent / 100)
                v['price'] = round(v['price'], 2)
                v['history'].append(v['price'])
                up_list.append(f"{v['name']}上漲 {percent}%")
        return '，'.join(up_list) if up_list else None

    def industry_crisis(self):
        for stock in self.game.data.stocks.values():
            stock['price'] *= random.uniform(0.8, 0.95)

    def industry_boom(self):
        # 隨機一個產業所有股票大漲
        industries = list({v['industry'] for v in self.game.data.stocks.values()})
        if not industries:
            return None
        ind = random.choice(industries)
        up_list = []
        for k, v in self.game.data.stocks.items():
            if v['industry'] == ind:
                percent = random.randint(15, 30)
                v['price'] *= (1 + percent / 100)
                v['price'] = round(v['price'], 2)
                v['history'].append(v['price'])
                up_list.append(f"{v['name']}上漲 {percent}%")
        return '，'.join(up_list) if up_list else None

    def industry_bust(self):
        industries = list({v['industry'] for v in self.game.data.stocks.values()})
        target = random.choice(industries)
        for stock in self.game.data.stocks.values():
            if stock['industry'] == target:
                stock['price'] *= random.uniform(0.7, 0.9)
        # BUG FIX: 返回效果字串，而不是直接呼叫UI
        return f"{target} 相關股票全面下跌！"

    def company_boom(self):
        # 隨機一家公司股價大漲
        codes = list(self.game.data.stocks.keys())
        if not codes:
            return None
        code = random.choice(codes)
        stock = self.game.data.stocks[code]
        percent = random.randint(20, 50)
        stock['price'] *= (1 + percent / 100)
        stock['price'] = round(stock['price'], 2)
        stock['history'].append(stock['price'])
        return f"{stock['name']}上漲 {percent}%"

    def company_bust(self):
        stock = random.choice(list(self.game.data.stocks.values()))
        stock['price'] *= random.uniform(0.6, 0.85)
        # BUG FIX: 返回效果字串，而不是直接呼叫UI
        return f"{stock['name']} 股價大跌！"

    def inflation(self):
        for stock in self.game.data.stocks.values():
            stock['price'] *= random.uniform(1.05, 1.15)
        self.game.data.cash *= 0.98
        # BUG FIX: 返回效果字串，而不是直接呼叫UI
        return "所有股票價格上漲，但現金購買力下降！"

    def deflation(self):
        for stock in self.game.data.stocks.values():
            stock['price'] *= random.uniform(0.85, 0.95)
        self.game.data.cash *= 1.02
        # BUG FIX: 返回效果字串，而不是直接呼叫UI
        return "所有股票價格下跌，但現金購買力上升！"

    def tax_event(self):
        tax = random.randint(100, 500)
        self.game.data.cash = max(0, self.game.data.cash - tax)
        # BUG FIX: 返回效果字串，而不是直接呼叫UI
        return f"現金減少 ${tax}"

    def investment_seminar(self):
        # BUG FIX: 原本只實現了正面效果，現在補上負面效果
        if random.random() < 0.6: # 60% 機率獲得正面效果
            amount = random.randint(200, 800)
            self.game.data.cash += amount
            return f"現金增加 ${amount}"
        else: # 40% 機率獲得負面效果
            amount = random.randint(100, 400)
            self.game.data.cash = max(0, self.game.data.cash - amount)
            return f"現金減少 ${amount}"