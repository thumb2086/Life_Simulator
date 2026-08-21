"""Health management system for Life Simulator.

Manages energy, mood, stress, fitness, nutrition, and overall health.
Health affects work efficiency, mining output, and decision quality.
"""

from __future__ import annotations

import random


class HealthManager:
    """Manages player health, energy, mood, stress, fitness and nutrition."""

    def __init__(self, data) -> None:
        self.data = data


    # ── Daily Processing ──────────────────────────────────────────────

    def process_daily(self) -> str:
        """Run daily health calculations: recovery, decay, sickness."""
        h = self.data.health
        messages = []

        # Natural energy recovery (base 15, modified by fitness)
        fitness_bonus = h["fitness"] / 100 * 8
        recovery = int(15 + fitness_bonus)
        h["energy"] = min(h["max_energy"], h["energy"] + recovery)

        # Stress naturally decays slowly
        h["stress"] = max(0, h["stress"] - 2)

        # Mood drifts toward neutral
        if h["mood"] > 50:
            h["mood"] = max(50, h["mood"] - 1)
        elif h["mood"] < 50:
            h["mood"] = min(50, h["mood"] + 1)

        # Nutrition decays if not maintained
        if h["meal_quality"] >= 2:
            h["nutrition"] = min(100, h["nutrition"] + 3)
        else:
            h["nutrition"] = max(0, h["nutrition"] - 2)

        # Gym effect on fitness
        if h["gym_level"] > 0:
            gym_gain = h["gym_level"] * 2
            h["fitness"] = min(100, h["fitness"] + gym_gain)

        # Calculate overall health
        h["health_points"] = self._calc_health_points()

        # Sickness check
        if h["health_points"] < 30 and h["sick_days"] == 0:
            if random.random() < 0.3:
                h["sick_days"] = random.randint(1, 3)
                h["energy"] = max(0, h["energy"] - 40)
                h["mood"] = max(0, h["mood"] - 20)
                messages.append("你生病了！體力大幅下降，需要休息。")
        elif h["sick_days"] > 0:
            h["sick_days"] -= 1
            h["energy"] = min(h["max_energy"], h["energy"] + 10)
            if h["sick_days"] == 0:
                messages.append("你康復了！")
            else:
                messages.append(f"你還在生病，預計 {h['sick_days']} 天後康復。")

        return "\n".join(messages) if messages else "健康狀況穩定。"

    # ── Player Actions ────────────────────────────────────────────────

    def eat_meal(self, quality: int = 1) -> str:
        """Eat a meal. quality: 1=basic($50), 2=good($150), 3=premium($400)."""
        h = self.data.health
        costs = {1: 50, 2: 150, 3: 400}
        mood_gain = {1: 3, 2: 8, 3: 15}
        nutri_gain = {1: 5, 2: 12, 3: 20}
        quality = max(1, min(3, quality))
        cost = costs[quality]
        if self.data.cash < cost:
            return f"現金不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        h["meal_quality"] = quality
        h["nutrition"] = min(100, h["nutrition"] + nutri_gain[quality])
        h["mood"] = min(100, h["mood"] + mood_gain[quality])
        h["energy"] = min(h["max_energy"], h["energy"] + quality * 5)
        names = {1: "便當", 2: "精緻餐點", 3: "高級料理"}
        return f"吃了{names[quality]}（${cost:,.0f}），心情 +{mood_gain[quality]}，體力 +{quality * 5}。"

    def exercise(self) -> str:
        """Exercise to improve fitness. Costs energy and time."""
        h = self.data.health
        if h["energy"] < 20:
            return "體力不足，無法運動。"
        if h["sick_days"] > 0:
            return "你還在生病，不宜運動。"
        h["energy"] -= 20
        gain = random.randint(3, 7)
        h["fitness"] = min(100, h["fitness"] + gain)
        h["mood"] = min(100, h["mood"] + 5)
        h["stress"] = max(0, h["stress"] - 8)
        return f"運動完成！體能 +{gain}，心情 +5，壓力 -8。"

    def rest(self) -> str:
        """Rest to recover energy and reduce stress."""
        h = self.data.health
        recover = 30 + h["fitness"] // 10
        h["energy"] = min(h["max_energy"], h["energy"] + recover)
        h["stress"] = max(0, h["stress"] - 10)
        h["mood"] = min(100, h["mood"] + 3)
        return f"休息完畢，體力 +{recover}，壓力 -10。"

    def meditate(self) -> str:
        """Meditate to reduce stress significantly."""
        h = self.data.health
        if h["energy"] < 10:
            return "體力不足，無法冥想。"
        h["energy"] -= 10
        stress_reduce = random.randint(10, 20)
        h["stress"] = max(0, h["stress"] - stress_reduce)
        h["mood"] = min(100, h["mood"] + 5)
        return f"冥想完成，壓力 -{stress_reduce}，心情 +5。"

    def join_gym(self, level: int = 1) -> str:
        """Join or upgrade gym membership."""
        h = self.data.health
        costs = {1: 2000, 2: 5000, 3: 12000}
        level = max(1, min(3, level))
        cost = costs[level]
        if h["gym_level"] >= level:
            return f"你已有 Lv.{h['gym_level']} 健身房會員。"
        if self.data.cash < cost:
            return f"現金不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        h["gym_level"] = level
        return f"加入 Lv.{level} 健身房（${cost:,.0f}），每日自動提升體能。"

    # ── Queries ───────────────────────────────────────────────────────

    def efficiency_modifier(self) -> float:
        """Return work efficiency multiplier based on health status.

        - Healthy (health > 70): 1.1x bonus
        - Normal: 1.0x
        - Stressed (stress > 70): 0.85x penalty
        - Sick: 0.6x penalty
        - Exhausted (energy < 20): 0.7x penalty
        """
        h = self.data.health
        mod = 1.0
        if h["sick_days"] > 0:
            mod *= 0.6
        if h["energy"] < 20:
            mod *= 0.7
        if h["stress"] > 70:
            mod *= 0.85
        if h["health_points"] > 70:
            mod *= 1.1
        if h["mood"] > 75:
            mod *= 1.05
        return round(mod, 2)

    def status_text(self) -> str:
        """Return a formatted health status summary."""
        h = self.data.health
        return (
            f"體力 {h['energy']}/{h['max_energy']} | "
            f"心情 {h['mood']} | 壓力 {h['stress']} | "
            f"體能 {h['fitness']} | 營養 {h['nutrition']} | "
            f"健康 {h['health_points']}"
        )

    def status_brief(self) -> str:
        """Short status for dashboard cards."""
        h = self.data.health
        hp = h["health_points"]
        if hp >= 80:
            label = "優良"
        elif hp >= 50:
            label = "普通"
        elif hp >= 30:
            label = "不佳"
        else:
            label = "危險"
        return f"健康 {hp} ({label})"

    # ── Internal ──────────────────────────────────────────────────────

    def _calc_health_points(self) -> int:
        """Calculate overall health from component stats."""
        h = self.data.health
        base = (
            h["fitness"] * 0.25
            + h["nutrition"] * 0.25
            + (100 - h["stress"]) * 0.2
            + h["mood"] * 0.15
            + (h["energy"] / h["max_energy"] * 100) * 0.15
        )
        # Sickness penalty
        if h["sick_days"] > 0:
            base -= h["sick_days"] * 10
        return max(0, min(100, int(base)))
