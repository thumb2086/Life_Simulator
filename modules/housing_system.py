import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class HousingSystem:
    """房屋系統管理器"""

    def __init__(self, game: 'BankGame'):
        self.game = game

    def can_buy_house(self, house_id):
        """檢查是否可以購買房屋"""
        if house_id not in self.game.data.houses_catalog:
            return False, "無效的房屋類型"

        house = self.game.data.houses_catalog[house_id]

        # 檢查是否已經有房屋
        if self.game.data.current_house is not None:
            return False, "已經擁有一棟房屋，請先賣掉現有房屋"

        # 檢查金錢
        if self.game.data.cash < house['price']:
            return False, f"現金不足，需要 ${house['price']}"

        return True, ""

    def buy_house(self, house_id):
        """購買房屋"""
        can_buy, reason = self.can_buy_house(house_id)
        if not can_buy:
            return False, reason

        house = self.game.data.houses_catalog[house_id]
        self.game.data.cash -= house['price']
        self.game.data.current_house = house_id

        # 設定維護費用到期日（30天後）
        self.game.data.house_maintenance_due = self.game.data.days + 30

        # 計算初始舒適度
        self._update_comfort_level()

        return True, f"成功購買 {house['name']}，花費 ${house['price']}"

    def sell_house(self):
        """賣掉房屋"""
        if self.game.data.current_house is None:
            return False, "沒有房屋可賣"

        house = self.game.data.houses_catalog[self.game.data.current_house]
        sell_price = house['price'] * 0.7  # 7折出售

        self.game.data.cash += sell_price
        self.game.data.current_house = None
        self.game.data.house_furniture.clear()
        self.game.data.house_comfort_level = 0

        return True, f"成功賣出房屋，獲得 ${sell_price:.0f}"

    def can_buy_furniture(self, furniture_id):
        """檢查是否可以購買家具"""
        if furniture_id not in self.game.data.furniture_catalog:
            return False, "無效的家具類型"

        if self.game.data.current_house is None:
            return False, "需要先擁有房屋才能購買家具"

        furniture = self.game.data.furniture_catalog[furniture_id]

        # 檢查金錢
        if self.game.data.cash < furniture['price']:
            return False, f"現金不足，需要 ${furniture['price']}"

        return True, ""

    def buy_furniture(self, furniture_id):
        """購買家具"""
        can_buy, reason = self.can_buy_furniture(furniture_id)
        if not can_buy:
            return False, reason

        furniture = self.game.data.furniture_catalog[furniture_id]
        self.game.data.cash -= furniture['price']

        # 添加到家具清單
        if furniture_id not in self.game.data.house_furniture:
            self.game.data.house_furniture[furniture_id] = 0
        self.game.data.house_furniture[furniture_id] += 1

        # 更新舒適度
        self._update_comfort_level()

        return True, f"成功購買 {furniture['name']}，花費 ${furniture['price']}"

    def _update_comfort_level(self):
        """更新房屋舒適度"""
        comfort = 0

        # 基礎房屋舒適度
        if self.game.data.current_house:
            house = self.game.data.houses_catalog[self.game.data.current_house]
            comfort += house['capacity'] * 5  # 每人基礎舒適度

        # 家具提供的舒適度
        for furniture_id, quantity in self.game.data.house_furniture.items():
            if furniture_id in self.game.data.furniture_catalog:
                furniture = self.game.data.furniture_catalog[furniture_id]
                comfort += furniture['comfort'] * quantity

        self.game.data.house_comfort_level = comfort

    def process_maintenance(self):
        """處理房屋維護費用"""
        if self.game.data.current_house is None:
            return

        if self.game.data.days >= self.game.data.house_maintenance_due:
            house = self.game.data.houses_catalog[self.game.data.current_house]
            maintenance_cost = house['maintenance_cost']

            if self.game.data.cash >= maintenance_cost:
                self.game.data.cash -= maintenance_cost
                self.game.data.house_maintenance_due = self.game.data.days + 30
                return True, f"繳納房屋維護費 ${maintenance_cost}"
            else:
                # 無法繳納維護費，舒適度下降
                self.game.data.house_comfort_level = max(0, self.game.data.house_comfort_level - 10)
                return False, f"無法繳納維護費 ${maintenance_cost}，房屋狀況惡化"

        return None, ""

    def get_house_info(self):
        """獲取房屋資訊"""
        if self.game.data.current_house is None:
            return None

        house = self.game.data.houses_catalog[self.game.data.current_house]
        furniture_count = sum(self.game.data.house_furniture.values())

        return {
            'name': house['name'],
            'comfort_level': self.game.data.house_comfort_level,
            'furniture_count': furniture_count,
            'maintenance_days_left': max(0, self.game.data.house_maintenance_due - self.game.data.days),
            'description': house['description']
        }

    def get_furniture_by_category(self, category):
        """按類別獲取家具"""
        return {k: v for k, v in self.game.data.furniture_catalog.items()
                if v['category'] == category}

    def get_available_upgrades(self):
        """獲取可用的房屋升級選項"""
        if self.game.data.current_house is None:
            return []

        current_house = self.game.data.houses_catalog[self.game.data.current_house]
        current_price = current_house['price']

        # 找到更好的房屋選項
        upgrades = []
        for house_id, house in self.game.data.houses_catalog.items():
            if house['price'] > current_price and house['capacity'] > current_house['capacity']:
                upgrade_cost = house['price'] - (current_price * 0.5)  # 舊房折價50%
                upgrades.append({
                    'house_id': house_id,
                    'name': house['name'],
                    'upgrade_cost': upgrade_cost,
                    'new_capacity': house['capacity'],
                    'description': house['description']
                })

        return sorted(upgrades, key=lambda x: x['upgrade_cost'])

    def upgrade_house(self, house_id):
        """升級房屋"""
        if self.game.data.current_house is None:
            return False, "沒有房屋可升級"

        upgrades = self.get_available_upgrades()
        upgrade_info = next((u for u in upgrades if u['house_id'] == house_id), None)

        if not upgrade_info:
            return False, "無效的升級選項"

        if self.game.data.cash < upgrade_info['upgrade_cost']:
            return False, f"現金不足，需要 ${upgrade_info['upgrade_cost']:.0f}"

        # 執行升級
        self.game.data.cash -= upgrade_info['upgrade_cost']
        old_house = self.game.data.houses_catalog[self.game.data.current_house]
        self.game.data.current_house = house_id

        # 保持原有家具，但可能需要額外費用
        extra_furniture_cost = 0
        if len(self.game.data.house_furniture) > 5:  # 如果家具太多
            extra_furniture_cost = (len(self.game.data.house_furniture) - 5) * 1000

        if extra_furniture_cost > 0 and self.game.data.cash >= extra_furniture_cost:
            self.game.data.cash -= extra_furniture_cost

        # 更新維護費用到期日
        self.game.data.house_maintenance_due = self.game.data.days + 30
        self._update_comfort_level()

        return True, f"成功升級到 {upgrade_info['name']}，花費 ${upgrade_info['upgrade_cost']:.0f}"

    def calculate_home_bonus(self):
        """計算居家環境帶來的加成"""
        if self.game.data.current_house is None:
            return 0, 0  # 沒有房屋，沒有加成

        comfort_level = self.game.data.house_comfort_level

        # 舒適度轉換為加成
        happiness_bonus = min(20, comfort_level // 5)  # 最高 +20 快樂
        stamina_recovery_bonus = min(10, comfort_level // 10)  # 最高 +10 體力恢復

        return happiness_bonus, stamina_recovery_bonus
