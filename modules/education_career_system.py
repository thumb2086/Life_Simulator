import random
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class EducationCareerSystem:
    """教育與職業進階系統管理器"""

    def __init__(self, game: 'BankGame'):
        self.game = game
        self._init_education_data()
        self._init_career_data()

    def _init_education_data(self):
        """初始化教育數據"""
        if not hasattr(self.game.data, 'education_study_progress'):
            self.game.data.education_study_progress = {}

    def _init_career_data(self):
        """初始化職業數據"""
        if not hasattr(self.game.data, 'professional_skills'):
            self.game.data.professional_skills = {
                '技術能力': {'level': 1, 'experience': 0, 'max_level': 10},
                '溝通能力': {'level': 1, 'experience': 0, 'max_level': 10},
                '領導能力': {'level': 1, 'experience': 0, 'max_level': 10},
                '創意思考': {'level': 1, 'experience': 0, 'max_level': 10},
                '分析能力': {'level': 1, 'experience': 0, 'max_level': 10},
                '團隊合作': {'level': 1, 'experience': 0, 'max_level': 10},
                '問題解決': {'level': 1, 'experience': 0, 'max_level': 10},
                '時間管理': {'level': 1, 'experience': 0, 'max_level': 10}
            }

    def can_upgrade_education(self, target_level):
        """檢查是否可以升級學歷"""
        if target_level not in self.game.data.education_levels:
            return False, "無效的學歷等級"

        current_index = self.game.data.education_levels.index(self.game.data.education_level)
        target_index = self.game.data.education_levels.index(target_level)

        if target_index <= current_index:
            return False, "目標學歷等級不能低於或等於當前學歷"

        # 檢查前置條件
        if target_level == '大學' and self.game.data.experience < 100:
            return False, "需要至少100經驗值才能升學"

        if target_level == '碩士' and self.game.data.experience < 300:
            return False, "需要至少300經驗值才能攻讀碩士"

        if target_level == '博士' and self.game.data.experience < 600:
            return False, "需要至少600經驗值才能攻讀博士"

        if target_level == '博士後' and self.game.data.experience < 1000:
            return False, "需要至少1000經驗值才能攻讀博士後"

        # 檢查金錢
        if target_level not in self.game.data.education_upgrade_cost:
            return False, "缺少升級費用資訊"

        cost = self.game.data.education_upgrade_cost[target_level]
        if self.game.data.cash < cost:
            return False, f"現金不足，需要 ${cost}"

        return True, ""

    def start_education_upgrade(self, target_level):
        """開始學歷升級"""
        can_upgrade, reason = self.can_upgrade_education(target_level)
        if not can_upgrade:
            return False, reason

        cost = self.game.data.education_upgrade_cost[target_level]
        self.game.data.cash -= cost

        # 計算升級所需時間（天）
        study_days = {
            '大學': 180,  # 半年
            '碩士': 360,  # 一年
            '博士': 720,   # 兩年
            '博士後': 540  # 一年半
        }

        days_required = study_days.get(target_level, 180)
        self.game.data.education_study_progress[target_level] = {
            'start_day': self.game.data.days,
            'end_day': self.game.data.days + days_required,
            'progress': 0
        }

        return True, f"開始升級學歷至 {target_level}，預計需要 {days_required} 天"

    def process_education_progress(self):
        """處理學歷進度"""
        for level, progress in list(self.game.data.education_study_progress.items()):
            if self.game.data.days >= progress['end_day']:
                # 完成升級
                self.game.data.education_level = level
                del self.game.data.education_study_progress[level]

                # 獲得技能經驗
                skill_gain = {
                    '大學': {'技術能力': 10, '分析能力': 10},
                    '碩士': {'技術能力': 15, '分析能力': 15, '溝通能力': 10},
                    '博士': {'技術能力': 20, '分析能力': 20, '問題解決': 15},
                    '博士後': {'技術能力': 25, '領導能力': 20, '問題解決': 20}
                }

                if level in skill_gain:
                    for skill, exp in skill_gain[level].items():
                        self.gain_skill_experience(skill, exp)

                return True, f"恭喜！學歷已升級至 {level}"

        return None, ""

    def gain_skill_experience(self, skill_name, experience):
        """獲得技能經驗"""
        if skill_name not in self.game.data.professional_skills:
            return False, f"未知技能: {skill_name}"

        skill = self.game.data.professional_skills[skill_name]
        skill['experience'] += experience

        # 檢查是否可以升級
        exp_needed = skill['level'] * 100  # 每級需要100經驗
        if skill['experience'] >= exp_needed and skill['level'] < skill['max_level']:
            skill['level'] += 1
            skill['experience'] -= exp_needed
            return True, f"{skill_name} 升級至等級 {skill['level']}！"

        return False, f"獲得 {experience} 點 {skill_name} 經驗"

    def can_advance_career(self, career_path, target_level):
        """檢查是否可以晉升職業"""
        if career_path not in self.game.data.career_paths:
            return False, "無效的職業道路"

        path_data = self.game.data.career_paths[career_path]
        if target_level >= len(path_data['levels']):
            return False, "已達職業頂峰"

        level_name = path_data['levels'][target_level]
        requirements = path_data['requirements'].get(level_name, {})

        # 檢查學歷要求
        if 'education' in requirements:
            required_edu = requirements['education']
            current_edu_index = self.game.data.education_levels.index(self.game.data.education_level)
            required_edu_index = self.game.data.education_levels.index(required_edu)
            if current_edu_index < required_edu_index:
                return False, f"需要學歷至少為 {required_edu}"

        # 檢查技能要求
        if 'skills' in requirements:
            for skill, required_level in requirements['skills'].items():
                if skill not in self.game.data.professional_skills:
                    return False, f"缺少必要技能: {skill}"
                if self.game.data.professional_skills[skill]['level'] < required_level:
                    return False, f"{skill} 等級不足，需要等級 {required_level}"

        # 檢查經驗要求
        if 'experience' in requirements:
            if self.game.data.career_experience < requirements['experience']:
                return False, f"職業經驗不足，需要 {requirements['experience']} 年經驗"

        return True, ""

    def advance_career(self, career_path, target_level):
        """晉升職業"""
        can_advance, reason = self.can_advance_career(career_path, target_level)
        if not can_advance:
            return False, reason

        path_data = self.game.data.career_paths[career_path]
        level_name = path_data['levels'][target_level]

        # 記錄職業變更
        if self.game.data.current_career_path != career_path or self.game.data.career_level != target_level:
            career_record = {
                'day': self.game.data.days,
                'path': career_path,
                'level': target_level,
                'title': level_name,
                'previous_path': self.game.data.current_career_path,
                'previous_level': self.game.data.career_level
            }
            self.game.data.career_history.append(career_record)

        # 更新職業狀態
        self.game.data.current_career_path = career_path
        self.game.data.career_level = target_level

        # 獲得技能經驗作為獎勵
        advancement_bonus = {
            '科技': {'技術能力': 5},
            '管理': {'領導能力': 5, '溝通能力': 3},
            '創意': {'創意思考': 5, '溝通能力': 3}
        }

        if career_path in advancement_bonus:
            for skill, exp in advancement_bonus[career_path].items():
                self.gain_skill_experience(skill, exp)

        return True, f"恭喜晉升為 {level_name}！"

    def gain_career_experience(self, experience):
        """獲得職業經驗"""
        old_level = self.game.data.career_level
        self.game.data.career_experience += experience

        # 檢查是否有自動晉升機會
        if self.game.data.current_career_path:
            path_data = self.game.data.career_paths[self.game.data.current_career_path]
            next_level = self.game.data.career_level + 1

            if next_level < len(path_data['levels']):
                can_advance, _ = self.can_advance_career(self.game.data.current_career_path, next_level)
                if can_advance:
                    return self.advance_career(self.game.data.current_career_path, next_level)

        return False, f"獲得 {experience} 年職業經驗"

    def get_skill_training_options(self):
        """獲取技能訓練選項"""
        training_options = {
            '技術能力': {
                'activities': ['程式設計', '學習新技術', '參與專案'],
                'cost_per_session': 200,
                'experience_per_session': 5
            },
            '溝通能力': {
                'activities': ['演講練習', '團隊會議', '客戶溝通'],
                'cost_per_session': 150,
                'experience_per_session': 4
            },
            '領導能力': {
                'activities': ['團隊管理', '專案領導', '決策訓練'],
                'cost_per_session': 300,
                'experience_per_session': 6
            },
            '創意思考': {
                'activities': ['創意工作坊', '設計思考', '腦力激盪'],
                'cost_per_session': 250,
                'experience_per_session': 5
            },
            '分析能力': {
                'activities': ['數據分析', '問題診斷', '策略規劃'],
                'cost_per_session': 180,
                'experience_per_session': 4
            },
            '團隊合作': {
                'activities': ['團隊建設', '協作練習', '團體活動'],
                'cost_per_session': 120,
                'experience_per_session': 3
            },
            '問題解決': {
                'activities': ['案例分析', '問題排查', '創新解決方案'],
                'cost_per_session': 220,
                'experience_per_session': 5
            },
            '時間管理': {
                'activities': ['時間規劃', '效率訓練', '優先順序設定'],
                'cost_per_session': 100,
                'experience_per_session': 3
            }
        }
        return training_options

    def train_skill(self, skill_name, sessions=1):
        """訓練技能"""
        if skill_name not in self.game.data.professional_skills:
            return False, f"未知技能: {skill_name}"

        training_options = self.get_skill_training_options()
        if skill_name not in training_options:
            return False, f"沒有 {skill_name} 的訓練選項"

        option = training_options[skill_name]
        total_cost = option['cost_per_session'] * sessions
        total_exp = option['experience_per_session'] * sessions

        if self.game.data.cash < total_cost:
            return False, f"現金不足，需要 ${total_cost}"

        if self.game.data.stamina < sessions * 10:
            return False, f"體力不足，需要 {sessions * 10} 體力"

        # 扣除成本
        self.game.data.cash -= total_cost
        self.game.data.stamina -= sessions * 10

        # 獲得經驗
        upgrade_result, msg = self.gain_skill_experience(skill_name, total_exp)

        return True, f"完成 {sessions} 次 {skill_name} 訓練，{msg}"

    def get_education_summary(self):
        """獲取教育總結"""
        current_edu = self.game.data.education_level
        edu_index = self.game.data.education_levels.index(current_edu)
        progress_percent = (edu_index / (len(self.game.data.education_levels) - 1)) * 100

        # 計算技能總等級
        total_skill_level = sum(skill['level'] for skill in self.game.data.professional_skills.values())
        avg_skill_level = total_skill_level / len(self.game.data.professional_skills)

        return {
            'current_education': current_edu,
            'education_progress': progress_percent,
            'total_skill_level': total_skill_level,
            'average_skill_level': avg_skill_level,
            'career_path': self.game.data.current_career_path,
            'career_level': self.game.data.career_level,
            'career_experience': self.game.data.career_experience
        }

    def generate_skill_event(self):
        """生成隨機技能事件"""
        if random.random() < 0.15:  # 15% 機率
            skill_events = [
                {
                    'name': '技能研討會',
                    'description': '參加專業技能研討會',
                    'effect': lambda: self._skill_workshop_event()
                },
                {
                    'name': '學習機會',
                    'description': '遇到貴人指導',
                    'effect': lambda: self._mentorship_event()
                },
                {
                    'name': '挑戰任務',
                    'description': '接到需要特殊技能的任務',
                    'effect': lambda: self._skill_challenge_event()
                },
                {
                    'name': '團隊合作',
                    'description': '參與團隊專案',
                    'effect': lambda: self._team_project_event()
                }
            ]

            event = random.choice(skill_events)
            return {
                'type': 'skill_event',
                'name': event['name'],
                'description': event['description'],
                'effect_func': event['effect']
            }

        return None

    def _skill_workshop_event(self):
        """技能研討會事件"""
        available_skills = list(self.game.data.professional_skills.keys())
        skill = random.choice(available_skills)
        exp_gain = random.randint(10, 25)

        upgrade_result, msg = self.gain_skill_experience(skill, exp_gain)
        return True, f"參加技能研討會，{msg}"

    def _mentorship_event(self):
        """指導事件"""
        available_skills = list(self.game.data.professional_skills.keys())
        skill = random.choice(available_skills)
        exp_gain = random.randint(15, 30)

        upgrade_result, msg = self.gain_skill_experience(skill, exp_gain)
        return True, f"獲得貴人指導，{msg}"

    def _skill_challenge_event(self):
        """技能挑戰事件"""
        available_skills = list(self.game.data.professional_skills.keys())
        skill = random.choice(available_skills)

        # 有一定機率成功
        if random.random() < 0.7:
            exp_gain = random.randint(20, 35)
            upgrade_result, msg = self.gain_skill_experience(skill, exp_gain)
            return True, f"成功完成挑戰任務，{msg}"
        else:
            return True, f"挑戰任務失敗，但獲得寶貴經驗"

    def _team_project_event(self):
        """團隊專案事件"""
        skills_to_gain = ['團隊合作', '溝通能力', '問題解決']
        total_exp = 0

        for skill in skills_to_gain:
            if skill in self.game.data.professional_skills:
                exp_gain = random.randint(5, 15)
                self.gain_skill_experience(skill, exp_gain)
                total_exp += exp_gain

        return True, f"參與團隊專案，獲得 {total_exp} 點綜合經驗"
