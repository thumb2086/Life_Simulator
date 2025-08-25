import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import json
from crypto_manager import CryptoManager

FONT = ("Microsoft JhengHei", 12)
HEADER_FONT = ("Microsoft JhengHei", 18, "bold")

# 標題區域
def create_header_section(root, game):
    frame = ttk.Frame(root)
    frame.pack(fill=tk.X, pady=10)
    # 三區塊：左（登入）、中（標題）、右（時間）
    left = ttk.Frame(frame)
    center = ttk.Frame(frame)
    right = ttk.Frame(frame)
    left.pack(side=tk.LEFT, anchor='w', padx=10)
    center.pack(side=tk.LEFT, expand=True)
    right.pack(side=tk.RIGHT, anchor='e', padx=10)
    # 左：登入區塊（移動原本登入區塊內容到這裡）
    game.top_left_frame = left
    # 中：標題
    ttk.Label(center, text="銀行系統", font=HEADER_FONT).pack(anchor='center')
    # 右：時間
    game.time_label = ttk.Label(right, font=FONT)
    game.time_label.pack(anchor='e')
    return frame

# 主體分頁（每個分頁一個大功能）
def create_main_tabs(root, game):
    # 先定義 function
    def disable_all_tabs():
        for i in range(tab_control.index('end')):
            tab_control.tab(i, state='disabled')
    def get_all_usernames():
        # 只顯示有 save_帳號.json 檔案的帳號
        files = [f for f in os.listdir('.') if f.startswith('save_') and f.endswith('.json')]
        usernames = [f[5:-5] for f in files]
        return usernames
    usernames = get_all_usernames()
    def do_login(event=None):
        username = game.username_var.get().strip()
        if username:
            game.username = username
            game.login_status_label.config(text=f"歡迎，{username}！")
            # 顯示重生次數
            game.reborn_label.config(text=f"重生次數：{getattr(game.data, 'reborn_count', 0)}")
            game.top_left_frame.lift()  # 保證在最上層
            game.login_btn.config(text="登出", command=do_logout)
            # 顯示現金標籤
            game.cash_label.pack(side=tk.LEFT, padx=10)
            game.cash_label.config(text=f"現金: ${game.data.cash:.2f}")
            tab_control.enable_traversal()
            for i in range(tab_control.index('end')):
                tab_control.tab(i, state='normal')
            # 載入存檔，若不存在則重設 GameData
            savefile = f"save_{username}.json"
            if os.path.exists(savefile):
                game.data.load(savefile, show_error=lambda msg: tk.messagebox.showerror("讀檔錯誤", msg))
            else:
                game.data.reset()  # 新帳號重設現金 1000
                game.data.save(savefile)  # 立刻存檔，避免自動儲存寫回舊資料
            game.savefile = savefile
            # 新增：即時刷新帳號下拉選單
            game.username_entry['values'] = get_all_usernames()
            game.update_display()
            tab_control.select(0)
        else:
            game.login_status_label.config(text="請輸入帳號！")
            game.reborn_label.config(text="")
    def do_logout():
        game.username = ""
        game.login_status_label.config(text="")
        game.login_btn.config(text="登入", command=do_login)
        # 隱藏現金標籤
        game.cash_label.pack_forget()
        disable_all_tabs()
        game.username_entry.delete(0, tk.END)
        game.top_left_frame.lift()
    def do_delete_account():
        # 彈出帳號選擇視窗
        win = tk.Toplevel(root)
        win.title("刪除帳號")
        win.geometry("300x260")
        tk.Label(win, text="選擇要刪除的帳號：", font=FONT).pack(pady=10)
        usernames_now = get_all_usernames()
        current_user = getattr(game, 'username', None)
        if current_user and current_user in usernames_now:
            sel_var = tk.StringVar(value=current_user)
        else:
            sel_var = tk.StringVar(value=usernames_now[0] if usernames_now else "")
        sel_box = ttk.Combobox(win, textvariable=sel_var, values=usernames_now, font=FONT, state='readonly')
        sel_box.pack(pady=5)
        # 直接在視窗內顯示確認訊息
        confirm_msg = tk.Label(win, text="此動作無法復原，確定要刪除嗎？", font=("Microsoft JhengHei", 10), fg="red")
        confirm_msg.pack(pady=10)
        confirmed_flag = {'done': False}  # 防呆旗標
        def do_confirm():
            if confirmed_flag['done']:
                return
            confirmed_flag['done'] = True
            username = sel_var.get().strip()
            if not username:
                tk.messagebox.showwarning("錯誤", "請選擇帳號！")
                return
            try:
                savefile = f"save_{username}.json"
                savefile_path = os.path.abspath(savefile)
                if os.path.exists(savefile_path):
                    os.remove(savefile_path)
                else:
                    print(f"找不到檔案: {savefile_path}")  # 除錯用
                # 更新排行榜資料（只保留現有帳號）
                usernames_valid = set(get_all_usernames())
                if os.path.exists('leaderboard.json'):
                    with open('leaderboard.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data = [r for r in data if r.get('username') in usernames_valid]
                    with open('leaderboard.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                # 更新賭場排行榜資料（只保留現有帳號）
                if os.path.exists('slot_casino.json'):
                    with open('slot_casino.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data = [r for r in data if r.get('username') in usernames_valid]
                    with open('slot_casino.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                # 更新下拉選單
                usernames_new = get_all_usernames()
                game.username_entry['values'] = usernames_new
                # 如果刪除的是當前登入帳號，自動登出並清空欄位，並停止自動儲存與 after 任務
                if hasattr(game, 'username') and game.username == username:
                    game.username = ""
                    game.username_var.set("")
                    game.login_status_label.config(text="已登出，帳號已刪除")
                    game.login_btn.config(text="登入", command=do_login)
                    game.cash_label.pack_forget()
                    disable_all_tabs()
                    if hasattr(game, '_after_ids'):
                        for aid in game._after_ids:
                            try:
                                game.root.after_cancel(aid)
                            except Exception:
                                pass
                        game._after_ids = []
                    if hasattr(game, 'savefile'):
                        del game.savefile
                else:
                    game.username_var.set("")
                    game.login_status_label.config(text="帳號已刪除")
                win.destroy()
            except Exception as e:
                tk.messagebox.showerror("刪除失敗", f"錯誤：{e}")
        ttk.Button(win, text="確認刪除", command=do_confirm).pack(pady=10)
        ttk.Button(win, text="取消", command=win.destroy).pack()
    def on_account_selected(event=None):
        username = game.username_var.get().strip()
        if username:
            do_login()
    # 設定全域 ttk 樣式
    style = ttk.Style()
    style.configure('TLabel', font=FONT)
    style.configure('TButton', font=FONT)
    style.configure('TCombobox', font=FONT)
    style.configure('TLabelframe.Label', font=FONT)
    # --- 全域現金顯示區 ---
    cash_frame = ttk.Frame(root)
    cash_frame.pack(fill=tk.X, pady=2)
    game.cash_label = ttk.Label(cash_frame, font=("Microsoft JhengHei", 16, "bold"), foreground="#ffe066", background="#23272e")
    # 預設隱藏
    # game.cash_label.pack(side=tk.LEFT, padx=10)
    # --- 主分頁 ---
    tab_control = ttk.Notebook(root)
    tab_control.pack(fill=tk.BOTH, expand=True)
    # --- 標題區域 ---
    # game.header = create_header_section(root, game)  # <-- 移除這行，header 只建立一次
    # --- 主視窗左上角區塊 ---
    # game.top_left_frame = ttk.Frame(root) # <-- 移除此行，改為 create_header_section 內部處理
    # game.top_left_frame.place(x=10, y=10) # <-- 秮除這行
    game.logout_btn = ttk.Button(game.top_left_frame, text="登出", command=do_logout)
    # 登入區塊
    login_inner = ttk.Frame(game.top_left_frame)
    login_inner.pack(anchor='w', pady=0)
    ttk.Label(login_inner, text="請輸入帳號：", font=("Microsoft JhengHei", 14)).pack(side=tk.LEFT, padx=(0, 4))
    game.username_var = tk.StringVar()
    game.username_entry = ttk.Combobox(login_inner, textvariable=game.username_var, values=usernames, font=FONT, width=16)
    game.username_entry.pack(side=tk.LEFT, ipady=3)
    game.username_entry.set('')  # 預設空白
    game.username_entry['state'] = 'normal'  # 可手動輸入
    game.username_entry.bind('<Return>', do_login)
    # 新增：選擇帳號即自動切換
    game.username_entry.bind('<<ComboboxSelected>>', on_account_selected)
    # 只用一個按鈕，預設為登入
    game.login_btn = ttk.Button(login_inner, text="登入", command=do_login)
    game.login_btn.pack(side=tk.LEFT, padx=(6, 0), ipadx=8, ipady=2)
    # 新增刪除帳號按鈕
    del_btn = ttk.Button(login_inner, text="刪除帳號", command=do_delete_account)
    del_btn.pack(side=tk.LEFT, padx=(6, 0), ipadx=8, ipady=2)
    game.username_entry.focus_set()
    # 狀態訊息
    game.login_status_label = ttk.Label(game.top_left_frame, text="", font=("Microsoft JhengHei", 10), foreground="#b36b00")
    game.login_status_label.pack(anchor='w', pady=2)
    # 新增：重生次數顯示
    game.reborn_label = ttk.Label(game.top_left_frame, text="", font=("Microsoft JhengHei", 10), foreground="#8888ff")
    game.reborn_label.pack(anchor='w', pady=2)
    game.username_entry.bind('<Return>', do_login)
    # --- 銀行分頁 ---
    bank_tab = ttk.Frame(tab_control)
    tab_control.add(bank_tab, text="🏦 銀行")
    # 銀行操作區塊
    op_frame = ttk.LabelFrame(bank_tab, text="銀行操作", padding="10")
    op_frame.pack(fill=tk.X, pady=10, padx=10)
    row1 = ttk.Frame(op_frame)
    row1.pack(fill=tk.X, pady=5)
    ttk.Label(row1, text="金額:", font=FONT).pack(side=tk.LEFT, padx=5)
    game.amount_entry = ttk.Entry(row1, width=10, font=FONT)
    game.amount_entry.pack(side=tk.LEFT, padx=5)
    row2 = ttk.Frame(op_frame)
    row2.pack(fill=tk.X, pady=5)
    ttk.Button(row2, text="存款", command=lambda: game.deposit(), width=12).pack(side=tk.LEFT, padx=8, pady=3)
    ttk.Button(row2, text="提款", command=lambda: game.withdraw(), width=12).pack(side=tk.LEFT, padx=8, pady=3)
    ttk.Button(row2, text="貸款", command=lambda: game.take_loan(), width=12).pack(side=tk.LEFT, padx=8, pady=3)
    ttk.Button(row2, text="還款", command=lambda: game.repay_loan(), width=12).pack(side=tk.LEFT, padx=8, pady=3)
    # 帳戶資訊
    info_frame = ttk.LabelFrame(bank_tab, text="帳戶資訊", padding="10")
    info_frame.pack(fill=tk.X, pady=10, padx=10)
    game.balance_label = ttk.Label(info_frame, font=FONT)
    game.balance_label.grid(row=0, column=0, padx=5, pady=2)
    # 刪除 info_frame 內的現金顯示
    # game.cash_label = ttk.Label(info_frame, font=FONT)
    # game.cash_label.grid(row=0, column=1, padx=5, pady=2)
    game.loan_label = ttk.Label(info_frame, font=FONT)
    game.loan_label.grid(row=1, column=0, padx=5, pady=2)
    game.asset_label = ttk.Label(info_frame, font=FONT)
    game.asset_label.grid(row=1, column=1, padx=5, pady=2)
    game.deposit_rate_label = ttk.Label(info_frame, font=FONT)
    game.deposit_rate_label.grid(row=2, column=0, padx=5, pady=2)
    game.loan_rate_label = ttk.Label(info_frame, font=FONT)
    game.loan_rate_label.grid(row=2, column=1, padx=5, pady=2)
    # 交易歷史
    history_frame = ttk.LabelFrame(bank_tab, text="交易歷史", padding="10")
    history_frame.pack(fill=tk.X, pady=10, padx=10)
    game.history_text = tk.Text(history_frame, height=8, width=60, font=FONT, state='disabled')
    game.history_text.pack(fill=tk.BOTH)
    # --- 股票圖表分頁（多圖表+買賣操作） ---
    chart_tab = ttk.Frame(tab_control)
    tab_control.add(chart_tab, text="📈 股票")
    # 新增：產業分頁，虛擬貨幣分頁不再顯示在這裡
    from industry_manager import IndustryManager
    
    industries = list({stock['industry'] for stock in game.data.stocks.values() if stock['industry'] != '虛擬貨幣'})
    industry_tabs = ttk.Notebook(chart_tab)
    industry_tabs.pack(fill=tk.BOTH, expand=True)
    game.industry_tabs = industry_tabs
    game.industry_tab_frames = {}
    
    # 建立產業管理器
    game.industry_manager = IndustryManager(game)
    
    # 為每個產業建立分頁
    for industry in industries:
        game.industry_manager.create_industry_tab(industry_tabs, industry)
    
    # 設定更新函數
    original_update_display = game.update_display
    
    def update_all_displays():
        game.industry_manager.update_stock_status_labels()
        if original_update_display:
            original_update_display()
    
    game.update_stock_status_labels = game.industry_manager.update_stock_status_labels
    game.update_display = update_all_displays


    # --- 比特幣獨立分頁 ---
    game.crypto_manager = CryptoManager(game)
    game.crypto_manager.create_crypto_tab(tab_control)
    # --- 拉霸機分頁（只保留一台） ---
    slot_tab = ttk.Frame(tab_control)
    tab_control.add(slot_tab, text="🎰 拉霸機")
    game.slot_machines = []
    sub = ttk.LabelFrame(slot_tab, text=f"拉霸機台 1", padding="10")
    sub.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    sm = game.slot_machine.create_ui(sub)
    game.slot_machines.append(sm)
    # --- 21點（Blackjack）入口 ---
    def open_blackjack():
        # 這裡之後會呼叫 blackjack 遊戲視窗
        import tkinter.messagebox as messagebox
        messagebox.showinfo("21點（Blackjack）", "21點遊戲開發中...")
    ttk.Button(slot_tab, text="玩 21點（Blackjack）", command=open_blackjack).pack(side=tk.LEFT, padx=20, pady=20)
    # --- 成就分頁 ---
    ach_tab = ttk.Frame(tab_control)
    tab_control.add(ach_tab, text="🏅 成就")
    game.ach_listbox = tk.Listbox(ach_tab, font=FONT, width=60, height=15)
    game.ach_listbox.pack(padx=20, pady=20)
    # --- 排行榜分頁 ---
    rank_tab = ttk.Frame(tab_control)
    tab_control.add(rank_tab, text="🏆 排行榜")
    game.rank_text = tk.Text(rank_tab, height=15, width=60, state='disabled', font=FONT)
    game.rank_text.pack(padx=10, pady=10)
    ttk.Button(rank_tab, text="刷新排行榜", command=game.show_leaderboard).pack(pady=5)
    # --- 事件分頁 ---
    event_tab = ttk.Frame(tab_control)
    tab_control.add(event_tab, text="📋 事件表")
    event_text = tk.Text(event_tab, height=30, width=90, font=FONT, state='normal', wrap='word')
    event_text.pack(padx=20, pady=20)
    # 取得所有事件
    try:
        from events import EventManager
        tmp_game = type('Tmp', (), {})()
        tmp_game.data = game.data
        event_manager = EventManager(tmp_game)
        event_list = [(e.name, e.description, getattr(e, 'effect_desc', '')) for e in event_manager.events]
        for name, desc, effect in event_list:
            event_text.insert('end', f"{name}：{desc}｜影響：{effect}\n")
    except Exception as e:
        event_text.insert('end', f"載入事件表失敗：{e}\n")
    event_text.config(state='disabled')
    # --- 主題分頁 ---
    theme_tab = ttk.Frame(tab_control)
    tab_control.add(theme_tab, text="🌙 主題")
    ttk.Button(theme_tab, text="切換主題", command=game.theme.toggle_theme).pack(pady=10)
    # --- 退出遊戲按鈕 ---
    exit_btn = ttk.Button(root, text="退出遊戲", command=game.on_close)
    exit_btn.place(relx=1, y=0, anchor='ne')
    disable_all_tabs()
    return tab_control