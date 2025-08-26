from ui_sections import create_header_section, create_main_tabs
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
from entrepreneurship import EntrepreneurshipManager
from reports_charts import ReportsChartsManager
from store_expenses import StoreExpensesManager
from logger import GameLogger
from job_manager import JobManager
from dividend_manager import DividendManager

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
        # 1 天 = 180 秒（3 分鐘）=> unified_timer 每秒 tick，滿 180 tick 視為一天
        self.DAY_TICKS = 180
        # 創業系統管理器
        self.entre = EntrepreneurshipManager(self)
        # 報表與圖表管理器
        self.reports = ReportsChartsManager(self)
        # 商店與支出管理器
        self.store = StoreExpensesManager(self)
        # 記錄器
        self.logger = GameLogger(self)
        # 工作/薪資管理器
        self.jobs = JobManager(self)
        # 股利/DRIP 管理器
        self.dividends = DividendManager(self)
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

        # 初始化商店/支出 UI（若 UI 已就緒）
        try:
            self.update_store_ui()
        except Exception:
            pass

    def create_ui(self):
        self.header = create_header_section(self.root, self)
        self.main_tabs = create_main_tabs(self.root, self)
        # 移除股票資訊顯示區
        self.stock_info_label = None
        # 新增：自動綁定股票分頁內的 label
        self.stock_status_labels = getattr(self, 'stock_status_labels', {})
        self.stock_dividend_labels = getattr(self, 'stock_dividend_labels', {})
        # 初始更新天數顯示
        self.update_game_day_label()
        # 主題套用至所有 tk/ttk 元件（建立 UI 後呼叫）
        try:
            if hasattr(self, 'theme') and self.theme:
                self.theme.apply_to_game(self)
        except Exception:
            pass

    # --- 偵錯工具 ---
    def debug_log(self, msg):
        return self.logger.debug_log(msg)

    # --- 支出：UI 綁定與列表更新 ---
    def update_expenses_ui(self):
        return self.store.update_expenses_ui()

    def add_expense_from_ui(self):
        return self.store.add_expense_from_ui()

    # --- 商店與固定支出：邏輯層 ---
    def ensure_default_expenses(self):
        return self.store.ensure_default_expenses()

    def subscribe_service(self, name, amount, frequency):
        return self.store.subscribe_service(name, amount, frequency)

    def cancel_subscription(self, name):
        return self.store.cancel_subscription(name)

    def cancel_subscription_from_ui(self):
        return self.store.cancel_subscription_from_ui()

    def buy_store_good(self, name, price):
        return self.store.buy_store_good(name, price)

    # --- 商店：UI 綁定 ---
    def update_store_ui(self):
        return self.store.update_store_ui()

    def subscribe_selected_from_ui(self):
        return self.store.subscribe_selected_from_ui()

    def buy_selected_good_from_ui(self):
        return self.store.buy_selected_good_from_ui()

    def delete_expense_from_ui(self):
        return self.store.delete_expense_from_ui()

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
        # 更新遊戲日數顯示
        self.update_game_day_label()
        self.update_stock_status_labels()
        # 更新配息資訊（如有）
        if hasattr(self, 'stock_dividend_labels'):
            for code, lbl in self.stock_dividend_labels.items():
                stock = self.data.stocks[code]
                lbl.config(text=f"配息：每股${stock.get('dividend_per_share', 0)}，下次配息第{stock.get('next_dividend_day', 30)}天")
        # 不再呼叫 self.update_stock_info_label()
        # 更新上班模式 UI
        self.update_job_ui()
        # 更新支出清單 UI
        self.update_expenses_ui()
        # 更新基金/ETF UI
        self.update_funds_ui()
        # 更新商店/物品欄 UI
        self.update_store_ui()
        # 更新報表 UI
        try:
            self.update_report_ui()
        except Exception:
            pass
        self.update_charts()
        self.update_achievements_list()
        # 將頻繁 I/O 轉為延遲合併寫入
        if hasattr(self, 'username') and self.username:
            self._pending_leaderboard = True
        if hasattr(self, 'savefile'):
            self._pending_save = True
        self.schedule_persist()

    def update_report_ui(self):
        # 委派至 ReportsChartsManager
        return self.reports.update_report_ui()

    def update_charts(self):
        # 委派至 ReportsChartsManager
        return self.reports.update_charts()

    def log_transaction(self, message):
        return self.logger.log_transaction(message)

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
            # 每 15 秒執行股票更新
            if tick % 15 == 0:
                for stock in self.data.stocks.values():
                    change_percent = random.gauss(0, self.data.market_volatility)
                    new_price = stock['price'] * (1 + change_percent)
                    new_price = max(10, round(new_price, 2))
                    stock['price'] = new_price
                    stock['history'].append(new_price)
                # 股票更新後，同步更新基金 NAV
                self.compute_fund_navs()
                self.update_display()
            # 每 self.DAY_TICKS 秒執行：利息、配息、礦機、每日結算（視為一天）
            if tick % self.DAY_TICKS == 0:
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
                # 上班模式：每日發薪與扣稅
                try:
                    if getattr(self.data, 'job', None):
                        job = self.data.job
                        gross = float(job.get('salary_per_day', 0.0))
                        tax_rate = float(job.get('tax_rate', 0.0))
                        tax = max(0.0, round(gross * tax_rate, 2))
                        net = round(gross - tax, 2)
                        if net > 0:
                            self.data.cash += net
                            self.data.income_history.append({
                                'day': self.data.days + 1,
                                'type': 'salary',
                                'gross': gross,
                                'tax': tax,
                                'net': net,
                            })
                            self.log_transaction(f"薪資入帳：毛薪 ${gross:.2f}，扣稅 ${tax:.2f}，實領 ${net:.2f}")
                except Exception as e:
                    self.debug_log(f"salary payout error: {e}")
                # 支出：到期扣款
                try:
                    freq_days = {'daily': 1, 'weekly': 7, 'monthly': 30}
                    today = self.data.days + 1
                    for exp in list(getattr(self.data, 'expenses', [])):
                        due = int(exp.get('next_due_day', today))
                        if due <= today:
                            amount = float(exp.get('amount', 0.0))
                            paid = 0.0
                            # 先扣現金，再扣存款
                            if self.data.cash >= amount:
                                self.data.cash -= amount
                                paid = amount
                            else:
                                paid = self.data.cash
                                self.data.cash = 0
                                need = amount - paid
                                if self.data.balance >= need:
                                    self.data.balance -= need
                                    paid = amount
                                else:
                                    # 存款也不足，只能扣到 0，留下未付不累積負債（MVP 簡化）
                                    paid += self.data.balance
                                    self.data.balance = 0
                            self.data.expense_history.append({'day': today, 'name': exp.get('name','支出'), 'amount': paid})
                            self.log_transaction(f"支出扣款：{exp.get('name','支出')} ${paid:.2f}")
                            # 安排下次到期
                            interval = freq_days.get(exp.get('frequency','daily'), 1)
                            exp['next_due_day'] = today + interval
                except Exception as e:
                    self.debug_log(f"expense deduction error: {e}")
                # 一天結束後，遊戲天數 +1（固定30天/月）
                self.data.days += 1
                # 股利與 DRIP 委派到 DividendManager
                try:
                    self.dividends.process_daily()
                except Exception as e:
                    self.debug_log(f"dividend manager error: {e}")
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
                # 創業/定投：每日處理
                try:
                    # 創業每日淨額
                    self.entre.process_daily()
                except Exception as e:
                    self.debug_log(f"auto features error: {e}")
                # 每日結束時也更新一次基金 NAV 並記錄歷史
                self.compute_fund_navs(record_history=True)
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
            self._last_unified_at = now
            drift_ms = delta_ms - 1000.0
            # 紀錄執行資訊
            try:
                ids_count = len(getattr(self, '_after_ids', []))
                map_count = len(getattr(self, '_after_map', {}))
            except Exception:
                ids_count = map_count = 0
            self.debug_log(f"unified_timer end, exec={dt:.1f} ms, delta={delta_ms:.1f} ms, drift={drift_ms:.1f} ms, after_ids={ids_count}, after_map={map_count}")
            # 重新排程下一次
            aid = self.root.after(1000, lambda: self._run_task('unified', self.unified_timer))
            self._after_map['unified'] = aid
            self._after_ids.append(aid)

    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"當前時間: {current_time}")
        aid = self.root.after(1000, lambda: self._run_task('time', self.update_time))
        self._after_map['time'] = aid
        self._after_ids.append(aid)
        self.debug_log(f"schedule time after 1000 ms -> id={aid}")

    # --- 遊戲日數顯示 ---
    def update_game_day_label(self):
        try:
            if hasattr(self, 'game_day_label') and self.game_day_label is not None:
                days = int(getattr(self.data, 'days', 0))
                month = days // 30 + 1
                day_in_month = days % 30 + 1
                self.game_day_label.config(text=f"遊戲日數：第 {days} 天（第 {month} 月 第 {day_in_month} 天）")
        except Exception:
            pass

    # --- Auto-Invest/DRIP/Business：邏輯層與 UI 綁定 ---
    def _buy_stock_by_code(self, code: str, shares: int, log_prefix: str = "買入"):
        try:
            if shares <= 0:
                return False
            if code not in self.data.stocks:
                return False
            s = self.data.stocks[code]
            price = float(s.get('price', 0.0))
            cost = shares * price
            if self.data.cash < cost:
                return False
            s['owned'] = int(s.get('owned', 0)) + shares
            s['total_cost'] = float(s.get('total_cost', 0.0)) + cost
            self.data.cash -= cost
            idx = len(s.get('history', [])) - 1
            s.setdefault('buy_points', []).append((idx, price))
            self.log_transaction(f"{log_prefix} {shares} 股 {s.get('name', code)}，單價 ${price:.2f}，花費 ${cost:.2f}")
            return True
        except Exception as e:
            self.debug_log(f"_buy_stock_by_code error: {e}")
            return False

    def _ensure_auto_structs(self):
        if not hasattr(self.data, 'dca_stocks') or not isinstance(self.data.dca_stocks, dict):
            self.data.dca_stocks = {}
        if not hasattr(self.data, 'dca_funds') or not isinstance(self.data.dca_funds, dict):
            self.data.dca_funds = {}
        if not hasattr(self.data, 'businesses') or not isinstance(self.data.businesses, list):
            self.data.businesses = []

    def _process_auto_invest_daily(self):
        self._ensure_auto_structs()
        today = getattr(self.data, 'days', 0)
        # 股票定投
        for code, cfg in list(self.data.dca_stocks.items()):
            try:
                amount = float(cfg.get('amount_cash', 0.0))
                next_day = int(cfg.get('next_day', today))
                interval = int(cfg.get('interval_days', 30))
                if today >= next_day and amount > 0 and code in self.data.stocks:
                    price = float(self.data.stocks[code].get('price', 0.0))
                    shares = int(amount // price) if price > 0 else 0
                    if shares > 0 and self._buy_stock_by_code(code, shares, log_prefix="定投買入"):
                        cfg['next_day'] = today + interval
                    else:
                        cfg['next_day'] = today + 1
            except Exception as e:
                self.debug_log(f"dca_stock error({code}): {e}")
        # 基金定投
        for fname, cfg in list(self.data.dca_funds.items()):
            try:
                amount = float(cfg.get('amount_cash', 0.0))
                next_day = int(cfg.get('next_day', today))
                interval = int(cfg.get('interval_days', 30))
                f = getattr(self.data, 'funds', {}).get(fname)
                finfo = getattr(self.data, 'funds_catalog', {}).get(fname)
                if not isinstance(f, dict) or not isinstance(finfo, dict):
                    continue
                if today >= next_day and amount > 0:
                    nav = float(f.get('nav', 100.0))
                    fee_rate = float(finfo.get('fee_rate', 0.0))
                    denom = nav * (1.0 + fee_rate)
                    units = amount / denom if denom > 0 else 0.0
                    if units > 0 and self.data.cash >= amount:
                        f['units'] = float(f.get('units', 0.0)) + units
                        f['total_cost'] = float(f.get('total_cost', 0.0)) + (units * nav)
                        self.data.cash -= amount
                        self.log_transaction(f"定投買入基金 {fname} {units:.4f} 單位，NAV ${nav:.4f}，投入現金 ${amount:.2f}")
                        cfg['next_day'] = today + interval
                    else:
                        cfg['next_day'] = today + 1
            except Exception as e:
                self.debug_log(f"dca_fund error({fname}): {e}")

    # 以下為 UI 綁定（由 ui_sections 建立之控制項呼叫）
    def ui_add_or_update_dca_stock(self):
        try:
            self._ensure_auto_structs()
            if not hasattr(self, 'dca_stock_code_var'):
                return
            code = self.dca_stock_code_var.get().strip()
            amt_str = self.dca_stock_amount_var.get().strip() if hasattr(self, 'dca_stock_amount_var') else ''
            freq = self.dca_stock_freq_var.get().strip() if hasattr(self, 'dca_stock_freq_var') else 'monthly'
            amount = float(amt_str)
            interval = {'daily':1,'weekly':7,'monthly':30}.get(freq, 30)
            today = getattr(self.data, 'days', 0)
            self.data.dca_stocks[code] = {'amount_cash': amount, 'interval_days': interval, 'next_day': today + interval}
            self.log_transaction(f"設定股票定投：{code} 每{freq} 投入 ${amount:.2f}")
            self.update_auto_invest_ui()
        except Exception as e:
            self.debug_log(f"ui_add_or_update_dca_stock error: {e}")

    def ui_remove_dca_stock(self):
        try:
            self._ensure_auto_structs()
            if not hasattr(self, 'dca_stock_list'):
                return
            sel = self.dca_stock_list.curselection()
            if not sel:
                return
            idx = sel[0]
            keys = list(self.data.dca_stocks.keys())
            if 0 <= idx < len(keys):
                code = keys[idx]
                self.data.dca_stocks.pop(code, None)
                self.log_transaction(f"移除股票定投：{code}")
                self.update_auto_invest_ui()
        except Exception as e:
            self.debug_log(f"ui_remove_dca_stock error: {e}")

    def ui_add_or_update_dca_fund(self):
        try:
            self._ensure_auto_structs()
            if not hasattr(self, 'dca_fund_name_var'):
                return
            name = self.dca_fund_name_var.get().strip()
            amt_str = self.dca_fund_amount_var.get().strip() if hasattr(self, 'dca_fund_amount_var') else ''
            freq = self.dca_fund_freq_var.get().strip() if hasattr(self, 'dca_fund_freq_var') else 'monthly'
            amount = float(amt_str)
            interval = {'daily':1,'weekly':7,'monthly':30}.get(freq, 30)
            today = getattr(self.data, 'days', 0)
            self.data.dca_funds[name] = {'amount_cash': amount, 'interval_days': interval, 'next_day': today + interval}
            self.log_transaction(f"設定基金定投：{name} 每{freq} 投入 ${amount:.2f}")
            self.update_auto_invest_ui()
        except Exception as e:
            self.debug_log(f"ui_add_or_update_dca_fund error: {e}")

    def ui_remove_dca_fund(self):
        try:
            self._ensure_auto_structs()
            if not hasattr(self, 'dca_fund_list'):
                return
            sel = self.dca_fund_list.curselection()
            if not sel:
                return
            idx = sel[0]
            keys = list(self.data.dca_funds.keys())
            if 0 <= idx < len(keys):
                name = keys[idx]
                self.data.dca_funds.pop(name, None)
                self.log_transaction(f"移除基金定投：{name}")
                self.update_auto_invest_ui()
        except Exception as e:
            self.debug_log(f"ui_remove_dca_fund error: {e}")

    def ui_toggle_drip(self):
        try:
            if not hasattr(self, 'drip_stock_code_var'):
                return
            code = self.drip_stock_code_var.get().strip()
            val = bool(self.drip_enable_var.get()) if hasattr(self, 'drip_enable_var') else False
            if code in self.data.stocks:
                self.data.stocks[code]['drip'] = val
                self.log_transaction(f"{code} DRIP {'開啟' if val else '關閉'}")
        except Exception as e:
            self.debug_log(f"ui_toggle_drip error: {e}")

    def update_auto_invest_ui(self):
        try:
            if hasattr(self, 'dca_stock_list') and self.dca_stock_list is not None:
                self.dca_stock_list.delete(0, tk.END)
                for code, cfg in getattr(self.data, 'dca_stocks', {}).items():
                    self.dca_stock_list.insert(tk.END, f"{code} | ${float(cfg.get('amount_cash',0.0)):.2f} / {int(cfg.get('interval_days',30))}天 | 下次第{int(cfg.get('next_day',0))}天")
            if hasattr(self, 'dca_fund_list') and self.dca_fund_list is not None:
                self.dca_fund_list.delete(0, tk.END)
                for name, cfg in getattr(self.data, 'dca_funds', {}).items():
                    self.dca_fund_list.insert(tk.END, f"{name} | ${float(cfg.get('amount_cash',0.0)):.2f} / {int(cfg.get('interval_days',30))}天 | 下次第{int(cfg.get('next_day',0))}天")
            if hasattr(self, 'business_list') and self.business_list is not None:
                self.business_list.delete(0, tk.END)
                try:
                    rows = self.entre.get_business_rows()
                except Exception:
                    rows = []
                for row in rows:
                    self.business_list.insert(tk.END, row)
        except Exception as e:
            self.debug_log(f"update_auto_invest_ui error: {e}")

    # --- 創業系統：UI 綁定（委派到 EntrepreneurshipManager） ---
    def ui_add_business(self):
        try:
            name = self.biz_name_var.get().strip() if hasattr(self, 'biz_name_var') else '事業'
            rev = float(self.biz_rev_var.get().strip()) if hasattr(self, 'biz_rev_var') and self.biz_rev_var.get().strip() else 0.0
            cost = float(self.biz_cost_var.get().strip()) if hasattr(self, 'biz_cost_var') and self.biz_cost_var.get().strip() else 0.0
            if self.entre.add_business(name, rev, cost):
                self.update_auto_invest_ui()
                self.update_display()
        except Exception as e:
            self.debug_log(f"ui_add_business error: {e}")

    def ui_remove_business(self):
        try:
            if not hasattr(self, 'business_list'):
                return
            sel = self.business_list.curselection()
            if not sel:
                return
            idx = sel[0]
            if self.entre.remove_business(idx):
                self.update_auto_invest_ui()
                self.update_display()
        except Exception as e:
            self.debug_log(f"ui_remove_business error: {e}")

    def ui_recruit_employee(self):
        try:
            if not hasattr(self, 'business_list'):
                return
            sel = self.business_list.curselection()
            if not sel:
                self.show_event_message("請先選擇要招募的事業！")
                return
            idx = sel[0]
            msg = self.entre.recruit_employee(idx)
            if msg:
                self.show_event_message(msg)
            self.update_auto_invest_ui()
            self.update_display()
        except Exception as e:
            self.debug_log(f"ui_recruit_employee error: {e}")

    def ui_add_business_legacy(self):
        """Deprecated: 保留舊版以相容，但委派到新實作。"""
        try:
            return self.ui_add_business()
        except Exception as e:
            self.debug_log(f"ui_add_business_legacy error: {e}")

    def ui_remove_business_legacy(self):
        """Deprecated: 保留舊版以相容，但委派到新實作。"""
        try:
            return self.ui_remove_business()
        except Exception as e:
            self.debug_log(f"ui_remove_business_legacy error: {e}")

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
        else:
            self.log_transaction("還款失敗：金額錯誤！")

    # --- 基金/ETF 功能 ---
    def compute_fund_navs(self, record_history=False):
        try:
            if not hasattr(self.data, 'funds_catalog') or not hasattr(self.data, 'funds'):
                return
            for fname, finfo in self.data.funds_catalog.items():
                f = self.data.funds.get(fname)
                if not isinstance(f, dict):
                    continue
                base_prices = f.get('base_prices') or {}
                value_sum = 0.0
                weight_sum = 0.0
                for code, w in finfo.get('weights', {}).items():
                    stock = self.data.stocks.get(code)
                    if not stock:
                        continue
                    price = float(stock.get('price', 0.0))
                    base = float(base_prices.get(code, 0.0))
                    if base <= 0:
                        base = price if price > 0 else 1.0
                        f.setdefault('base_prices', {})[code] = base
                    value_sum += w * (price / base)
                    weight_sum += w
                if weight_sum <= 0:
                    nav = f.get('nav', 100.0)
                else:
                    nav = 100.0 * value_sum  # 權重和視為 1
                f['nav'] = round(nav, 4)
                if record_history:
                    f.setdefault('history', []).append(f['nav'])
        except Exception as e:
            self.debug_log(f"compute_fund_navs error: {e}")

    def update_funds_ui(self):
        try:
            if not hasattr(self, 'fund_select_var'):
                return
            fname = self.fund_select_var.get().strip()
            if not fname or fname not in getattr(self.data, 'funds', {}):
                return
            f = self.data.funds[fname]
            finfo = self.data.funds_catalog.get(fname, {})
            nav = f.get('nav', 100.0)
            units = float(f.get('units', 0.0))
            total_cost = float(f.get('total_cost', 0.0))
            avg = (total_cost / units) if units > 0 else 0.0
            if hasattr(self, 'fund_nav_label'):
                self.fund_nav_label.config(text=f"NAV：${nav:.4f}  手續費率：{finfo.get('fee_rate',0.0)*100:.2f}%")
            if hasattr(self, 'fund_hold_label'):
                self.fund_hold_label.config(text=f"持有單位：{units:.4f}")
            if hasattr(self, 'fund_avg_label'):
                self.fund_avg_label.config(text=f"平均成本：${avg:.4f}")
        except Exception as e:
            self.debug_log(f"update_funds_ui error: {e}")

    def _get_fund_units_from_ui(self):
        try:
            if hasattr(self, 'fund_units_var'):
                val = self.fund_units_var.get().strip()
            elif hasattr(self, 'fund_units_entry'):
                val = self.fund_units_entry.get().strip()
            else:
                return None
            if val == '':
                self.show_event_message("請輸入基金單位數！")
                return None
            units = float(val)
            if units <= 0:
                self.show_event_message("單位數需為正數！")
                return None
            return units
        except Exception:
            self.show_event_message("請輸入有效的單位數！")
            return None

    def buy_fund_from_ui(self):
        try:
            if not hasattr(self, 'fund_select_var'):
                return
            fname = self.fund_select_var.get().strip()
            if not fname or fname not in self.data.funds:
                return
            units = self._get_fund_units_from_ui()
            if units is None:
                return
            f = self.data.funds[fname]
            finfo = self.data.funds_catalog.get(fname, {})
            nav = float(f.get('nav', 100.0))
            fee_rate = float(finfo.get('fee_rate', 0.0))
            total_cost_cash = units * nav * (1.0 + fee_rate)
            if self.data.cash >= total_cost_cash:
                f['units'] = float(f.get('units', 0.0)) + units
                f['total_cost'] = float(f.get('total_cost', 0.0)) + (units * nav)
                self.data.cash -= total_cost_cash
                self.log_transaction(f"買入基金 {fname} {units:.4f} 單位，成交價 NAV ${nav:.4f}，手續費率 {fee_rate*100:.2f}% ，支出現金 ${total_cost_cash:.2f}")
                self.update_funds_ui()
                self.update_display()
            else:
                self.log_transaction(f"買入基金失敗：現金不足，需要 ${total_cost_cash:.2f}")
        except Exception as e:
            self.debug_log(f"buy_fund_from_ui error: {e}")

    def sell_fund_from_ui(self):
        try:
            if not hasattr(self, 'fund_select_var'):
                return
            fname = self.fund_select_var.get().strip()
            if not fname or fname not in self.data.funds:
                return
            units = self._get_fund_units_from_ui()
            if units is None:
                return
            f = self.data.funds[fname]
            current_units = float(f.get('units', 0.0))
            if units > current_units:
                self.log_transaction(f"賣出基金失敗：持有單位不足（持有 {current_units:.4f}）")
                return
            finfo = self.data.funds_catalog.get(fname, {})
            nav = float(f.get('nav', 100.0))
            fee_rate = float(finfo.get('fee_rate', 0.0))
            proceeds = units * nav * (1.0 - fee_rate)
            # 調整持倉與成本
            f['units'] = current_units - units
            if f['units'] <= 0:
                f['units'] = 0.0
                f['total_cost'] = 0.0
            else:
                # 成本按比例遞減
                f['total_cost'] *= f['units'] / (f['units'] + units)
            self.data.cash += proceeds
            self.log_transaction(f"賣出基金 {fname} {units:.4f} 單位，成交價 NAV ${nav:.4f}，手續費率 {fee_rate*100:.2f}% ，入帳現金 ${proceeds:.2f}")
            self.update_funds_ui()
            self.update_display()
        except Exception as e:
            self.debug_log(f"sell_fund_from_ui error: {e}")

    # --- 上班模式：工作選擇與升職 ---
    def ui_select_job(self):
        try:
            if hasattr(self, 'job_select_var'):
                name = self.job_select_var.get().strip()
                if name:
                    self.select_job(name)
        except Exception as e:
            self.debug_log(f"ui_select_job error: {e}")

    def select_job(self, name):
        return self.jobs.select_job(name)

    def promote_job(self):
        return self.jobs.promote_job()

    def update_job_ui(self):
        return self.jobs.update_job_ui()

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
        # 只顯示現有帳號的前100名（同時掃描根目錄與 saves/ 以相容新舊路徑）
        from os import listdir
        import os as _os
        usernames_valid = set([f[5:-5] for f in listdir('.') if f.startswith('save_') and f.endswith('.json')])
        save_dir = _os.path.join('.', 'saves')
        try:
            for f in listdir(save_dir):
                if f.startswith('save_') and f.endswith('.json'):
                    usernames_valid.add(f[5:-5])
        except Exception:
            pass
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