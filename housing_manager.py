"""Housing management system for Life Simulator.

Manages player's living situation: renting, buying property, mortgage,
facilities, comfort, and property appreciation.
"""

from __future__ import annotations

import random


# Housing tiers with their properties
HOUSING_TIERS = {
    "租屋": {
        "label": "租屋套房",
        "buy_cost": 0,
        "monthly_cost": 8000,
        "comfort": 30,
        "storage": 0,
        "value": 0,
    },
    "小套房": {
        "label": "小型套房",
        "buy_cost": 250000,
        "monthly_cost": 3000,
        "comfort": 45,
        "storage": 10,
        "value": 250000,
    },
    "公寓": {
        "label": "溫馨公寓",
        "buy_cost": 600000,
        "monthly_cost": 2000,
        "comfort": 60,
        "storage": 25,
        "value": 600000,
    },
    "透天": {
        "label": "獨棟透天",
        "buy_cost": 1500000,
        "monthly_cost": 1500,
        "comfort": 75,
        "storage": 50,
        "value": 1500000,
    },
    "豪宅": {
        "label": "豪華別墅",
        "buy_cost": 5000000,
        "monthly_cost": 1000,
        "comfort": 95,
        "storage": 100,
        "value": 5000000,
    },
}

HOUSING_ORDER = ["租屋", "小套房", "公寓", "透天", "豪宅"]

FACILITIES = {
    "冷氣": {"cost": 15000, "comfort_bonus": 5, "monthly_upkeep": 200},
    "洗衣機": {"cost": 12000, "comfort_bonus": 3, "monthly_upkeep": 50},
    "健身房": {"cost": 30000, "comfort_bonus": 8, "monthly_upkeep": 0},
    "家庭影院": {"cost": 45000, "comfort_bonus": 10, "monthly_upkeep": 0},
    "智能家電": {"cost": 60000, "comfort_bonus": 12, "monthly_upkeep": 100},
}


