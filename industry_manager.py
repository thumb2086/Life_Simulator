import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FONT = ("Microsoft JhengHei", 12)

class IndustryManager:
    def __init__(self, game):
        self.game = game
        
    def update_stock_status_labels(self):
        """更新所有股票的狀態標籤"""
        if hasattr(self.game, 'stock_status_labels'):
            for code, label in self.game.stock_status_labels.items():
                stock = self.game.data.stocks[code]
                label.config(text=f"{stock['name']} ${stock['price']:.2f} 持有{stock['owned']}股")
                
        if hasattr(self.game, 'stock_dividend_labels'):
            for code, label in self.game.stock_dividend_labels.items():
                stock = self.game.data.stocks[code]
                label.config(text=f"配息：每股${stock.get('dividend_per_share', 0)}，下次配息第{stock.get('next_dividend_day', 30)}天")
        
    def create_industry_tab(self, tab_control, industry):
        # 建立產業分頁
        ind_tab = ttk.Frame(tab_control)
        tab_control.add(ind_tab, text=industry)

        # 儲存當前的 tab 和 industry 對應關係
        if not hasattr(self, '_tab_info'):
            self._tab_info = {}
            self._current_canvas = None  # 追蹤當前活動的 canvas
        
        # 先建立一個空的 tab_info，稍後補充完整資訊
        self._tab_info[industry] = {}

        # 建立通用的分頁切換處理函式
        def activate_scroll_canvas():
            tab_info = self._tab_info.get(industry)
            if not tab_info or 'scroll_canvas' not in tab_info:
                return

            canvas = tab_info['scroll_canvas']
            
            # 如果已經是當前 canvas，不需要重複設置
            if self._current_canvas == canvas:
                return
                
            # 解除前一個 canvas 的綁定
            if self._current_canvas:
                try:
                    self._current_canvas.unbind_all('<MouseWheel>')
                except:
                    pass

            # 設置新的 canvas
            self._current_canvas = canvas
            
            # 設置焦點和綁定滾輪
            canvas.focus_set()
            
            # 使用特定的標籤來綁定滾輪事件
            def on_mousewheel(e):
                canvas.yview_scroll(-1 * (e.delta // 120), "units")
                return "break"  # 防止事件傳播
                
            canvas.bind_all('<MouseWheel>', on_mousewheel, add='+')

        # 分頁切換事件處理
        def on_tab_changed(event):
            current = tab_control.select()
            if current == tab_control.tabs()[tab_control.index(ind_tab)]:
                # 使用多個延遲呼叫，確保在不同時機都能正確設置焦點
                for delay in [100, 200, 300]:
                    ind_tab.after(delay, activate_scroll_canvas)

        # 綁定分頁事件，使用 add='+' 確保不會覆蓋其他事件處理器
        tab_control.bind('<<NotebookTabChanged>>', on_tab_changed, add='+')
        
        # 綁定額外的事件來增加穩定性
        ind_tab.bind('<Visibility>', lambda e: activate_scroll_canvas(), add='+')
        ind_tab.bind('<Map>', lambda e: activate_scroll_canvas(), add='+')
        ind_tab.bind('<FocusIn>', lambda e: activate_scroll_canvas(), add='+')
        
        # 定期檢查焦點（每 5 秒）
        def check_focus():
            current = tab_control.select()
            if current == tab_control.tabs()[tab_control.index(ind_tab)]:
                activate_scroll_canvas()
            ind_tab.after(5000, check_focus)
        
        check_focus()

        # 股票操作區域
        stock_op_frame = ttk.LabelFrame(ind_tab, text=f"{industry} 股票操作", padding="10")
        stock_op_frame.pack(fill=tk.X, pady=(10,0), padx=10)
        
        # 操作區塊第一行
        row1 = ttk.Frame(stock_op_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="股數:", font=FONT).pack(side=tk.LEFT, padx=5)
        stock_amount_entry = ttk.Entry(row1, width=10, font=FONT)
        stock_amount_entry.pack(side=tk.LEFT, padx=5)

        # 取得該產業的股票列表
        stocks_in_ind = [k for k, v in self.game.data.stocks.items() if v['industry'] == industry]
        stock_code_to_name = {k: self.game.data.stocks[k]['name'] for k in stocks_in_ind}
        
        # 股票選擇下拉選單
        stock_var = tk.StringVar(value=list(stock_code_to_name.values())[0])
        stock_menu = ttk.Combobox(row1, textvariable=stock_var, values=list(stock_code_to_name.values()), 
                                state='readonly', width=8, font=FONT)
        stock_menu.pack(side=tk.LEFT, padx=5)

        # 儲存到 game 實例中
        if not hasattr(self.game, 'industry_stock_vars'):
            self.game.industry_stock_vars = {}
        if not hasattr(self.game, 'industry_stock_menus'):
            self.game.industry_stock_menus = {}
        if not hasattr(self.game, 'industry_stock_amount_entries'):
            self.game.industry_stock_amount_entries = {}
            
        self.game.industry_stock_vars[industry] = stock_var
        self.game.industry_stock_menus[industry] = stock_menu
        self.game.industry_stock_amount_entries[industry] = stock_amount_entry

        # 買賣按鈕區域
        row2 = ttk.Frame(stock_op_frame)
        row2.pack(fill=tk.X, pady=5)
        
        def make_buy(ind):
            return lambda: self.game.stock_manager.buy_stock_industry(
                ind,
                self.game.industry_stock_vars,
                self.game.industry_stock_amount_entries,
                self.game.show_event_message,
                self.game.check_achievements,
                getattr(self.game, 'trade_tip_label', None),
                getattr(self.game, 'update_stock_status_labels', None),
                getattr(self.game, 'update_trade_log', None)
            )
            
        def make_sell(ind):
            return lambda: self.game.stock_manager.sell_stock_industry(
                ind,
                self.game.industry_stock_vars,
                self.game.industry_stock_amount_entries,
                self.game.show_event_message,
                self.game.check_achievements,
                getattr(self.game, 'trade_tip_label', None),
                getattr(self.game, 'update_stock_status_labels', None),
                getattr(self.game, 'update_trade_log', None)
            )

        ttk.Button(row2, text="買入股票", command=make_buy(industry), width=12).pack(side=tk.LEFT, padx=8, pady=3)
        ttk.Button(row2, text="賣出股票", command=make_sell(industry), width=12).pack(side=tk.LEFT, padx=8, pady=3)

        # 可滾動圖表區域
        content_frame = ttk.Frame(ind_tab)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        scroll_canvas = tk.Canvas(content_frame, borderwidth=0, background='white', height=400)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=scroll_canvas.yview, width=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_frame = ttk.Frame(scroll_canvas, style='White.TFrame')
        scroll_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        canvas_frame = scroll_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 更新 tab_info 中的 scroll_canvas
        self._tab_info[industry].update({
            'scroll_canvas': scroll_canvas
        })
        
        # 立即執行一次聚焦（如果這是當前分頁）
        if tab_control.select() == tab_control.tabs()[tab_control.index(ind_tab)]:
            ind_tab.after(200, activate_scroll_canvas)

        # 滾輪事件處理
        def _bind_mousewheel(event):
            scroll_canvas.bind_all('<MouseWheel>', lambda e: scroll_canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        def _unbind_mousewheel(event):
            scroll_canvas.unbind_all('<MouseWheel>')

        scroll_canvas.bind('<Enter>', _bind_mousewheel)
        scroll_canvas.bind('<Leave>', _unbind_mousewheel)
        scroll_frame.bind('<Enter>', _bind_mousewheel)
        scroll_frame.bind('<Leave>', _unbind_mousewheel)

        # 確保滾動區域正確更新
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_frame.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))

        # 股票圖表區域
        chart_frame = ttk.Frame(scroll_frame, style='White.TFrame')
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # 設定樣式
        style = ttk.Style()
        style.configure('White.TFrame', background='white')
        style.configure('White.TLabelframe', background='white')
        style.configure('White.TLabelframe.Label', background='white')

        # 繪製每支股票的圖表
        for i, code in enumerate(stocks_in_ind):
            stock = self.game.data.stocks[code]
            row = i // 2
            col = i % 2
            
            subframe = ttk.LabelFrame(chart_frame, text=f"{stock['name']} 走勢", padding="5", style='White.TLabelframe')
            subframe.grid(row=row, column=col, sticky='nsew', padx=10, pady=10)
            chart_frame.grid_rowconfigure(row, weight=1)
            chart_frame.grid_columnconfigure(col, weight=1)

            # 增加股票現價與持有量顯示
            status_frame = ttk.Frame(subframe)
            status_frame.pack(anchor='w', pady=(0, 5))
            lbl = ttk.Label(status_frame, text="", font=("Microsoft JhengHei", 10))
            lbl.pack(side=tk.LEFT)
            div_lbl = ttk.Label(status_frame, text="", font=("Microsoft JhengHei", 9), foreground="#008800")
            div_lbl.pack(side=tk.LEFT, padx=(10, 0))

            if not hasattr(self.game, 'stock_status_labels'):
                self.game.stock_status_labels = {}
            if not hasattr(self.game, 'stock_dividend_labels'):
                self.game.stock_dividend_labels = {}
            
            self.game.stock_status_labels[code] = lbl
            self.game.stock_dividend_labels[code] = div_lbl

            # 時間範圍選擇
            range_var = tk.StringVar(value='近50筆')
            range_frame = ttk.Frame(subframe)
            range_frame.pack(fill=tk.X, pady=(0, 5))
            ttk.Radiobutton(range_frame, text="近50筆", variable=range_var, value="近50筆").pack(side=tk.LEFT)
            ttk.Radiobutton(range_frame, text="全部", variable=range_var, value="全部").pack(side=tk.LEFT)
            fig, ax = plt.subplots(figsize=(5, 3))
            fig.patch.set_facecolor('white')
            canvas = FigureCanvasTkAgg(fig, master=subframe)
            chart_widget = canvas.get_tk_widget()
            chart_widget.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            canvas.figure.set_tight_layout(True)

            # 設定圖表互動
            def on_motion(event, stock_code=code):
                stock = self.game.data.stocks[stock_code]
                ax = self.game.axes[stock_code]
                canvas = self.game.canvases[stock_code]
                range_val = self.game.chart_ranges[stock_code].get()
                if range_val == '全部':
                    h = stock['history']
                else:
                    n = int(''.join(filter(str.isdigit, range_val)))
                    h = stock['history'][-n:]
                if event.inaxes == ax:
                    x = int(round(event.xdata)) if event.xdata is not None else None
                    if x is not None and 0 <= x < len(h):
                        price = h[x]
                        ax.set_title(f"{stock['name']} 價格走勢  |  時間: {x}  價格: {price}", fontsize=12)
                    else:
                        ax.set_title(f"{stock['name']} 價格走勢", fontsize=12)
                    canvas.draw_idle()

            if hasattr(canvas, 'mpl_connect'):
                canvas._motion_cid = canvas.mpl_connect('motion_notify_event', on_motion)

            # 儲存圖表相關物件
            if not hasattr(self.game, 'axes'):
                self.game.axes = {}
            if not hasattr(self.game, 'canvases'):
                self.game.canvases = {}
            if not hasattr(self.game, 'chart_ranges'):
                self.game.chart_ranges = {}
                
            self.game.axes[code] = ax
            self.game.canvases[code] = canvas
            self.game.chart_ranges[code] = range_var

        # 股票狀態顯示區
        stock_status_frame = ttk.Frame(stock_op_frame)
        stock_status_frame.pack(fill=tk.X, pady=2)
        
        # 每個股票的狀態標籤
        if not hasattr(self.game, 'stock_status_labels'):
            self.game.stock_status_labels = {}
        if not hasattr(self.game, 'stock_dividend_labels'):
            self.game.stock_dividend_labels = {}
            
        for code in stocks_in_ind:
            stock = self.game.data.stocks[code]
            status_frame = ttk.Frame(stock_status_frame)
            status_frame.pack(anchor='w', pady=1)
            
            lbl = ttk.Label(status_frame, text="", font=FONT)
            lbl.pack(side=tk.LEFT)
            
            div_lbl = ttk.Label(status_frame, text="", font=FONT, foreground="#00b894")
            div_lbl.pack(side=tk.LEFT, padx=(10, 0))
            
            self.game.stock_status_labels[code] = lbl
            self.game.stock_dividend_labels[code] = div_lbl
