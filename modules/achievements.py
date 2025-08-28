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
        # 擴充成就系統，包含多種類型與進度追蹤
        return [
            # 基礎股票成就
            Achievement('first_stock', '第一次買股票', '成功購買任一股票', lambda gd: any(s['owned'] > 0 for s in gd.stocks.values()), '股票'),
            Achievement('stock_portfolio_5', '投資組合擴張', '擁有5種不同股票', lambda gd: sum(1 for s in gd.stocks.values() if s['owned'] > 0) >= 5, '股票'),
            Achievement('stock_portfolio_10', '全方位投資者', '擁有10種不同股票', lambda gd: sum(1 for s in gd.stocks.values() if s['owned'] > 0) >= 10, '股票'),
            Achievement('stock_millionaire', '股票百萬富翁', '股票投資總價值超過$100萬', lambda gd: sum(s['price'] * s['owned'] for s in gd.stocks.values() if s['name'] != '比特幣') >= 1000000, '股票'),
            
            # 比特幣成就
            Achievement('btc_first', '加密貨幣新手', '首次購買比特幣', lambda gd: gd.btc_balance > 0, '加密貨幣'),
            Achievement('btc_whale', '比特幣鯨魚', '擁有價值超過$10萬的比特幣', lambda gd: gd.btc_balance * gd.stocks['BTC']['price'] >= 100000, '加密貨幣'),
            
            # 基金成就
            Achievement('fund_first', '基金投資者', '首次購買基金', lambda gd: any(f['units'] > 0 for f in gd.funds.values()), '基金'),
            Achievement('fund_diversified', '多元化投資', '擁有所有類型的基金', lambda gd: all(f['units'] > 0 for f in gd.funds.values()), '基金'),
            
            # 理財成就
            Achievement('rich', '資產破萬', '總資產達到 $10,000', lambda gd: gd.total_assets() >= 10000, '理財'),
            Achievement('wealthy', '小有積蓄', '總資產達到 $100,000', lambda gd: gd.total_assets() >= 100000, '理財'),
            Achievement('millionaire', '百萬富翁', '總資產達到 $1,000,000', lambda gd: gd.total_assets() >= 1000000, '理財'),
            Achievement('multimillionaire', '千萬富翁', '總資產達到 $10,000,000', lambda gd: gd.total_assets() >= 10000000, '理財'),
            Achievement('billionaire', '億萬富翁', '總資產達到 $100,000,000', lambda gd: gd.total_assets() >= 100000000, '理財'),
            Achievement('payoff_loan', '還清貸款', '貸款歸零', lambda gd: gd.loan == 0, '理財'),
            Achievement('debt_free', '債務自由', '在擁有$100萬資產的同時保持零貸款', lambda gd: gd.total_assets() >= 1000000 and gd.loan == 0, '理財'),
            
            # 工作成就
            Achievement('first_job', '初入職場', '獲得第一份工作', lambda gd: gd.job is not None, '職業'),
            Achievement('career_advancement', '職業晉升', '工作等級達到3級以上', lambda gd: gd.job and gd.job.get('level', 0) >= 3, '職業'),
            Achievement('executive', '企業高管', '成為經理或更高職位', lambda gd: gd.job and gd.job.get('name', '') in ['資深工程師', '經理'], '職業'),
            
            # 教育成就
            Achievement('graduate', '大學畢業', '學歷達到大學', lambda gd: gd.education_level in ['大學', '碩士', '博士'], '教育'),
            Achievement('masters', '碩士學位', '學歷達到碩士', lambda gd: gd.education_level in ['碩士', '博士'], '教育'),
            Achievement('phd', '博士學位', '學歷達到博士', lambda gd: gd.education_level == '博士', '教育'),
            
            # 屬性成就
            Achievement('happy_life', '幸福人生', '快樂度達到90以上', lambda gd: gd.happiness >= 90, '屬性'),
            Achievement('energized', '精力充沛', '體力值達到90以上', lambda gd: gd.stamina >= 90, '屬性'),
            Achievement('genius', '天才', '智力值達到90以上', lambda gd: gd.intelligence >= 90, '屬性'),
            Achievement('diligent_worker', '勤奮工作者', '勤奮度達到90以上', lambda gd: gd.diligence >= 90, '屬性'),
            Achievement('charismatic', '魅力四射', '魅力值達到90以上', lambda gd: gd.charisma >= 90, '屬性'),
            Achievement('lucky_charm', '幸運兒', '今日運氣達到90以上', lambda gd: gd.luck_today >= 90, '屬性'),
            Achievement('experienced', '經驗豐富', '經驗值達到500以上', lambda gd: gd.experience >= 500, '屬性'),
            Achievement('well_balanced', '均衡發展', '所有屬性都達到70以上', lambda gd: all(getattr(gd, attr, 0) >= 70 for attr in ['happiness', 'stamina', 'intelligence', 'diligence', 'charisma']), '屬性'),
            
            # 活動成就
            Achievement('studious', '勤學好問', '完成讀書活動50次', lambda gd: getattr(gd, 'activity_study_count', 0) >= 50, '活動'),
            Achievement('fitness_freak', '健身狂熱者', '完成健身活動50次', lambda gd: getattr(gd, 'activity_workout_count', 0) >= 50, '活動'),
            Achievement('social_butterfly', '社交高手', '完成社交活動50次', lambda gd: getattr(gd, 'activity_social_count', 0) >= 50, '活動'),
            Achievement('zen_master', '禪定大師', '完成冥想活動50次', lambda gd: getattr(gd, 'activity_meditate_count', 0) >= 50, '活動'),
            
            # 事件成就
            Achievement('event_survivor', '事件生存者', '經歷50個隨機事件', lambda gd: getattr(gd, 'event_count', 0) >= 50, '事件'),
            Achievement('lucky_day', '幸運日', '單日獲得3個正面事件', lambda gd: getattr(gd, 'daily_positive_events', 0) >= 3, '事件'),
            Achievement('crisis_manager', '危機管理', '成功度過5個黑天鵝事件', lambda gd: getattr(gd, 'black_swan_survived', 0) >= 5, '事件'),
            
            # 遊戲進度成就
            Achievement('survivor', '生存者', '遊戲進行超過100天', lambda gd: gd.days >= 100, '進度'),
            Achievement('veteran', '老兵', '遊戲進行超過365天', lambda gd: gd.days >= 365, '進度'),
            Achievement('decade', '十年玩家', '遊戲進行超過3650天', lambda gd: gd.days >= 3650, '進度'),
            Achievement('rebirth', '重生者', '進行第一次重生', lambda gd: gd.reborn_count >= 1, '進度'),
            Achievement('rebirth_master', '重生大師', '進行10次重生', lambda gd: gd.reborn_count >= 10, '進度'),
            Achievement('rebirth_legend', '重生傳說', '進行50次重生', lambda gd: gd.reborn_count >= 50, '進度'),
            
            # 特殊成就
            Achievement('jackpot', '頭獎得主', '單筆交易獲利超過$10萬', lambda gd: getattr(gd, 'max_single_profit', 0) >= 100000, '特殊'),
            Achievement('perfect_day', '完美的一天', '單日所有屬性都達90以上', lambda gd: getattr(gd, 'perfect_day_count', 0) >= 1, '特殊'),
            Achievement('trading_master', '交易大師', '累積交易次數超過1000次', lambda gd: len(gd.transaction_history) >= 1000, '特殊'),
            Achievement('collection_master', '收藏家', '收集所有種類的消耗品', lambda gd: len(gd.inventory) >= len(gd.consumables), '特殊'),
            
            # 賭場成就
            Achievement('slot_bigwin', '拉霸大贏家', '拉霸單次贏得超過 $1000', lambda gd: gd.last_slot_win >= 1000, '賭場'),
            Achievement('slot_totalwin', '拉霸累積贏家', '拉霸累積贏得超過 $5000', lambda gd: getattr(gd, 'slot_total_win', 0) >= 5000, '賭場'),
            Achievement('slot_streak', '拉霸連勝三場', '拉霸連續三次贏錢', lambda gd: getattr(gd, 'slot_win_streak', 0) >= 3, '賭場'),
            
            # 創業成就
            Achievement('entrepreneur', '企業家', '創辦第一家事業', lambda gd: len(gd.businesses) >= 1, '創業'),
            Achievement('business_empire', '商業帝國', '同時經營5家事業', lambda gd: len(gd.businesses) >= 5, '創業'),
            Achievement('business_tycoon', '商業大亨', '事業每日總收入超過$10萬', lambda gd: sum(b.get('revenue_per_day', 0) for b in gd.businesses) >= 100000, '創業'),
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

    def get_by_category(self, category):
        """按類別獲取成就"""
        return [a for a in self.achievements if a.category == category]
    
    def get_unlocked_by_category(self, category):
        """按類別獲取已解鎖成就"""
        return [a for a in self.achievements if a.category == category and a.unlocked]
    
    def get_completion_rate(self):
        """獲取成就完成率"""
        total = len(self.achievements)
        unlocked = len(self.get_unlocked())
        return unlocked / total if total > 0 else 0
    
    def get_category_stats(self):
        """獲取各類別成就統計"""
        categories = {}
        for ach in self.achievements:
            if ach.category not in categories:
                categories[ach.category] = {'total': 0, 'unlocked': 0}
            categories[ach.category]['total'] += 1
            if ach.unlocked:
                categories[ach.category]['unlocked'] += 1
        
        # 計算完成率
        for cat in categories:
            total = categories[cat]['total']
            unlocked = categories[cat]['unlocked']
            categories[cat]['rate'] = unlocked / total if total > 0 else 0
        
        return categories 