class TransactionManager:
    def __init__(self, game_data, log_func=None, update_display_func=None):
        self.data = game_data
        self.log = log_func
        self.update_display = update_display_func
    # 之後搬移存提款、貸款、資金流動等方法 