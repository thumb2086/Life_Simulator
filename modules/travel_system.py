import random
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class TravelSystem:
    """旅行系統管理器"""

    def __init__(self, game: 'BankGame'):
        self.game = game

    def can_travel(self, destination_id):
        """檢查是否可以旅行"""
        if destination_id not in self.game.data.destinations_catalog:
            return False, "無效的目的地"

        destination = self.game.data.destinations_catalog[destination_id]

        # 檢查是否正在旅行中
        if self.game.data.current_trip is not None:
            return False, "正在旅行中，請等待旅行結束"

        # 檢查冷卻時間
        if self.game.data.days < self.game.data.travel_cooldown:
            remaining = self.game.data.travel_cooldown - self.game.data.days
            return False, f"旅行冷卻中，還需 {remaining} 天"

        # 檢查金錢
        if self.game.data.cash < destination['cost']:
            return False, f"現金不足，需要 ${destination['cost']}"

        # 檢查體力
        if self.game.data.stamina < 20:
            return False, "體力不足，至少需要 20 體力"

        return True, ""

    def start_trip(self, destination_id):
        """開始旅行"""
        can_travel, reason = self.can_travel(destination_id)
        if not can_travel:
            return False, reason

        destination = self.game.data.destinations_catalog[destination_id]

        # 扣除成本
        self.game.data.cash -= destination['cost']
        self.game.data.stamina -= 20

        # 開始旅行
        self.game.data.current_trip = {
            'destination': destination_id,
            'start_day': self.game.data.days,
            'end_day': self.game.data.days + destination['duration'],
            'destination_name': destination['name'],
            'experience_gain': destination['experience_gain'],
            'culture_bonus': destination['culture_bonus'],
            'special_events': destination['special_events'].copy()
        }

        return True, f"開始前往 {destination['name']} 的旅行，預計 {destination['duration']} 天"

    def process_trip(self):
        """處理旅行進度"""
        if self.game.data.current_trip is None:
            return None, ""

        trip = self.game.data.current_trip
        current_day = self.game.data.days

        if current_day >= trip['end_day']:
            # 旅行結束
            return self._complete_trip()
        else:
            # 旅行進行中
            days_elapsed = current_day - trip['start_day']
            total_days = trip['end_day'] - trip['start_day']
            progress = (days_elapsed / total_days) * 100

            # 隨機旅行事件
            if random.random() < 0.3:  # 30% 機率發生事件
                return self._generate_travel_event(trip)

            return True, f"{trip['destination_name']} 旅行進行中 ({progress:.1f}%)"

    def _complete_trip(self):
        """完成旅行"""
        trip = self.game.data.current_trip
        destination = self.game.data.destinations_catalog[trip['destination']]

        # 獲得經驗和文化積分
        experience_gain = trip['experience_gain']
        culture_gain = trip['culture_bonus']

        self.game.data.experience = min(1000, self.game.data.experience + experience_gain)
        self.game.data.culture_points += culture_gain

        # 額外獎勵
        bonus_happiness = random.randint(10, 20)
        bonus_charisma = random.randint(5, 15)

        self.game.data.happiness = min(100, self.game.data.happiness + bonus_happiness)
        self.game.data.charisma = min(100, self.game.data.charisma + bonus_charisma)

        # 記錄旅行
        travel_record = {
            'destination': trip['destination_name'],
            'start_day': trip['start_day'],
            'end_day': trip['end_day'],
            'experience_gain': experience_gain,
            'culture_gain': culture_gain,
            'happiness_bonus': bonus_happiness,
            'charisma_bonus': bonus_charisma
        }
        self.game.data.travel_history.append(travel_record)

        # 限制歷史記錄長度
        if len(self.game.data.travel_history) > 20:
            self.game.data.travel_history = self.game.data.travel_history[-20:]

        # 設定冷卻時間（7天）
        self.game.data.travel_cooldown = self.game.data.days + 7

        # 清除當前旅行
        trip_result = self.game.data.current_trip
        self.game.data.current_trip = None

        return True, f"完成 {trip_result['destination_name']} 旅行！獲得經驗 +{experience_gain}，文化積分 +{culture_gain}，快樂 +{bonus_happiness}，魅力 +{bonus_charisma}"

    def _generate_travel_event(self, trip):
        """生成旅行事件"""
        events = [
            {
                'name': '文化體驗',
                'effect': lambda: self._cultural_experience(trip)
            },
            {
                'name': '意外邂逅',
                'effect': lambda: self._unexpected_encounter()
            },
            {
                'name': '美食探索',
                'effect': lambda: self._food_adventure()
            },
            {
                'name': '風景攝影',
                'effect': lambda: self._scenic_photography()
            },
            {
                'name': '當地節慶',
                'effect': lambda: self._local_festival(trip)
            }
        ]

        event = random.choice(events)
        return event['effect']()

    def _cultural_experience(self, trip):
        """文化體驗事件"""
        culture_gain = random.randint(5, 15)
        self.game.data.culture_points += culture_gain

        if trip['special_events']:
            special_event = random.choice(trip['special_events'])
            trip['special_events'].remove(special_event)
            return True, f"參加 {special_event} 文化活動，文化積分 +{culture_gain}"

        return True, f"體驗當地文化，文化積分 +{culture_gain}"

    def _unexpected_encounter(self):
        """意外邂逅事件"""
        if random.random() < 0.5:
            charisma_gain = random.randint(3, 8)
            self.game.data.charisma = min(100, self.game.data.charisma + charisma_gain)
            return True, f"結識有趣的旅人，魅力 +{charisma_gain}"
        else:
            happiness_gain = random.randint(5, 12)
            self.game.data.happiness = min(100, self.game.data.happiness + happiness_gain)
            return True, f"遇到友善的當地人，快樂 +{happiness_gain}"

    def _food_adventure(self):
        """美食探索事件"""
        stamina_cost = random.randint(5, 15)
        happiness_gain = random.randint(8, 18)

        self.game.data.stamina = max(0, self.game.data.stamina - stamina_cost)
        self.game.data.happiness = min(100, self.game.data.happiness + happiness_gain)

        return True, f"探索當地美食，體力 -{stamina_cost}，快樂 +{happiness_gain}"

    def _scenic_photography(self):
        """風景攝影事件"""
        experience_gain = random.randint(5, 15)
        self.game.data.experience = min(1000, self.game.data.experience + experience_gain)

        return True, f"拍攝美麗風景，經驗 +{experience_gain}"

    def _local_festival(self, trip):
        """當地節慶事件"""
        culture_gain = random.randint(8, 20)
        happiness_gain = random.randint(10, 25)

        self.game.data.culture_points += culture_gain
        self.game.data.happiness = min(100, self.game.data.happiness + happiness_gain)

        return True, f"參加當地節慶活動，文化積分 +{culture_gain}，快樂 +{happiness_gain}"

    def get_travel_summary(self):
        """獲取旅行總結"""
        total_trips = len(self.game.data.travel_history)
        total_culture = self.game.data.culture_points
        unique_destinations = len(set(t['destination'] for t in self.game.data.travel_history)) if self.game.data.travel_history else 0

        return {
            'total_trips': total_trips,
            'unique_destinations': unique_destinations,
            'culture_points': total_culture,
            'travel_score': total_trips * 10 + unique_destinations * 20 + total_culture
        }

    def get_available_destinations(self):
        """獲取可用目的地"""
        return self.game.data.destinations_catalog

    def get_culture_level(self):
        """獲取文化等級"""
        culture_points = self.game.data.culture_points

        if culture_points < 50:
            return "初學者", "剛開始探索世界文化"
        elif culture_points < 150:
            return "文化愛好者", "對多元文化有一定了解"
        elif culture_points < 300:
            return "文化探索者", "深入體驗不同文化"
        elif culture_points < 500:
            return "文化大師", "對世界文化有深刻理解"
        else:
            return "文化傳奇", "世界文化專家"

    def get_travel_recommendation(self):
        """獲取旅行建議"""
        if not self.game.data.travel_history:
            return "建議從東京或京都開始您的第一次旅行！"

        visited = set(t['destination'] for t in self.game.data.travel_history)
        available = set(self.game.data.destinations_catalog.keys())

        unvisited = available - visited

        if not unvisited:
            return "您已經探索了所有目的地！考慮重溫喜歡的地方。"

        # 根據文化積分建議難度
        culture_level = self.get_culture_level()[0]

        if culture_level in ["初學者", "文化愛好者"]:
            recommendations = ['tokyo', 'kyoto', 'bali']
        else:
            recommendations = list(unvisited)

        recommended = random.choice([d for d in recommendations if d in unvisited])
        dest_name = self.game.data.destinations_catalog[recommended]['name']

        return f"建議前往 {dest_name}，這將是完美的下一站！"
