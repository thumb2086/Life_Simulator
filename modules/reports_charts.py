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
                # 只有在有帶標籤的圖層時才顯示圖例，避免 UserWarning
                handles, labels = ax.get_legend_handles_labels()
                if labels:
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
    # 屬性視覺化
    def create_attribute_visualization(self):
        """建立屬性趨勢圖表"""
        g = self.game
        try:
            # 建立新的圖表視窗
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # 建立屬性歷史記錄（如果不存在）
            if not hasattr(g.data, 'attribute_history'):
                g.data.attribute_history = []
                
            # 記錄當前屬性值
            current_attrs = {
                'day': getattr(g.data, 'days', 0),
                'happiness': getattr(g.data, 'happiness', 50),
                'stamina': getattr(g.data, 'stamina', 50),
                'intelligence': getattr(g.data, 'intelligence', 50),
                'diligence': getattr(g.data, 'diligence', 50),
                'charisma': getattr(g.data, 'charisma', 50),
                'experience': getattr(g.data, 'experience', 0),
                'luck_today': getattr(g.data, 'luck_today', 50)
            }
            g.data.attribute_history.append(current_attrs)
            
            # 只保留最近50天的記錄
            if len(g.data.attribute_history) > 50:
                g.data.attribute_history = g.data.attribute_history[-50:]
                
            # 建立圖表
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.patch.set_facecolor('white')
            
            days = [h['day'] for h in g.data.attribute_history]
            
            # 子圖1：快樂與體力
            ax1 = axes[0, 0]
            if g.data.attribute_history:
                happiness = [h['happiness'] for h in g.data.attribute_history]
                stamina = [h['stamina'] for h in g.data.attribute_history]
                ax1.plot(days, happiness, label='快樂', color='orange', linewidth=2)
                ax1.plot(days, stamina, label='體力', color='red', linewidth=2)
            ax1.set_title('快樂與體力趨勢', fontsize=12)
            ax1.set_xlabel('天數')
            ax1.set_ylabel('數值')
            ax1.legend()
            ax1.grid(True)
            
            # 子圖2：智力與勤奮
            ax2 = axes[0, 1]
            if g.data.attribute_history:
                intelligence = [h['intelligence'] for h in g.data.attribute_history]
                diligence = [h['diligence'] for h in g.data.attribute_history]
                ax2.plot(days, intelligence, label='智力', color='blue', linewidth=2)
                ax2.plot(days, diligence, label='勤奮', color='green', linewidth=2)
            ax2.set_title('智力與勤奮趨勢', fontsize=12)
            ax2.set_xlabel('天數')
            ax2.set_ylabel('數值')
            ax2.legend()
            ax2.grid(True)
            
            # 子圖3：魅力與運氣
            ax3 = axes[1, 0]
            if g.data.attribute_history:
                charisma = [h['charisma'] for h in g.data.attribute_history]
                luck = [h['luck_today'] for h in g.data.attribute_history]
                ax3.plot(days, charisma, label='魅力', color='purple', linewidth=2)
                ax3.plot(days, luck, label='今日運氣', color='pink', linewidth=2)
            ax3.set_title('魅力與運氣趨勢', fontsize=12)
            ax3.set_xlabel('天數')
            ax3.set_ylabel('數值')
            ax3.legend()
            ax3.grid(True)
            
            # 子圖4：經驗值
            ax4 = axes[1, 1]
            if g.data.attribute_history:
                experience = [h['experience'] for h in g.data.attribute_history]
                ax4.plot(days, experience, label='經驗值', color='brown', linewidth=2)
            ax4.set_title('經驗值趨勢', fontsize=12)
            ax4.set_xlabel('天數')
            ax4.set_ylabel('數值')
            ax4.legend()
            ax4.grid(True)
            
            plt.tight_layout()
            
            # 建立或更新視窗
            if hasattr(g, 'attribute_chart_window') and g.attribute_chart_window and g.attribute_chart_window.winfo_exists():
                # 更新現有視窗
                for widget in g.attribute_chart_window.winfo_children():
                    widget.destroy()
            else:
                # 建立新視窗
                g.attribute_chart_window = tk.Toplevel(g.root)
                g.attribute_chart_window.title("屬性趨勢圖表")
                g.attribute_chart_window.geometry("1200x800")
                
            # 添加圖表到視窗
            canvas = FigureCanvasTkAgg(fig, master=g.attribute_chart_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            
            # 添加屬性摘要資訊
            summary_frame = ttk.Frame(g.attribute_chart_window)
            summary_frame.pack(fill=tk.X, padx=10, pady=5)
            
            current = g.data.attribute_history[-1] if g.data.attribute_history else current_attrs
            
            summary_text = f"當前屬性狀態 - 快樂: {current['happiness']:.1f}, 體力: {current['stamina']:.1f}, 智力: {current['intelligence']:.1f}, 勤奮: {current['diligence']:.1f}, 魅力: {current['charisma']:.1f}, 運氣: {current['luck_today']:.1f}, 經驗: {current['experience']:.1f}"
            ttk.Label(summary_frame, text=summary_text, font=("Microsoft JhengHei", 10)).pack()
            
            canvas.draw()
            
        except Exception as e:
            g.debug_log(f"create_attribute_visualization error: {e}")
    
    def update_attribute_report_ui(self):
        """更新屬性報表UI"""
        g = self.game
        try:
            # 建立屬性報表區域（如果不存在）
            if not hasattr(g, 'attribute_report_frame'):
                # 在報表分頁中添加屬性報表區域
                if hasattr(g, 'report_tab'):
                    attr_frame = ttk.LabelFrame(g.report_tab, text="屬性報表", padding="10")
                    attr_frame.pack(fill=tk.X, pady=10, padx=10)
                    g.attribute_report_frame = attr_frame
                    
                    # 屬性數值顯示
                    attr_display = ttk.Frame(attr_frame)
                    attr_display.pack(fill=tk.X, pady=5)
                    
                    g.attribute_labels = {}
                    attributes = [
                        ('快樂', 'happiness'),
                        ('體力', 'stamina'), 
                        ('智力', 'intelligence'),
                        ('勤奮', 'diligence'),
                        ('魅力', 'charisma'),
                        ('經驗', 'experience'),
                        ('今日運氣', 'luck_today')
                    ]
                    
                    for i, (name, attr) in enumerate(attributes):
                        row = i // 4
                        col = i % 4
                        
                        frame = ttk.Frame(attr_display)
                        frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')
                        
                        ttk.Label(frame, text=f"{name}:", font=("Microsoft JhengHei", 10)).pack(side=tk.LEFT)
                        label = ttk.Label(frame, text="0", font=("Microsoft JhengHei", 10, "bold"))
                        label.pack(side=tk.LEFT, padx=(5, 0))
                        g.attribute_labels[attr] = label
                    
                    # 屬性趨勢按鈕
                    ttk.Button(attr_frame, text="查看屬性趨勢圖表", 
                             command=self.create_attribute_visualization).pack(pady=10)
            
            # 更新屬性數值
            if hasattr(g, 'attribute_labels'):
                for attr, label in g.attribute_labels.items():
                    value = getattr(g.data, attr, 0)
                    if attr == 'experience':
                        display_value = f"{value:.1f}"
                    else:
                        display_value = f"{value:.1f}"
                    label.config(text=display_value)
                    
        except Exception as e:
            g.debug_log(f"update_attribute_report_ui error: {e}")
