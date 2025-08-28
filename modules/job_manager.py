from __future__ import annotations

from typing import TYPE_CHECKING

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
                if job:
                    g.job_labels['name'].config(text=f"職稱：{job.get('name','-')}")
                    g.job_labels['level'].config(text=f"等級：{job.get('level',1)}")
                    g.job_labels['salary'].config(text=f"日薪：${job.get('salary_per_day',0.0):.2f}")
                    g.job_labels['tax'].config(text=f"稅率：{job.get('tax_rate',0.0)*100:.1f}%")
                    g.job_labels['next'].config(text=f"下次升職日：第 {job.get('next_promotion_day','-')} 天")
                    if 'company' in g.job_labels:
                        g.job_labels['company'].config(text=f"公司：{comp_name}（x{comp_mult:.2f}）")
                    if 'education' in g.job_labels:
                        g.job_labels['education'].config(text=f"學歷：{edu_level}（x{edu_mult:.2f}）")
                else:
                    g.job_labels['name'].config(text="職稱：未就業")
                    g.job_labels['level'].config(text="等級：-")
                    g.job_labels['salary'].config(text="日薪：$0.00")
                    g.job_labels['tax'].config(text="稅率：0.0%")
                    g.job_labels['next'].config(text="下次升職日：-")
                    if 'company' in g.job_labels:
                        g.job_labels['company'].config(text=f"公司：{comp_name}（x{comp_mult:.2f}）")
                    if 'education' in g.job_labels:
                        g.job_labels['education'].config(text=f"學歷：{edu_level}（x{edu_mult:.2f}）")
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
        job['level'] = int(job.get('level', 1)) + 1
        job['salary_per_day'] = round(float(job.get('salary_per_day', 0.0)) * 1.2, 2)
        job['next_promotion_day'] = g.data.days + 14
        g.log_transaction(f"升職成功！目前等級 {job['level']}，新日薪 ${job['salary_per_day']:.2f}")
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
        next_level = levels[cur_idx + 1]
        costs = getattr(g.data, 'education_upgrade_cost', {})
        need = float(costs.get(next_level, 0.0))
        if g.data.cash < need:
            g.show_event_message(f"現金不足，升學至{next_level}需要 ${need:.2f}")
            return False
        g.data.cash -= need
        g.data.education_level = next_level
        mult = float(getattr(g.data, 'education_multipliers', {}).get(next_level, 1.0))
        g.log_transaction(f"進修成功：取得 {next_level} 學歷（薪資倍率 x{mult:.2f}），花費 ${need:.2f}")
        self.update_job_ui()
        g._pending_save = True
        g.schedule_persist()
        return True
