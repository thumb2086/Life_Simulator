"""Education and career system for Life Simulator.

Manages degrees, skills, certifications, jobs, and salaries.
Higher education unlocks better jobs and higher income.
Skills affect efficiency in various game systems.
"""

from __future__ import annotations

import random


DEGREE_ORDER = ["高中", "專科", "學士", "碩士", "博士"]

DEGREE_INFO = {
    "高中": {"label": "高中", "cost": 0, "daily_salary": 300, "study_days": 0},
    "專科": {"label": "專科", "cost": 80000, "daily_salary": 500, "study_days": 60},
    "學士": {"label": "大學學士", "cost": 200000, "daily_salary": 800, "study_days": 120},
    "碩士": {"label": "碩士", "cost": 350000, "daily_salary": 1200, "study_days": 180},
    "博士": {"label": "博士", "cost": 600000, "daily_salary": 1800, "study_days": 300},
}

JOBS = [
    {"title": "無業", "min_degree": "高中", "salary": 0, "skill_req": {}},
    {"title": "作業員", "min_degree": "高中", "salary": 400, "skill_req": {}},
    {"title": "技術員", "min_degree": "專科", "salary": 650, "skill_req": {"技術": 2}},
    {"title": "工程師", "min_degree": "學士", "salary": 1000, "skill_req": {"程式": 3}},
    {"title": "資深工程師", "min_degree": "學士", "salary": 1500, "skill_req": {"程式": 5}},
    {"title": "產品經理", "min_degree": "學士", "salary": 1300, "skill_req": {"管理": 3}},
    {"title": "技術主管", "min_degree": "碩士", "salary": 2000, "skill_req": {"程式": 5, "管理": 3}},
    {"title": "架構師", "min_degree": "碩士", "salary": 2500, "skill_req": {"程式": 7}},
    {"title": "研究員", "min_degree": "碩士", "salary": 1800, "skill_req": {"研究": 4}},
    {"title": "教授", "min_degree": "博士", "salary": 2200, "skill_req": {"研究": 6}},
    {"title": "CTO", "min_degree": "碩士", "salary": 3500, "skill_req": {"程式": 7, "管理": 5}},
    {"title": "CEO", "min_degree": "學士", "salary": 4000, "skill_req": {"管理": 8}},
]

SKILLS = ["程式", "技術", "管理", "研究", "金融", "社交", "創意"]

SKILL_COSTS = {
    "基礎": {"cash": 2000, "study_days": 15, "gain": 1},
    "進階": {"cash": 8000, "study_days": 30, "gain": 1},
    "精通": {"cash": 25000, "study_days": 60, "gain": 1},
}

CERTIFICATIONS = {
    "PMP": {"cost": 15000, "skill": "管理", "bonus": 2},
    "AWS": {"cost": 12000, "skill": "程式", "bonus": 2},
    "CFA": {"cost": 20000, "skill": "金融", "bonus": 3},
    "TOEIC": {"cost": 5000, "skill": "社交", "bonus": 1},
}


