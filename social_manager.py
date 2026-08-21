"""Social system for Life Simulator.

Manages reputation, relationships, networking, and social events.
High social standing unlocks business opportunities and special events.
"""

from __future__ import annotations

import random


SOCIAL_EVENTS = [
    {"name": "商業聚會", "cost": 2000, "rep_gain": 3, "network_gain": 2, "mood_gain": 5},
    {"name": "慈善晚宴", "cost": 8000, "rep_gain": 8, "network_gain": 3, "mood_gain": 10},
    {"name": "同學會", "cost": 500, "rep_gain": 1, "network_gain": 1, "mood_gain": 8},
    {"name": "產業研討會", "cost": 3000, "rep_gain": 4, "network_gain": 5, "mood_gain": 3},
    {"name": "志工活動", "cost": 200, "rep_gain": 5, "network_gain": 1, "mood_gain": 12},
    {"name": "藝術展覽", "cost": 1500, "rep_gain": 2, "network_gain": 1, "mood_gain": 7},
]

NPC_NAMES = [
    "王大明", "李小華", "張志強", "陳美玲", "林家豪",
    "黃雅芬", "劉建宏", "鄭秀蘭", "周俊傑", "吳曉薇",
    "蔡明憲", "許淑惠", "郭振宇", "賴美慧", "曾國城",
]


class SocialManager:
    """Manages reputation, relationships, and social interactions."""

    def __init__(self, data) -> None:
        self.data = data


    # ── Daily Processing ──────────────────────────────────────────────

    def process_daily(self) -> str:
        """Process daily social effects: reputation decay, relationship updates."""
        soc = self.data.social
        messages = []

        # Reputation slowly decays if not maintained
        if soc["reputation"] > 10:
            soc["reputation"] = max(10, soc["reputation"] - 0.5)

        # Network relationships decay slightly
        for rel in soc.get("relationships", []):
            rel["closeness"] = max(0, rel.get("closeness", 50) - 0.3)

        # High reputation boosts mood
        if soc["reputation"] >= 50:
            self.data.health["mood"] = min(100, self.data.health.get("mood", 50) + 2)
        elif soc["reputation"] >= 30:
            self.data.health["mood"] = min(100, self.data.health.get("mood", 50) + 1)

        return "\n".join(messages) if messages else "社交狀況穩定。"

    # ── Player Actions ────────────────────────────────────────────────

    def attend_event(self, event_name: str = None) -> str:
        """Attend a social event."""
        soc = self.data.social
        if event_name is None:
            event_name = random.choice(SOCIAL_EVENTS)["name"]
        event = next((e for e in SOCIAL_EVENTS if e["name"] == event_name), None)
        if not event:
            return f"未知活動：{event_name}"
        cost = event["cost"]
        if self.data.cash < cost:
            return f"現金不足，需要 ${cost:,.0f}。"
        self.data.cash -= cost
        soc["reputation"] = min(100, soc["reputation"] + event["rep_gain"])
        soc["network_size"] = soc.get("network_size", 0) + event["network_gain"]
        soc["events_attended"] = soc.get("events_attended", 0) + 1
        self.data.health["mood"] = min(100, self.data.health.get("mood", 50) + event["mood_gain"])
        self.data.health["energy"] = max(0, self.data.health.get("energy", 100) - 10)
        return (
            f"參加{event['name']}（${cost:,.0f}），"
            f"聲望 +{event['rep_gain']}，人脈 +{event['network_gain']}，"
            f"心情 +{event['mood_gain']}。"
        )

    def network(self) -> str:
        """Network with contacts to build relationships."""
        soc = self.data.social
        if self.data.health.get("energy", 100) < 15:
            return "體力不足，無法社交。"
        self.data.health["energy"] -= 15
        # Chance to meet new NPC
        if random.random() < 0.4 or len(soc.get("relationships", [])) < 3:
            name = random.choice(NPC_NAMES)
            existing = [r["name"] for r in soc.get("relationships", [])]
            if name not in existing:
                npc = {
                    "name": name,
                    "closeness": 30,
                    "type": random.choice(["朋友", "同事", "客戶", "投資人"]),
                    "benefit": random.choice(["discount", "info", "connection", "support"]),
                }
                soc.setdefault("relationships", []).append(npc)
                soc["reputation"] = min(100, soc["reputation"] + 2)
                return f"認識新朋友：{npc['name']}（{npc['type']}）！"
            else:
                # Strengthen existing relationship
                for r in soc.get("relationships", []):
                    if r["name"] == name:
                        r["closeness"] = min(100, r["closeness"] + 10)
                        soc["reputation"] = min(100, soc["reputation"] + 1)
                        return f"與{ name}深化關係，親密度 +10。"
        soc["reputation"] = min(100, soc["reputation"] + 1)
        return "社交活動完成，聲望 +1。"

    def give_gift(self, target_name: str = None) -> str:
        """Give a gift to an NPC to boost relationship."""
        soc = self.data.social
        relationships = soc.get("relationships", [])
        if not relationships:
            return "你還沒有任何朋友。"
        if target_name is None:
            target = random.choice(relationships)
        else:
            target = next((r for r in relationships if r["name"] == target_name), None)
            if not target:
                return f"找不到{target_name}。"
        cost = 1000
        if self.data.cash < cost:
            return "現金不足（需要 $1,000）。"
        self.data.cash -= cost
        target["closeness"] = min(100, target["closeness"] + 15)
        soc["reputation"] = min(100, soc["reputation"] + 2)
        return f"送禮給{target['name']}（${cost:,.0f}），親密度 +15。"

    # ── Queries ───────────────────────────────────────────────────────

    def influence_modifier(self) -> float:
        """Return business/economic modifier from social influence."""
        rep = self.data.social.get("reputation", 10)
        if rep >= 80:
            return 1.15
        elif rep >= 50:
            return 1.08
        elif rep >= 30:
            return 1.03
        else:
            return 1.0

    def available_events(self) -> list[str]:
        """Return list of available social events."""
        return [f"{e['name']} (${e['cost']:,})" for e in SOCIAL_EVENTS]

    def status_text(self) -> str:
        """Return formatted social status."""
        soc = self.data.social
        rels = soc.get("relationships", [])
        rel_str = ", ".join(f"{r['name']}({r['type']})" for r in rels[:5]) if rels else "無"
        return (
            f"聲望 {soc['reputation']:.0f} | "
            f"人脈 {soc.get('network_size', 0)} | "
            f"好友 {soc.get('friendships', 0)} | "
            f"參與活動 {soc.get('events_attended', 0)} | "
            f"人際：{rel_str}"
        )
