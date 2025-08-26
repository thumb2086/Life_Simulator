from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame


class ReportsChartsManager:
    def __init__(self, game: 'BankGame'):
        self.game = game

    # 報表 UI 更新（移自 BankGame.update_report_ui）
    def update_report_ui(self):
        g = self.game
        try:
            incomes = getattr(g.data, 'income_history', []) or []
            expenses = getattr(g.data, 'expense_history', []) or []
            today = getattr(g.data, 'days', 0)

            # 彙總每日收入/支出
            inc_by_day = {}
            for r in incomes:
                try:
                    d = int(r.get('day', 0))
                    inc_by_day[d] = inc_by_day.get(d, 0.0) + float(r.get('net', 0.0))
                except Exception:
                    pass
            exp_by_day = {}
            for r in expenses:
                try:
                    d = int(r.get('day', 0))
                    exp_by_day[d] = exp_by_day.get(d, 0.0) + float(r.get('amount', 0.0))
                except Exception:
                    pass

            days = sorted(set(list(inc_by_day.keys()) + list(exp_by_day.keys())))

            def sum_range(dct, start_day, end_day):
                total = 0.0
                for d, v in dct.items():
                    if start_day <= d <= end_day:
                        total += float(v)
                return total

            inc_today = sum_range(inc_by_day, today, today)
            exp_today = sum_range(exp_by_day, today, today)
            inc_7 = sum_range(inc_by_day, max(0, today - 6), today)
            exp_7 = sum_range(exp_by_day, max(0, today - 6), today)
            inc_30 = sum_range(inc_by_day, max(0, today - 29), today)
            exp_30 = sum_range(exp_by_day, max(0, today - 29), today)

            # 更新摘要標籤
            if hasattr(g, 'report_income_summary_label') and g.report_income_summary_label is not None:
                g.report_income_summary_label.config(
                    text=f"收入：今日 ${inc_today:.2f}｜近7天 ${inc_7:.2f}｜近30天 ${inc_30:.2f}"
                )
            if hasattr(g, 'report_expense_summary_label') and g.report_expense_summary_label is not None:
                g.report_expense_summary_label.config(
                    text=f"支出：今日 ${exp_today:.2f}｜近7天 ${exp_7:.2f}｜近30天 ${exp_30:.2f}"
                )
            if hasattr(g, 'report_net_summary_label') and g.report_net_summary_label is not None:
                net_today = inc_today - exp_today
                net_7 = inc_7 - exp_7
                net_30 = inc_30 - exp_30
                g.report_net_summary_label.config(
                    text=f"淨額：今日 ${net_today:.2f}｜近7天 ${net_7:.2f}｜近30天 ${net_30:.2f}"
                )

            # 畫每日趨勢
            if hasattr(g, 'report_ax') and hasattr(g, 'report_canvas') and g.report_ax is not None:
                ax = g.report_ax
                ax.clear()
                ax.set_facecolor('white')
                if days:
                    inc_series = [inc_by_day.get(d, 0.0) for d in days]
                    exp_series = [exp_by_day.get(d, 0.0) for d in days]
                    ax.plot(days, inc_series, label='收入', color='green', linewidth=2)
                    ax.plot(days, exp_series, label='支出', color='red', linewidth=2)
                ax.set_title("收入 vs 支出（每日）")
                ax.set_xlabel("天數")
                ax.set_ylabel("金額")
                ax.grid(True, linestyle='--', alpha=0.3)
                ax.legend(loc='upper left')
                try:
                    g.report_fig.tight_layout()
                except Exception:
                    pass
                g.report_canvas.draw()
        except Exception as e:
            g.debug_log(f"update_report_ui error: {e}")

    # 股票圖表重繪（移自 BankGame.update_charts）
    def update_charts(self):
        g = self.game
        color_list = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'cyan', 'magenta', 'gray']
        stock_codes = list(g.data.stocks.keys())
        color_map = {code: color_list[i % len(color_list)] for i, code in enumerate(stock_codes)}
        # 只處理有初始化圖表元件的股票
        t0 = time.perf_counter()
        updated = 0
        skipped = 0
        for k in g.axes.keys():
            if k not in g.data.stocks:
                continue
            stock = g.data.stocks[k]
            try:
                ax = g.axes[k]
                canvas = g.canvases[k]
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
                range_val = g.chart_ranges[k].get()
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
                g.debug_log(f"股票圖表更新失敗: {k}, 錯誤: {e}")
        dt = (time.perf_counter() - t0) * 1000
        g.debug_log(f"update_charts: updated={updated}, skipped={skipped}, {dt:.1f} ms")
