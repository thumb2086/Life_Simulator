import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import time
import psutil
import os
import threading
import gc

class DebugPanel:
    """調試面板，提供遊戲狀態檢查與開發者工具"""
    
    def __init__(self, game):
        self.game = game
        self.window = None
        self.performance_monitoring = False
        self.performance_data = []
        
    def show(self):
        """顯示調試面板"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.game.root)
        self.window.title("調試面板 - 開發者工具")
        self.window.geometry("1200x800")
        
        # 建立分頁
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 遊戲狀態分頁
        state_frame = ttk.Frame(notebook)
        notebook.add(state_frame, text="遊戲狀態")
        self._create_game_state_tab(state_frame)
        
        # 性能監控分頁
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="性能監控")
        self._create_performance_tab(perf_frame)
        
        # 變數操作分頁
        var_frame = ttk.Frame(notebook)
        notebook.add(var_frame, text="變數操作")
        self._create_variable_tab(var_frame)
        
        # 事件日誌分頁
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="事件日誌")
        self._create_log_tab(log_frame)
        
        # 測試工具分頁
        test_frame = ttk.Frame(notebook)
        notebook.add(test_frame, text="測試工具")
        self._create_test_tab(test_frame)
        
    def _create_game_state_tab(self, parent):
        """建立遊戲狀態檢查分頁"""
        # 左側：狀態樹狀圖
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_frame, text="遊戲狀態檢查", font=("Microsoft JhengHei", 12, "bold")).pack(pady=5)
        
        # 狀態樹狀圖
        self.state_tree = ttk.Treeview(left_frame, height=20)
        self.state_tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.state_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.state_tree.configure(yscrollcommand=tree_scroll.set)
        
        # 右側：詳細資訊
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="詳細資訊", font=("Microsoft JhengHei", 12, "bold")).pack(pady=5)
        
        self.detail_text = scrolledtext.ScrolledText(right_frame, width=60, height=25, font=("Consolas", 9))
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 按鈕區域
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="刷新狀態", command=self._refresh_game_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="導出狀態", command=self._export_game_state).pack(side=tk.LEFT, padx=5)
        
        # 綁定樹狀圖選擇事件
        self.state_tree.bind('<<TreeviewSelect>>', self._on_state_select)
        
        # 初始刷新
        self._refresh_game_state()
    
    def _create_performance_tab(self, parent):
        """建立性能監控分頁"""
        # 控制區域
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="性能監控", font=("Microsoft JhengHei", 12, "bold")).pack(pady=5)
        
        # 控制按鈕
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_btn = ttk.Button(btn_frame, text="開始監控", command=self._toggle_performance_monitoring)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="清除數據", command=self._clear_performance_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="導出報告", command=self._export_performance_report).pack(side=tk.LEFT, padx=5)
        
        # 性能數據顯示
        self.perf_text = scrolledtext.ScrolledText(parent, height=30, font=("Consolas", 9))
        self.perf_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 實時狀態
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="狀態:", font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="未監控", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
    
    def _create_variable_tab(self, parent):
        """建立變數操作分頁"""
        # 變數選擇
        var_frame = ttk.Frame(parent)
        var_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(var_frame, text="變數操作", font=("Microsoft JhengHei", 12, "bold")).pack(pady=5)
        
        ttk.Label(var_frame, text="選擇變數:").pack(anchor=tk.W)
        self.var_combo = ttk.Combobox(var_frame, values=self._get_variable_list())
        self.var_combo.pack(fill=tk.X, pady=2)
        self.var_combo.bind('<<ComboboxSelected>>', self._on_variable_select)
        
        # 當前值顯示
        ttk.Label(var_frame, text="當前值:").pack(anchor=tk.W, pady=(10, 0))
        self.current_value_label = ttk.Label(var_frame, text="", background="#f0f0f0", relief="sunken")
        self.current_value_label.pack(fill=tk.X, pady=2)
        
        # 新值輸入
        ttk.Label(var_frame, text="新值:").pack(anchor=tk.W, pady=(10, 0))
        self.new_value_entry = ttk.Entry(var_frame)
        self.new_value_entry.pack(fill=tk.X, pady=2)
        
        # 操作按鈕
        btn_frame = ttk.Frame(var_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="設置值", command=self._set_variable_value).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重置為默認", command=self._reset_variable).pack(side=tk.LEFT, padx=5)
        
        # 快捷操作
        ttk.Label(var_frame, text="快捷操作:").pack(anchor=tk.W, pady=(10, 0))
        shortcut_frame = ttk.Frame(var_frame)
        shortcut_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(shortcut_frame, text="最大化屬性", command=self._maximize_attributes).pack(side=tk.LEFT, padx=5)
        ttk.Button(shortcut_frame, text="清空債務", command=self._clear_debt).pack(side=tk.LEFT, padx=5)
        ttk.Button(shortcut_frame, text="增加現金", command=self._add_cash).pack(side=tk.LEFT, padx=5)
    
    def _create_log_tab(self, parent):
        """建立事件日誌分頁"""
        ttk.Label(parent, text="事件日誌", font=("Microsoft JhengHei", 12, "bold")).pack(pady=5)
        
        # 日誌顯示
        self.log_text = scrolledtext.ScrolledText(parent, height=30, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 控制按鈕
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="刷新日誌", command=self._refresh_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清除日誌", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="導出日誌", command=self._export_log).pack(side=tk.LEFT, padx=5)
        
        # 初始刷新
        self._refresh_log()
    
    def _create_test_tab(self, parent):
        """建立測試工具分頁"""
        ttk.Label(parent, text="測試工具", font=("Microsoft JhengHei", 12, "bold")).pack(pady=5)
        
        # 事件測試
        event_frame = ttk.LabelFrame(parent, text="事件測試")
        event_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(event_frame, text="觸發隨機事件", command=self._trigger_random_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(event_frame, text="觸發特定事件", command=self._trigger_specific_event).pack(side=tk.LEFT, padx=5)
        
        # 成就測試
        ach_frame = ttk.LabelFrame(parent, text="成就測試")
        ach_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ach_frame, text="檢查成就", command=self._check_achievements).pack(side=tk.LEFT, padx=5)
        ttk.Button(ach_frame, text="解鎖所有成就", command=self._unlock_all_achievements).pack(side=tk.LEFT, padx=5)
        
        # 系統測試
        system_frame = ttk.LabelFrame(parent, text="系統測試")
        system_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(system_frame, text="記憶體清理", command=self._run_gc).pack(side=tk.LEFT, padx=5)
        ttk.Button(system_frame, text="儲存遊戲", command=self._force_save).pack(side=tk.LEFT, padx=5)
        
        # 測試結果顯示
        self.test_result_text = scrolledtext.ScrolledText(parent, height=15, font=("Consolas", 9))
        self.test_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _refresh_game_state(self):
        """刷新遊戲狀態樹狀圖"""
        # 清空現有項目
        for item in self.state_tree.get_children():
            self.state_tree.delete(item)
        
        # 建立狀態樹狀結構
        game_data = self.game.data
        
        # 基本資訊
        basic = self.state_tree.insert("", "end", text="基本資訊", open=True)
        self.state_tree.insert(basic, "end", text=f"遊戲天數: {game_data.days}")
        self.state_tree.insert(basic, "end", text=f"重生次數: {game_data.reborn_count}")
        self.state_tree.insert(basic, "end", text=f"總資產: ${game_data.total_assets():.2f}")
        
        # 財務資訊
        finance = self.state_tree.insert("", "end", text="財務資訊", open=True)
        self.state_tree.insert(finance, "end", text=f"現金: ${game_data.cash:.2f}")
        self.state_tree.insert(finance, "end", text=f"銀行存款: ${game_data.balance:.2f}")
        self.state_tree.insert(finance, "end", text=f"貸款: ${game_data.loan:.2f}")
        self.state_tree.insert(finance, "end", text=f"存款利率: {game_data.deposit_interest_rate*100:.2f}%")
        
        # 屬性資訊
        attrs = self.state_tree.insert("", "end", text="屬性資訊", open=True)
        self.state_tree.insert(attrs, "end", text=f"快樂: {game_data.happiness:.1f}")
        self.state_tree.insert(attrs, "end", text=f"體力: {game_data.stamina:.1f}")
        self.state_tree.insert(attrs, "end", text=f"智力: {game_data.intelligence:.1f}")
        self.state_tree.insert(attrs, "end", text=f"勤奮: {game_data.diligence:.1f}")
        self.state_tree.insert(attrs, "end", text=f"魅力: {game_data.charisma:.1f}")
        self.state_tree.insert(attrs, "end", text=f"經驗: {game_data.experience:.1f}")
        self.state_tree.insert(attrs, "end", text=f"今日運氣: {game_data.luck_today:.1f}")
        
        # 股票資訊
        stocks = self.state_tree.insert("", "end", text="股票資訊", open=False)
        for code, stock in game_data.stocks.items():
            stock_item = self.state_tree.insert(stocks, "end", text=f"{stock['name']} ({code})", open=False)
            self.state_tree.insert(stock_item, "end", text=f"價格: ${stock['price']:.2f}")
            self.state_tree.insert(stock_item, "end", text=f"持有: {stock['owned']}")
            self.state_tree.insert(stock_item, "end", text=f"總成本: ${stock['total_cost']:.2f}")
        
        # 工作資訊
        if game_data.job:
            job = self.state_tree.insert("", "end", text="工作資訊", open=True)
            self.state_tree.insert(job, "end", text=f"職稱: {game_data.job.get('name', '無')}")
            self.state_tree.insert(job, "end", text=f"等級: {game_data.job.get('level', 0)}")
            self.state_tree.insert(job, "end", text=f"薪資: ${game_data.job.get('salary_per_day', 0):.2f}/日")
        
        # 成就統計
        if hasattr(self.game, 'achievements'):
            ach = self.state_tree.insert("", "end", text="成就統計", open=True)
            total = len(self.game.achievements.get_all())
            unlocked = len(self.game.achievements.get_unlocked())
            rate = self.game.achievements.get_completion_rate()
            self.state_tree.insert(ach, "end", text=f"總成就: {total}")
            self.state_tree.insert(ach, "end", text=f"已解鎖: {unlocked}")
            self.state_tree.insert(ach, "end", text=f"完成率: {rate:.1%}")
    
    def _on_state_select(self, event):
        """處理狀態樹狀圖選擇事件"""
        selection = self.state_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        item_text = self.state_tree.item(item, "text")
        
        # 清空詳細資訊
        self.detail_text.delete(1.0, tk.END)
        
        # 根據選擇的項目顯示詳細資訊
        if "股票" in item_text and "(" in item_text:
            # 股票詳細資訊
            code = item_text.split("(")[1].split(")")[0]
            if code in self.game.data.stocks:
                stock = self.game.data.stocks[code]
                details = f"""