class HousingManager:
    """Manages player housing, mortgage, facilities, and property value."""

    def __init__(self, data) -> None:
        self.data = data


    # ── Daily Processing ──────────────────────────────────────────────

    def process_daily(self) -> str:
        """Process daily housing costs and property appreciation."""
        house = self.data.housing
        messages = []

        # Monthly rent / mortgage payment (every 30 days)
        if self.data.days % 30 == 0 and self.data.days > 0:
            tier = HOUSING_TIERS.get(house["type"], HOUSING_TIERS["租屋"])
            cost = tier["monthly_cost"]

            # Facility upkeep
            for fac_name in house.get("facilities", []):
                fac = FACILITIES.get(fac_name, {})
                cost += fac.get("monthly_upkeep", 0)

            if cost > 0:
                if self.data.cash >= cost:
                    self.data.cash -= cost
                    if house["mortgage"] > 0:
                        principal = min(cost * 0.6, house["mortgage"])
                        house["mortgage"] -= principal
                    messages.append(f"房屋支出 ${cost:,.0f}（租金/貸款+管理費）。")
                else:
                    # Can't pay - stress increases
                    self.data.health["stress"] = min(100, self.data.health["stress"] + 15)
                    messages.append("無法支付房屋費用，壓力上升！")

        # Property appreciation (slow)
        if house["property_value"] > 0:
            appreciation = random.uniform(0.0001, 0.0005)
            house["property_value"] *= (1 + appreciation)

        # Comfort affects mood
        comfort = self._calc_comfort()
        house["comfort"] = comfort
        if comfort >= 70:
            self.data.health["mood"] = min(100, self.data.health["mood"] + 2)
        elif comfort < 30:
            self.data.health["mood"] = max(0, self.data.health["mood"] - 1)

        return "\n".join(messages) if messages else "房屋狀況正常。"

    # ── Player Actions ────────────────────────────────────────────────

    def buy_property(self, housing_type: str) -> str:
        """Purchase a new property (upgrade from current)."""
        house = self.data.housing
        if housing_type not in HOUSING_TIERS:
            return f"未知的房型：{housing_type}。可選：{', '.join(HOUSING_ORDER)}"
        tier = HOUSING_TIERS[housing_type]
        current_idx = HOUSING_ORDER.index(house["type"]) if house["type"] in HOUSING_ORDER else 0
        target_idx = HOUSING_ORDER.index(housing_type)
        if target_idx <= current_idx:
            return "只能升級，不能降級。"
        cost = tier["buy_cost"]
        if self.data.cash < cost:
            return f"現金不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        # Sell old property (recover 70% of value)
        old_value = house.get("property_value", 0)
        refund = int(old_value * 0.7)
        self.data.cash += refund
        # Update housing
        house["type"] = housing_type
        house["property_value"] = tier["value"]
        house["mortgage"] = 0
        house["monthly_cost"] = tier["monthly_cost"]
        house["storage"] = tier["storage"]
        house["facilities"] = []
        msg = f"購入{tier['label']}（${cost:,.0f}），舊房回收 ${refund:,.0f}。"
        return msg

    def take_mortgage(self, amount: float) -> str:
        """Take out a mortgage loan for property purchase."""
        house = self.data.housing
        if house["type"] == "租屋":
            return "租屋無法辦理房貸。"
        max_mortgage = HOUSING_TIERS[house["type"]]["value"] * 0.7
        if house["mortgage"] + amount > max_mortgage:
            return f"房貸額度上限 ${max_mortgage:,.0f}，目前已有 ${house['mortgage']:,.0f}。"
        house["mortgage"] += amount
        self.data.cash += amount
        return f"辦理房貸 ${amount:,.0f}，總房貸 ${house['mortgage']:,.0f}。"

    def install_facility(self, facility_name: str) -> str:
        """Install a facility in current home."""
        house = self.data.housing
        if facility_name not in FACILITIES:
            return f"未知設備：{facility_name}。可選：{', '.join(FACILITIES.keys())}"
        if facility_name in house.get("facilities", []):
            return f"已安裝{facility_name}。"
        fac = FACILITIES[facility_name]
        cost = fac["cost"]
        if self.data.cash < cost:
            return f"現金不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        house.setdefault("facilities", []).append(facility_name)
        return f"安裝{facility_name}（${cost:,.0f}），舒適度 +{fac['comfort_bonus']}。"

    def rent_property(self) -> str:
        """Start renting (initial setup)."""
        house = self.data.housing
        if house["type"] != "租屋":
            return f"你已經有房產（{house['type']}）。"
        cost = 16000  # First + last month
        if self.data.cash < cost:
            return f"現金不足，需要 ${cost:,.0f}（兩個月押金）。"
        self.data.cash -= cost
        house["monthly_cost"] = HOUSING_TIERS["租屋"]["monthly_cost"]
        return f"租屋 setup 完成（${cost:,.0f}押金），月租 ${house['monthly_cost']:,.0f}。"

    def sell_property(self) -> str:
        """Sell current property and downgrade to renting."""
        house = self.data.housing
        if house["type"] == "租屋":
            return "你沒有房產可出售。"
        tier = HOUSING_TIERS[house["type"]]
        sale_price = int(house["property_value"] * 0.85)  # 15% transaction cost
        self.data.cash += sale_price
        mortgage_remaining = house["mortgage"]
        self.data.cash -= mortgage_remaining
        house["type"] = "租屋"
        house["property_value"] = 0
        house["mortgage"] = 0
        house["monthly_cost"] = HOUSING_TIERS["租屋"]["monthly_cost"]
        house["storage"] = 0
        house["facilities"] = []
        return f"出售房產，得款 ${sale_price:,.0f}，償還貸款 ${mortgage_remaining:,.0f}。"

    # ── Queries ───────────────────────────────────────────────────────

    def comfort_bonus(self) -> float:
        """Return mood/efficiency multiplier from housing comfort."""
        comfort = self._calc_comfort()
        if comfort >= 80:
            return 1.1
        elif comfort >= 60:
            return 1.05
        elif comfort >= 40:
            return 1.0
        else:
            return 0.95

    def monthly_cost(self) -> float:
        """Return total monthly housing cost."""
        house = self.data.housing
        tier = HOUSING_TIERS.get(house["type"], HOUSING_TIERS["租屋"])
        cost = tier["monthly_cost"]
        for fac_name in house.get("facilities", []):
            fac = FACILITIES.get(fac_name, {})
            cost += fac.get("monthly_upkeep", 0)
        return cost

    def status_text(self) -> str:
        """Return formatted housing status."""
        house = self.data.housing
        tier = HOUSING_TIERS.get(house["type"], {})
        facilities = ", ".join(house.get("facilities", [])) or "無"
        return (
            f"房型：{tier.get('label', house['type'])} | "
            f"市值 ${house['property_value']:,.0f} | "
            f"房貸 ${house['mortgage']:,.0f} | "
            f"舒適度 {house['comfort']} | "
            f"設備：{facilities}"
        )

    def _calc_comfort(self) -> int:
        """Calculate total comfort from housing type + facilities."""
        house = self.data.housing
        tier = HOUSING_TIERS.get(house["type"], HOUSING_TIERS["租屋"])
        base = tier["comfort"]
        for fac_name in house.get("facilities", []):
            fac = FACILITIES.get(fac_name, {})
            base += fac.get("comfort_bonus", 0)
        return min(100, base)
