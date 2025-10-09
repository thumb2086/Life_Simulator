class PlayerAttributes:
    """代表玩家的屬性。"""
    def __init__(self):
        # 基礎屬性
        self.happiness = 50      # 幸福度
        self.stamina = 50       # 體力
        self.intelligence = 50  # 智力
        self.diligence = 50    # 勤奮度
        self.charisma = 50     # 魅力
        self.experience = 0     # 經驗值
        self.luck_today = 50    # 今日幸運值
        self.last_luck_day = -1  # 上次更新幸運值的日期
        
        # 新增擴展屬性
        self.creativity = 50    # 創造力
        self.wisdom = 50       # 智慧
        self.resilience = 50   # 韌性
        self.focus = 50        # 專注力
        self.social_network = 50  # 人脈關係
        
        # 技能熟練度
        self.skills = {
            'negotiation': 0,     # 談判能力
            'management': 0,      # 管理能力
            'research': 0,        # 研究能力
            'innovation': 0,      # 創新能力
            'leadership': 0,      # 領導力
        }
        
        # 特殊狀態
        self.status_effects = []  # 當前狀態效果列表