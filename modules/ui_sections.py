import tkinter as tk
from modules.tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import json
from modules.crypto_manager import CryptoManager

FONT = ("Microsoft JhengHei", 12)
HEADER_FONT = ("Microsoft JhengHei", 18, "bold")

# 集中存檔資料夾（保留舊檔相容）
SAVE_DIR = os.path.join('.', 'saves')
os.makedirs(SAVE_DIR, exist_ok=True)

# 標題區域
def create_header_section(root, game):
    frame = ttk.Frame(root)
    frame.pack(fill=tk.X, pady=5)
    
    # 頂部區域：登入、標題、時間
    top_frame = ttk.Frame(frame)
    top_frame.pack(fill=tk.X, pady=(0, 5))
    
    # 左：登入區塊
    left = ttk.Frame(top_frame)
    left.pack(side=tk.LEFT, anchor='w', padx=10)
    
    # 中：標題
    center = ttk.Frame(top_frame)
    center.pack(side=tk.LEFT, expand=True)
    
    # 右：時間與遊戲日數
    right = ttk.Frame(top_frame)
    right.pack(side=tk.RIGHT, anchor='e', padx=10)
    
    # 右上角添加調試按鈕（僅開發者模式）
    debug_frame = ttk.Frame(right)
    debug_frame.pack(side=tk.TOP, anchor='e', pady=(0, 5))
    ttk.Button(debug_frame, text="🐛 調試", command=lambda: game.debug_panel.show()).pack(side=tk.RIGHT)
    
    # 左：登入區塊
    game.top_left_frame = left
    
    # 中：標題
    ttk.Label(center, text="銀行系統", style='Header.TLabel').pack(anchor='center')
    
    # 右：時間與遊戲日數
    game.time_label = ttk.Label(right, font=FONT)
    game.time_label.pack(anchor='e')
    game.game_day_label = ttk.Label(right, font=FONT)
    game.game_day_label.pack(anchor='e')
    
    # 底部區域：狀態效果和物品欄
    bottom_frame = ttk.Frame(frame, style='Status.TFrame')
    bottom_frame.pack(fill=tk.X, pady=(5, 0), padx=5, ipady=5)
    
    # 狀態效果標籤
    game.buffs_label = ttk.Label(
        bottom_frame, 
        text="當前沒有活躍效果",
        font=('Microsoft JhengHei', 9),
        foreground='#2e7d32',  # 深綠色
        wraplength=400,
        justify='left'
    )
    game.buffs_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 分隔線
    ttk.Separator(bottom_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=5)
    
    # 物品欄標籤
    game.consumables_label = ttk.Label(
        bottom_frame, 
        text="物品欄: 空",
        font=('Microsoft JhengHei', 9),
        foreground='#1565c0',  # 深藍色
        wraplength=300,
        justify='left'
    )
    game.consumables_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 添加樣式
    style = ttk.Style()
    style.configure('Status.TFrame', background='#f5f5f5')
    
    return frame

