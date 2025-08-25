from ui_sections import *
from theme_manager import ThemeManager
from game_data import GameData
from slot_machine import SlotMachine
from achievements import AchievementsManager
from events import EventManager
from leaderboard import Leaderboard
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import time
import random
import os
from stock_manager import StockManager

class BankGame:
    def __init__(self, root, data=None):
        self.root = root
        self.data = data if data else GameData()
        self.amount_entry = None  # 確保 UI 綁定正確
        self.history_text = None  # 確保 UI 綁定正確
        self.balance_label = None
        self.cash_label = None
        self.loan_label = None
        self.asset_label = None
        self.deposit_rate_label = None
        self.loan_rate_label = None
        self.theme = ThemeManager(self.root)
        self.slot_machine = SlotMachine(self)
        # 新增：成就管理器初始化時傳入已解鎖 key
        self.achievements = AchievementsManager(self.data, getattr(self.data, 'achievements_unlocked', []))
        self.data.achievements_manager = self.achievements
        self.event_manager = EventManager(self)
        self.leaderboard = Leaderboard()
        self.stock_manager = StockManager(self.data, self.log_transaction, self.update_display)
        self.create_ui()
        # after() 計時器與 I/O 相關旗標/映射
        self._after_map = {}
        self._persist_scheduled = False
        self._pending_save = False
        self._pending_leaderboard = False
        # 新增：隨機事件顯示欄（用 place 固定在最下方，永遠可見）
        self.event_bar = tk.Label(self.root, text="", font=("Microsoft JhengHei", 13), bg="#fffbe6", fg="#b36b00", anchor="w", relief="groove")
        self.event_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # self.update_display()  # 移除這行，避免 UI 尚未初始化時出錯
        self.start_scheduled_tasks()
        self.start_event_timer()
        self.start_leaderboard_refresh()
        # 登入後自動寫入排行榜
        if hasattr(self, 'username') and self.username:
            self.leaderboard.add_record(self.username, self.data.total_assets(), self.data.days)

    def create_ui(self):
        self.header = create_header_section(self.root, self)
        self.main_tabs = create_main_tabs(self.root, self)
        # 移除股票資訊顯示區
        self.stock_info_label = None
        # 新增：自動綁定股票分頁內的 label
        self.stock_status_labels = getattr(self, 'stock_status_labels', {})
        self.stock_dividend_labels = getattr(self, 'stock_dividend_labels', {})

    # --- 偵錯工具 ---
    def debug_log(self, msg):
        try:
            # 允許以環境變數 SG_DEBUG=1 開啟偵錯
            if getattr(self, 'DEBUG', False) or os.environ.get('SG_DEBUG') == '1':
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[DEBUG {ts}] {msg}")
        except Exception:
            pass

    def _run_task(self, name, func):
        t0 = time.perf_counter()
        try:
            self.debug_log(f"task '{name}' start")
            func()
        except Exception as e:
            self.debug_log(f"task '{name}' error: {e}")
        finally:
            dt = (time.perf_counter() - t0) * 1000
            self.debug_log(f"task '{name}' end, {dt:.1f} ms")

    def update_display(self):
        self.balance_label.config(text=f"銀行餘額: ${self.data.balance:.2f}")
        self.cash_label.config(text=f"現金: ${self.data.cash:.2f}")
        self.loan_label.config(text=f"貸款: ${self.data.loan:.2f}")
        self.deposit_rate_label.config(text=f"存款利率: {self.data.deposit_interest_rate*100:.2f}%")
        self.loan_rate_label.config(text=f"貸款利率: {self.data.loan_interest_rate*100:.2f}%")
        self.asset_label.config(text=f"總資產: ${self.data.total_assets():.2f}")
        self.update_stock_status_labels()
        # 更新配息資訊（如有）
        if hasattr(self, 'stock_dividend_labels'):
            for code, lbl in self.stock_dividend_labels.items():
                stock = self.data.stocks[code]
                lbl.config(text=f"配息：每股${stock.get('dividend_per_share', 0)}，下次配息第{stock.get('next_dividend_day', 30)}天")
        # 不再呼叫 self.update_stock_info_label()
        self.update_charts()
        self.update_achievements_list()
        # 將頻繁 I/O 轉為延遲合併寫入
        if hasattr(self, 'username') and self.username:
            self._pending_leaderboard = True
        if hasattr(self, 'savefile'):
            self._pending_save = True
        self.schedule_persist()

    def update_charts(self):
        color_list = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'cyan', 'magenta', 'gray']
        stock_codes = list(self.data.stocks.keys())
        color_map = {code: color_list[i % len(color_list)] for i, code in enumerate(stock_codes)}
        # 只處理有初始化圖表元件的股票
        t0 = time.perf_counter()
        updated = 0
        skipped = 0
        for k in self.axes.keys():
            if k not in self.data.stocks:
                continue
            stock = self.data.stocks[k]
            try:
                ax = self.axes[k]
                canvas = self.canvases[k]
                # 只在圖表 widget 可見時才重繪
                try:
                    if not canvas.get_tk_widget().winfo_viewable():
                        skipped += 1
                        continue
                except Exception:
                    pass
                ax.clear()
                # 設定白色背景
                ax.set_facecolor('white')
                range_val = self.chart_ranges[k].get()
                if range_val == '全部':
                    h = stock['history']
                    offset = 0
                else:
                    n = int(''.join(filter(str.isdigit, range_val)))
                    h = stock['history'][-n:]
                    offset = len(stock['history']) - len(h)
                line, = ax.plot(h, marker='', linewidth=2, color=color_map.get(k, 'black'))
                if stock['owned'] > 0 and stock['total_cost'] > 0:
                    avg_price = stock['total_cost'] / stock['owned']
                    ax.axhline(avg_price, color='orange', linestyle='--', linewidth=1.5, label='平均買入價')
                filtered_sell = [(i-offset, p) for i, p in stock['sell_points'] if i >= offset and i < offset+len(h)]
                if filtered_sell:
                    xs, ys = zip(*filtered_sell)
                else:
                    xs, ys = [], []
                ax.scatter(xs, ys, color='purple', marker='v', label='賣出', zorder=5)
                if h:
                    max_idx, min_idx = h.index(max(h)), h.index(min(h))
                    ax.scatter([max_idx], [max(h)], color='red', marker='*', s=150, label='最大', edgecolors='black', linewidths=1.5)
                    ax.scatter([min_idx], [min(h)], color='blue', marker='*', s=150, label='最小', edgecolors='black', linewidths=1.5)
                ax.set_title(f"{stock['name']} 價格走勢", fontsize=12)
                ax.set_xlabel('時間', fontsize=10)
                ax.set_ylabel('價格', fontsize=10)
                ax.grid(True)
                ax.legend(loc='lower left')
                canvas.draw()
                # 移除每次更新時的滑鼠事件重綁，事件在建立圖表時已綁定
                updated += 1
            except Exception as e:
                print(f"股票圖表更新失敗: {k}, 錯誤: {e}")
        dt = (time.perf_counter() - t0) * 1000
        self.debug_log(f"update_charts: updated={updated}, skipped={skipped}, {dt:.1f} ms")


    def log_transaction(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data.transaction_history.append({'timestamp': timestamp, 'message': message})
        self.history_text.config(state='normal')
        self.history_text.insert('1.0', f"[{timestamp}] {message}\n")
        if int(self.history_text.index('end-1c').split('.')[0]) > 20:
            self.history_text.delete('end-1c linestart', 'end-1c')
        self.history_text.config(state='disabled')

    def start_scheduled_tasks(self):
        self._after_ids = []
        self._after_map = {}
        self._unified_timer_tick = 0
        # 用於檢測 unified_timer 的節拍漂移（事件迴圈延遲）
        self._last_unified_at = time.perf_counter()
        aid = self.root.after(1000, lambda: self._run_task('unified', self.unified_timer))
        self._after_map['unified'] = aid
        self._after_ids.append(aid)
        self.update_time()

    def unified_timer(self):
        t0 = time.perf_counter()
        try:
            self._unified_timer_tick += 1
            tick = self._unified_timer_tick
            self.debug_log(f"unified_timer tick={tick} start")
            # 每 5 秒執行股票更新
            if tick % 5 == 0:
                for stock in self.data.stocks.values():
                    change_percent = random.gauss(0, self.data.market_volatility)
                    new_price = stock['price'] * (1 + change_percent)
                    new_price = max(10, round(new_price, 2))
                    stock['price'] = new_price
                    stock['history'].append(new_price)
                self.update_display()
            # 每 30 秒執行利息與配息與比特幣產幣
            if tick % 30 == 0:
                if self.data.balance > 0:
                    interest = self.data.balance * self.data.deposit_interest_rate
                    self.data.balance += interest
                    self.log_transaction(f"獲得存款利息 ${interest:.2f}")
                if self.data.loan > 0:
                    interest = self.data.loan * self.data.loan_interest_rate
                    self.data.loan += interest
                    if self.data.cash >= interest:
                        self.data.cash -= interest
                        self.log_transaction(f"產生貸款利息 ${interest:.2f}")
                    elif self.data.cash + self.data.balance >= interest:
                        needed = interest - self.data.cash
                        self.log_transaction(f"現金不足，從存款扣除貸款利息 ${needed:.2f}")
                        self.data.cash = 0
                        self.data.balance -= needed
                    else:
                        total = self.data.cash + self.data.balance
                        self.data.cash = 0
                        self.data.balance = 0
                        self.log_transaction(f"現金與存款皆不足，已扣除所有剩餘金額 ${total:.2f} 作為貸款利息")
                self.data.days += 1
                for code, stock in self.data.stocks.items():
                    if self.data.days >= stock.get('next_dividend_day', 30):
                        if stock['owned'] > 0 and stock.get('dividend_per_share', 0) > 0:
                            dividend = stock['owned'] * stock['dividend_per_share']
                            self.data.cash += dividend
                            msg = f"{stock['name']} 配息：持有 {stock['owned']} 股，獲得股息 ${dividend:.2f}"
                            self.log_transaction(msg)
                            self.show_event_message(msg)
                        stock['next_dividend_day'] = self.data.days + stock.get('dividend_interval', 30)
                # 比特幣價格隨機波動
                btc = self.data.stocks['BTC']
                btc_change = random.gauss(0, 0.03)
                btc['price'] = max(10000, round(btc['price'] * (1 + btc_change)))
                btc['history'].append(btc['price'])
                # 自動產生比特幣
                hashrate = getattr(self.data, 'btc_hashrate', 0)
                if hashrate > 0:
                    mined = hashrate * 0.01  # 每30秒產生的比特幣數量，可調整
                    self.data.btc_balance += mined
                    self.log_transaction(f"礦機自動挖礦，獲得比特幣 {mined:.4f}")
                self.update_display()
            # 破產偵測
            self.check_bankruptcy_and_reborn()
        except Exception as e:
            self.debug_log(f"unified_timer exception: {e}")
        finally:
            dt = (time.perf_counter() - t0) * 1000
            # 檢測節拍漂移：距離上次 unified 呼叫的時間是否明顯超過 1000ms
            now = time.perf_counter()
            delta_ms = (now - getattr(self, '_last_unified_at', now)) * 1000
            drift_ms = max(0.0, delta_ms - 1000.0)
            self._last_unified_at = now
            ids_count = len(getattr(self, '_after_ids', []))
            map_count = len(getattr(self, '_after_map', {}))
            self.debug_log(f"unified_timer tick={self._unified_timer_tick} end, exec={dt:.1f} ms, delta={delta_ms:.1f} ms, drift={drift_ms:.1f} ms, after_ids={ids_count}, after_map={map_count}")
            if ids_count > 200:
                self.debug_log(f"WARNING: after_ids ballooning: {ids_count}")
            # 持續循環（包裝在 _run_task 以便錯誤隔離與耗時紀錄）
            aid = self.root.after(1000, lambda: self._run_task('unified', self.unified_timer))
            self._after_map['unified'] = aid
            self._after_ids.append(aid)

    def start_event_timer(self):
        delay = random.randint(20000, 40000)
        aid = self.root.after(delay, lambda: self._run_task('event', self.trigger_event))
        self._after_map['event'] = aid
        self._after_ids.append(aid)
        self.debug_log(f"schedule event after {delay} ms -> id={aid}")

    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"當前時間: {current_time}")
        aid = self.root.after(1000, lambda: self._run_task('time', self.update_time))
        self._after_map['time'] = aid
        self._after_ids.append(aid)
        self.debug_log(f"schedule time after 1000 ms -> id={aid}")

    # --- 操作邏輯 ---
    def get_amount(self, min_value=1, max_value=100000000):
        try:
            value = self.amount_entry.get().strip()
            if value == '':
                self.show_event_message("請輸入金額！")
                return None
            amount = float(value)
            if not (min_value <= amount <= max_value):
                self.show_event_message(f"金額需介於 {min_value} ~ {max_value}！")
                return None
            return amount
        except ValueError:
            self.show_event_message("請輸入有效的數字！")
            return None

    def get_stock_amount(self, min_value=1, max_value=1000000):
        try:
            value = self.stock_amount_entry.get().strip()
            if value == '':
                self.show_event_message("請輸入股數！")
                return None
            amount = int(value)
            if not (min_value <= amount <= max_value):
                self.show_event_message(f"股數需介於 {min_value} ~ {max_value}！")
                return None
            return amount
        except ValueError:
            self.show_event_message("請輸入有效的股數！")
            return None

    def deposit(self):
        amount = self.get_amount()
        if amount is not None and amount <= self.data.cash:
            self.data.cash -= amount
            self.data.balance += amount
            self.log_transaction(f"存款 ${amount:.2f}")
            self.update_display()
        # 不再 show_event_message

    def withdraw(self):
        amount = self.get_amount()
        if amount is not None:
            if amount <= self.data.balance:
                self.data.balance -= amount
                self.data.cash += amount
                self.log_transaction(f"提款 ${amount:.2f}")
                self.update_display()
            elif self.data.balance > 0:
                all_amount = self.data.balance
                self.data.cash += all_amount
                self.data.balance = 0
                self.log_transaction(f"提款金額超過存款，已全部提出 ${all_amount:.2f}")
                self.update_display()
            else:
                self.log_transaction("提款失敗：存款為零！")
        # 不再 show_event_message

    def update_stock_status_labels(self):
        # 自動更新股票分頁內所有現價/持有 label
        if hasattr(self, 'stock_status_labels'):
            for code, lbl in self.stock_status_labels.items():
                stock = self.data.stocks[code]
                lbl.config(text=f"{stock['name']} ${stock['price']:.2f} 持有{stock['owned']}股")
        # 自動更新配息 label
        if hasattr(self, 'stock_dividend_labels'):
            for code, lbl in self.stock_dividend_labels.items():
                stock = self.data.stocks[code]
                lbl.config(text=f"配息：每股${stock.get('dividend_per_share', 0)}，下次配息第{stock.get('next_dividend_day', 30)}天")

    def update_trade_log(self, action, amount, price, stock_name):
        if hasattr(self, 'trade_log_var'):
            self.trade_log_var.set(f"{action} {amount} 股 {stock_name} @ ${price:.2f}")

    def buy_stock(self):
        amount = self.get_stock_amount()
        stock_name = self.stock_var.get()
        stock_key = self.stock_name_to_code[stock_name]
        stock = self.data.stocks[stock_key]
        price = stock['price']
        if amount is None:
            return
        total_cost = amount * price
        if total_cost <= self.data.cash:
            stock['owned'] += amount
            stock['total_cost'] += total_cost
            self.data.cash -= total_cost
            idx = len(stock['history']) - 1
            # 買入點加到 buy_points
            stock['buy_points'].append((idx, price))
            self.log_transaction(f"已購買 {amount} 股 {stock['name']}，花費 ${total_cost:.2f}")
            self.update_display()
            self.check_achievements()
            if hasattr(self, 'trade_tip_label'):
                self.trade_tip_label.config(text=f"買入 {amount} 股，價格 ${price:.2f}，持有 {stock['owned']} 股")
            self.update_stock_status_labels()
            self.update_trade_log("買入", amount, price, stock['name'])

    def sell_stock(self):
        amount = self.get_stock_amount()
        stock_name = self.stock_var.get()
        stock_key = self.stock_name_to_code[stock_name]
        stock = self.data.stocks[stock_key]
        price = stock['price']
        if amount is None:
            return
        if amount > stock['owned']:
            self.log_transaction(f"賣出失敗：持有股票不足！目前持有 {stock['owned']} 股")
            return
        total_value = amount * price
        stock['owned'] -= amount
        if stock['owned'] == 0:
            stock['total_cost'] = 0
        else:
            stock['total_cost'] *= (stock['owned']) / (stock['owned'] + amount)
        self.data.cash += total_value
        idx = len(stock['history']) - 1
        # 賣出時移除最早的買點線
        if stock['buy_points']:
            stock['buy_points'].pop(0)
        stock['sell_points'].append((idx, price))
        self.log_transaction(f"已賣出 {amount} 股 {stock['name']}，獲得 ${total_value:.2f}")
        self.update_display()
        self.check_achievements()
        if hasattr(self, 'trade_tip_label'):
            self.trade_tip_label.config(text=f"賣出 {amount} 股，價格 ${price:.2f}，持有 {stock['owned']} 股")
        self.update_stock_status_labels()
        self.update_trade_log("賣出", amount, price, stock['name'])

    def take_loan(self):
        amount = self.get_amount()
        if amount is not None:
            if self.data.loan + amount <= self.data.loan_limit:
                self.data.loan += amount
                self.data.cash += amount
                self.log_transaction(f"貸款 ${amount:.2f}")
                self.update_display()
            else:
                self.log_transaction(f"貸款失敗：超過貸款上限！最多還可以貸款 ${self.data.loan_limit - self.data.loan:.2f}")
        # 不再 show_event_message

    def repay_loan(self):
        amount = self.get_amount()
        if amount == 0:
            if self.data.cash >= self.data.loan:
                repay_amount = self.data.loan
                self.data.cash -= repay_amount
                self.data.loan = 0
                self.log_transaction(f"還清貸款 ${repay_amount:.2f}")
                self.update_display()
            else:
                self.log_transaction("還款失敗：現金不足以還清所有貸款！")
        elif amount is not None:
            if amount >= self.data.loan:
                if self.data.cash >= self.data.loan:
                    repay_amount = self.data.loan
                    self.data.cash -= repay_amount
                    self.data.loan = 0
                    self.log_transaction(f"還清貸款 ${repay_amount:.2f}")
                    self.update_display()
                else:
                    self.log_transaction("還款失敗：現金不足以還清所有貸款！")
            elif amount <= self.data.loan:
                if amount <= self.data.cash:
                    self.data.cash -= amount
                    self.data.loan -= amount
                    self.log_transaction(f"還款 ${amount:.2f}")
                    self.update_display()
                else:
                    self.log_transaction("還款失敗：現金不足！")

    # --- 成就、事件、排行榜 ---
    def check_achievements(self):
        unlocked = self.achievements.check_achievements()
        self.update_achievements_list()
        for ach in unlocked:
            self.log_transaction(f"成就解鎖：{ach.name} - {ach.description}")

    def update_achievements_list(self):
        self.ach_listbox.delete(0, tk.END)
        for a in self.achievements.get_all():
            mark = '✓' if a.unlocked else '✗'
            # 顯示分類
            desc = f"[{a.category}] {a.name}：{a.description}"
            self.ach_listbox.insert(tk.END, f"[{mark}] {desc}")

    def show_event_message(self, msg):
        self.event_bar.config(text=msg)

    def trigger_event(self):
        event_msg = self.event_manager.trigger_random_event()
        if event_msg:
            self.show_event_message(event_msg)
        self.update_display()
        self.start_event_timer()
        self.debug_log("trigger_event executed")

    def show_leaderboard(self):
        # 只顯示現有帳號的前100名
        from os import listdir
        usernames_valid = set([f[5:-5] for f in listdir('.') if f.startswith('save_') and f.endswith('.json')])
        top = [r for r in self.leaderboard.get_top() if r['username'] in usernames_valid]
        msg = "排行榜：\n" + "\n".join([
            f"{i+1}. {r['username']} 資產: ${r['asset']} 天數: {r['days']}" for i, r in enumerate(top)
        ])
        self.rank_text.config(state='normal')
        self.rank_text.delete('1.0', 'end')
        self.rank_text.insert('1.0', msg)
        self.rank_text.config(state='disabled')

    def on_close(self):
        # 停止所有 after 任務，避免 invalid command name 錯誤
        if hasattr(self, '_after_ids'):
            for aid in self._after_ids:
                try:
                    self.root.after_cancel(aid)
                    self.debug_log(f"after_cancel id={aid}")
                except Exception:
                    pass
        if hasattr(self, '_after_map'):
            for key, aid in list(self._after_map.items()):
                try:
                    self.root.after_cancel(aid)
                    self.debug_log(f"after_cancel name={key} id={aid}")
                except Exception:
                    pass
        # 關閉前最後一次同步持久化，避免待寫入資料遺失
        try:
            self.persist_state()
        except Exception:
            pass
        self.root.destroy()
        os._exit(0)

    def start_leaderboard_refresh(self):
        self.show_leaderboard()
        aid = self.root.after(10000, lambda: self._run_task('leaderboard', self.start_leaderboard_refresh))
        self._after_map['leaderboard'] = aid
        if hasattr(self, '_after_ids'):
            self._after_ids.append(aid)
        self.debug_log(f"schedule leaderboard after 10000 ms -> id={aid}")

    def update_stock_info_label(self):
        pass 

    # 將頻繁 I/O 合併並延遲寫入，降低 UI 卡頓
    def schedule_persist(self, delay_ms=10000):
        if self._persist_scheduled:
            return
        def _flush():
            self._persist_scheduled = False
            self.persist_state()
        aid = self.root.after(delay_ms, lambda: self._run_task('persist', _flush))
        self._after_map['persist'] = aid
        self._after_ids.append(aid)
        self._persist_scheduled = True
        self.debug_log(f"schedule persist after {delay_ms} ms -> id={aid}")

    def persist_state(self):
        t0 = time.perf_counter()
        try:
            did_rank = False
            did_save = False
            if self._pending_leaderboard and hasattr(self, 'username') and self.username:
                self.leaderboard.add_record(self.username, self.data.total_assets(), self.data.days)
                did_rank = True
            if self._pending_save and hasattr(self, 'savefile'):
                self.data.save(self.savefile, show_error=lambda msg: messagebox.showerror("存檔錯誤", msg))
                did_save = True
        finally:
            dt = (time.perf_counter() - t0) * 1000
            self.debug_log(f"persist_state: rank={did_rank}, save={did_save}, {dt:.1f} ms")
            self._pending_leaderboard = False
            self._pending_save = False

    def check_bankruptcy_and_reborn(self):
        if self.data.cash <= 0 and self.data.balance <= 0 and self.data.loan > 0:
            # 只重置帳號資料，不更換帳號名稱
            self.data.reset(is_reborn=True)
            self.data.save(self.savefile)
            messagebox.showinfo("破產重生", f"你已破產，已自動重生！\n現金 $1000，存款 $0，貸款 $0\n重生次數：{self.data.reborn_count}")
            self.update_display() 