股票代碼: {code}
股票名稱: {stock['name']}
當前價格: ${stock['price']:.2f}
持有數量: {stock['owned']}
總成本: ${stock['total_cost']:.2f}
平均成本: ${stock['total_cost']/stock['owned']:.2f} (如果持有 > 0)
產業: {stock.get('industry', '未知')}
股利: 每股 ${stock.get('dividend_per_share', 0)}，每 {stock.get('dividend_interval', 30)} 天
歷史價格點數: {len(stock['history'])}
買入點: {len(stock.get('buy_points', []))}
賣出點: {len(stock.get('sell_points', []))}
                """
                self.detail_text.insert(tk.END, details.strip())
        
        elif "財務資訊" in item_text:
            # 財務詳細資訊
            gd = self.game.data
            details = f"""
=== 財務詳細資訊 ===

現金: ${gd.cash:.2f}
銀行存款: ${gd.balance:.2f}
貸款餘額: ${gd.loan:.2f}
總資產: ${gd.total_assets():.2f}

存款利率: {gd.deposit_interest_rate*100:.2f}%
貸款利率: {gd.loan_interest_rate*100:.2f}%

淨資產: ${gd.balance + gd.cash - gd.loan:.2f}
資產配置:
- 現金占比: {(gd.cash / gd.total_assets() * 100):.1f}% (如果總資產 > 0)
- 存款占比: {(gd.balance / gd.total_assets() * 100):.1f}% (如果總資產 > 0)

