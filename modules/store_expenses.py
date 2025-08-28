from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame


class StoreExpensesManager:
    def __init__(self, game: 'BankGame'):
        self.game = game

    # --- 共用小工具：集中重複邏輯 ---
    FREQ_DAYS = {'daily': 1, 'weekly': 7, 'monthly': 30}

    def _freq_interval(self, frequency: str, default: int = 30) -> int:
        return self.FREQ_DAYS.get(frequency, default)

    def _append_expense(self, name: str, amount: float, frequency: str, today: int | None = None):
        g = self.game
        try:
            if today is None:
                today = g.data.days
            interval = self._freq_interval(frequency, 30)
            g.data.expenses.append({
                'name': name,
                'amount': float(amount),
                'frequency': frequency,
                'next_due_day': today + 1 + interval,
            })
            return True
        except Exception as e:
            g.debug_log(f"_append_expense error: {e}")
            return False

    def _is_essential(self, name: str) -> bool:
        # 與 ensure_default_expenses 中的預設清單保持一致
        essentials = {'水電瓦斯', '網路費', '手機費'}
        return name in essentials

    def _refresh_and_persist(self, update_store: bool = False, update_display: bool = False):
        g = self.game
        try:
            self.update_expenses_ui()
            if update_store:
                self.update_store_ui()
            if update_display:
                g.update_display()
            g._pending_save = True
            g.schedule_persist()
        except Exception as e:
            g.debug_log(f"_refresh_and_persist error: {e}")

    def _is_subscribed(self, name: str) -> bool:
        g = self.game
        return any(e.get('name') == name for e in getattr(g.data, 'expenses', []))

    def _format_expense_row(self, exp: dict) -> str:
        try:
            name = exp.get('name', '支出')
            amt = float(exp.get('amount', 0.0))
            freq = exp.get('frequency', 'daily')
            next_due = exp.get('next_due_day', '-')
            return f"{name} | ${amt:.2f} | {freq} | 下次第{next_due}天"
        except Exception:
            return str(exp)

    def _populate_listbox(self, widget, rows):
        g = self.game
        try:
            if not hasattr(g, widget) or getattr(g, widget) is None:
                return
            lb = getattr(g, widget)
            lb.delete(0, tk.END)
            for r in rows:
                lb.insert(tk.END, r)
        except Exception as e:
            g.debug_log(f"_populate_listbox error: {e}")

    def _get_selected_index(self, widget) -> int | None:
        g = self.game
        try:
            if not hasattr(g, widget) or getattr(g, widget) is None:
                return None
            lb = getattr(g, widget)
            sel = lb.curselection()
            if not sel:
                return None
            return sel[0]
        except Exception:
            return None

    def _notify(self, msg: str, also_event: bool = True):
        g = self.game
        try:
            g.log_transaction(msg)
            if also_event and hasattr(g, 'show_event_message'):
                g.show_event_message(msg)
        except Exception:
            pass

    # --- 支出：UI 綁定與列表更新 ---
    def update_expenses_ui(self):
        g = self.game
        try:
            if hasattr(g, 'expense_listbox'):
                g.expense_listbox.delete(0, tk.END)
                for exp in getattr(g.data, 'expenses', []):
                    g.expense_listbox.insert(tk.END, self._format_expense_row(exp))
            # 計算支出總覽（換算成每日/每週/每月）
            exps = getattr(g.data, 'expenses', [])
            daily = weekly = monthly = 0.0
            for e in exps:
                amt = float(e.get('amount', 0.0))
                freq = e.get('frequency', 'daily')
                if freq == 'daily':
                    daily += amt
                    weekly += amt * 7
                    monthly += amt * 30
                elif freq == 'weekly':
                    daily += amt / 7
                    weekly += amt
                    monthly += (amt / 7) * 30
                else:  # monthly
                    daily += amt / 30
                    weekly += (amt / 30) * 7
                    monthly += amt
            if hasattr(g, 'expense_summary_label') and g.expense_summary_label is not None:
                g.expense_summary_label.config(text=f"預估支出：每日 ${daily:.2f}｜每週 ${weekly:.2f}｜每月 ${monthly:.2f}")
        except Exception:
            pass

    def add_expense_from_ui(self):
        g = self.game
        try:
            if not (hasattr(g, 'expense_name_var') and hasattr(g, 'expense_amount_var') and hasattr(g, 'expense_freq_var')):
                return
            name = g.expense_name_var.get().strip() or '支出'
            amt_str = g.expense_amount_var.get().strip()
            try:
                amount = max(0.0, float(amt_str))
            except Exception:
                g.show_event_message("金額格式錯誤！")
                return
            freq = g.expense_freq_var.get().strip() or 'daily'
            self._append_expense(name, amount, freq)
            g.log_transaction(f"新增支出：{name} ${amount:.2f} ({freq})")
            self._refresh_and_persist()
        except Exception as e:
            g.debug_log(f"add_expense_from_ui error: {e}")

    # --- 商店與固定支出：邏輯層 ---
    def ensure_default_expenses(self):
        g = self.game
        try:
            if getattr(g.data, 'expense_defaults_added', False):
                return
            # 預設固定支出（以月計費）
            defaults = [
                {'name': '水電瓦斯', 'amount': 50.0, 'frequency': 'monthly'},
                {'name': '網路費', 'amount': 25.0, 'frequency': 'monthly'},
                {'name': '手機費', 'amount': 20.0, 'frequency': 'monthly'},
            ]
            today = g.data.days
            names_existing = {e.get('name') for e in getattr(g.data, 'expenses', [])}
            for d in defaults:
                if d['name'] in names_existing:
                    continue
                self._append_expense(d['name'], d['amount'], d['frequency'], today)
                g.log_transaction(f"加入固定支出：{d['name']} ${d['amount']:.2f} ({d['frequency']})")
            g.data.expense_defaults_added = True
            self._refresh_and_persist()
        except Exception as e:
            g.debug_log(f"ensure_default_expenses error: {e}")

    def subscribe_service(self, name, amount, frequency):
        g = self.game
        try:
            # 若已存在相同名稱的支出，則不重複新增
            for e in getattr(g.data, 'expenses', []):
                if e.get('name') == name:
                    self._notify(f"已訂閱：{name}")
                    return False
            self._append_expense(name, amount, frequency)
            g.log_transaction(f"訂閱服務：{name} ${amount:.2f} ({frequency})")
            self._refresh_and_persist(update_store=True)
            return True
        except Exception as e:
            g.debug_log(f"subscribe_service error: {e}")
            return False

    def cancel_subscription(self, name):
        g = self.game
        try:
            # 只允許取消商店中的訂閱類型
            subs = set(g.data.store_catalog.get('subscriptions', {}).keys()) if isinstance(g.data.store_catalog, dict) else set()
            if name not in subs:
                self._notify("選取的支出不是訂閱項目！")
                return False
            exps = getattr(g.data, 'expenses', [])
            idx_to_remove = next((i for i, e in enumerate(exps) if e.get('name') == name), None)
            if idx_to_remove is None:
                self._notify("找不到該訂閱於支出清單！")
                return False
            exp = exps.pop(idx_to_remove)
            g.log_transaction(f"取消訂閱：{exp.get('name','')} 每{exp.get('frequency','-')} ${float(exp.get('amount',0.0)):.2f}")
            self._refresh_and_persist(update_store=True)
            return True
        except Exception as e:
            g.debug_log(f"cancel_subscription error: {e}")
            return False

    def cancel_subscription_from_ui(self):
        g = self.game
        try:
            idx = self._get_selected_index('expense_listbox')
            if idx is None:
                self._notify("請先選擇要取消的訂閱！")
                return
            if 0 <= idx < len(g.data.expenses):
                name = g.data.expenses[idx].get('name', '')
                self.cancel_subscription(name)
        except Exception as e:
            g.debug_log(f"cancel_subscription_from_ui error: {e}")

    # --- 商店：UI 綁定 ---
    def update_store_ui(self):
        g = self.game
        try:
            # 物品清單
            if isinstance(g.data.store_catalog, dict):
                goods_rows = [
                    f"{name} | ${float(item.get('price',0.0)):.2f}"
                    for name, item in g.data.store_catalog.get('goods', {}).items()
                ]
                self._populate_listbox('store_goods_list', goods_rows)
                # 訂閱清單
                subscribed = {e.get('name') for e in getattr(g.data, 'expenses', [])}
                subs_rows = []
                for name, item in g.data.store_catalog.get('subscriptions', {}).items():
                    amt = float(item.get('amount', 0.0))
                    freq = item.get('frequency', 'monthly')
                    tag = " [已訂閱]" if name in subscribed else ""
                    subs_rows.append(f"{name} | ${amt:.2f}/{freq}{tag}")
                self._populate_listbox('store_subs_list', subs_rows)
            # 物品欄
            inv_rows = [f"{it}" for it in getattr(g.data, 'inventory', [])]
            self._populate_listbox('inventory_list', inv_rows)
        except Exception:
            pass

    def subscribe_selected_from_ui(self):
        g = self.game
        try:
            idx = self._get_selected_index('store_subs_list')
            if idx is None:
                return
            names = list(g.data.store_catalog.get('subscriptions', {}).keys())
            if 0 <= idx < len(names):
                name = names[idx]
                cfg = g.data.store_catalog['subscriptions'][name]
                self.subscribe_service(name, cfg.get('amount', 0.0), cfg.get('frequency', 'monthly'))
        except Exception as e:
            g.debug_log(f"subscribe_selected_from_ui error: {e}")

    def buy_selected_good_from_ui(self):
        g = self.game
        try:
            idx = self._get_selected_index('store_goods_list')
            if idx is None:
                return
            names = list(g.data.store_catalog.get('goods', {}).keys())
            if 0 <= idx < len(names):
                name = names[idx]
                price = g.data.store_catalog['goods'][name].get('price', 0.0)
                self.buy_store_good(name, price)
        except Exception as e:
            g.debug_log(f"buy_selected_good_from_ui error: {e}")

    def buy_store_good(self, name, price):
        g = self.game
        try:
            price = float(price)
            if g.data.cash < price:
                g.log_transaction(f"購買失敗（現金不足）：{name} 需要 ${price:.2f}")
                return False
            g.data.cash -= price
            inv = getattr(g.data, 'inventory', [])
            inv.append(name)
            g.data.inventory = inv
            g.log_transaction(f"購買物品：{name} 花費 ${price:.2f}")
            self.update_store_ui()
            g.update_display()
            g._pending_save = True
            g.schedule_persist()
            return True
        except Exception as e:
            g.debug_log(f"buy_store_good error: {e}")
            return False

    def delete_expense_from_ui(self):
        g = self.game
        try:
            idx = self._get_selected_index('expense_listbox')
            if idx is None:
                return
            if 0 <= idx < len(g.data.expenses):
                exp = g.data.expenses[idx]
                name = exp.get('name', '')
                # 若為訂閱或基本必需支出，禁止直接刪除
                subs = set(g.data.store_catalog.get('subscriptions', {}).keys()) if isinstance(g.data.store_catalog, dict) else set()
                if name in subs:
                    self._notify("訂閱無法直接刪除，請使用『取消訂閱』功能。")
                    return
                if self._is_essential(name):
                    self._notify("此為必要固定支出，無法刪除！")
                    return
                exp = g.data.expenses.pop(idx)
                g.log_transaction(f"刪除支出：{exp.get('name','支出')} ${float(exp.get('amount',0.0)):.2f}")
                self._refresh_and_persist()
        except Exception as e:
            g.debug_log(f"delete_expense_from_ui error: {e}")