# 主體分頁（每個分頁一個大功能）
def create_main_tabs(root, game):
    # 先定義 function
    def disable_all_tabs():
        for i in range(tab_control.index('end')):
            tab_control.tab(i, state='disabled')
    def get_all_usernames():
        # 同時掃描根目錄與 SAVE_DIR，並去重
        names = set()
        try:
            for f in os.listdir('.'):
                if f.startswith('save_') and f.endswith('.json'):
                    names.add(f[5:-5])
        except Exception:
            pass
        try:
            for f in os.listdir(SAVE_DIR):
                if f.startswith('save_') and f.endswith('.json'):
                    names.add(f[5:-5])
        except Exception:
            pass
        return sorted(names)
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
            # 統一路徑：saves/save_username.json
            savefile = os.path.join(SAVE_DIR, f"save_{username}.json")
            old_path = os.path.abspath(f"save_{username}.json")
            new_path = os.path.abspath(savefile)
            if os.path.exists(new_path):
                game.data.load(new_path, show_error=lambda msg: tk.messagebox.showerror("讀檔錯誤", msg))
            elif os.path.exists(old_path):
                # 從舊位置遷移到新資料夾
                try:
                    os.replace(old_path, new_path)
                except Exception:
                    # 若無法搬移，至少先讀舊檔，稍後存檔會寫入新路徑
                    pass
                try:
                    game.data.load(new_path if os.path.exists(new_path) else old_path, show_error=lambda msg: tk.messagebox.showerror("讀檔錯誤", msg))
                except Exception:
                    game.data.reset()
            else:
                game.data.reset()  # 新帳號重設現金 1000
                game.data.save(new_path)  # 立刻存檔，避免自動儲存寫回舊資料
            game.savefile = new_path
            # 新增：初始化預設固定支出與商店 UI
            try:
                if hasattr(game, 'ensure_default_expenses'):
                    game.ensure_default_expenses()
                if hasattr(game, 'update_store_ui'):
                    game.update_store_ui()
            except Exception:
                pass
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
                # 優先刪除新路徑，其次舊路徑
                savefile_new = os.path.abspath(os.path.join(SAVE_DIR, f"save_{username}.json"))
                savefile_old = os.path.abspath(f"save_{username}.json")
                removed = False
                if os.path.exists(savefile_new):
                    os.remove(savefile_new)
                    removed = True
                elif os.path.exists(savefile_old):
                    os.remove(savefile_old)
                    removed = True
                if not removed:
                    game.debug_log(f"找不到檔案: {savefile_new} 或 {savefile_old}")  # 除錯用
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
    game.cash_label = ttk.Label(cash_frame, style='Cash.TLabel')
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
    # --- 生活分頁（工作/之後可擴充支出/基金） ---
    life_tab = ttk.Frame(tab_control)
    tab_control.add(life_tab, text="👤 生活")
    # 工作區塊
    job_frame = ttk.LabelFrame(life_tab, text="工作", padding="10")
    job_frame.pack(fill=tk.X, pady=10, padx=10)
    # 顯示目前工作資訊
    info_row = ttk.Frame(job_frame)
    info_row.pack(fill=tk.X, pady=5)
    job_name_lbl = ttk.Label(info_row, text="職稱：未就業", font=FONT)
    job_name_lbl.grid(row=0, column=0, padx=6, pady=2, sticky='w')
    job_level_lbl = ttk.Label(info_row, text="等級：-", font=FONT)
    job_level_lbl.grid(row=0, column=1, padx=6, pady=2, sticky='w')
    job_salary_lbl = ttk.Label(info_row, text="日薪：$0.00", font=FONT)
    job_salary_lbl.grid(row=1, column=0, padx=6, pady=2, sticky='w')
    job_tax_lbl = ttk.Label(info_row, text="稅率：0.0%", font=FONT)
    job_tax_lbl.grid(row=1, column=1, padx=6, pady=2, sticky='w')
    job_next_lbl = ttk.Label(info_row, text="下次升職日：-", font=FONT)
    job_next_lbl.grid(row=2, column=0, padx=6, pady=2, sticky='w')
    # 額外顯示：公司與學歷
    job_company_lbl = ttk.Label(info_row, text="公司：-", font=FONT)
    job_company_lbl.grid(row=2, column=1, padx=6, pady=2, sticky='w')
    job_edu_lbl = ttk.Label(info_row, text="學歷：-", font=FONT)
    job_edu_lbl.grid(row=3, column=0, padx=6, pady=2, sticky='w')
    # 綁定到 game 以便更新
    game.job_labels = {
        'name': job_name_lbl,
        'level': job_level_lbl,
        'salary': job_salary_lbl,
        'tax': job_tax_lbl,
        'next': job_next_lbl,
        'company': job_company_lbl,
        'education': job_edu_lbl,
    }
    # 選擇工作
    select_row = ttk.Frame(job_frame)
    select_row.pack(fill=tk.X, pady=5)
    ttk.Label(select_row, text="選擇職業：", font=FONT).pack(side=tk.LEFT, padx=6)
    job_names = list(getattr(game.data, 'jobs_catalog', {}).keys())
    game.job_select_var = tk.StringVar(value=(job_names[0] if job_names else ""))
    job_combo = ttk.Combobox(select_row, textvariable=game.job_select_var, values=job_names, font=FONT, state='readonly', width=20, height=8)
    job_combo.pack(side=tk.LEFT, padx=6, ipady=3)
    # 設定下拉選單樣式
    style = ttk.Style()
    style.configure('TCombobox', font=FONT, background='#ffffff', foreground='#000000')
    style.map('TCombobox', fieldbackground=[('readonly', '#ffffff')])
    ttk.Button(select_row, text="就職", command=game.ui_select_job, width=12).pack(side=tk.LEFT, padx=6)
    ttk.Button(select_row, text="申請升職", command=game.promote_job, width=12).pack(side=tk.LEFT, padx=6)
    # 公司選擇與進修
    company_row = ttk.Frame(job_frame)
    company_row.pack(fill=tk.X, pady=5)
    ttk.Label(company_row, text="選擇公司：", font=FONT).pack(side=tk.LEFT, padx=6)
    comp_names = list(getattr(game.data, 'companies_catalog', {}).keys())
    game.company_select_var = tk.StringVar(value=(comp_names[0] if comp_names else ""))
    ttk.Combobox(company_row, textvariable=game.company_select_var, values=comp_names, font=FONT, state='readonly', width=16).pack(side=tk.LEFT, padx=6)
    ttk.Button(company_row, text="加入公司", command=lambda: game.select_company(game.company_select_var.get()), width=10).pack(side=tk.LEFT, padx=6)
    ttk.Button(company_row, text="進修升學", command=game.study_upgrade, width=10).pack(side=tk.LEFT, padx=12)
    # 行為/活動區塊
    act_frame = ttk.LabelFrame(life_tab, text="行為 / 活動（消耗體力/金錢，提升屬性）", padding="10")
    act_frame.pack(fill=tk.X, pady=6, padx=10)
    row_act1 = ttk.Frame(act_frame)
    row_act1.pack(fill=tk.X, pady=4)
    # 將活動按鈕保存到 game，方便動態更新（冷卻/CD 與剩餘次數顯示）
    game.btn_study = ttk.Button(row_act1, text="讀書（$50、-10體力）", width=20, command=lambda: game.do_study_action())
    game.btn_study.pack(side=tk.LEFT, padx=6)
    game.btn_workout = ttk.Button(row_act1, text="健身（$30、-15體力）", width=20, command=lambda: game.do_workout_action())
    game.btn_workout.pack(side=tk.LEFT, padx=6)
    row_act2 = ttk.Frame(act_frame)
    row_act2.pack(fill=tk.X, pady=4)
    game.btn_social = ttk.Button(row_act2, text="社交（$40、-10體力）", width=20, command=lambda: game.do_social_action())
    game.btn_social.pack(side=tk.LEFT, padx=6)
    game.btn_meditate = ttk.Button(row_act2, text="冥想（免費、-8體力）", width=20, command=lambda: game.do_meditate_action())
    game.btn_meditate.pack(side=tk.LEFT, padx=6)
    # 支出區塊
    expense_frame = ttk.LabelFrame(life_tab, text="支出", padding="10")
    expense_frame.pack(fill=tk.BOTH, pady=10, padx=10)
    input_row = ttk.Frame(expense_frame)
    input_row.pack(fill=tk.X, pady=5)
    ttk.Label(input_row, text="名稱：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.expense_name_var = tk.StringVar()
    name_entry = ttk.Entry(input_row, textvariable=game.expense_name_var, width=12, font=FONT)
    name_entry.pack(side=tk.LEFT)
    ttk.Label(input_row, text="金額：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.expense_amount_var = tk.StringVar()
    amount_entry = ttk.Entry(input_row, textvariable=game.expense_amount_var, width=10, font=FONT)
    amount_entry.pack(side=tk.LEFT)
    ttk.Label(input_row, text="頻率：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.expense_freq_var = tk.StringVar(value='daily')
    freq_combo = ttk.Combobox(input_row, textvariable=game.expense_freq_var, values=['daily','weekly','monthly'], state='readonly', width=10, font=FONT)
    freq_combo.pack(side=tk.LEFT)
    ttk.Button(input_row, text="新增支出", command=game.add_expense_from_ui, width=12).pack(side=tk.LEFT, padx=8)
    # 支出列表
    list_row = ttk.Frame(expense_frame)
    list_row.pack(fill=tk.BOTH, expand=True, pady=5)
    game.expense_listbox = tk.Listbox(list_row, height=6, font=FONT)
    game.expense_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb = ttk.Scrollbar(list_row, orient=tk.VERTICAL, command=game.expense_listbox.yview)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    game.expense_listbox.config(yscrollcommand=sb.set)
    btn_row = ttk.Frame(expense_frame)
    btn_row.pack(fill=tk.X, pady=5)
    ttk.Button(btn_row, text="刪除選取支出", command=game.delete_expense_from_ui, width=16).pack(side=tk.LEFT, padx=6)
    ttk.Button(btn_row, text="取消訂閱", command=game.cancel_subscription_from_ui, width=12).pack(side=tk.LEFT, padx=6)
    # 支出總覽
    game.expense_summary_label = ttk.Label(expense_frame, text="預估支出：每日 $0.00｜每週 $0.00｜每月 $0.00", font=FONT, foreground="#888")
    game.expense_summary_label.pack(fill=tk.X, padx=6)
    # --- 屬性分頁 ---
    attr_tab = ttk.Frame(tab_control)
    tab_control.add(attr_tab, text="🧠 屬性")
    attr_frame = ttk.LabelFrame(attr_tab, text="個人屬性", padding="10")
    attr_frame.pack(fill=tk.X, pady=10, padx=10)
    # 兩欄顯示
    col_left = ttk.Frame(attr_frame)
    col_right = ttk.Frame(attr_frame)
    col_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
    col_right.pack(side=tk.LEFT, fill=tk.X, expand=True)
    # 建立並綁定屬性標籤
    def _mk_attr_row(parent, label_text):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text + "：", font=FONT).pack(side=tk.LEFT, padx=6)
        val_lbl = ttk.Label(row, text="-", font=FONT)
        val_lbl.pack(side=tk.LEFT)
        return val_lbl
    game.attr_labels = {}
    game.attr_labels['happiness'] = _mk_attr_row(col_left, '快樂')
    game.attr_labels['stamina'] = _mk_attr_row(col_left, '體力')
    game.attr_labels['intelligence'] = _mk_attr_row(col_left, '智力')
    game.attr_labels['diligence'] = _mk_attr_row(col_right, '勤奮')
    game.attr_labels['charisma'] = _mk_attr_row(col_right, '魅力')
    game.attr_labels['experience'] = _mk_attr_row(col_right, '經驗')
    game.attr_labels['luck_today'] = _mk_attr_row(attr_frame, '今日運氣')
    # --- 股票圖表分頁（多圖表+買賣操作） ---
    chart_tab = ttk.Frame(tab_control)
    tab_control.add(chart_tab, text="📈 股票")
    # 新增：產業分頁，虛擬貨幣分頁不再顯示在這裡
    from modules.industry_manager import IndustryManager
    
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
    # --- 基金/ETF 分頁 ---
    funds_tab = ttk.Frame(tab_control)
    tab_control.add(funds_tab, text="📊 基金/ETF")
    funds_frame = ttk.LabelFrame(funds_tab, text="基金/ETF", padding="10")
    funds_frame.pack(fill=tk.X, pady=10, padx=10)
    # 選擇基金
    row_sel = ttk.Frame(funds_frame)
    row_sel.pack(fill=tk.X, pady=4)
    ttk.Label(row_sel, text="選擇基金：", font=FONT).pack(side=tk.LEFT, padx=6)
    fund_names = list(getattr(game.data, 'funds_catalog', {}).keys())
    game.fund_select_var = tk.StringVar(value=(fund_names[0] if fund_names else ""))
    fund_combo = ttk.Combobox(row_sel, textvariable=game.fund_select_var, values=fund_names, font=FONT, state='readonly', width=18)
    fund_combo.pack(side=tk.LEFT, padx=6)
    # NAV 與持倉資訊
    row_info = ttk.Frame(funds_frame)
    row_info.pack(fill=tk.X, pady=4)
    game.fund_nav_label = ttk.Label(row_info, text="NAV：-", font=FONT)
    game.fund_nav_label.grid(row=0, column=0, padx=6, pady=2, sticky='w')
    game.fund_hold_label = ttk.Label(row_info, text="持有單位：0.0000", font=FONT)
    game.fund_hold_label.grid(row=0, column=1, padx=6, pady=2, sticky='w')
    game.fund_avg_label = ttk.Label(row_info, text="平均成本：$0.0000", font=FONT)
    game.fund_avg_label.grid(row=0, column=2, padx=6, pady=2, sticky='w')
    # 輸入與買賣
    row_trade = ttk.Frame(funds_frame)
    row_trade.pack(fill=tk.X, pady=6)
    ttk.Label(row_trade, text="單位數：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.fund_units_var = tk.StringVar()
    game.fund_units_entry = ttk.Entry(row_trade, textvariable=game.fund_units_var, width=12, font=FONT)
    game.fund_units_entry.pack(side=tk.LEFT, padx=4)
    ttk.Button(row_trade, text="買入", command=game.buy_fund_from_ui, width=10).pack(side=tk.LEFT, padx=6)
    ttk.Button(row_trade, text="賣出", command=game.sell_fund_from_ui, width=10).pack(side=tk.LEFT, padx=6)
    # 綁定變更時更新顯示
    def on_fund_selected(event=None):
        try:
            game.compute_fund_navs()
            game.update_funds_ui()
        except Exception:
            pass
    fund_combo.bind('<<ComboboxSelected>>', on_fund_selected)
    # 初始刷新
    on_fund_selected()
    # --- 定投/創業 分頁 ---
    auto_tab = ttk.Frame(tab_control)
    tab_control.add(auto_tab, text="🤖 定投/創業")
    # 定投區域
    dca_frame = ttk.LabelFrame(auto_tab, text="定投設定", padding="10")
    dca_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
    # 股票定投輸入
    row_stock = ttk.Frame(dca_frame)
    row_stock.pack(fill=tk.X, pady=4)
    ttk.Label(row_stock, text="股票代碼：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.dca_stock_code_var = tk.StringVar()
    ttk.Entry(row_stock, textvariable=game.dca_stock_code_var, width=12, font=FONT).pack(side=tk.LEFT)
    ttk.Label(row_stock, text="金額：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.dca_stock_amount_var = tk.StringVar()
    ttk.Entry(row_stock, textvariable=game.dca_stock_amount_var, width=10, font=FONT).pack(side=tk.LEFT)
    ttk.Label(row_stock, text="頻率：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.dca_stock_freq_var = tk.StringVar(value='monthly')
    ttk.Combobox(row_stock, textvariable=game.dca_stock_freq_var, values=['daily','weekly','monthly'], state='readonly', width=10, font=FONT).pack(side=tk.LEFT)
    ttk.Button(row_stock, text="新增/更新股票定投", command=game.ui_add_or_update_dca_stock).pack(side=tk.LEFT, padx=8)
    # 股票定投清單
    row_stock_list = ttk.Frame(dca_frame)
    row_stock_list.pack(fill=tk.BOTH, expand=True, pady=4)
    game.dca_stock_list = tk.Listbox(row_stock_list, height=5, font=FONT)
    game.dca_stock_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb_stock = ttk.Scrollbar(row_stock_list, orient=tk.VERTICAL, command=game.dca_stock_list.yview)
    sb_stock.pack(side=tk.RIGHT, fill=tk.Y)
    game.dca_stock_list.config(yscrollcommand=sb_stock.set)
    ttk.Button(dca_frame, text="刪除選取股票定投", command=game.ui_remove_dca_stock).pack(anchor='w', padx=6, pady=4)
    # 基金定投輸入
    row_fund = ttk.Frame(dca_frame)
    row_fund.pack(fill=tk.X, pady=6)
    ttk.Label(row_fund, text="基金名稱：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.dca_fund_name_var = tk.StringVar()
    ttk.Entry(row_fund, textvariable=game.dca_fund_name_var, width=16, font=FONT).pack(side=tk.LEFT)
    ttk.Label(row_fund, text="金額：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.dca_fund_amount_var = tk.StringVar()
    ttk.Entry(row_fund, textvariable=game.dca_fund_amount_var, width=10, font=FONT).pack(side=tk.LEFT)
    ttk.Label(row_fund, text="頻率：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.dca_fund_freq_var = tk.StringVar(value='monthly')
    ttk.Combobox(row_fund, textvariable=game.dca_fund_freq_var, values=['daily','weekly','monthly'], state='readonly', width=10, font=FONT).pack(side=tk.LEFT)
    ttk.Button(row_fund, text="新增/更新基金定投", command=game.ui_add_or_update_dca_fund).pack(side=tk.LEFT, padx=8)
    # 基金定投清單
    row_fund_list = ttk.Frame(dca_frame)
    row_fund_list.pack(fill=tk.BOTH, expand=True, pady=4)
    game.dca_fund_list = tk.Listbox(row_fund_list, height=5, font=FONT)
    game.dca_fund_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb_fund = ttk.Scrollbar(row_fund_list, orient=tk.VERTICAL, command=game.dca_fund_list.yview)
    sb_fund.pack(side=tk.RIGHT, fill=tk.Y)
    game.dca_fund_list.config(yscrollcommand=sb_fund.set)
    ttk.Button(dca_frame, text="刪除選取基金定投", command=game.ui_remove_dca_fund).pack(anchor='w', padx=6, pady=4)
    # DRIP 區域
    drip_frame = ttk.LabelFrame(auto_tab, text="股息再投資（DRIP）", padding="10")
    drip_frame.pack(fill=tk.X, padx=10, pady=8)
    row_drip = ttk.Frame(drip_frame)
    row_drip.pack(fill=tk.X)
    ttk.Label(row_drip, text="股票代碼：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.drip_stock_code_var = tk.StringVar()
    ttk.Entry(row_drip, textvariable=game.drip_stock_code_var, width=12, font=FONT).pack(side=tk.LEFT)
    game.drip_enable_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(row_drip, text="開啟 DRIP", variable=game.drip_enable_var, command=game.ui_toggle_drip).pack(side=tk.LEFT, padx=10)
    # 創業區域
    biz_frame = ttk.LabelFrame(auto_tab, text="創業管理", padding="10")
    biz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
    row_biz = ttk.Frame(biz_frame)
    row_biz.pack(fill=tk.X, pady=4)
    ttk.Label(row_biz, text="名稱：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.biz_name_var = tk.StringVar()
    ttk.Entry(row_biz, textvariable=game.biz_name_var, width=12, font=FONT).pack(side=tk.LEFT)
    ttk.Label(row_biz, text="收入/日：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.biz_rev_var = tk.StringVar()
    ttk.Entry(row_biz, textvariable=game.biz_rev_var, width=10, font=FONT).pack(side=tk.LEFT)
    ttk.Label(row_biz, text="成本/日：", font=FONT).pack(side=tk.LEFT, padx=6)
    game.biz_cost_var = tk.StringVar()
    ttk.Entry(row_biz, textvariable=game.biz_cost_var, width=10, font=FONT).pack(side=tk.LEFT)
    ttk.Button(row_biz, text="新增事業", command=game.ui_add_business).pack(side=tk.LEFT, padx=8)
    # 事業清單
    row_biz_list = ttk.Frame(biz_frame)
    row_biz_list.pack(fill=tk.BOTH, expand=True, pady=4)
    game.business_list = tk.Listbox(row_biz_list, height=6, font=FONT)
    game.business_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb_biz = ttk.Scrollbar(row_biz_list, orient=tk.VERTICAL, command=game.business_list.yview)
    sb_biz.pack(side=tk.RIGHT, fill=tk.Y)
    game.business_list.config(yscrollcommand=sb_biz.set)
    ttk.Button(biz_frame, text="刪除選取事業", command=game.ui_remove_business).pack(anchor='w', padx=6, pady=4)
    # 招募員工按鈕
    ttk.Button(biz_frame, text="招募員工（$50）", command=game.ui_recruit_employee).pack(anchor='w', padx=6, pady=4)
    # 初始刷新定投/創業清單
    try:
        if hasattr(game, 'update_auto_invest_ui'):
            game.update_auto_invest_ui()
    except Exception:
        pass
    # --- 報表分頁 ---
    report_tab = ttk.Frame(tab_control)
    tab_control.add(report_tab, text="📑 報表")
    # 上方：摘要區
    report_summary = ttk.LabelFrame(report_tab, text="摘要", padding="10")
    report_summary.pack(fill=tk.X, pady=10, padx=10)
    game.report_income_summary_label = ttk.Label(report_summary, text="收入：今日 $0.00｜近7天 $0.00｜近30天 $0.00", font=FONT)
    game.report_income_summary_label.grid(row=0, column=0, padx=6, pady=2, sticky='w')
    game.report_expense_summary_label = ttk.Label(report_summary, text="支出：今日 $0.00｜近7天 $0.00｜近30天 $0.00", font=FONT)
    game.report_expense_summary_label.grid(row=1, column=0, padx=6, pady=2, sticky='w')
    game.report_net_summary_label = ttk.Label(report_summary, text="淨額：今日 $0.00｜近7天 $0.00｜近30天 $0.00", font=FONT)
    game.report_net_summary_label.grid(row=2, column=0, padx=6, pady=2, sticky='w')
    # 下方：趨勢圖
    report_chart_frame = ttk.LabelFrame(report_tab, text="收入/支出趨勢（每日）", padding="10")
    report_chart_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
    game.report_fig, game.report_ax = plt.subplots(figsize=(6, 3))
    game.report_canvas = FigureCanvasTkAgg(game.report_fig, master=report_chart_frame)
    game.report_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    # 初始化圖表樣式
    try:
        ax = game.report_ax
        ax.set_title("收入 vs 支出（每日）")
        ax.set_xlabel("天數")
        ax.set_ylabel("金額")
        ax.grid(True, linestyle='--', alpha=0.3)
        game.report_fig.tight_layout()
    except Exception:
        pass
    # 初始刷新一次
    try:
        if hasattr(game, 'update_report_ui'):
            game.update_report_ui()
    except Exception:
        pass
    # --- 商店分頁 ---
    store_tab = ttk.Frame(tab_control)
    tab_control.add(store_tab, text="🛒 商店")
    # 訂閱與商品區塊
    store_frame = ttk.LabelFrame(store_tab, text="商店", padding="10")
    store_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
    # 左：訂閱列表
    left_col = ttk.Frame(store_frame)
    left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
    ttk.Label(left_col, text="訂閱服務", font=FONT).pack(anchor='w')
    game.store_subs_list = tk.Listbox(left_col, height=8, font=FONT)
    game.store_subs_list.pack(fill=tk.BOTH, expand=True)
    ttk.Button(left_col, text="訂閱選取服務", command=game.subscribe_selected_from_ui).pack(pady=6)
    # 中：商品列表
    mid_col = ttk.Frame(store_frame)
    mid_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
    ttk.Label(mid_col, text="商品", font=FONT).pack(anchor='w')
    game.store_goods_list = tk.Listbox(mid_col, height=8, font=FONT)
    game.store_goods_list.pack(fill=tk.BOTH, expand=True)
    ttk.Button(mid_col, text="購買選取商品", command=game.buy_selected_good_from_ui).pack(pady=6)
    # 右：物品欄
    right_col = ttk.Frame(store_frame)
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
    ttk.Label(right_col, text="物品欄", font=FONT).pack(anchor='w')
    game.inventory_list = tk.Listbox(right_col, height=8, font=FONT)
    game.inventory_list.pack(fill=tk.BOTH, expand=True)
    # 初始刷新商店
    try:
        game.update_store_ui()
    except Exception:
        pass
    # --- 賭場分頁（整合各種玩法） ---
    casino_tab = ttk.Frame(tab_control)
    tab_control.add(casino_tab, text="🎰 賭場")
    casino_wrap = ttk.Frame(casino_tab)
    casino_wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    info_frame = ttk.LabelFrame(casino_wrap, text="玩家資訊", padding="10")
    info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

    ttk.Label(info_frame, text="狀態：", font=FONT).pack(anchor='w')
    status_label = ttk.Label(info_frame, textvariable=game.casino_status_var, font=("Microsoft JhengHei", 11), wraplength=260)
    status_label.pack(anchor='w', pady=(0, 8))

    ttk.Label(info_frame, text="VIP 與紅利", font=FONT).pack(anchor='w')
    game.casino_vip_label = ttk.Label(info_frame, text="請登入以查看 VIP 狀態", font=("Microsoft JhengHei", 10), wraplength=260)
    game.casino_vip_label.pack(anchor='w', pady=(0, 8))

    ttk.Label(info_frame, text="賭場統計", font=FONT).pack(anchor='w')
    game.casino_stats_label = ttk.Label(info_frame, text="尚無紀錄", font=("Microsoft JhengHei", 10), wraplength=260)
    game.casino_stats_label.pack(anchor='w', pady=(0, 8))

    jackpot_frame = ttk.LabelFrame(info_frame, text="累積獎池", padding="6")
    jackpot_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
    columns = ("name", "amount", "min_bet")
    tree = ttk.Treeview(jackpot_frame, columns=columns, show='headings', height=5)
    tree.heading('name', text='獎池')
    tree.heading('amount', text='當前金額')
    tree.heading('min_bet', text='最低下注')
    tree.column('name', width=110, anchor='center')
    tree.column('amount', width=110, anchor='e')
    tree.column('min_bet', width=100, anchor='e')
    tree.pack(fill=tk.BOTH, expand=True)
    game.casino_jackpot_tree = tree
    ttk.Button(jackpot_frame, text="刷新獎池資訊", command=game.update_casino_ui).pack(pady=4)

    log_frame = ttk.LabelFrame(info_frame, text="賭局紀錄", padding="6")
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_text = tk.Text(log_frame, height=10, state='disabled', font=("Microsoft JhengHei", 10))
    log_text.pack(fill=tk.BOTH, expand=True)
    game.casino_log_widget = log_text

    games_frame = ttk.LabelFrame(casino_wrap, text="賭場遊戲", padding="10")
    games_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    slot_frame = ttk.LabelFrame(games_frame, text="拉霸機", padding="10")
    slot_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    game.slot_machines = []
    slot_ui = game.slot_machine.create_ui(slot_frame)
    game.slot_machines.append(slot_ui)

    button_frame = ttk.Frame(games_frame)
    button_frame.pack(fill=tk.X, pady=4)
    ttk.Button(button_frame, text="啟動 21點 (Blackjack)", command=game.open_blackjack_window).pack(fill=tk.X, pady=3)
    ttk.Button(button_frame, text="輪盤下注 (Roulette)", command=game.play_roulette_prompt).pack(fill=tk.X, pady=3)
    ttk.Button(button_frame, text="百家樂下注 (Baccarat)", command=game.play_baccarat_prompt).pack(fill=tk.X, pady=3)
    ttk.Button(button_frame, text="骰子遊戲 (Dice)", command=game.play_dice_prompt).pack(fill=tk.X, pady=3)
    ttk.Button(button_frame, text="刷新玩家資訊", command=game.update_casino_ui).pack(fill=tk.X, pady=(8, 0))

    try:
        game.update_casino_ui()
    except Exception:
        pass
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
        from modules.events import EventManager
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