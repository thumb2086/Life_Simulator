import random
from typing import List, Dict, Any

class EntrepreneurshipManager:
    """
    管理創業相關邏輯：建立/移除事業、每日結算、招募人才。
    - 事業結構：{
        name, level, revenue_per_day, cost_per_day,
        next_upgrade_cost, start_cost, employees: [ {name, tier, salary_per_day, productivity_per_day} ]
      }
    - 淨額 = 事業自身收入 - 自身成本 + Σ(員工生產力) - Σ(員工薪水)
    """
    def __init__(self, game):
        self.game = game
        self.data = game.data
        # 基本參數
        self.default_start_cost = 500.0  # 創業門檻
        self.recruit_fee = 50.0          # 每次招募費用
        # 招募卡池（權重）：tier -> (權重, 薪資範圍, 生產力範圍)
        # 注意：數值單位皆為/日
        self.tier_pool = {
            'S': {'weight': 5,  'salary': (120.0, 180.0), 'prod': (300.0, 450.0)},
            'A': {'weight': 15, 'salary': (90.0, 130.0),  'prod': (180.0, 280.0)},
            'B': {'weight': 30, 'salary': (60.0, 90.0),   'prod': (100.0, 160.0)},
            'C': {'weight': 50, 'salary': (30.0, 60.0),   'prod': (40.0, 90.0)},
        }

    # --------- 基礎工具 ---------
    def _ensure(self):
        if not hasattr(self.data, 'businesses') or not isinstance(self.data.businesses, list):
            self.data.businesses = []

    def _roll_tier(self) -> str:
        items = []
        for t, info in self.tier_pool.items():
            items.extend([t] * int(info['weight']))
        return random.choice(items)

    def _roll_range(self, low: float, high: float) -> float:
        return round(random.uniform(low, high), 2)

    # --------- 介面 API ---------
    def process_daily(self):
        """每日結算所有事業的淨額，累加到現金並寫交易記錄。"""
        self._ensure()
        total_net = 0.0
        for b in self.data.businesses:
            rev = float(b.get('revenue_per_day', 0.0))
            cost = float(b.get('cost_per_day', 0.0))
            employees: List[Dict[str, Any]] = b.get('employees', []) or []
            emp_prod = sum(float(e.get('productivity_per_day', 0.0)) for e in employees)
            emp_salary = sum(float(e.get('salary_per_day', 0.0)) for e in employees)
            net = (rev + emp_prod) - (cost + emp_salary)
            total_net += net
        if abs(total_net) > 1e-9:
            self.data.cash += total_net
            self.game.log_transaction(f"創業收益（淨額） ${total_net:.2f}")

    def add_business(self, name: str, rev: float, cost: float) -> bool:
        """建立新事業，需支付 start_cost 門檻。"""
        self._ensure()
        start_cost = max(self.default_start_cost, rev * 5)
        if self.data.cash < start_cost:
            self.game.log_transaction(f"創業失敗：需要門檻 ${start_cost:.2f}（現金不足）")
            return False
        self.data.cash -= start_cost
        biz = {
            'name': name or '事業',
            'level': 1,
            'revenue_per_day': float(rev),
            'cost_per_day': float(cost),
            'next_upgrade_cost': max(100.0, float(rev) * 10),
            'start_cost': start_cost,
            'employees': [],
        }
        self.data.businesses.append(biz)
        self.game.log_transaction(f"創立事業：{biz['name']}（門檻 ${start_cost:.2f}，收入 ${rev:.2f} / 成本 ${cost:.2f}）")
        return True

    def remove_business(self, index: int) -> bool:
        self._ensure()
        if 0 <= index < len(self.data.businesses):
            b = self.data.businesses.pop(index)
            self.game.log_transaction(f"關閉事業：{b.get('name','事業')}")
            return True
        return False

    def recruit_employee(self, biz_index: int) -> str:
        """
        支付招募費用，隨機獲得一位員工。回傳描述文字。
        員工結構：{name, tier, salary_per_day, productivity_per_day}
        """
        self._ensure()
        if not (0 <= biz_index < len(self.data.businesses)):
            return "請先選擇事業！"
        if self.data.cash < self.recruit_fee:
            return f"招募失敗：需要 ${self.recruit_fee:.2f} 招募費"
        self.data.cash -= self.recruit_fee
        tier = self._roll_tier()
        cfg = self.tier_pool[tier]
        salary = self._roll_range(*cfg['salary'])
        prod = self._roll_range(*cfg['prod'])
        emp = {
            'name': f"員工#{random.randint(1000,9999)}",
            'tier': tier,
            'salary_per_day': salary,
            'productivity_per_day': prod,
        }
        self.data.businesses[biz_index].setdefault('employees', []).append(emp)
        msg = f"招募到 {tier} 級員工：{emp['name']}｜薪資 ${salary:.2f}/日｜生產力 ${prod:.2f}/日"
        self.game.log_transaction(msg)
        return msg

    # --------- 顯示工具 ---------
    @staticmethod
    def format_business_row(b: Dict[str, Any]) -> str:
        name = b.get('name','事業')
        lvl = int(b.get('level',1))
        rev = float(b.get('revenue_per_day',0.0))
        cost = float(b.get('cost_per_day',0.0))
        emps: List[Dict[str, Any]] = b.get('employees', []) or []
        emp_prod = sum(float(e.get('productivity_per_day', 0.0)) for e in emps)
        emp_salary = sum(float(e.get('salary_per_day', 0.0)) for e in emps)
        net = (rev + emp_prod) - (cost + emp_salary)
        return f"{name} Lv.{lvl} | 收入 ${rev:.2f} | 成本 ${cost:.2f} | 員工 {len(emps)} | 淨額 ${net:.2f}"

    def get_business_rows(self) -> List[str]:
        self._ensure()
        return [self.format_business_row(b) for b in self.data.businesses]
