class Achievement:
    def __init__(self, key, name, description, condition, category):
        self.key = key
        self.name = name
        self.description = description
        self.condition = condition
        self.category = category
        self.unlocked = False

class AchievementsManager:
    def __init__(self, game_data, unlocked_keys=None):
        self.game_data = game_data
        self.achievements = self._init_achievements()
        if unlocked_keys:
            for ach in self.achievements:
                if ach.key in unlocked_keys:
                    ach.unlocked = True

    def _init_achievements(self):
        # 可擴充更多成就
        return [
            Achievement('first_stock', '第一次買股票', '成功購買任一股票', lambda gd: any(s['owned'] > 0 for s in gd.stocks.values()), '股票'),
            Achievement('rich', '資產破萬', '總資產達到 $10,000', lambda gd: gd.total_assets() >= 10000, '理財'),
            Achievement('payoff_loan', '還清貸款', '貸款歸零', lambda gd: gd.loan == 0, '理財'),
            Achievement('slot_bigwin', '拉霸大贏家', '拉霸單次贏得超過 $1000', lambda gd: gd.last_slot_win >= 1000, '賭場'),
            Achievement('slot_totalwin', '拉霸累積贏家', '拉霸累積贏得超過 $5000', lambda gd: getattr(gd, 'slot_total_win', 0) >= 5000, '賭場'),
            Achievement('slot_streak', '拉霸連勝三場', '拉霸連續三次贏錢', lambda gd: getattr(gd, 'slot_win_streak', 0) >= 3, '賭場'),
        ]

    def check_achievements(self):
        unlocked = []
        for ach in self.achievements:
            if not ach.unlocked and ach.condition(self.game_data):
                ach.unlocked = True
                unlocked.append(ach)
        return unlocked

    def get_unlocked(self):
        return [a for a in self.achievements if a.unlocked]

    def get_all(self):
        return self.achievements

    def export_unlocked_keys(self):
        return [a.key for a in self.achievements if a.unlocked] 