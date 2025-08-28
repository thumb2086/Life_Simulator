import random
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class HealthSystem:
    """健康系統管理器"""

    def __init__(self, game: 'BankGame'):
        self.game = game

    def update_daily_health(self):
        """每日健康更新"""
        # 隨機疾病機率
        disease_chance = self._calculate_disease_risk()
        if random.random() < disease_chance:
            self._contract_random_disease()

        # 更新現有疾病
        self._update_diseases()

        # 計算健康指標
        self._update_health_indicators()

        # 自然恢復
        self._natural_recovery()

    def _calculate_disease_risk(self):
        """計算疾病風險"""
        base_risk = 0.05  # 基礎風險 5%

        # 年齡因子（遊戲天數）
        age_factor = min(self.game.data.days / 3650, 2.0)  # 最高2倍風險

        # 健康狀態因子
        health_factor = (100 - self.game.data.health_status) / 100.0

        # 免疫系統因子
        immune_factor = (100 - self.game.data.immune_system) / 100.0

        # 生活方式因子
        lifestyle_factor = 0
        if self.game.data.daily_exercise < 30:  # 每日運動少於30分鐘
            lifestyle_factor += 0.02
        if self.game.data.sleep_quality < 70:
            lifestyle_factor += 0.02
        if self.game.data.diet_quality < 70:
            lifestyle_factor += 0.02

        total_risk = base_risk * (1 + age_factor + health_factor + immune_factor + lifestyle_factor)
        return min(total_risk, 0.3)  # 最高30%風險

    def _contract_random_disease(self):
        """感染隨機疾病"""
        available_diseases = list(self.game.data.disease_types.keys())

        # 根據季節和健康狀態調整疾病機率
        disease_weights = {}
        for disease_name in available_diseases:
            weight = 1.0
            disease = self.game.data.disease_types[disease_name]

            # 季節因子
            if disease['contagious'] and random.random() < 0.3:  # 30%機會在流行季節
                weight *= 2.0

            # 免疫抗性
            if disease_name in self.game.data.illness_resistance:
                resistance = self.game.data.illness_resistance[disease_name]
                weight *= max(0.1, 1.0 - resistance)

            disease_weights[disease_name] = weight

        # 選擇疾病
        diseases = list(disease_weights.keys())
        weights = list(disease_weights.values())
        selected_disease = random.choices(diseases, weights=weights, k=1)[0]

        # 感染疾病
        self._contract_disease(selected_disease)

    def _contract_disease(self, disease_name):
        """感染指定疾病"""
        if disease_name in [d['name'] for d in self.game.data.current_illnesses]:
            return  # 已經感染此疾病

        disease = self.game.data.disease_types[disease_name]

        illness_record = {
            'name': disease_name,
            'start_day': self.game.data.days,
            'end_day': self.game.data.days + disease['duration_days'],
            'severity': disease['severity'],
            'treated': False
        }

        self.game.data.current_illnesses.append(illness_record)

        # 立即應用疾病效果
        self._apply_disease_effects(disease_name)

        # 記錄醫療記錄
        medical_record = {
            'day': self.game.data.days,
            'type': 'diagnosis',
            'condition': disease_name,
            'severity': disease['severity'],
            'description': f"診斷出患有{disease_name}"
        }
        self.game.data.medical_records.append(medical_record)

    def _apply_disease_effects(self, disease_name):
        """應用疾病效果"""
        disease = self.game.data.disease_types[disease_name]

        if 'health_penalty' in disease:
            self.game.data.health_status = max(0, self.game.data.health_status - disease['health_penalty'])
        if 'stamina_penalty' in disease:
            self.game.data.stamina = max(0, self.game.data.stamina - disease['stamina_penalty'])
        if 'mental_penalty' in disease:
            self.game.data.mental_health = max(0, self.game.data.mental_health - disease['mental_penalty'])
        if 'happiness_penalty' in disease:
            self.game.data.happiness = max(0, self.game.data.happiness - disease['happiness_penalty'])

    def _update_diseases(self):
        """更新疾病狀態"""
        remaining_illnesses = []

        for illness in self.game.data.current_illnesses:
            if self.game.data.days >= illness['end_day']:
                # 疾病痊癒
                self._cure_disease(illness)
            else:
                remaining_illnesses.append(illness)
                # 繼續應用疾病效果（較輕微）
                disease = self.game.data.disease_types[illness['name']]
                if 'health_penalty' in disease:
                    penalty = disease['health_penalty'] // 3  # 恢復期間效果減弱
                    self.game.data.health_status = max(0, self.game.data.health_status - penalty)

        self.game.data.current_illnesses = remaining_illnesses

    def _cure_disease(self, illness):
        """治癒疾病"""
        disease_name = illness['name']
        disease = self.game.data.disease_types[disease_name]

        # 恢復部分健康
        recovery_rate = 0.7 if illness['treated'] else 0.5

        if 'health_penalty' in disease:
            recovery = int(disease['health_penalty'] * recovery_rate)
            self.game.data.health_status = min(100, self.game.data.health_status + recovery)

        # 增加免疫力
        if disease_name not in self.game.data.illness_resistance:
            self.game.data.illness_resistance[disease_name] = 0
        self.game.data.illness_resistance[disease_name] = min(1.0, self.game.data.illness_resistance[disease_name] + 0.1)

        # 記錄治癒
        medical_record = {
            'day': self.game.data.days,
            'type': 'recovery',
            'condition': disease_name,
            'treated': illness['treated'],
            'description': f"{disease_name}痊癒"
        }
        self.game.data.medical_records.append(medical_record)

        # 添加到病史
        self.game.data.past_illnesses.append({
            'name': disease_name,
            'start_day': illness['start_day'],
            'end_day': self.game.data.days,
            'treated': illness['treated']
        })

    def treat_disease(self, illness_index):
        """治療疾病"""
        if illness_index >= len(self.game.data.current_illnesses):
            return False, "無效的疾病索引"

        illness = self.game.data.current_illnesses[illness_index]
        disease_name = illness['name']
        disease = self.game.data.disease_types[disease_name]

        treatment_cost = disease['treatment_cost']

        if self.game.data.cash < treatment_cost:
            return False, f"治療費用不足，需要 ${treatment_cost}"

        # 扣費
        self.game.data.cash -= treatment_cost
        self.game.data.medical_costs_paid += treatment_cost

        # 標記為已治療
        illness['treated'] = True

        # 立即恢復部分健康
        immediate_recovery = disease['treatment_cost'] // 50
        self.game.data.health_status = min(100, self.game.data.health_status + immediate_recovery)

        # 記錄治療
        medical_record = {
            'day': self.game.data.days,
            'type': 'treatment',
            'condition': disease_name,
            'cost': treatment_cost,
            'description': f"{disease_name}接受治療"
        }
        self.game.data.medical_records.append(medical_record)

        return True, f"治療 {disease_name} 成功，花費 ${treatment_cost}"

    def perform_health_activity(self, activity_name):
        """執行健康活動"""
        if activity_name not in self.game.data.health_activities:
            return False, "無效的健康活動"

        activity = self.game.data.health_activities[activity_name]

        # 檢查體力
        if self.game.data.stamina < activity.get('stamina_cost', 0):
            return False, "體力不足"

        # 檢查金錢（如果需要）
        cost = activity.get('cost', 0)
        if cost > 0 and self.game.data.cash < cost:
            return False, "現金不足"

        # 扣除成本
        if cost > 0:
            self.game.data.cash -= cost

        stamina_cost = activity.get('stamina_cost', 0)
        self.game.data.stamina = max(0, self.game.data.stamina - stamina_cost)

        # 應用效果
        results = []
        if 'health_gain' in activity:
            gain = activity['health_gain']
            self.game.data.health_status = min(100, self.game.data.health_status + gain)
            results.append(f"健康 +{gain}")

        if 'mental_gain' in activity:
            gain = activity['mental_gain']
            self.game.data.mental_health = min(100, self.game.data.mental_health + gain)
            results.append(f"心理健康 +{gain}")

        if 'stress_reduction' in activity:
            reduction = activity['stress_reduction']
            self.game.data.stress_level = max(0, self.game.data.stress_level - reduction)
            results.append(f"壓力 -{reduction}")

        if 'health_boost' in activity:
            boost = activity['health_boost']
            self.game.data.health_status = min(100, self.game.data.health_status + boost)
            results.append(f"健康檢查：健康 +{boost}")

        # 更新健康指標
        if activity_name in ['輕度運動', '中度運動', '劇烈運動']:
            self.game.data.daily_exercise += activity.get('duration', 30)

        return True, f"{activity['name']}完成！效果：{', '.join(results)}"

    def _update_health_indicators(self):
        """更新健康指標"""
        # 計算睡眠品質（基於壓力水平）
        stress_factor = self.game.data.stress_level / 100.0
        self.game.data.sleep_quality = max(20, 100 - (stress_factor * 50))

        # 計算飲食品質（基於現金水平）
        cash_factor = min(self.game.data.cash / 1000.0, 1.0)
        self.game.data.diet_quality = max(30, 100 - (cash_factor * 30))

        # 更新免疫系統（基於健康狀態）
        health_factor = self.game.data.health_status / 100.0
        self.game.data.immune_system = min(100, max(20, self.game.data.immune_system + (health_factor - 0.5) * 2))

    def _natural_recovery(self):
        """自然恢復"""
        # 健康恢復
        if self.game.data.health_status < 100:
            recovery = random.randint(1, 3)
            self.game.data.health_status = min(100, self.game.data.health_status + recovery)

        # 體力恢復
        if self.game.data.stamina < 100:
            recovery = random.randint(5, 15)
            self.game.data.stamina = min(100, self.game.data.stamina + recovery)

        # 心理健康恢復
        if self.game.data.mental_health < 100:
            recovery = random.randint(1, 5)
            self.game.data.mental_health = min(100, self.game.data.mental_health + recovery)

    def get_health_summary(self):
        """獲取健康總結"""
        illness_count = len(self.game.data.current_illnesses)
        immune_level = self.game.data.immune_system
        health_score = (self.game.data.health_status + self.game.data.mental_health) / 2

        # 計算健康等級
        if health_score >= 90:
            health_level = "優秀"
        elif health_score >= 75:
            health_level = "良好"
        elif health_score >= 60:
            health_level = "一般"
        elif health_score >= 40:
            health_level = "堪憂"
        else:
            health_level = "危險"

        return {
            'overall_health': health_score,
            'health_level': health_level,
            'current_illnesses': illness_count,
            'immune_system': immune_level,
            'stress_level': self.game.data.stress_level,
            'sleep_quality': self.game.data.sleep_quality,
            'diet_quality': self.game.data.diet_quality
        }

    def generate_health_event(self):
        """生成隨機健康事件"""
        if random.random() < 0.1:  # 10% 機率
            health_events = [
                {
                    'name': '健康檢查提醒',
                    'description': '醫生建議進行定期健康檢查',
                    'effect': lambda: self._health_check_reminder()
                },
                {
                    'name': '營養專家建議',
                    'description': '收到營養師的飲食建議',
                    'effect': lambda: self._nutrition_advice()
                },
                {
                    'name': '健身動機提升',
                    'description': '看到健身成功案例，獲得運動動機',
                    'effect': lambda: self._fitness_motivation()
                },
                {
                    'name': '壓力管理課程',
                    'description': '免費壓力管理課程機會',
                    'effect': lambda: self._stress_management()
                }
            ]

            event = random.choice(health_events)
            return {
                'type': 'health_event',
                'name': event['name'],
                'description': event['description'],
                'effect_func': event['effect']
            }

        return None

    def _health_check_reminder(self):
        """健康檢查提醒"""
        checkup_cost = 200
        if self.game.data.cash >= checkup_cost:
            self.game.data.cash -= checkup_cost
            health_boost = random.randint(15, 25)
            self.game.data.health_status = min(100, self.game.data.health_status + health_boost)
            return True, f"進行健康檢查，花費 ${checkup_cost}，健康 +{health_boost}"
        return True, "收到健康檢查提醒，但現金不足"

    def _nutrition_advice(self):
        """營養建議"""
        diet_boost = random.randint(10, 20)
        self.game.data.diet_quality = min(100, self.game.data.diet_quality + diet_boost)
        return True, f"獲得營養建議，飲食品質提升 {diet_boost} 點"

    def _fitness_motivation(self):
        """健身動機"""
        stamina_boost = random.randint(10, 20)
        self.game.data.stamina = min(100, self.game.data.stamina + stamina_boost)
        return True, f"獲得健身動機，體力 +{stamina_boost}"

    def _stress_management(self):
        """壓力管理"""
        stress_reduction = random.randint(15, 30)
        self.game.data.stress_level = max(0, self.game.data.stress_level - stress_reduction)
        mental_boost = random.randint(5, 15)
        self.game.data.mental_health = min(100, self.game.data.mental_health + mental_boost)
        return True, f"學習壓力管理技巧，壓力 -{stress_reduction}，心理健康 +{mental_boost}"
