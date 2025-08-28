import random
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class SocialSystem:
    """社交系統管理器"""

    def __init__(self, game: 'BankGame'):
        self.game = game
        self._init_social_contacts()

    def _init_social_contacts(self):
        """初始化社交聯絡人"""
        if not hasattr(self.game.data, 'social_contacts') or not self.game.data.social_contacts:
            # 預設聯絡人
            default_contacts = {
                'friend_1': {
                    'name': '小明',
                    'relationship': '朋友',
                    'affinity': 50,
                    'last_interaction': 0,
                    'description': '大學同學，喜歡聊天'
                },
                'friend_2': {
                    'name': '小華',
                    'relationship': '朋友',
                    'affinity': 45,
                    'last_interaction': 0,
                    'description': '同事，熱愛運動'
                },
                'family_1': {
                    'name': '媽媽',
                    'relationship': '家人',
                    'affinity': 80,
                    'last_interaction': 0,
                    'description': '母親，總是關心你'
                },
                'colleague_1': {
                    'name': '老闆',
                    'relationship': '同事',
                    'affinity': 30,
                    'last_interaction': 0,
                    'description': '公司主管，工作機會的來源'
                }
            }
            self.game.data.social_contacts = default_contacts

    def get_contacts_by_relationship(self, relationship_type):
        """按關係類型獲取聯絡人"""
        return {k: v for k, v in self.game.data.social_contacts.items()
                if v['relationship'] == relationship_type}

    def add_contact(self, name, relationship, description=""):
        """新增聯絡人"""
        contact_id = f"{relationship.lower()}_{len(self.game.data.social_contacts)}"
        self.game.data.social_contacts[contact_id] = {
            'name': name,
            'relationship': relationship,
            'affinity': 50,  # 預設親密度
            'last_interaction': self.game.data.days,
            'description': description
        }
        return contact_id

    def update_affinity(self, contact_id, change):
        """更新聯絡人親密度"""
        if contact_id in self.game.data.social_contacts:
            contact = self.game.data.social_contacts[contact_id]
            contact['affinity'] = max(0, min(100, contact['affinity'] + change))
            contact['last_interaction'] = self.game.data.days

    def can_do_social_activity(self, activity_id):
        """檢查是否可以進行社交活動"""
        if activity_id not in self.game.data.available_social_activities:
            return False, "無效的活動"

        activity = self.game.data.available_social_activities[activity_id]

        # 檢查金錢
        if self.game.data.cash < activity['cost']:
            return False, f"現金不足，需要 ${activity['cost']}"

        # 檢查體力
        if self.game.data.stamina < activity['stamina_cost']:
            return False, f"體力不足，需要 {activity['stamina_cost']} 體力"

        # 檢查冷卻時間
        if activity_id in self.game.data.social_cooldowns:
            cooldown_end = self.game.data.social_cooldowns[activity_id]
            if self.game.data.days < cooldown_end:
                remaining = cooldown_end - self.game.data.days
                return False, f"活動冷卻中，還需 {remaining} 天"

        return True, ""

    def do_social_activity(self, activity_id, target_contact=None):
        """進行社交活動"""
        can_do, reason = self.can_do_social_activity(activity_id)
        if not can_do:
            return False, reason

        activity = self.game.data.available_social_activities[activity_id]

        # 扣除成本
        self.game.data.cash -= activity['cost']
        self.game.data.stamina = max(0, self.game.data.stamina - activity['stamina_cost'])

        # 設定冷卻時間（3天）
        self.game.data.social_cooldowns[activity_id] = self.game.data.days + 3

        # 獲得親密度
        affinity_gain = activity['affinity_gain']

        # 如果指定了目標聯絡人，增加該聯絡人的親密度
        if target_contact and target_contact in self.game.data.social_contacts:
            self.update_affinity(target_contact, affinity_gain)
            contact_name = self.game.data.social_contacts[target_contact]['name']
            result_msg = f"與 {contact_name} 進行 {activity['name']}，親密度 +{affinity_gain}"
        else:
            # 隨機選擇聯絡人獲得親密度
            available_contacts = list(self.game.data.social_contacts.keys())
            if available_contacts:
                random_contact = random.choice(available_contacts)
                self.update_affinity(random_contact, affinity_gain)
                contact_name = self.game.data.social_contacts[random_contact]['name']
                result_msg = f"與 {contact_name} 進行 {activity['name']}，親密度 +{affinity_gain}"
            else:
                result_msg = f"進行 {activity['name']}，社交經驗 +{affinity_gain}"

        # 額外效果
        if activity_id == 'meet_friend':
            self.game.data.happiness = min(100, self.game.data.happiness + 5)
            result_msg += "，快樂 +5"
        elif activity_id == 'family_gathering':
            self.game.data.happiness = min(100, self.game.data.happiness + 8)
            result_msg += "，快樂 +8"
        elif activity_id == 'business_networking':
            self.game.data.charisma = min(100, self.game.data.charisma + 3)
            result_msg += "，魅力 +3"
        elif activity_id == 'date_night':
            self.game.data.happiness = min(100, self.game.data.happiness + 10)
            self.game.data.charisma = min(100, self.game.data.charisma + 5)
            result_msg += "，快樂 +10，魅力 +5"
        elif activity_id == 'party':
            self.game.data.happiness = min(100, self.game.data.happiness + 12)
            self.game.data.stamina = max(0, self.game.data.stamina - 5)  # 額外體力消耗
            result_msg += "，快樂 +12，體力 -5"

        # 記錄社交事件
        self.game.data.social_events.append({
            'day': self.game.data.days,
            'activity': activity_id,
            'contact': target_contact,
            'affinity_gain': affinity_gain,
            'description': result_msg
        })

        # 限制事件歷史長度
        if len(self.game.data.social_events) > 50:
            self.game.data.social_events = self.game.data.social_events[-50:]

        return True, result_msg

    def get_social_summary(self):
        """獲取社交總結"""
        total_contacts = len(self.game.data.social_contacts)
        high_affinity = sum(1 for c in self.game.data.social_contacts.values() if c['affinity'] >= 70)
        recent_events = len([e for e in self.game.data.social_events if e['day'] >= self.game.data.days - 7])

        return {
            'total_contacts': total_contacts,
            'high_affinity_contacts': high_affinity,
            'recent_social_events': recent_events,
            'social_score': high_affinity * 10 + recent_events * 5
        }

    def generate_social_event(self):
        """生成隨機社交事件"""
        # 30% 機率生成社交事件
        if random.random() < 0.3:
            events = [
                {
                    'name': '老朋友來訪',
                    'description': '大學同學突然來訪，想和你敘舊',
                    'effect': lambda: self._handle_friend_visit()
                },
                {
                    'name': '家庭聚會邀請',
                    'description': '家人邀請你參加家庭聚會',
                    'effect': lambda: self._handle_family_invitation()
                },
                {
                    'name': '商業機會',
                    'description': '商業夥伴聯繫你討論合作機會',
                    'effect': lambda: self._handle_business_opportunity()
                },
                {
                    'name': '社交邀請',
                    'description': '收到派對邀請函',
                    'effect': lambda: self._handle_party_invitation()
                }
            ]

            event = random.choice(events)
            return {
                'type': 'social_event',
                'name': event['name'],
                'description': event['description'],
                'effect_func': event['effect']
            }

        return None

    def _handle_friend_visit(self):
        """處理朋友來訪事件"""
        friends = self.get_contacts_by_relationship('朋友')
        if friends:
            friend_id = random.choice(list(friends.keys()))
            friend = friends[friend_id]
            self.update_affinity(friend_id, 3)
            self.game.data.happiness = min(100, self.game.data.happiness + 5)
            return f"與 {friend['name']} 敘舊，親密度 +3，快樂 +5"
        return "朋友來訪，但沒有找到合適的朋友"

    def _handle_family_invitation(self):
        """處理家庭聚會邀請"""
        family = self.get_contacts_by_relationship('家人')
        if family:
            family_member = random.choice(list(family.values()))
            self.update_affinity(list(family.keys())[0], 5)
            self.game.data.happiness = min(100, self.game.data.happiness + 8)
            return f"參加家庭聚會，親密度 +5，快樂 +8"
        return "收到家庭聚會邀請，但沒有找到家人"

    def _handle_business_opportunity(self):
        """處理商業機會"""
        colleagues = self.get_contacts_by_relationship('同事')
        if colleagues:
            colleague_id = random.choice(list(colleagues.keys()))
            colleague = colleagues[colleague_id]
            self.update_affinity(colleague_id, 4)
            self.game.data.charisma = min(100, self.game.data.charisma + 3)
            return f"與 {colleague['name']} 討論商業機會，親密度 +4，魅力 +3"
        return "收到商業機會，但沒有找到合適的同事"

    def _handle_party_invitation(self):
        """處理派對邀請"""
        if random.random() < 0.7:  # 70% 接受邀請
            self.game.data.happiness = min(100, self.game.data.happiness + 10)
            self.game.data.charisma = min(100, self.game.data.charisma + 4)
            return "參加派對，快樂 +10，魅力 +4"
        else:
            return "婉拒派對邀請，專注休息"
