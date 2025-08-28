from __future__ import annotations

from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from bank_game import BankGame


class JobManager:
    def __init__(self, game: 'BankGame'):
        self.game = game

    # --- UI ---
    def update_job_ui(self):
        g = self.game
        try:
            if hasattr(g, 'job_labels'):
                job = getattr(g.data, 'job', None)
                # 共同資訊：公司與學歷（若有對應的標籤）
                comp_name = getattr(g.data, 'current_company', '一般公司')
                comp_mult = float(getattr(g.data, 'companies_catalog', {}).get(comp_name, {}).get('salary_multiplier', 1.0))
                edu_level = getattr(g.data, 'education_level', '高中')
                edu_mult = float(getattr(g.data, 'education_multipliers', {}).get(edu_level, 1.0))
                # 若進修中，顯示預計完成日
                edu_suffix = ""
                try:
                    sip = getattr(g.data, 'study_in_progress', None)
                    if isinstance(sip, dict):
                        finish_day = int(sip.get('finish_day', 0))
                        target = str(sip.get('target', ''))
                        if target:
                            edu_suffix = f"（進修中→{target}，預計第 {finish_day} 天完成）"
                except Exception:
                    pass
                if job:
                    g.job_labels['name'].config(text=f"職稱：{job.get('name','-')}")
                    g.job_labels['level'].config(text=f"等級：{job.get('level',1)}")
                    g.job_labels['salary'].config(text=f"日薪：${job.get('salary_per_day',0.0):.2f}")
                    g.job_labels['tax'].config(text=f"稅率：{job.get('tax_rate',0.0)*100:.1f}%")
                    g.job_labels['next'].config(text=f"下次升職日：第 {job.get('next_promotion_day','-')} 天")
                    if 'company' in g.job_labels:
                        g.job_labels['company'].config(text=f"公司：{comp_name}（x{comp_mult:.2f}）")
                    if 'education' in g.job_labels:
                        g.job_labels['education'].config(text=f"學歷：{edu_level}（x{edu_mult:.2f}）{edu_suffix}")
                else:
                    g.job_labels['name'].config(text="職稱：未就業")
                    g.job_labels['level'].config(text="等級：-")
                    g.job_labels['salary'].config(text="日薪：$0.00")
                    g.job_labels['tax'].config(text="稅率：0.0%")
                    g.job_labels['next'].config(text="下次升職日：-")
                    if 'company' in g.job_labels:
                        g.job_labels['company'].config(text=f"公司：{comp_name}（x{comp_mult:.2f}）")
                    if 'education' in g.job_labels:
                        g.job_labels['education'].config(text=f"學歷：{edu_level}（x{edu_mult:.2f}）{edu_suffix}")
        except Exception:
            pass

    # --- 邏輯 ---
    def select_job(self, name: str):
        g = self.game
        cat = getattr(g.data, 'jobs_catalog', {})
        if name not in cat:
            g.show_event_message("無效的職業！")
            return
        current = getattr(g.data, 'job', None)
        # 規則：
        # 1) 未就業時，只能選擇入門職位「實習生」。
        # 2) 已就業時，不可直接更換工作，請透過升遷。
        if current:
            if current.get('name') == name:
                g.show_event_message("已在該職位上班中！")
                return
            g.show_event_message("不可直接更換職位，請透過升遷路徑提升。")
            return
        entry = '實習生'
        if name != entry:
            g.show_event_message(f"入門僅能選擇「{entry}」！")
            return
        info = cat[name]
        g.data.job = {
            'name': name,
            'level': 1,
            'salary_per_day': float(info.get('base_salary_per_day', 0.0)),
            'tax_rate': float(info.get('tax_rate', 0.0)),
            'next_promotion_day': g.data.days + 7,
        }
        g.log_transaction(f"已選擇工作：{name}，日薪 ${g.data.job['salary_per_day']:.2f}")
        self.update_job_ui()
        g._pending_save = True
        g.schedule_persist()

    def promote_job(self):
        g = self.game
        job = getattr(g.data, 'job', None)
        if not job:
            g.show_event_message("尚未選擇工作！")
            return
        if g.data.days < job.get('next_promotion_day', 0):
            g.show_event_message("還沒到可升職的日子！")
            return
        # 機率判定：基礎 60% 成功率，學歷與屬性（智力/勤奮/魅力/今日運氣/經驗）提供加成
        try:
            edu_level = getattr(g.data, 'education_level', '高中')
            bonus_map = {'高中': 0.00, '大學': 0.05, '碩士': 0.08, '博士': 0.10}
            base_rate = 0.60
            # 屬性權重（轉為 -/+ 的微幅加成）
            intel = float(getattr(g.data, 'intelligence', 50.0))
            dili = float(getattr(g.data, 'diligence', 50.0))
            chrm = float(getattr(g.data, 'charisma', 50.0))
            luck = float(getattr(g.data, 'luck_today', 50.0))
            exp = float(getattr(g.data, 'experience', 0.0))
            attr_bonus = 0.0
            attr_bonus += (intel - 50.0) / 200.0   # -0.25 ~ +0.25
            attr_bonus += (dili - 50.0) / 250.0   # -0.20 ~ +0.20
            attr_bonus += (chrm - 50.0) / 250.0   # -0.20 ~ +0.20
            attr_bonus += (luck - 50.0) / 200.0   # -0.25 ~ +0.25（當日）
            attr_bonus += min(exp, 100.0) / 500.0 # +0.00 ~ +0.20（上限）
            success_rate = base_rate + bonus_map.get(edu_level, 0.0) + attr_bonus
            success_rate = max(0.10, min(0.95, success_rate))
            roll = random.random()
            if roll <= success_rate:
                job['level'] = int(job.get('level', 1)) + 1
                job['salary_per_day'] = round(float(job.get('salary_per_day', 0.0)) * 1.2, 2)
                # 成功後冷卻：基礎 14 天，勤奮高者可微幅縮短（-0~2天）
                cooldown = 14 - int(max(0, (dili - 50.0)) // 25)
                cooldown = max(10, min(14, cooldown))
                job['next_promotion_day'] = g.data.days + cooldown
                g.log_transaction(f"升職成功（機率 {success_rate*100:.0f}%）！目前等級 {job['level']}，新日薪 ${job['salary_per_day']:.2f}（下次可於第 {job['next_promotion_day']} 天）")
                g.show_event_message("升職成功！恭喜晉升！")
            else:
                # 失敗：基礎冷卻 7 天，勤奮高者縮短 1~2 天，最低 5 天
                fail_cd = 7 - int(max(0, (dili - 50.0)) // 25)
                fail_cd = max(5, min(9, fail_cd))
                job['next_promotion_day'] = g.data.days + fail_cd
                g.log_transaction(f"升職失敗（機率 {success_rate*100:.0f}%）！可於第 {job['next_promotion_day']} 天再試")
                g.show_event_message("升職失敗，請再接再厲！")
            self.update_job_ui()
            g._pending_save = True
            g.schedule_persist()
        except Exception:
            # 若出錯，回退為必定成功（避免卡死）
            job['level'] = int(job.get('level', 1)) + 1
            job['salary_per_day'] = round(float(job.get('salary_per_day', 0.0)) * 1.2, 2)
            job['next_promotion_day'] = g.data.days + 14
            g.log_transaction(f"升職成功！目前等級 {job['level']}，新日薪 ${job['salary_per_day']:.2f}")
            g.show_event_message("升職成功！")
            self.update_job_ui()
            g._pending_save = True
            g.schedule_persist()

    # --- 公司選擇 ---
    def select_company(self, name: str):
        g = self.game
        cats = getattr(g.data, 'companies_catalog', {})
        if name not in cats:
            g.show_event_message("無效的公司！")
            return False
        if getattr(g.data, 'current_company', None) == name:
            g.show_event_message("已在該公司任職！")
            return False
        g.data.current_company = name
        mult = float(cats[name].get('salary_multiplier', 1.0))
        g.log_transaction(f"加入公司：{name}（薪資倍率 x{mult:.2f}）")
        self.update_job_ui()
        g._pending_save = True
        g.schedule_persist()
        return True

    # --- 進修升學：學歷越高薪水越高 ---
    def study_upgrade(self):
        g = self.game
        levels = list(getattr(g.data, 'education_levels', []))
        cur = getattr(g.data, 'education_level', '高中')
        if cur not in levels:
            cur_idx = 0
        else:
            cur_idx = levels.index(cur)
        if cur_idx >= len(levels) - 1:
            g.show_event_message("學歷已達最高等級！")
            return False
        # 若已在進修中，提示剩餘時間
        sip = getattr(g.data, 'study_in_progress', None)
        if isinstance(sip, dict):
            finish_day = int(sip.get('finish_day', 0))
            g.show_event_message(f"進修進行中，預計第 {finish_day} 天完成！")
            return False
        next_level = levels[cur_idx + 1]
        costs = getattr(g.data, 'education_upgrade_cost', {})
        need = float(costs.get(next_level, 0.0))
        if g.data.cash < need:
            g.show_event_message(f"現金不足，升學至{next_level}需要 ${need:.2f}")
            return False
        # 設定進修所需天數（預設 14/20/30），受智力/勤奮/經驗影響縮短
        study_days_map = {'大學': 14, '碩士': 20, '博士': 30}
        base_days = int(study_days_map.get(next_level, 14))
        intel = float(getattr(g.data, 'intelligence', 50.0))
        dili = float(getattr(g.data, 'diligence', 50.0))
        exp = float(getattr(g.data, 'experience', 0.0))
        # 最高可加速 40%
        accel = 0.0
        accel += max(-0.2, (intel - 50.0) / 250.0)   # -0.2 ~ +0.2
        accel += max(-0.2, (dili - 50.0) / 250.0)    # -0.2 ~ +0.2
        accel += min(0.2, min(exp, 100.0) / 500.0)   # 0.0 ~ +0.2
        accel = max(-0.2, min(0.4, accel))
        speed_mult = max(0.6, min(1.2, 1.0 - accel))
        study_days = int(max(5, round(base_days * speed_mult)))
        finish_day = g.data.days + study_days
        # 扣款並開始進修
        g.data.cash -= need
        g.data.study_in_progress = {'target': next_level, 'finish_day': finish_day}
        g.log_transaction(f"開始進修：目標 {next_level}，需時 {study_days} 天（基礎{base_days}天，屬性加速 x{(base_days/max(study_days,1)):.2f}），預計第 {finish_day} 天完成，花費 ${need:.2f}")
        g.show_event_message(f"已開始進修（{next_level}），需時 {study_days} 天！")
        self.update_job_ui()
        g._pending_save = True
        g.schedule_persist()
        return True
