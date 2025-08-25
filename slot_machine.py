import tkinter as tk
from tkinter import ttk, messagebox
import random

class SlotMachine:
    def __init__(self, game):
        self.game = game
        self.instances = []  # 儲存多台機台的元件與狀態
        # 預設每台機台的賠率表，可自訂
        self.machine_configs = [
            {  # 機台1：高風險高報酬
                'name': '高風險機',
                'cost': 100,  # <-- 新增：參數化參加費
                'rates': {
                    '777': 200,
                    'triple': 40,
                    'double': 8,
                    'other': -1
                }
            },
            {  # 機台2：低風險穩定
                'name': '穩健機',
                'cost': 50,   # <-- 新增：為不同機台設定不同費用
                'rates': {
                    '777': 50,
                    'triple': 10,
                    'double': 3,
                    'other': -1
                }
            }
        ]

    def create_ui(self, root):
        idx = len(self.instances)
        config = self.machine_configs[idx % len(self.machine_configs)]
        frame = ttk.LabelFrame(root, text=f"拉霸機 - {config['name']}", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        # 賠率表顯示
        rate_text = f"賠率表：777={config['rates']['777']}倍，三同={config['rates']['triple']}倍，兩同={config['rates']['double']}倍，其他={config['rates']['other']}倍"
        ttk.Label(frame, text=rate_text, foreground="#888", font=("Microsoft JhengHei", 10)).pack(pady=2)
        # 賭注輸入
        bet_frame = ttk.Frame(frame)
        bet_frame.pack(pady=5)
        ttk.Label(bet_frame, text="賭注:").pack(side=tk.LEFT)
        bet_entry = ttk.Entry(bet_frame, width=8)
        bet_entry.pack(side=tk.LEFT, padx=5)
        bet_entry.insert(0, "100")
        # 拉霸顯示區域
        slot_display = ttk.Frame(frame)
        slot_display.pack(pady=10)
        slot_labels = []
        for i in range(3):
            label = ttk.Label(slot_display, text="0", font=("Arial", 24, "bold"), width=3, anchor="center")
            label.pack(side=tk.LEFT, padx=5)
            slot_labels.append(label)
        
        # 使用設定檔中的參加費來顯示提示
        spin_result_label = ttk.Label(frame, text=f"參加費 ${config['cost']}", font=("Microsoft JhengHei", 11))
        spin_result_label.pack(pady=5)
        
        # 將本機台所有元件與狀態打包
        instance = {
            'bet_entry': bet_entry,
            'slot_labels': slot_labels,
            'spin_result_label': spin_result_label,
            'spin_button': None,
            'config': config,  # <-- 儲存整個設定檔
        }

        def spin_button_click_local(inst=instance):
            try:
                bet_amount = int(inst['bet_entry'].get())
                if bet_amount <= 0:
                    self.game.log_transaction("拉霸失敗：請輸入正整數賭注！")
                    return
            except ValueError:
                self.game.log_transaction("拉霸失敗：請輸入有效賭注！")
                return
            self.spin(bet_amount, inst)
            
        spin_button = ttk.Button(frame, text="拉霸！", command=spin_button_click_local)
        spin_button.pack(pady=10)
        instance['spin_button'] = spin_button
        self.instances.append(instance)
        return frame

    def spin(self, bet_amount, inst):
        cost = inst['config']['cost']
        if self.game.data.cash < cost + bet_amount:
            inst['spin_result_label'].config(text="現金不足，無法玩！")
            self.game.log_transaction(f"拉霸失敗：現金不足 (需要 ${cost+bet_amount})")
            return
            
        inst['spin_button'].config(state='disabled')
        inst['spin_result_label'].config(text="拉霸中...")
        
        # 先扣除參加費和賭注
        self.game.data.cash -= cost
        self.game.data.cash -= bet_amount
        
        # 拉霸機三個轉盤，數字 1~7
        results = [random.randint(1, 7) for _ in range(3)]
        
        # 決定賠率
        rates = inst['config']['rates']
        if results == [7, 7, 7]:
            multiplier = rates['777']
        elif results[0] == results[1] == results[2]:
            multiplier = rates['triple']
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            multiplier = rates['double']
        else:
            multiplier = rates['other']
            
        winnings = int(bet_amount * multiplier)
        self.game.data.last_slot_win = winnings

        # 初始化累積贏金和連勝紀錄 (如果不存在)
        if not hasattr(self.game.data, 'slot_total_win'):
            self.game.data.slot_total_win = 0
        if not hasattr(self.game.data, 'slot_win_streak'):
            self.game.data.slot_win_streak = 0
        
        if winnings > 0:
            self.game.data.slot_total_win += winnings
            self.game.data.slot_win_streak += 1
        else:
            self.game.data.slot_win_streak = 0
        
        # 寫入賭場排行榜 (只記錄贏的金額)
        if winnings > 0:
            try:
                from leaderboard import CasinoLeaderboard
                if hasattr(self.game, 'username'):
                    CasinoLeaderboard().add_casino_record(self.game.username, winnings)
            except Exception as e:
                print("CasinoLeaderboard error:", e)

        # 動畫效果
        for i, num in enumerate(results):
            self.animate_slot(inst['slot_labels'][i], num, i * 500)
            
        def show_result():
            # 將贏得的金額加回現金
            if winnings > 0:
                self.game.data.cash += winnings

            result_text = f"結果: {results[0]} {results[1]} {results[2]}\n倍數: {multiplier:+.1f}倍\n獲得: ${winnings:+d}"
            inst['spin_result_label'].config(text=result_text)
            self.game.log_transaction(f"拉霸結果: {results} 倍數 {multiplier:+.1f}倍, 獲得 ${winnings:+d}")
            self.game.update_display()
            inst['spin_button'].config(state='normal')
            
            # --- 關鍵修改：改變成就解鎖的提示方式 ---
            # 改為呼叫主遊戲的 check_achievements，它會自動將解鎖訊息寫入日誌
            if hasattr(self.game, 'check_achievements'):
                self.game.check_achievements()

        self.game.root.after(2500, show_result)

    def animate_slot(self, label, final_number, delay):
        numbers = list(range(10))
        frames = 20
        def update_number(frame):
            if frame < frames:
                label.config(text=str(random.choice(numbers)))
                self.game.root.after(50, update_number, frame + 1)
            else:
                label.config(text=str(final_number))
        self.game.root.after(delay, update_number, 0)