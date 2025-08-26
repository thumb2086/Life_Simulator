class DividendManager:
    """
    Handles stock dividend and DRIP processing on a daily basis.
    Delegated from BankGame.unified_timer() at end-of-day.
    """
    def __init__(self, game):
        self.game = game

    def process_daily(self):
        """
        Iterate all stocks and, if a stock reaches its next_dividend_day,
        pay dividend either to cash or via DRIP (reinvestment). Always moves
        next_dividend_day forward by dividend_interval (default 30).
        """
        data = self.game.data
        today = data.days
        for code, stock in data.stocks.items():
            try:
                next_day = int(stock.get('next_dividend_day', 30))
                if today >= next_day:
                    owned = int(stock.get('owned', 0))
                    dps = float(stock.get('dividend_per_share', 0.0))
                    if owned > 0 and dps > 0:
                        dividend = owned * dps
                        if stock.get('drip'):
                            price = float(stock.get('price', 0.0)) or 0.0
                            shares = int(dividend // price) if price > 0 else 0
                            leftover = dividend - shares * price
                            if shares > 0:
                                # use internal helper to keep logs/cost consistent
                                self.game._buy_stock_by_code(code, shares, log_prefix="DRIP再投資")
                            if leftover > 0:
                                data.cash += leftover
                            msg = f"{stock.get('name', code)} 配息（DRIP）：配息 ${dividend:.2f}，再投資買入 {shares} 股，餘額 ${leftover:.2f}"
                            self.game.log_transaction(msg)
                            self.game.show_event_message(msg)
                        else:
                            data.cash += dividend
                            msg = f"{stock.get('name', code)} 配息：持有 {owned} 股，獲得股息 ${dividend:.2f}"
                            self.game.log_transaction(msg)
                            self.game.show_event_message(msg)
                    # move next dividend day forward
                    interval = int(stock.get('dividend_interval', 30))
                    stock['next_dividend_day'] = today + interval
            except Exception as e:
                # safe log; avoid breaking daily tick
                try:
                    self.game.debug_log(f"dividend processing error({code}): {e}")
                except Exception:
                    pass
