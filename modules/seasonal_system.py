import random
import tkinter as tk
from modules.tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.bank_game import BankGame

class SeasonalSystem:
    """季節系統管理器"""

    def __init__(self, game: 'BankGame'):
        self.game = game

    def update_daily_season(self):
        """每日季節更新"""
        # 更新季節進度
        self.game.data.day_of_season += 1

        # 檢查是否需要轉換季節
        if self.game.data.day_of_season >= self.game.data.season_duration_days:
            self._transition_season()
            self.game.data.day_of_season = 0

        # 更新天氣
        self._update_weather()

        # 應用季節效果
        self._apply_seasonal_effects()

    def _transition_season(self):
        """轉換季節"""
        current_index = self.game.data.seasons.index(self.game.data.current_season)
        next_index = (current_index + 1) % len(self.game.data.seasons)
        new_season = self.game.data.seasons[next_index]

        old_season_name = self.game.data.seasonal_activities[self.game.data.current_season]['name']
        new_season_name = self.game.data.seasonal_activities[new_season]['name']

        self.game.data.current_season = new_season

        # 觸發季節事件
        self._trigger_seasonal_event(old_season_name, new_season_name)

    def _trigger_seasonal_event(self, old_season, new_season):
        """觸發季節轉換事件"""
        event_msg = f"季節轉換：從 {old_season} 進入 {new_season}"

        # 季節特有效果
        if new_season == 'spring':
            self.game.data.happiness = min(100, self.game.data.happiness + 5)
            event_msg += "\n🌸 春暖花開，心情愉悅 +5"
        elif new_season == 'summer':
            self.game.data.stamina = max(0, self.game.data.stamina - 5)
            event_msg += "\n☀️ 炎炎夏日，體力消耗增加"
        elif new_season == 'autumn':
            self.game.data.intelligence = min(100, self.game.data.intelligence + 3)
            event_msg += "\n🍂 金秋時節，智力提升 +3"
        elif new_season == 'winter':
            self.game.data.health_status = max(0, self.game.data.health_status - 3)
            event_msg += "\n❄️ 寒冬來臨，健康狀況稍降"

        self.game.log_transaction(event_msg)

    def _update_weather(self):
        """更新天氣"""
        self.game.data.weather_duration += 1

        # 天氣持續時間（1-5天）
        if self.game.data.weather_duration >= random.randint(1, 5):
            self._change_weather()

    def _change_weather(self):
        """改變天氣"""
        # 根據季節決定天氣機率
        season = self.game.data.current_season
        weather_weights = {}

        if season == 'spring':
            weather_weights = {'sunny': 0.4, 'cloudy': 0.3, 'rainy': 0.3}
        elif season == 'summer':
            weather_weights = {'sunny': 0.6, 'cloudy': 0.2, 'rainy': 0.15, 'stormy': 0.05}
        elif season == 'autumn':
            weather_weights = {'sunny': 0.3, 'cloudy': 0.4, 'rainy': 0.3}
        elif season == 'winter':
            weather_weights = {'sunny': 0.2, 'cloudy': 0.4, 'rainy': 0.2, 'snowy': 0.2}

        # 隨機選擇天氣
        weather_types = list(weather_weights.keys())
        weights = list(weather_weights.values())
        new_weather = random.choices(weather_types, weights=weights, k=1)[0]

        # 應用天氣效果
        old_weather_info = self.game.data.weather_types[self.game.data.current_weather]
        new_weather_info = self.game.data.weather_types[new_weather]

        # 天氣改變通知
        if self.game.data.current_weather != new_weather:
            weather_msg = f"天氣變更：從 {old_weather_info['name']} 變為 {new_weather_info['name']}"
            self.game.log_transaction(weather_msg)

        self.game.data.current_weather = new_weather
        self.game.data.weather_duration = 0

    def _apply_seasonal_effects(self):
        """應用季節效果"""
        season_data = self.game.data.seasonal_activities[self.game.data.current_season]
        weather_data = self.game.data.weather_types[self.game.data.current_weather]

        # 季節基礎效果
        season_effects = season_data.get('effects', {})
        for attr, value in season_effects.items():
            if hasattr(self.game.data, attr):
                current_value = getattr(self.game.data, attr)
                if attr in ['happiness', 'health_status']:
                    new_value = min(100, max(0, current_value + value))
                elif attr == 'stamina':
                    new_value = min(100, max(0, current_value + value))
                elif attr == 'intelligence':
                    new_value = min(100, max(0, current_value + value))
                else:
                    new_value = current_value + value
                setattr(self.game.data, attr, new_value)

        # 天氣效果
        weather_effects = weather_data.get('effect', {})
        for attr, value in weather_effects.items():
            if hasattr(self.game.data, attr):
                current_value = getattr(self.game.data, attr)
                if attr == 'happiness':
                    new_value = min(100, max(0, current_value + value))
                elif attr == 'energy':
                    new_value = min(100, max(0, current_value + value))
                else:
                    new_value = current_value + value
                setattr(self.game.data, attr, new_value)

    def perform_seasonal_activity(self, activity_name):
        """進行季節活動"""
        season_data = self.game.data.seasonal_activities[self.game.data.current_season]

        if activity_name not in season_data['activities']:
            return False, "此活動不屬於當前季節"

        # 活動效果
        season_effects = season_data.get('effects', {})

        results = []
        for attr, base_value in season_effects.items():
            # 季節活動效果加倍
            effect_value = base_value * 2
            if hasattr(self.game.data, attr):
                current_value = getattr(self.game.data, attr)
                if attr in ['happiness', 'health_status']:
                    new_value = min(100, max(0, current_value + effect_value))
                elif attr == 'stamina':
                    new_value = min(100, max(0, current_value + effect_value))
                elif attr == 'intelligence':
                    new_value = min(100, max(0, current_value + effect_value))
                else:
                    new_value = current_value + effect_value
                setattr(self.game.data, attr, new_value)
                results.append(f"{attr} +{effect_value}")

        # 消耗體力
        stamina_cost = random.randint(10, 20)
        self.game.data.stamina = max(0, self.game.data.stamina - stamina_cost)
        results.append(f"體力 -{stamina_cost}")

        return True, f"進行 {activity_name} 完成！效果：{', '.join(results)}"

    def trigger_seasonal_event(self):
        """觸發季節事件"""
        season_data = self.game.data.seasonal_activities[self.game.data.current_season]
        special_events = season_data.get('special_events', [])

        if not special_events:
            return None

        # 10% 機率觸發特殊事件
        if random.random() < 0.1:
            event_name = random.choice(special_events)

            # 事件效果
            if '櫻花' in event_name:
                self.game.data.happiness = min(100, self.game.data.happiness + 15)
                self.game.data.charisma = min(100, self.game.data.charisma + 8)
                effect_desc = "快樂 +15，魅力 +8"
            elif '楓葉' in event_name:
                self.game.data.happiness = min(100, self.game.data.happiness + 12)
                self.game.data.intelligence = min(100, self.game.data.intelligence + 6)
                effect_desc = "快樂 +12，智力 +6"
            elif '聖誕' in event_name:
                self.game.data.happiness = min(100, self.game.data.happiness + 20)
                effect_desc = "快樂 +20"
            elif '跨年' in event_name:
                self.game.data.happiness = min(100, self.game.data.happiness + 18)
                self.game.data.experience = min(1000, self.game.data.experience + 10)
                effect_desc = "快樂 +18，經驗 +10"
            elif '海灘' in event_name:
                self.game.data.happiness = min(100, self.game.data.happiness + 14)
                self.game.data.stamina = max(0, self.game.data.stamina - 8)
                effect_desc = "快樂 +14，體力 -8"
            elif '火山' in event_name:
                self.game.data.intelligence = min(100, self.game.data.intelligence + 8)
                self.game.data.stamina = max(0, self.game.data.stamina - 12)
                effect_desc = "智力 +8，體力 -12"
            else:
                self.game.data.happiness = min(100, self.game.data.happiness + 10)
                effect_desc = "快樂 +10"

            return {
                'type': 'seasonal_event',
                'name': event_name,
                'description': f"季節活動：{event_name}",
                'effect_desc': effect_desc
            }

        return None

    def get_seasonal_info(self):
        """獲取季節資訊"""
        season_data = self.game.data.seasonal_activities[self.game.data.current_season]
        weather_data = self.game.data.weather_types[self.game.data.current_weather]

        # 計算季節進度
        season_progress = (self.game.data.day_of_season / self.game.data.season_duration_days) * 100

        return {
            'current_season': season_data['name'],
            'season_progress': season_progress,
            'days_remaining': self.game.data.season_duration_days - self.game.data.day_of_season,
            'current_weather': weather_data['name'],
            'available_activities': season_data['activities'],
            'seasonal_effects': season_data['effects']
        }

    def get_seasonal_recommendation(self):
        """獲取季節建議"""
        season_info = self.get_seasonal_info()

        recommendations = []

        # 根據季節給出建議
        if season_info['current_season'] == '春天':
            recommendations.append("🌸 春天是學習的好季節，建議多參加教育活動")
            if self.game.data.intelligence < 70:
                recommendations.append("建議提升智力，春天學習效率更高")
        elif season_info['current_season'] == '夏天':
            recommendations.append("☀️ 夏天適合戶外活動，但要注意體力消耗")
            if self.game.data.stamina < 50:
                recommendations.append("體力較低，建議減少劇烈運動")
        elif season_info['current_season'] == '秋天':
            recommendations.append("🍂 秋天是創作的好季節，適合發展創意")
            if self.game.data.charisma < 70:
                recommendations.append("建議提升魅力，秋天社交活動更有效")
        elif season_info['current_season'] == '冬天':
            recommendations.append("❄️ 冬天適合休息和反思，多參加冥想活動")
            if self.game.data.mental_health < 60:
                recommendations.append("心理健康需要關注，建議多休息")

        # 天氣建議
        weather = season_info['current_weather']
        if weather == '雨天':
            recommendations.append("🌧️ 雨天不適合戶外活動，建議待在家裡")
        elif weather == '暴風雨':
            recommendations.append("⛈️ 惡劣天氣，請注意安全，避免外出")
        elif weather == '雪天':
            recommendations.append("❄️ 雪天適合溫暖活動，如閱讀或冥想")

        return recommendations

    def apply_seasonal_market_effects(self):
        """應用季節性市場效果"""
        season = self.game.data.current_season
        weather = self.game.data.current_weather

        # 季節市場效果
        seasonal_effects = {
            'spring': {'market_volatility': 0.8, 'description': '春季市場平穩，適合長期投資'},
            'summer': {'market_volatility': 1.2, 'description': '夏季市場波動較大'},
            'autumn': {'market_volatility': 0.9, 'description': '秋季市場趨於穩定'},
            'winter': {'market_volatility': 1.1, 'description': '冬季市場略有波動'}
        }

        # 天氣市場效果
        weather_effects = {
            'sunny': {'market_volatility': 0.9, 'description': '晴天市場樂觀'},
            'rainy': {'market_volatility': 1.1, 'description': '雨天市場謹慎'},
            'stormy': {'market_volatility': 1.3, 'description': '惡劣天氣市場恐慌'},
            'snowy': {'market_volatility': 1.2, 'description': '雪天市場觀望'}
        }

        # 應用效果
        season_effect = seasonal_effects.get(season, {'market_volatility': 1.0})
        weather_effect = weather_effects.get(weather, {'market_volatility': 1.0})

        # 綜合波動性
        combined_volatility = (season_effect['market_volatility'] + weather_effect['market_volatility']) / 2

        # 輕微調整市場波動
        if hasattr(self.game.data, 'market_volatility'):
            original_volatility = self.game.data.market_volatility
            self.game.data.market_volatility = original_volatility * combined_volatility

        return {
            'season_effect': season_effect,
            'weather_effect': weather_effect,
            'combined_volatility': combined_volatility
        }
