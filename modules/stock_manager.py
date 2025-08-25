class StockManager:
    def __init__(self, game_data, log_func=None, update_display_func=None):
        self.data = game_data
        self.log = log_func
        self.update_display = update_display_func
    # 股票分頁買入
    def buy_stock_industry(self, industry, industry_stock_vars, industry_stock_amount_entries, show_event_message, check_achievements, trade_tip_label=None, update_stock_status_labels=None, update_trade_log=None):
        stock_var = industry_stock_vars[industry]
        stock_name = stock_var.get()
        stock_code = None
        for k, v in self.data.stocks.items():
            if v['name'] == stock_name and v['industry'] == industry:
                stock_code = k
                break
        if stock_code is None:
            show_event_message("找不到該股票！")
            return
        try:
            amount = int(industry_stock_amount_entries[industry].get())
        except Exception:
            show_event_message("請輸入有效股數！")
            return
        if amount <= 0:
            show_event_message("請輸入正整數股數！")
            return
        stock = self.data.stocks[stock_code]
        price = stock['price']
        total_cost = amount * price
        if total_cost > self.data.cash:
            show_event_message("現金不足！")
            return
        stock['owned'] += amount
        stock['total_cost'] += total_cost
        self.data.cash -= total_cost
        idx = len(stock['history']) - 1
        stock['buy_points'].append((idx, price))
        self.log(f"已購買 {amount} 股 {stock['name']}，花費 ${total_cost:.2f}")
        self.update_display()
        check_achievements()
        if trade_tip_label:
            trade_tip_label.config(text=f"買入 {amount} 股，價格 ${price:.2f}，持有 {stock['owned']} 股")
        if update_stock_status_labels:
            update_stock_status_labels()
        if update_trade_log:
            update_trade_log("買入", amount, price, stock['name'])
    # 股票分頁賣出
    def sell_stock_industry(self, industry, industry_stock_vars, industry_stock_amount_entries, show_event_message, check_achievements, trade_tip_label=None, update_stock_status_labels=None, update_trade_log=None):
        stock_var = industry_stock_vars[industry]
        stock_name = stock_var.get()
        stock_code = None
        for k, v in self.data.stocks.items():
            if v['name'] == stock_name and v['industry'] == industry:
                stock_code = k
                break
        if stock_code is None:
            show_event_message("找不到該股票！")
            return
        try:
            amount = int(industry_stock_amount_entries[industry].get())
        except Exception:
            show_event_message("請輸入有效股數！")
            return
        if amount <= 0:
            show_event_message("請輸入正整數股數！")
            return
        stock = self.data.stocks[stock_code]
        if amount > stock['owned']:
            show_event_message(f"持有股票不足！目前持有 {stock['owned']} 股")
            return
        price = stock['price']
        total_value = amount * price
        stock['owned'] -= amount
        if stock['owned'] == 0:
            stock['total_cost'] = 0
        else:
            stock['total_cost'] *= (stock['owned']) / (stock['owned'] + amount)
        self.data.cash += total_value
        idx = len(stock['history']) - 1
        if stock['buy_points']:
            stock['buy_points'].pop(0)
        stock['sell_points'].append((idx, price))
        self.log(f"已賣出 {amount} 股 {stock['name']}，獲得 ${total_value:.2f}")
        self.update_display()
        check_achievements()
        if trade_tip_label:
            trade_tip_label.config(text=f"賣出 {amount} 股，價格 ${price:.2f}，持有 {stock['owned']} 股")
        if update_stock_status_labels:
            update_stock_status_labels()
        if update_trade_log:
            update_trade_log("賣出", amount, price, stock['name']) 