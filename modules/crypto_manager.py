import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from config import BTC_VOLATILITY, BTC_MIN_PRICE, CRYPTO_MINED_PER_HASHRATE

class CryptoManager:
    def __init__(self, game):
        self.game = game
        self.btc_info_label = None
        self.btc_value_label = None
        self.btc_mine_label = None
        self.btc_fig = None
        self.btc_ax = None
        self.btc_canvas = None
        self.btc_range_var = None

    def create_crypto_tab(self, tab_control):
        # 比特幣獨立分頁
        btc_tab = ttk.Frame(tab_control)
        tab_control.add(btc_tab, text="₿ 比特幣")
        
        # 分頁切換事件處理函式
        def on_tab_changed(event):
            current = tab_control.select()
            if current == tab_control.tabs()[tab_control.index(btc_tab)]:
                btc_tab.after(100, lambda: btc_tab.focus_set())
        
        # 礦機與比特幣資訊區塊
        btc_info_frame = ttk.LabelFrame(btc_tab, text="礦機與比特幣資訊", padding="8")
        btc_info_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.btc_info_label = ttk.Label(btc_info_frame, text="", font=("Microsoft JhengHei", 12))
        self.btc_info_label.pack(anchor='w')
        
        self.btc_value_label = ttk.Label(btc_info_frame, text="", font=("Microsoft JhengHei", 11), foreground="#fdcb6e")
        self.btc_value_label.pack(anchor='w', pady=(0,0))
        
        self.btc_mine_label = ttk.Label(btc_info_frame, text="", font=("Microsoft JhengHei", 11), foreground="#00b894")
        self.btc_mine_label.pack(anchor='w', pady=(2,0))
        
        self.update_btc_info()

        # 礦機購買按鈕區
        buy_btns_frame = ttk.Frame(btc_info_frame)
        buy_btns_frame.pack(anchor='w', pady=(4,0))
        ttk.Button(buy_btns_frame, text="購買 1 kh（$500）", command=lambda: self.buy_miner_with_kh(1, 500)).pack(side=tk.LEFT, padx=2)
        ttk.Button(buy_btns_frame, text="購買 2 kh（$1000）", command=lambda: self.buy_miner_with_kh(2, 1000)).pack(side=tk.LEFT, padx=2)
        ttk.Button(buy_btns_frame, text="購買 3 kh（$1500）", command=lambda: self.buy_miner_with_kh(3, 1500)).pack(side=tk.LEFT, padx=2)
        ttk.Button(buy_btns_frame, text="購買 4 kh（$2000）", command=lambda: self.buy_miner_with_kh(4, 2000)).pack(side=tk.LEFT, padx=2)

        # 比特幣賣出區塊
        sell_frame = ttk.Frame(btc_info_frame)
        sell_frame.pack(anchor='w', pady=(8,0))
        ttk.Label(sell_frame, text="賣出比特幣：", font=("Microsoft JhengHei", 11)).pack(side=tk.LEFT)
        btc_sell_var = tk.StringVar()
        btc_sell_entry = ttk.Entry(sell_frame, textvariable=btc_sell_var, width=8, font=("Microsoft JhengHei", 11))
        btc_sell_entry.pack(side=tk.LEFT, padx=4)
        
        def sell_btc():
            try:
                amount = float(btc_sell_var.get())
                btc_balance = getattr(self.game.data, 'btc_balance', 0)
                price = self.game.data.stocks['BTC']['price']
                if amount <= 0:
                    messagebox.showwarning("輸入錯誤", "請輸入正確的比特幣數量！")
                    return
                if amount > btc_balance:
                    messagebox.showwarning("餘額不足", f"比特幣餘額不足！目前餘額：{btc_balance:.4f} BTC")
                    return
                    
                self.game.data.btc_balance -= amount
                self.game.data.cash += amount * price
                self.game.log_transaction(f"賣出比特幣 {amount:.4f}，單價 ${price:.2f}，獲得 ${amount*price:.2f}")
                self.update_btc_info()
                self.game.update_display()
            except ValueError:
                messagebox.showwarning("輸入錯誤", "請輸入正確的數字！")

        ttk.Button(sell_frame, text="賣出", command=sell_btc).pack(side=tk.LEFT, padx=4)

        # 比特幣價格走勢圖表
        btc_chart_frame = ttk.LabelFrame(btc_tab, text="比特幣價格走勢", padding="8")
        btc_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 綁定分頁切換事件
        tab_control.bind('<<NotebookTabChanged>>', on_tab_changed)
        self.btc_range_var = tk.StringVar(value='近50筆')
        self.btc_fig, self.btc_ax = plt.subplots(figsize=(7, 4))
        self.btc_canvas = FigureCanvasTkAgg(self.btc_fig, master=btc_chart_frame)
        btc_chart_widget = self.btc_canvas.get_tk_widget()
        btc_chart_widget.pack(fill=tk.BOTH, expand=True)

        # 設定正確的圖表標題
        self.btc_ax.set_title(f"{self.game.data.stocks['BTC']['name']} 價格走勢", fontsize=12)
        
        # 存入主 game 以便 update_charts 使用
        if not hasattr(self.game, 'axes'):
            self.game.axes = {}
        if not hasattr(self.game, 'canvases'):
            self.game.canvases = {}
        if not hasattr(self.game, 'chart_ranges'):
            self.game.chart_ranges = {}
            
        self.game.axes['BTC'] = self.btc_ax
        self.game.canvases['BTC'] = self.btc_canvas
        self.game.chart_ranges['BTC'] = self.btc_range_var

    def on_daily_tick(self):
        """
        Daily crypto updates:
        - Random BTC price movement and history append
        - Mining yield based on hashrate
        - Refresh BTC info labels
        """
        try:
            btc = self.game.data.stocks.get('BTC')
            if not btc:
                return
            # 價格隨機波動
            btc_change = random.gauss(0, BTC_VOLATILITY)
            btc['price'] = max(BTC_MIN_PRICE, round(btc['price'] * (1 + btc_change)))
            btc.setdefault('history', []).append(btc['price'])
            # 自動產出比特幣
            hashrate = getattr(self.game.data, 'btc_hashrate', 0)
            if hashrate > 0:
                mined = hashrate * CRYPTO_MINED_PER_HASHRATE
                self.game.data.btc_balance = getattr(self.game.data, 'btc_balance', 0) + mined
            # 更新顯示
            if self.btc_info_label is not None:
                self.update_btc_info()
        except Exception as e:
            try:
                self.game.debug_log(f"crypto on_daily_tick error: {e}")
            except Exception:
                pass

    def update_btc_info(self):
        btc = self.game.data.stocks['BTC']
        btc_balance = self.game.data.btc_balance
        miner_count = getattr(self.game.data, 'btc_miner_count', 0)
        hashrate = getattr(self.game.data, 'btc_hashrate', 0)
        self.btc_info_label.config(text=f"礦機數：{miner_count} 台｜算力：{hashrate:.2f} kh｜比特幣持有：{btc_balance:.4f}")
        btc_per_round = hashrate * 0.01
        self.btc_mine_label.config(text=f"每回合產出：{btc_per_round:.4f} BTC")
        # 顯示比特幣市值
        btc_value = btc_balance * btc['price']
        self.btc_value_label.config(text=f"市值：${btc_value:,.2f}")

    def buy_miner_with_kh(self, kh, price):
        if self.game.data.cash >= price:
            self.game.data.cash -= price
            self.game.data.btc_miner_count += kh
            self.game.data.btc_hashrate += kh  # 每 kh 算力
            self.game.log_transaction(f"購買礦機，花費 ${price}，增加 {kh} kh，總算力：{self.game.data.btc_hashrate:.2f} kh")
            self.update_btc_info()
            self.game.update_display()
        else:
            messagebox.showwarning("現金不足", f"購買 {kh} kh 礦機需要 ${price} 現金！")