交易歷史數量: {len(gd.transaction_history)}
            """
            self.detail_text.insert(tk.END, details.strip())
    
    def _export_game_state(self):
        """導出遊戲狀態"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                # 將遊戲狀態轉換為可序列化的字典
                state = {
                    'basic_info': {
                        'days': self.game.data.days,
                        'reborn_count': self.game.data.reborn_count,
                        'total_assets': self.game.data.total_assets(),
                        'cash': self.game.data.cash,
                        'balance': self.game.data.balance,
                        'loan': self.game.data.loan
                    },
                    'attributes': {
                        'happiness': self.game.data.happiness,
                        'stamina': self.game.data.stamina,
                        'intelligence': self.game.data.intelligence,
                        'diligence': self.game.data.diligence,
                        'charisma': self.game.data.charisma,
                        'experience': self.game.data.experience,
                        'luck_today': self.game.data.luck_today
                    },
                    'stocks': dict(self.game.data.stocks),
                    'achievements': {
                        'total': len(self.game.achievements.get_all()),
                        'unlocked': len(self.game.achievements.get_unlocked()),
                        'completion_rate': self.game.achievements.get_completion_rate()
                    }
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"遊戲狀態已導出到 {filename}")
        except Exception as e:
            messagebox.showerror("錯誤", f"導出失敗: {str(e)}")
    
    def _toggle_performance_monitoring(self):
        """切換性能監控"""
        if self.performance_monitoring:
            self.performance_monitoring = False
            self.monitor_btn.config(text="開始監控")
            self.status_label.config(text="未監控", foreground="red")
        else:
            self.performance_monitoring = True
            self.monitor_btn.config(text="停止監控")
            self.status_label.config(text="監控中", foreground="green")
            # 啟動監控線程
            threading.Thread(target=self._performance_monitor_thread, daemon=True).start()
    
    def _performance_monitor_thread(self):
        """性能監控線程"""
        while self.performance_monitoring:
            try:
                # 收集性能數據
                process = psutil.Process()
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent(interval=0.1)
                
                data = {
                    'timestamp': time.time(),
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent,
                    'num_threads': process.num_threads(),
                    'game_days': self.game.data.days
                }
                
                self.performance_data.append(data)
                
                # 更新顯示（最近10個數據點）
                if len(self.performance_data) > 10:
                    self.performance_data = self.performance_data[-10:]
                
                # 更新UI
                self._update_performance_display()
                
                time.sleep(1)  # 每秒更新一次
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                break
    
    def _update_performance_display(self):
        """更新性能顯示"""
        if not self.performance_data:
            return
            
        # 清空現有內容
        self.perf_text.delete(1.0, tk.END)
        
        # 顯示標題
        self.perf_text.insert(tk.END, "=== 性能監控數據 ===\n\n")
        
        # 顯示最新數據
        latest = self.performance_data[-1]
        self.perf_text.insert(tk.END, f"最新數據:\n")
        self.perf_text.insert(tk.END, f"  記憶體使用: {latest['memory_mb']:.1f} MB\n")
        self.perf_text.insert(tk.END, f"  CPU 使用率: {latest['cpu_percent']:.1f}%\n")
        self.perf_text.insert(tk.END, f"  線程數量: {latest['num_threads']}\n")
        self.perf_text.insert(tk.END, f"  遊戲天數: {latest['game_days']}\n\n")
        
        # 顯示統計數據
        if len(self.performance_data) > 1:
            memory_values = [d['memory_mb'] for d in self.performance_data]
            cpu_values = [d['cpu_percent'] for d in self.performance_data]
            
            self.perf_text.insert(tk.END, f"統計數據 (最近{len(self.performance_data)}個數據點):\n")
            self.perf_text.insert(tk.END, f"  記憶體 - 平均: {sum(memory_values)/len(memory_values):.1f} MB, 最大: {max(memory_values):.1f} MB\n")
            self.perf_text.insert(tk.END, f"  CPU - 平均: {sum(cpu_values)/len(cpu_values):.1f}%, 最大: {max(cpu_values):.1f}%\n")
    
    def _clear_performance_data(self):
        """清除性能數據"""
        self.performance_data.clear()
        self.perf_text.delete(1.0, tk.END)
        self.perf_text.insert(tk.END, "性能數據已清除")
    
    def _export_performance_report(self):
        """導出性能報告"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.performance_data, f, indent=2)
                messagebox.showinfo("成功", f"性能報告已導出到 {filename}")
        except Exception as e:
            messagebox.showerror("錯誤", f"導出失敗: {str(e)}")
    
    def _get_variable_list(self):
        """獲取可操作的變數列表"""
        variables = []
        gd = self.game.data
        
        # 財務變數
        variables.extend(['cash', 'balance', 'loan', 'deposit_interest_rate', 'loan_interest_rate'])
        
        # 屬性變數
        variables.extend(['happiness', 'stamina', 'intelligence', 'diligence', 'charisma', 'experience', 'luck_today'])
        
        # 遊戲狀態變數
        variables.extend(['days', 'reborn_count'])
        
        return variables
    
    def _on_variable_select(self, event):
        """處理變數選擇事件"""
        var_name = self.var_combo.get()
        if var_name and hasattr(self.game.data, var_name):
            current_value = getattr(self.game.data, var_name)
            self.current_value_label.config(text=str(current_value))
            self.new_value_entry.delete(0, tk.END)
            self.new_value_entry.insert(0, str(current_value))
    
    def _set_variable_value(self):
        """設置變數值"""
        var_name = self.var_combo.get()
        new_value_str = self.new_value_entry.get()
        
        if not var_name or not new_value_str:
            messagebox.showerror("錯誤", "請選擇變數並輸入新值")
            return
        
        try:
            # 根據變數類型轉換值
            if var_name in ['cash', 'balance', 'loan']:
                new_value = float(new_value_str)
            elif var_name in ['happiness', 'stamina', 'intelligence', 'diligence', 'charisma', 'experience', 'luck_today']:
                new_value = float(new_value_str)
            elif var_name in ['days', 'reborn_count']:
                new_value = int(new_value_str)
            elif var_name in ['deposit_interest_rate', 'loan_interest_rate']:
                new_value = float(new_value_str)
            else:
                new_value = float(new_value_str)
            
            setattr(self.game.data, var_name, new_value)
            self.current_value_label.config(text=str(new_value))
            self.game.update_display()
            messagebox.showinfo("成功", f"變數 {var_name} 已設置為 {new_value}")
            
        except ValueError as e:
            messagebox.showerror("錯誤", f"無效的值格式: {str(e)}")
    
    def _reset_variable(self):
        """重置變數為默認值"""
        var_name = self.var_combo.get()
        if not var_name:
            messagebox.showerror("錯誤", "請選擇變數")
            return
        
        # 定義默認值
        defaults = {
            'cash': 1000.0,
            'balance': 0.0,
            'loan': 0.0,
            'deposit_interest_rate': 0.01,
            'loan_interest_rate': 0.005,
            'happiness': 50.0,
            'stamina': 50.0,
            'intelligence': 50.0,
            'diligence': 50.0,
            'charisma': 50.0,
            'experience': 0.0,
            'luck_today': 50.0,
            'days': 0,
            'reborn_count': 0
        }
        
        if var_name in defaults:
            default_value = defaults[var_name]
            setattr(self.game.data, var_name, default_value)
            self.current_value_label.config(text=str(default_value))
            self.new_value_entry.delete(0, tk.END)
            self.new_value_entry.insert(0, str(default_value))
            self.game.update_display()
            messagebox.showinfo("成功", f"變數 {var_name} 已重置為默認值 {default_value}")
    
    def _maximize_attributes(self):
        """最大化所有屬性"""
        attributes = ['happiness', 'stamina', 'intelligence', 'diligence', 'charisma', 'luck_today']
        for attr in attributes:
            if hasattr(self.game.data, attr):
                setattr(self.game.data, attr, 100.0)
        self.game.update_display()
        messagebox.showinfo("成功", "所有屬性已最大化")
    
    def _clear_debt(self):
        """清空債務"""
        self.game.data.loan = 0.0
        self.game.update_display()
        messagebox.showinfo("成功", "債務已清空")
    
    def _add_cash(self):
        """增加現金"""
        self.game.data.cash += 10000.0
        self.game.update_display()
        messagebox.showinfo("成功", "已增加 $10,000 現金")
    
    def _refresh_log(self):
        """刷新事件日誌"""
        self.log_text.delete(1.0, tk.END)
        
        # 獲取遊戲日誌（如果有的話）
        if hasattr(self.game, 'logger') and hasattr(self.game.logger, 'get_recent_logs'):
            logs = self.game.logger.get_recent_logs(100)  # 最近100條日誌
            for log in logs:
                self.log_text.insert(tk.END, f"{log}\n")
        else:
            self.log_text.insert(tk.END, "無可用日誌\n")
    
    def _clear_log(self):
        """清除日誌"""
        self.log_text.delete(1.0, tk.END)
        if hasattr(self.game, 'logger') and hasattr(self.game.logger, 'clear_logs'):
            self.game.logger.clear_logs()
    
    def _export_log(self):
        """導出日誌"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("成功", f"日誌已導出到 {filename}")
        except Exception as e:
            messagebox.showerror("錯誤", f"導出失敗: {str(e)}")
    
    def _trigger_random_event(self):
        """觸發隨機事件"""
        try:
            msg = self.game.event_manager.trigger_random_event()
            self.test_result_text.insert(tk.END, f"觸發事件: {msg}\n")
            self.test_result_text.see(tk.END)
        except Exception as e:
            self.test_result_text.insert(tk.END, f"事件觸發失敗: {str(e)}\n")
    
    def _trigger_specific_event(self):
        """觸發特定事件（可擴充）"""
        # 這裡可以添加選擇特定事件的UI
        messagebox.showinfo("提示", "特定事件觸發功能待實現")
    
    def _check_achievements(self):
        """檢查成就"""
        try:
            unlocked = self.game.achievements.check_achievements()
            if unlocked:
                result = "新解鎖成就:\n" + "\n".join([f"- {ach.name}: {ach.description}" for ach in unlocked])
            else:
                result = "沒有新解鎖的成就"
            
            self.test_result_text.insert(tk.END, result + "\n")
            self.test_result_text.see(tk.END)
        except Exception as e:
            self.test_result_text.insert(tk.END, f"成就檢查失敗: {str(e)}\n")
    
    def _unlock_all_achievements(self):
        """解鎖所有成就（測試用）"""
        try:
            for ach in self.game.achievements.get_all():
                ach.unlocked = True
            self.test_result_text.insert(tk.END, "所有成就已解鎖\n")
            self.test_result_text.see(tk.END)
        except Exception as e:
            self.test_result_text.insert(tk.END, f"成就解鎖失敗: {str(e)}\n")
    
    def _run_gc(self):
        """運行垃圾回收"""
        try:
            collected = gc.collect()
            self.test_result_text.insert(tk.END, f"垃圾回收完成，共回收 {collected} 個物件\n")
            self.test_result_text.see(tk.END)
        except Exception as e:
            self.test_result_text.insert(tk.END, f"垃圾回收失敗: {str(e)}\n")
    
    def _force_save(self):
        """強制儲存遊戲"""
        try:
            self.game._pending_save = True
            self.game.schedule_persist()
            self.test_result_text.insert(tk.END, "遊戲儲存已排程\n")
            self.test_result_text.see(tk.END)
        except Exception as e:
            self.test_result_text.insert(tk.END, f"儲存失敗: {str(e)}\n")