class EducationManager:
    """Manages education, skills, jobs, and career progression."""

    def __init__(self, data) -> None:
        self.data = data


    # ── Daily Processing ──────────────────────────────────────────────

    def process_daily(self) -> str:
        """Process daily salary and study progress."""
        edu = self.data.education
        messages = []

        # Daily salary deposit
        salary = edu.get("base_salary", 0)
        if salary > 0:
            # Efficiency modifier from health
            health_mod = 1.0
            if hasattr(self.data, "health"):
                stress = self.data.health.get("stress", 0)
                if stress > 70:
                    health_mod = 0.85
            actual_salary = int(salary * health_mod)
            self.data.cash += actual_salary
            if health_mod < 1.0:
                messages.append(f"工作薪資 ${actual_salary:,.0f}（壓力影響效率）。")
            else:
                messages.append(f"工作薪資 +${actual_salary:,.0f}。")

        # Study hours recovery
        edu["study_hours"] = min(8, edu.get("study_hours", 0) + 4)

        # Experience gain
        if salary > 0:
            edu["experience"] = edu.get("experience", 0) + random.randint(1, 3)

        return "\n".join(messages) if messages else "今日無薪資收入。"

    # ── Player Actions ────────────────────────────────────────────────

    def study_degree(self, target_degree: str) -> str:
        """Enroll in a degree program."""
        edu = self.data.education
        if target_degree not in DEGREE_ORDER:
            return f"未知學歷：{target_degree}"
        current_idx = DEGREE_ORDER.index(edu["degree"]) if edu["degree"] in DEGREE_ORDER else 0
        target_idx = DEGREE_ORDER.index(target_degree)
        if target_idx <= current_idx:
            return f"你已有{edu['degree']}或更高學歷。"
        info = DEGREE_INFO[target_degree]
        cost = info["cost"]
        if self.data.cash < cost:
            return f"學費不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        edu["degree"] = target_degree
        # Apply new salary
        edu["base_salary"] = info["daily_salary"]
        # Stress increase from studying
        self.data.health["stress"] = min(100, self.data.health.get("stress", 0) + 20)
        return f"取得{info['label']}學歷！（學費 ${cost:,.0f}），日薪調整為 ${info['daily_salary']:,.0f}。"

    def learn_skill(self, skill_name: str, level: str = "基礎") -> str:
        """Study a specific skill."""
        edu = self.data.education
        if skill_name not in SKILLS:
            return f"未知技能：{skill_name}。可選：{', '.join(SKILLS)}"
        if level not in SKILL_COSTS:
            return f"未知等級：{level}。可選：{', '.join(SKILL_COSTS.keys())}"
        info = SKILL_COSTS[level]
        cost = info["cash"]
        if self.data.cash < cost:
            return f"學費不足，需要 ${cost:,.0f}。"
        current_level = edu.get("skills", {}).get(skill_name, 0)
        if level == "基礎" and current_level >= 1:
            return f"{skill_name}已達基礎以上。"
        if level == "進階" and current_level >= 3:
            return f"{skill_name}已達進階以上。"
        if level == "精通" and current_level >= 5:
            return f"{skill_name}已達精通。"
        self.data.cash -= cost
        edu.setdefault("skills", {})[skill_name] = current_level + info["gain"]
        self.data.health["energy"] = max(0, self.data.health.get("energy", 100) - 15)
        return f"學習{skill_name}（{level}），費用 ${cost:,.0f}，技能 +{info['gain']}。"

    def get_certification(self, cert_name: str) -> str:
        """Earn a professional certification."""
        edu = self.data.education
        if cert_name not in CERTIFICATIONS:
            return f"未知證照：{cert_name}。可選：{', '.join(CERTIFICATIONS.keys())}"
        certs = edu.get("certifications", [])
        if cert_name in certs:
            return f"你已擁有{cert_name}證照。"
        info = CERTIFICATIONS[cert_name]
        cost = info["cost"]
        if self.data.cash < cost:
            return f"考試費用不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        certs.append(cert_name)
        edu["certifications"] = certs
        # Skill bonus
        skill = info["skill"]
        edu.setdefault("skills", {})[skill] = edu.get("skills", {}).get(skill, 0) + info["bonus"]
        return f"取得{cert_name}證照！（${cost:,.0f}），{skill} +{info['bonus']}。"

    def apply_job(self, job_title: str) -> str:
        """Apply for a new job."""
        edu = self.data.education
        job = next((j for j in JOBS if j["title"] == job_title), None)
        if not job:
            return f"未知職位：{job_title}"
        # Check degree requirement
        deg_idx = DEGREE_ORDER.index(job["min_degree"]) if job["min_degree"] in DEGREE_ORDER else 0
        cur_idx = DEGREE_ORDER.index(edu["degree"]) if edu["degree"] in DEGREE_ORDER else 0
        if cur_idx < deg_idx:
            return f"學歷不足，需要{job['min_degree']}。"
        # Check skill requirements
        skills = edu.get("skills", {})
        for skill, req_level in job["skill_req"].items():
            if skills.get(skill, 0) < req_level:
                return f"技能不足，{skill}需要 Lv.{req_level}，目前 Lv.{skills.get(skill, 0)}。"
        edu["job_title"] = job["title"]
        edu["base_salary"] = job["salary"]
        return f"錄取{job['title']}！日薪 ${job['salary']:,.0f}。"

    def quit_job(self) -> str:
        """Quit current job."""
        edu = self.data.education
        if edu["job_title"] == "無業":
            return "你已經沒有工作。"
        old = edu["job_title"]
        edu["job_title"] = "無業"
        edu["base_salary"] = 0
        return f"辭去{old}。"

    # ── Queries ───────────────────────────────────────────────────────

    def available_jobs(self) -> list[str]:
        """Return list of jobs the player qualifies for."""
        edu = self.data.education
        skills = edu.get("skills", {})
        available = []
        for job in JOBS:
            deg_idx = DEGREE_ORDER.index(job["min_degree"]) if job["min_degree"] in DEGREE_ORDER else 0
            cur_idx = DEGREE_ORDER.index(edu["degree"]) if edu["degree"] in DEGREE_ORDER else 0
            if cur_idx < deg_idx:
                continue
            qualified = True
            for skill, req in job["skill_req"].items():
                if skills.get(skill, 0) < req:
                    qualified = False
                    break
            if qualified:
                available.append(f"{job['title']} (${job['salary']:,}/日)")
        return available

    def status_text(self) -> str:
        """Return formatted education status."""
        edu = self.data.education
        skills = edu.get("skills", [])
        skill_str = ", ".join(f"{k} Lv.{v}" for k, v in skills.items()) if skills else "無"
        certs = edu.get("certifications", [])
        cert_str = ", ".join(certs) if certs else "無"
        return (
            f"學歷：{edu['degree']} | "
            f"職位：{edu['job_title']} | "
            f"日薪 ${edu['base_salary']:,.0f} | "
            f"經驗 {edu.get('experience', 0)} | "
            f"技能：{skill_str} | "
            f"證照：{cert_str}"
        )
