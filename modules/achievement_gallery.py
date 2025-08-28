import tkinter as tk
from tkinter import ttk, scrolledtext
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame

class AchievementGallery:
    """成就圖鑒系統"""

    def __init__(self, game: 'BankGame'):
        self.game = game
        self.window = None

    def show_gallery(self):
        """顯示成就圖鑒"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.game.root)
        self.window.title("成就圖鑒 - 遊戲統計")
        self.window.geometry("1000x700")

        # 建立分頁
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 成就牆分頁
        wall_frame = ttk.Frame(notebook)
        notebook.add(wall_frame, text="成就牆")
        self._create_achievement_wall(wall_frame)

        # 統計數據分頁
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="統計數據")
        self._create_statistics_tab(stats_frame)

        # 進度追蹤分頁
        progress_frame = ttk.Frame(notebook)
        notebook.add(progress_frame, text="進度追蹤")
        self._create_progress_tab(progress_frame)

    def _create_achievement_wall(self, parent):
        """建立成就牆"""
        # 標題區域
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=10)

        ttk.Label(title_frame, text="🏆 成就牆", font=("Microsoft JhengHei", 16, "bold")).pack(side=tk.LEFT)

        # 成就統計
        if hasattr(self.game, 'achievements'):
            total_achievements = len(self.game.achievements.get_all())
            unlocked_achievements = len(self.game.achievements.get_unlocked())
            completion_rate = self.game.achievements.get_completion_rate()

            stats_text = f"總成就: {total_achievements} | 已解鎖: {unlocked_achievements} | 完成率: {completion_rate:.1%}"
            ttk.Label(title_frame, text=stats_text, font=("Microsoft JhengHei", 10)).pack(side=tk.RIGHT)

        # 成就網格區域
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 創建滾動畫布
        canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 成就按類別組織
        categories = self.game.achievements.get_category_stats()

        row = 0
        for category, stats in categories.items():
            # 類別標題
            category_frame = ttk.LabelFrame(scrollable_frame, text=f"{category} ({stats['unlocked']}/{stats['total']})")
            category_frame.grid(row=row, column=0, columnspan=4, sticky='ew', padx=10, pady=5)
            row += 1

            # 該類別的成就
            category_achievements = self.game.achievements.get_by_category(category)

            for i, achievement in enumerate(category_achievements):
                col = i % 4
                if col == 0 and i > 0:
                    row += 1

                # 成就卡片
                card_frame = ttk.Frame(category_frame, relief='ridge', borderwidth=2)
                card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

                # 成就狀態
                status_color = 'green' if achievement.unlocked else 'gray'
                status_symbol = '✅' if achievement.unlocked else '❌'

                # 成就圖標
                icon_label = ttk.Label(card_frame, text=status_symbol, font=("Arial", 20), foreground=status_color)
                icon_label.pack(pady=5)

                # 成就名稱
                name_label = ttk.Label(card_frame, text=achievement.name, font=("Microsoft JhengHei", 10, "bold"))
                name_label.pack(pady=2)

                # 成就描述
                desc_label = ttk.Label(card_frame, text=achievement.description, font=("Microsoft JhengHei", 8), wraplength=120)
                desc_label.pack(pady=2)

                # 設置卡片大小
                card_frame.configure(width=150, height=100)
                category_frame.grid_columnconfigure(col, weight=1)

        # 佈局滾動區域
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_statistics_tab(self, parent):
        """建立統計數據分頁"""
        # 遊戲總體統計
        overall_frame = ttk.LabelFrame(parent, text="遊戲總體統計")
        overall_frame.pack(fill=tk.X, padx=10, pady=10)

        # 基本統計
        basic_stats = self._get_basic_stats()
        for stat_name, stat_value in basic_stats.items():
            stat_frame = ttk.Frame(overall_frame)
            stat_frame.pack(fill=tk.X, pady=2)

            ttk.Label(stat_frame, text=f"{stat_name}:", font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)
            ttk.Label(stat_frame, text=str(stat_value), font=("Microsoft JhengHei", 10, "bold")).pack(side=tk.RIGHT)

        # 成就統計
        achievement_frame = ttk.LabelFrame(parent, text="成就統計")
        achievement_frame.pack(fill=tk.X, padx=10, pady=10)

        if hasattr(self.game, 'achievements'):
            category_stats = self.game.achievements.get_category_stats()

            for category, stats in category_stats.items():
                category_frame = ttk.Frame(achievement_frame)
                category_frame.pack(fill=tk.X, pady=2)

                ttk.Label(category_frame, text=f"{category}:", font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)

                # 進度條
                progress_var = tk.DoubleVar(value=stats['rate'] * 100)
                progress_bar = ttk.Progressbar(category_frame, variable=progress_var, maximum=100, length=200)
                progress_bar.pack(side=tk.RIGHT)

                ttk.Label(category_frame, text=f"{stats['unlocked']}/{stats['total']} ({stats['rate']:.1%})",
                         font=("Microsoft JhengHei", 9)).pack(side=tk.RIGHT, padx=5)

        # 系統使用統計
        usage_frame = ttk.LabelFrame(parent, text="系統使用統計")
        usage_frame.pack(fill=tk.X, padx=10, pady=10)

        usage_stats = self._get_usage_stats()
        for stat_name, stat_value in usage_stats.items():
            stat_frame = ttk.Frame(usage_frame)
            stat_frame.pack(fill=tk.X, pady=2)

            ttk.Label(stat_frame, text=f"{stat_name}:", font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)
            ttk.Label(stat_frame, text=str(stat_value), font=("Microsoft JhengHei", 10, "bold")).pack(side=tk.RIGHT)

    def _create_progress_tab(self, parent):
        """建立進度追蹤分頁"""
        # 近期成就
        recent_frame = ttk.LabelFrame(parent, text="近期解鎖成就")
        recent_frame.pack(fill=tk.X, padx=10, pady=10)

        if hasattr(self.game, 'achievements'):
            unlocked_achievements = self.game.achievements.get_unlocked()
            recent_achievements = unlocked_achievements[-10:]  # 最近10個成就

            if recent_achievements:
                for achievement in reversed(recent_achievements):
                    achievement_frame = ttk.Frame(recent_frame)
                    achievement_frame.pack(fill=tk.X, pady=3)

                    ttk.Label(achievement_frame, text="🏆", font=("Arial", 14)).pack(side=tk.LEFT, padx=5)
                    ttk.Label(achievement_frame, text=achievement.name, font=("Microsoft JhengHei", 10, "bold")).pack(side=tk.LEFT)
                    ttk.Label(achievement_frame, text=achievement.description, font=("Microsoft JhengHei", 9)).pack(side=tk.RIGHT)
            else:
                ttk.Label(recent_frame, text="尚未解鎖任何成就", font=("Microsoft JhengHei", 10)).pack(pady=10)

        # 進度指標
        progress_frame = ttk.LabelFrame(parent, text="進度指標")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)

        # 遊戲進度
        game_progress = self._calculate_game_progress()
        for progress_name, progress_value in game_progress.items():
            progress_item_frame = ttk.Frame(progress_frame)
            progress_item_frame.pack(fill=tk.X, pady=3)

            ttk.Label(progress_item_frame, text=f"{progress_name}:", font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)

            # 進度條
            progress_var = tk.DoubleVar(value=progress_value)
            progress_bar = ttk.Progressbar(progress_item_frame, variable=progress_var, maximum=100, length=150)
            progress_bar.pack(side=tk.RIGHT)

            ttk.Label(progress_item_frame, text=f"{progress_value:.1f}%", font=("Microsoft JhengHei", 9)).pack(side=tk.RIGHT, padx=5)

        # 里程碑
        milestone_frame = ttk.LabelFrame(parent, text="里程碑")
        milestone_frame.pack(fill=tk.X, padx=10, pady=10)

        milestones = self._get_milestones()
        for milestone in milestones:
            milestone_item_frame = ttk.Frame(milestone_frame)
            milestone_item_frame.pack(fill=tk.X, pady=2)

            status_symbol = "✅" if milestone['achieved'] else "⏳"
            ttk.Label(milestone_item_frame, text=status_symbol, font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
            ttk.Label(milestone_item_frame, text=milestone['name'], font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)

            if milestone['achieved']:
                ttk.Label(milestone_item_frame, text=milestone['description'], font=("Microsoft JhengHei", 9), foreground="green").pack(side=tk.RIGHT)
            else:
                ttk.Label(milestone_item_frame, text=f"還需: {milestone['remaining']}", font=("Microsoft JhengHei", 9), foreground="gray").pack(side=tk.RIGHT)

    def _get_basic_stats(self):
        """獲取基本統計數據"""
        stats = {
            "遊戲天數": self.game.data.days,
            "重生次數": self.game.data.reborn_count,
            "總資產": f"${self.game.data.total_assets():.0f}",
            "現金餘額": f"${self.game.data.cash:.0f}",
            "存款餘額": f"${self.game.data.balance:.0f}",
            "貸款餘額": f"${self.game.data.loan:.0f}",
            "快樂度": f"{self.game.data.happiness:.1f}",
            "體力值": f"{self.game.data.stamina:.1f}",
            "智力值": f"{self.game.data.intelligence:.1f}",
            "經驗值": f"{self.game.data.experience:.1f}"
        }
        return stats

    def _get_usage_stats(self):
        """獲取系統使用統計"""
        stats = {}

        # 活動統計
        stats["讀書次數"] = getattr(self.game.data, 'activity_study_count', 0)
        stats["健身次數"] = getattr(self.game.data, 'activity_workout_count', 0)
        stats["社交次數"] = getattr(self.game.data, 'activity_social_count', 0)
        stats["冥想次數"] = getattr(self.game.data, 'activity_meditate_count', 0)

        # 事件統計
        stats["經歷事件數"] = getattr(self.game.data, 'event_count', 0)
        stats["旅行次數"] = len(getattr(self.game.data, 'travel_history', []))
        stats["購買物品數"] = len(getattr(self.game.data, 'inventory', {}))

        # 健康統計
        stats["看病次數"] = len(getattr(self.game.data, 'medical_records', []))
        stats["疾病康復次數"] = len(getattr(self.game.data, 'past_illnesses', []))

        return stats

    def _calculate_game_progress(self):
        """計算遊戲進度"""
        progress = {}

        # 資產進度
        asset_levels = [10000, 100000, 1000000, 10000000, 100000000]
        current_assets = self.game.data.total_assets()

        for i, threshold in enumerate(asset_levels):
            if current_assets >= threshold:
                progress[f"資產等級 {i+1}"] = 100
            else:
                prev_threshold = asset_levels[i-1] if i > 0 else 0
                progress_value = ((current_assets - prev_threshold) / (threshold - prev_threshold)) * 100
                progress[f"資產等級 {i+1}"] = min(100, max(0, progress_value))
                break

        # 屬性進度
        attributes = ['happiness', 'stamina', 'intelligence', 'diligence', 'charisma']
        for attr in attributes:
            value = getattr(self.game.data, attr, 0)
            progress[f"{attr}大師"] = min(100, (value / 90) * 100)

        # 職業進度
        if hasattr(self.game.data, 'career_level') and hasattr(self.game.data, 'career_experience'):
            career_progress = (self.game.data.career_experience / 50) * 10  # 每50年經驗值算10%
            progress["職業生涯"] = min(100, career_progress)

        return progress

    def _get_milestones(self):
        """獲取里程碑"""
        milestones = [
            {
                'name': '初入社會',
                'achieved': self.game.data.days >= 30,
                'description': '遊戲30天',
                'remaining': f"{max(0, 30 - self.game.data.days)}天"
            },
            {
                'name': '小有積蓄',
                'achieved': self.game.data.total_assets() >= 10000,
                'description': '資產達$10,000',
                'remaining': f"${max(0, 10000 - self.game.data.total_assets()):.0f}"
            },
            {
                'name': '百萬富翁',
                'achieved': self.game.data.total_assets() >= 1000000,
                'description': '資產達$1,000,000',
                'remaining': f"${max(0, 1000000 - self.game.data.total_assets()):.0f}"
            },
            {
                'name': '全能發展',
                'achieved': all(getattr(self.game.data, attr, 0) >= 70 for attr in ['happiness', 'stamina', 'intelligence', 'diligence', 'charisma']),
                'description': '所有屬性達70以上',
                'remaining': '繼續提升屬性'
            },
            {
                'name': '世界探索者',
                'achieved': len(getattr(self.game.data, 'travel_history', [])) >= 5,
                'description': '旅行5次以上',
                'remaining': f"{max(0, 5 - len(getattr(self.game.data, 'travel_history', [])))}次旅行"
            }
        ]

        return milestones
