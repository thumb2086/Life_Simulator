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
                if job:
                    g.job_labels['name'].config(text=f"職稱：{job.get('name','-')}")
                    g.job_labels['level'].config(text=f"等級：{job.get('level',1)}")
                    g.job_labels['salary'].config(text=f"日薪：${job.get('salary_per_day',0.0):.2f}")
                    g.job_labels['tax'].config(text=f"稅率：{job.get('tax_rate',0.0)*100:.1f}%")
                    g.job_labels['next'].config(text=f"下次升職日：第 {job.get('next_promotion_day','-')} 天")
                else:
                    g.job_labels['name'].config(text="職稱：未就業")
                    g.job_labels['level'].config(text="等級：-")
                    g.job_labels['salary'].config(text="日薪：$0.00")
                    g.job_labels['tax'].config(text="稅率：0.0%")
                    g.job_labels['next'].config(text="下次升職日：-")
        except Exception:
            pass

    # --- 邏輯 ---
    def select_job(self, name: str):
        g = self.game
        cat = getattr(g.data, 'jobs_catalog', {})
        if name not in cat:
            g.show_event_message("無效的職業！")
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
