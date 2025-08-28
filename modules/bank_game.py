from ui_sections import create_header_section, create_main_tabs
from theme_manager import ThemeManager
from game_data import GameData
from slot_machine import SlotMachine
from achievements import AchievementsManager
from consumables_ui import ConsumablesUI
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
from achievement_gallery import AchievementGallery
from travel_system import TravelSystem
try:
    import requests  # optional for server sync
except Exception:  # pragma: no cover
    requests = None

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
        # 消耗品UI
        self.consumables_ui = None
        # 初始化消耗品數據
        self._init_consumables()
        # 記錄器
        self.logger = GameLogger(self)
        # 工作/薪資管理器
        self.jobs = JobManager(self)
        # 股利/DRIP 管理器
        self.dividends = DividendManager(self)
        # 調試面板
        self.debug_panel = DebugPanel(self)
        # 社交系統
        self.social_system = SocialSystem(self)
        # 房屋系統
        self.housing_system = HousingSystem(self)
        # 旅行系統
        self.travel_system = TravelSystem(self)
        # 投資組合管理器
        self.investment_portfolio = InvestmentPortfolioManager(self)
        # 教育與職業系統
        self.education_career_system = EducationCareerSystem(self)
        # 健康系統
        self.health_system = HealthSystem(self)
        # 季節系統
        self.seasonal_system = SeasonalSystem(self)
        # 成就圖鑒
        self.achievement_gallery = AchievementGallery(self)
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
        # 初始化合併寫入與 UI 防抖旗標
        self._persist_scheduled = False
        self._pending_leaderboard = False
        self._pending_save = False
        self._ui_update_scheduled = False

    # --- 生活行為 / 屬性訓練 ---
    def do_study_action(self):
        """讀書：花費 $50、-10 體力；提升 智力、勤奮、經驗、少量快樂。"""
        try:
            if not self._activity_can_do('study'):
                return
            cost_cash = 50.0
            cost_stm = 10.0
            if self.data.cash < cost_cash:
                self.log_transaction("讀書失敗：現金不足！需要 $50")
                return
            if self.data.stamina < cost_stm:
                self.log_transaction("讀書失敗：體力不足！需要 10 體力")
                return
            self.data.cash -= cost_cash
            self.data.stamina = self._clamp_attr(self.data.stamina - cost_stm)
            # 屬性成長（微幅）
            self.data.intelligence = self._clamp_attr(self.data.intelligence + 3)
            self.data.diligence = self._clamp_attr(self.data.diligence + 1)
            self.data.experience = float(self.data.experience) + 2.0
            self.data.happiness = self._clamp_attr(self.data.happiness + 1)
            self.log_transaction("進行讀書：-現金 $50、-體力 10；+智力 3、+勤奮 1、+經驗 2、+快樂 1")
            self._activity_consume('study')
            # 添加學習Buff：臨時提升智力成長
            self.data.add_buff('intelligence', 0.5, 1, '讀書學習效果')
            # 增加活動計數
            self.data.activity_study_count += 1
            self.update_display()
        except Exception as e:
            self.debug_log(f"do_study_action error: {e}")

    def do_workout_action(self):
        """健身：花費 $30、-15 體力；提升 勤奮、少量魅力與快樂。"""
        try:
            if not self._activity_can_do('workout'):
                return
            cost_cash = 30.0
            cost_stm = 15.0
            if self.data.cash < cost_cash:
                self.log_transaction("健身失敗：現金不足！需要 $30")
                return
            if self.data.stamina < cost_stm:
                self.log_transaction("健身失敗：體力不足！需要 15 體力")
                return
            self.data.cash -= cost_cash
            self.data.stamina = self._clamp_attr(self.data.stamina - cost_stm)
            # 屬性成長
            self.data.diligence = self._clamp_attr(self.data.diligence + 2)
            self.data.charisma = self._clamp_attr(self.data.charisma + 1)
            self.data.happiness = self._clamp_attr(self.data.happiness + 2)
            self.log_transaction("進行健身：-現金 $30、-體力 15；+勤奮 2、+魅力 1、+快樂 2")
            self._activity_consume('workout')
            # 添加健身Buff：臨時提升生產力
            self.data.add_buff('productivity', 0.3, 1, '健身訓練效果')
            # 增加活動計數
            self.data.activity_workout_count += 1
            self.update_display()
        except Exception as e:
            self.debug_log(f"do_workout_action error: {e}")

    def do_social_action(self):
        """社交：花費 $40、-10 體力；提升 魅力 與 快樂，少量經驗。"""
        try:
            if not self._activity_can_do('social'):
                return
            cost_cash = 40.0
            cost_stm = 10.0
            if self.data.cash < cost_cash:
                self.log_transaction("社交失敗：現金不足！需要 $40")
                return
            if self.data.stamina < cost_stm:
                self.log_transaction("社交失敗：體力不足！需要 10 體力")
                return
            self.data.cash -= cost_cash
            self.data.stamina = self._clamp_attr(self.data.stamina - cost_stm)
            # 屬性成長
            self.data.charisma = self._clamp_attr(self.data.charisma + 3)
            self.data.happiness = self._clamp_attr(self.data.happiness + 3)
            self.data.experience = float(self.data.experience) + 1.0
            self.log_transaction("進行社交：-現金 $40、-體力 10；+魅力 3、+快樂 3、+經驗 1")
            self._activity_consume('social')
            # 添加社交Buff：臨時提升運氣
            self.data.add_buff('luck', 0.4, 1, '社交互動效果')
            # 增加活動計數
            self.data.activity_social_count += 1
            self.update_display()
        except Exception as e:
            self.debug_log(f"do_social_action error: {e}")

    def do_meditate_action(self):
        """冥想：免費、-8 體力；提升 快樂 與 少量勤奮，當日小幅影響運氣。"""
        try:
            if not self._activity_can_do('meditate'):
                return
            cost_stm = 8.0
            if self.data.stamina < cost_stm:
                self.log_transaction("冥想失敗：體力不足！需要 8 體力")
                return
            self.data.stamina = self._clamp_attr(self.data.stamina - cost_stm)
            # 屬性成長
            self.data.happiness = self._clamp_attr(self.data.happiness + 4)
            self.data.diligence = self._clamp_attr(self.data.diligence + 1)
            # 今日運氣微幅上調（冥想穩心）
            try:
                self.data.luck_today = self._clamp_attr(float(self.data.luck_today) + 2)
            except Exception:
                pass
            self.log_transaction("進行冥想：-體力 8；+快樂 4、+勤奮 1、今日運氣 +2")
            self._activity_consume('meditate')
            # 添加冥想Buff：臨時提升運氣
            self.data.add_buff('luck', 0.5, 2, '冥想平靜效果')
            # 增加活動計數
            self.data.activity_meditate_count += 1
            self.update_display()
        except Exception as e:
            self.debug_log(f"do_meditate_action error: {e}")

    # 將頻繁的 UI 刷新合併，避免 UI thrash
    def schedule_ui_update(self, delay_ms=0):
        try:
            if self._ui_update_scheduled:
                return
        except Exception:
            self._ui_update_scheduled = False
        def _do_update():
            self._ui_update_scheduled = False
            self.update_display()
        aid = self.root.after(delay_ms, lambda: self._run_task('ui_update', _do_update))
        self._after_map['ui_update'] = aid
        self._after_ids.append(aid)
        self._ui_update_scheduled = True
        self.debug_log(f"schedule ui_update after {delay_ms} ms -> id={aid}")

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

    def _init_consumables(self):
        """初始化消耗品數據"""
        if not hasattr(self.data, 'consumables') or not isinstance(self.data.consumables, dict):
            self.data.consumables = {
                'energy_drink': {
                    'name': '能量飲料',
                    'price': 50.0,
                    'daily_limit': 3,
                    'daily_bought': 0,
                    'description': '恢復體力，讓你更有活力',
                    'restore': {'energy': 30},
                    'important': True
                },
                'study_kit': {
                    'name': '學習包',
                    'price': 100.0,
                    'daily_limit': 2,
                    'daily_bought': 0,
                    'description': '提升學習效率',
                    'buffs': [
                        {'stat': 'intelligence', 'amount': 5, 'duration': 1},
                        {'stat': 'diligence', 'amount': 5, 'duration': 1}
                    ]
                },
                'social_card': {
                    'name': '社交卡',
                    'price': 80.0,
                    'daily_limit': 2,
                    'daily_bought': 0,
                    'description': '提升社交能力',
                    'buffs': [
                        {'stat': 'charisma', 'amount': 8, 'duration': 1},
                        {'stat': 'happiness', 'amount': 5, 'duration': 1}
                    ]
                }
            }
            
        # 確保所有消耗品都有必要的欄位
        for item_id, item in self.data.consumables.items():
            item.setdefault('daily_bought', 0)
            item.setdefault('daily_limit', 1)
            item.setdefault('important', False)
    
    def buy_store_good(self, name, price):
        return self.store.buy_store_good(name, price)
        
    def use_item(self, item_id: str) -> tuple[bool, str]:
        """
        使用指定物品
        
        Args:
            item_id: 物品ID
            
        Returns:
            tuple[bool, str]: (是否成功, 結果訊息)
        """
        try:
            # 檢查物品是否存在於庫存
            if item_id not in self.data.inventory or self.data.inventory[item_id] <= 0:
                return False, f"沒有可用的 {item_id}"
                
            # 檢查是否為有效的消耗品
            if item_id not in self.data.consumables:
                return False, f"無法使用此物品: {item_id}"
                
            item = self.data.consumables[item_id]
            item_name = item.get('name', item_id)
            
            # 處理物品效果
            success = True
            message = f"已使用 {item_name}"
            
            # 處理恢復效果
            if 'restore' in item:
                for stat, amount in item['restore'].items():
                    if hasattr(self.data, stat):
                        current = getattr(self.data, stat, 0)
                        max_val = 100  # 假設最大值為100
                        new_val = min(max_val, current + amount)
                        setattr(self.data, stat, new_val)
                        message += f"\n{stat} 恢復了 {amount} 點"
            
            # 處理增益效果
            if 'buffs' in item:
                for buff in item['buffs']:
                    stat = buff.get('stat')
                    amount = buff.get('amount', 0)
                    duration = buff.get('duration', 1)  # 默認持續1天
                    
                    if stat and hasattr(self.data, stat):
                        # 添加或更新buff
                        description = f"{item_name} 效果"
                        self.data.add_buff(stat, amount, duration, description)
                        message += f"\n{stat} 提升了 {amount} 點，持續 {duration} 天"
            
            # 從庫存中移除物品
            self.data.inventory[item_id] -= 1
            if self.data.inventory[item_id] <= 0:
                del self.data.inventory[item_id]
            
            # 更新UI和存檔
            self.update_display()
            self._pending_save = True
            self.schedule_persist()
            
            return True, message
            
        except Exception as e:
            self.debug_log(f"use_item error: {e}")
            return False, f"使用物品時發生錯誤: {str(e)}"

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
        
        # 更新Buff顯示
        if hasattr(self, 'buffs_label'):
            buffs = getattr(self.data, 'active_buffs', [])
            if buffs:
                buff_text = "當前效果: " + ", ".join([
                    f"{buff.get('description', buff['stat'])} ({buff['duration']//60}天)" 
                    for buff in buffs
                ])
                self.buffs_label.config(text=buff_text)
            else:
                self.buffs_label.config(text="當前沒有活躍效果")
                
        # 更新消耗品數量顯示
        if hasattr(self, 'consumables_label') and hasattr(self.data, 'inventory'):
            consumables = []
            for item_id, quantity in self.data.inventory.items():
                if item_id in getattr(self.data, 'consumables', {}):
                    item_name = self.data.consumables[item_id].get('name', item_id)
                    consumables.append(f"{item_name} x{quantity}")
            
            if consumables:
                self.consumables_label.config(
                    text="物品欄: " + ", ".join(consumables),
                    wraplength=400
                )
            else:
                self.consumables_label.config(text="物品欄: 空")
        self.deposit_rate_label.config(text=f"存款利率: {self.data.deposit_interest_rate*100:.2f}%")
        self.loan_rate_label.config(text=f"貸款利率: {self.data.loan_interest_rate*100:.2f}%")
        self.asset_label.config(text=f"總資產: ${self.data.total_assets():.2f}")
        # 更新遊戲日數顯示
        self.update_game_day_label()
        self.update_stock_status_labels()
        # 屬性分頁標籤更新（若存在）
        try:
            if hasattr(self, 'attr_labels') and isinstance(self.attr_labels, dict):
                al = self.attr_labels
                al.get('happiness', None) and al['happiness'].config(text=f"{self.data.happiness:.0f}")
                al.get('stamina', None) and al['stamina'].config(text=f"{self.data.stamina:.0f}")
                al.get('intelligence', None) and al['intelligence'].config(text=f"{getattr(self.data,'intelligence',0):.0f}")
                al.get('diligence', None) and al['diligence'].config(text=f"{getattr(self.data,'diligence',0):.0f}")
                al.get('charisma', None) and al['charisma'].config(text=f"{getattr(self.data,'charisma',0):.0f}")
                al.get('experience', None) and al['experience'].config(text=f"{getattr(self.data,'experience',0):.0f}")
                al.get('luck_today', None) and al['luck_today'].config(text=f"{getattr(self.data,'luck_today',50):.0f}")
        except Exception:
            pass
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
        # 更新屬性報表UI
        try:
            self.reports.update_attribute_report_ui()
        except Exception:
            pass
        self.update_charts()
        self.update_achievements_list()
        # 活動按鈕狀態/文字更新
        try:
            self.update_activity_buttons()
        except Exception:
            pass
        # 將頻繁 I/O 轉為延遲合併寫入
        if hasattr(self, 'username') and self.username:
            self._pending_leaderboard = True
        if hasattr(self, 'savefile'):
            self._pending_save = True
        self.schedule_persist()

    # --- 活動（每日上限與冷卻）---
    def _ensure_activity_structs(self):
        try:
            rules = getattr(self.data, 'activity_rules', None)
            state = getattr(self.data, 'activity_state', None)
            if not isinstance(rules, dict):
                self.data.activity_rules = {
                    'study': {'daily_max': 3, 'cooldown_days': 1},
                    'workout': {'daily_max': 3, 'cooldown_days': 1},
                    'social': {'daily_max': 3, 'cooldown_days': 1},
                    'meditate': {'daily_max': 3, 'cooldown_days': 1},
                }
                rules = self.data.activity_rules
            if not isinstance(state, dict):
                state = {}
            for k, rule in self.data.activity_rules.items():
                st = state.get(k, {})
                st.setdefault('remaining', int(rule.get('daily_max', 3)))
                st.setdefault('cd_left', 0)
                state[k] = st
            self.data.activity_state = state
        except Exception as e:
            self.debug_log(f"_ensure_activity_structs error: {e}")

    def _activity_can_do(self, key: str) -> bool:
        self._ensure_activity_structs()
        st = self.data.activity_state.get(key, {})
        cd = int(st.get('cd_left', 0))
        rem = int(st.get('remaining', 0))
        if cd > 0:
            self.log_transaction(f"{self._activity_label(key)}冷卻中：剩餘 {cd} 天")
            return False
        if rem <= 0:
            self.log_transaction(f"{self._activity_label(key)}今日次數已用盡！")
            return False
        return True

    def _activity_consume(self, key: str):
        try:
            self._ensure_activity_structs()
            rule = self.data.activity_rules.get(key, {'daily_max': 3, 'cooldown_days': 1})
            st = self.data.activity_state.get(key, {'remaining': rule.get('daily_max', 3), 'cd_left': 0})
            st['remaining'] = max(0, int(st.get('remaining', 0)) - 1)
            if st['remaining'] <= 0:
                st['cd_left'] = int(rule.get('cooldown_days', 1))
            self.data.activity_state[key] = st
        except Exception as e:
            self.debug_log(f"_activity_consume error: {e}")

    def _daily_activity_rollover(self):
        self._ensure_activity_structs()
        try:
            for k, rule in self.data.activity_rules.items():
                st = self.data.activity_state.get(k, {})
                cd = max(0, int(st.get('cd_left', 0)) - 1)
                st['cd_left'] = cd
                st['remaining'] = int(rule.get('daily_max', 3))
                self.data.activity_state[k] = st
        except Exception as e:
            self.debug_log(f"_daily_activity_rollover error: {e}")

    def _activity_label(self, key: str) -> str:
        return {
            'study': '讀書',
            'workout': '健身',
            'social': '社交',
            'meditate': '冥想',
        }.get(key, key)

    def update_activity_buttons(self):
        self._ensure_activity_structs()
        btn_map = {
            'study': getattr(self, 'btn_study', None),
            'workout': getattr(self, 'btn_workout', None),
            'social': getattr(self, 'btn_social', None),
            'meditate': getattr(self, 'btn_meditate', None),
        }
        base_text = {
            'study': '讀書（$50、-10體力）',
            'workout': '健身（$30、-15體力）',
            'social': '社交（$40、-10體力）',
            'meditate': '冥想（免費、-8體力）',
        }
        for key, btn in btn_map.items():
            if btn is None:
                continue
            st = self.data.activity_state.get(key, {})
            rule = self.data.activity_rules.get(key, {})
            rem = int(st.get('remaining', int(rule.get('daily_max', 3))))
            cd = int(st.get('cd_left', 0))
            text = f"{base_text.get(key, key)} | 次數 {rem}/{int(rule.get('daily_max', 3))}"
            if cd > 0:
                text += f" (CD:{cd}天)"
            try:
                btn.config(text=text)
                if cd > 0 or rem <= 0:
                    btn.state(['disabled'])
                else:
                    btn.state(['!disabled'])
            except Exception:
                pass

    def update_report_ui(self):
        # 委派至 ReportsChartsManager
        return self.reports.update_report_ui()

    def update_charts(self):
        # 委派至 ReportsChartsManager
        return self.reports.update_charts()

    def log_transaction(self, message):
        return self.logger.log_transaction(message)

    # --- 屬性調整輔助 ---
    def _clamp_attr(self, val: float, lo: float = 0.0, hi: float = 100.0) -> float:
        try:
            return max(lo, min(hi, float(val)))
        except Exception:
            return val

    # --- 就業/進修：提供 UI 呼叫的委派方法 ---
    def select_company(self, name: str):
        return self.jobs.select_company(name)

    def study_upgrade(self):
        return self.jobs.study_upgrade()

    def start_scheduled_tasks(self):
        self._after_ids = []
        self._after_map = {}
        self._unified_timer_tick = 0
        # 用於檢測 unified_timer 的節拍漂移（事件迴圈延遲）
        self._last_unified_at = time.perf_counter()
        aid = self.root.after(UNIFIED_TICK_MS, lambda: self._run_task('unified', self.unified_timer))
        self._after_map['unified'] = aid
        self._after_ids.append(aid)
        self.update_time()

    def unified_timer(self):
        t0 = time.perf_counter()
        try:
            self._unified_timer_tick += 1
            tick = self._unified_timer_tick
            self.debug_log(f"unified_timer tick={tick} start")
            # 依設定的節拍次數執行股票更新（支援伺服器統一價格）
            if tick % STOCK_UPDATE_TICKS == 0:
                used_server = False
                if API_BASE_URL and requests is not None:
                    try:
                        # 先請伺服器推進一次價格（需要 API Key）
                        tick_url = f"{API_BASE_URL.rstrip('/')}/stocks/tick"
                        headers = {"X-API-Key": API_KEY or ""}
                        requests.post(tick_url, headers=headers, timeout=5).raise_for_status()
                        # 取得最新價格列表
                        list_url = f"{API_BASE_URL.rstrip('/')}/stocks/list"
                        resp = requests.get(list_url, timeout=5)
                        resp.raise_for_status()
                        prices = resp.json().get('prices', {})
                        # 套用到本地股票並記錄歷史
                        for code, stock in self.data.stocks.items():
                            if code in prices:
                                p = float(prices[code])
                                stock['price'] = p
                                stock['history'].append(p)
                        # 立即刷新一次標籤與圖表，避免 UI 防抖延遲導致看起來未更新
                        try:
                            self.update_stock_status_labels()
                            # 只更新現有圖表元件，reports.update_charts 已處理可見性
                            self.reports.update_charts()
                        except Exception:
                            pass
                        used_server = True
                    except Exception as e:
                        self.debug_log(f"server price sync failed, fallback local: {e}")
                if not used_server:
                    # 本地隨機走動回退
                    for stock in self.data.stocks.values():
                        change_percent = random.gauss(0, self.data.market_volatility * self.data.get_difficulty_multiplier('stock_volatility'))
                        new_price = stock['price'] * (1 + change_percent)
                        new_price = max(10, round(new_price, 2))
                        stock['price'] = new_price
                        stock['history'].append(new_price)
                # 股票更新後，同步更新基金 NAV
                self.compute_fund_navs()
                self.schedule_ui_update()
            # 每 tick 更新 buff 持續時間（每秒）
            expired_buffs = self.data.update_buffs()
            for buff in expired_buffs:
                self.log_transaction(f"{buff['stat']} 加成效果已結束")
                
            # 每 self.DAY_TICKS 秒執行：利息、配息、礦機、每日結算（視為一天）
            if tick % self.DAY_TICKS == 0:
                # 每日重置
                try:
                    today = self.data.days + 1
                    
                    # 重置消耗品每日購買計數
                    if hasattr(self.data, 'consumables'):
                        for item_id, item in self.data.consumables.items():
                            if 'daily_bought' in item:
                                item['daily_bought'] = 0
                    
                    # 生成今日運氣（受魅力微幅影響）
                    if int(getattr(self.data, 'last_luck_day', -1)) != today:
                        base = random.gauss(50.0, 10.0)
                        adj = 0.1 * (float(getattr(self.data, 'charisma', 50)) - 50.0)
                        luck = self._clamp_attr(base + adj, 0.0, 100.0)
                        self.data.luck_today = round(luck, 0)
                        self.data.last_luck_day = today
                except Exception as e:
                    self.debug_log(f"luck roll error: {e}")
                if self.data.balance > 0:
                    interest = self.data.balance * self.data.deposit_interest_rate * self.data.get_difficulty_multiplier('salary_multiplier')
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
                        gross_base = float(job.get('salary_per_day', 0.0))
                        # 公司與學歷薪資倍率
                        comp_name = getattr(self.data, 'current_company', '一般公司')
                        comp_mult = float(getattr(self.data, 'companies_catalog', {}).get(comp_name, {}).get('salary_multiplier', 1.0))
                        edu_level = getattr(self.data, 'education_level', '高中')
                        edu_mult = float(getattr(self.data, 'education_multipliers', {}).get(edu_level, 1.0))
                        # 生產力加成（屬性 + Buff）：智力/勤奮/魅力/今日運氣，皆提供極小幅加成 + productivity buff
                        # 平衡調整：生產力加成從0.8-1.3調整為0.9-1.4，提升整體生產力
                        try:
                            intel = float(getattr(self.data, 'intelligence', 50.0))
                            dili = float(getattr(self.data, 'diligence', 50.0))
                            chrm = float(getattr(self.data, 'charisma', 50.0))
                            luck = float(getattr(self.data, 'luck_today', 50.0))
                            prod_buff = self.data.get_buff_value('productivity')
                            prod_mult = 0.9 + (intel - 50.0) / 500.0 + (dili - 50.0) / 500.0 + (chrm - 50.0) / 1000.0 + (luck - 50.0) / 1000.0 + prod_buff
                            prod_mult = max(0.9, min(1.4, prod_mult))  # 平衡調整：提高最小值和最大值
                        except Exception:
                            prod_mult = 1.0
                        gross = round(gross_base * comp_mult * edu_mult * prod_mult, 2)
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
                            self.log_transaction(
                                f"薪資入帳：毛薪 ${gross:.2f} (基礎 ${gross_base:.2f} x 公司{comp_mult:.2f} x 學歷{edu_mult:.2f} x 生產力{prod_mult:.2f})，扣稅 ${tax:.2f}，實領 ${net:.2f}"
                            )
                except Exception as e:
                    self.debug_log(f"salary payout error: {e}")
                # 進修完成檢查：若達到預定完成日，套用學歷升級
                try:
                    sip = getattr(self.data, 'study_in_progress', None)
                    if isinstance(sip, dict):
                        today = self.data.days + 1
                        finish_day = int(sip.get('finish_day', 0))
                        target = str(sip.get('target', ''))
                        if target and today >= finish_day:
                            # 完成進修：提升學歷並清除進修狀態
                            self.data.education_level = target
                            self.data.study_in_progress = None
                            self.log_transaction(f"進修完成：學歷提升為 {target}！")
                            self.show_event_message(f"進修完成！學歷提升為 {target}")
                            try:
                                self.jobs.update_job_ui()
                            except Exception:
                                pass
                            # 安排保存
                            self._pending_save = True
                except Exception as e:
                    self.debug_log(f"study finalize error: {e}")
                # 支出：到期扣款
                try:
                    freq_days = {'daily': 1, 'weekly': 7, 'monthly': 30}
                    today = self.data.days + 1
                    for exp in list(getattr(self.data, 'expenses', [])):
                        due = int(exp.get('next_due_day', today))
                        if due <= today:
                            amount = float(exp.get('amount', 0.0)) * self.data.get_difficulty_multiplier('expense_multiplier')
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
                            # 訂閱影響：僅在成功全額扣款時生效
                            try:
                                name = str(exp.get('name', ''))
                                if paid >= amount and amount > 0:
                                    effects = {
                                        'Netflix 訂閱': {'happiness': 3},
                                        'Spotify 訂閱': {'happiness': 2},
                                        '健身房會員': {'stamina': 4, 'happiness': 1},
                                    }
                                    eff = effects.get(name)
                                    if eff is not None:
                                        if 'happiness' in eff:
                                            self.data.happiness = self._clamp_attr(self.data.happiness + eff['happiness'])
                                        if 'stamina' in eff:
                                            self.data.stamina = self._clamp_attr(self.data.stamina + eff['stamina'])
                            except Exception as _:
                                pass
                            # 安排下次到期
                            interval = freq_days.get(exp.get('frequency','daily'), 1)
                            exp['next_due_day'] = today + interval
                except Exception as e:
                    self.debug_log(f"expense deduction error: {e}")
                # 一天結束後，遊戲天數 +1（固定30天/月）
                self.data.days += 1
                # 自然成長：經驗隨每日累積成長（就業+1，進修中再+1），並對快樂/體力做微幅回復/衰減（保留既有機制）
                try:
                    exp_gain = 0
                    if getattr(self.data, 'job', None):
                        exp_gain += 1
                    sip = getattr(self.data, 'study_in_progress', None)
                    if isinstance(sip, dict):
                        exp_gain += 1
                    if exp_gain > 0:
                        cur_exp = float(getattr(self.data, 'experience', 0.0))
                        self.data.experience = self._clamp_attr(cur_exp + exp_gain, 0.0, 1000.0)
                except Exception as e:
                    self.debug_log(f"exp growth error: {e}")
                # 股利與 DRIP 委派到 DividendManager
                try:
                    self.dividends.process_daily()
                except Exception as e:
                    self.debug_log(f"dividend manager error: {e}")
                # 加密貨幣每日邏輯委派到 CryptoManager（若已建立）
                try:
                    if hasattr(self, 'crypto_manager') and self.crypto_manager:
                        self.crypto_manager.on_daily_tick()
                except Exception as e:
                    self.debug_log(f"crypto manager error: {e}")
                # 創業/定投：每日處理
                try:
                    # 創業每日淨額
                    self.entre.process_daily()
                except Exception as e:
                    self.debug_log(f"auto features error: {e}")
                # 每日結束時也更新一次基金 NAV 並記錄歷史
                self.compute_fund_navs(record_history=True)
                # 房屋維護
                try:
                    maintenance_result = self.housing_system.process_maintenance()
                    if maintenance_result[0] is not None:
                        success, msg = maintenance_result
                        if success:
                            self.log_transaction(msg)
                        else:
                            self.log_transaction(f"房屋維護問題：{msg}")
                except Exception as e:
                    self.debug_log(f"housing maintenance error: {e}")
                # 更新產業景氣循環
                try:
                    self.data.update_economic_cycles()
                except Exception as e:
                    self.debug_log(f"economic cycle update error: {e}")
                try:
                    travel_result = self.travel_system.process_trip()
                    if travel_result[0] is not None:
                        success, msg = travel_result
                        if success:
                            self.log_transaction(msg)
                        else:
                            self.log_transaction(f"旅行事件：{msg}")
                except Exception as e:
                    self.debug_log(f"travel processing error: {e}")
            # 破產偵測
            self.check_bankruptcy_and_reborn()
        except Exception as e:
            self.debug_log(f"unified_timer exception: {e}")
        finally:
            dt = (time.perf_counter() - t0) * 1000
            # 檢測節拍漂移：距離上次 unified 呼叫的時間是否明顯超過 UNIFIED_TICK_MS
            now = time.perf_counter()
            delta_ms = (now - getattr(self, '_last_unified_at', now)) * 1000
            self._last_unified_at = now
            drift_ms = delta_ms - float(UNIFIED_TICK_MS)
            # 紀錄執行資訊
            try:
                ids_count = len(getattr(self, '_after_ids', []))
                map_count = len(getattr(self, '_after_map', {}))
            except Exception:
                ids_count = map_count = 0
            self.debug_log(f"unified_timer end, exec={dt:.1f} ms, delta={delta_ms:.1f} ms, drift={drift_ms:.1f} ms, after_ids={ids_count}, after_map={map_count}")
            # 重新排程下一次
            aid = self.root.after(UNIFIED_TICK_MS, lambda: self._run_task('unified', self.unified_timer))
            self._after_map['unified'] = aid
            self._after_ids.append(aid)

    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"當前時間: {current_time}")
        aid = self.root.after(TIME_LABEL_MS, lambda: self._run_task('time', self.update_time))
        self._after_map['time'] = aid
        self._after_ids.append(aid)
        self.debug_log(f"schedule time after {TIME_LABEL_MS} ms -> id={aid}")

    # --- 遊戲日數顯示 ---
    def update_game_day_label(self):
        try:
            if hasattr(self, 'game_day_label') and self.game_day_label is not None:
                days = int(getattr(self.data, 'days', 0))
                month = days // MONTH_DAYS + 1
                day_in_month = days % MONTH_DAYS + 1
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
        aid = self.root.after(LEADERBOARD_REFRESH_MS, lambda: self._run_task('leaderboard', self.start_leaderboard_refresh))
        self._after_map['leaderboard'] = aid
        if hasattr(self, '_after_ids'):
            self._after_ids.append(aid)
        self.debug_log(f"schedule leaderboard after {LEADERBOARD_REFRESH_MS} ms -> id={aid}")

    def start_event_timer(self):
        """
        Schedule the next random game event after a random delay.
        Uses Tkinter's after() and records the id for proper cleanup.
        """
        try:
            # Cancel previous scheduled event timer if any
            old_id = self._after_map.get('event')
            if old_id is not None:
                try:
                    self.root.after_cancel(old_id)
                    self.debug_log(f"after_cancel name=event id={old_id}")
                except Exception:
                    pass
        except Exception:
            pass
        # Random delay between 15s ~ 30s for events
        delay_ms = random.randint(15000, 30000)
        aid = self.root.after(delay_ms, lambda: self._run_task('event', self.trigger_event))
        self._after_map['event'] = aid
        if hasattr(self, '_after_ids'):
            self._after_ids.append(aid)
        self.debug_log(f"schedule event after {delay_ms} ms -> id={aid}")

    def update_stock_info_label(self):
        pass 

    # 將頻繁 I/O 合併並延遲寫入，降低 UI 卡頓
    def schedule_persist(self, delay_ms=PERSIST_DEBOUNCE_MS):
        # 若已存在排程，取消並重新排程（真正的 debounce：以最後一次觸發為準）
        try:
            if getattr(self, '_persist_scheduled', False):
                old_id = self._after_map.get('persist')
                if old_id is not None:
                    try:
                        self.root.after_cancel(old_id)
                        self.debug_log(f"after_cancel name=persist id={old_id}")
                    except Exception:
                        pass
        except Exception:
            self._persist_scheduled = False
        def _flush():
            self._persist_scheduled = False
            self.persist_state()
        aid = self.root.after(delay_ms, lambda: self._run_task('persist', _flush))
        self._after_map['persist'] = aid
        if hasattr(self, '_after_ids'):
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