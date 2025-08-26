import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from tkinter import ttk
import datetime

class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.is_dark_mode = False
        self.style = ttk.Style()
        self.setup_chinese_font()
        # 顏色主題（基礎色票）
        self.palette_light = {
            'bg': '#f8fafc',
            'fg': '#1f2937',
            'muted': '#6b7280',
            'panel': '#ffffff',
            'primary': '#3b82f6',
            'primary_hover': '#2563eb',
            'accent': '#10b981',
            'danger': '#ef4444',
            'warning_bg': '#fff7ed',
            'warning_fg': '#b45309',
            'input_bg': '#ffffff',
            'border': '#e5e7eb',
        }
        self.palette_dark = {
            'bg': '#0f172a',
            'fg': '#e5e7eb',
            'muted': '#94a3b8',
            'panel': '#111827',
            'primary': '#60a5fa',
            'primary_hover': '#3b82f6',
            'accent': '#34d399',
            'danger': '#f87171',
            'warning_bg': '#1f2937',
            'warning_fg': '#fde68a',
            'input_bg': '#111827',
            'border': '#1f2937',
        }
        self.apply_light_theme()
        self.auto_switch_theme() # 初始化時啟動自動切換

    def setup_chinese_font(self):
        # 改用微軟正黑體等常見字型
        noto_fonts = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei', 'sans-serif']
        for font in noto_fonts:
            try:
                plt.rcParams['font.family'] = [font]
                break
            except Exception:
                continue
        plt.rcParams['axes.unicode_minus'] = False
        fm.fontManager.ttflist

    def apply_light_theme(self):
        p = self.palette_light
        # 現代化亮色主題
        self.style.theme_use('clam')
        # 通用元件
        self.style.configure('TFrame', background=p['bg'])
        self.style.configure('TLabelframe', background=p['bg'], bordercolor=p['border'])
        self.style.configure('TLabelframe.Label', background=p['bg'], foreground=p['fg'], font=("Microsoft JhengHei", 12, 'bold'))
        self.style.configure('TLabel', background=p['bg'], foreground=p['fg'], font=("Microsoft JhengHei", 12))
        # Header 樣式
        self.style.configure('Header.TLabel', background=p['bg'], foreground=p['fg'], font=("Microsoft JhengHei", 18, 'bold'))
        self.style.configure('Subtle.TLabel', background=p['bg'], foreground=p['muted'])
        self.style.configure('Cash.TLabel', background=p['bg'], foreground='#16a34a', font=("Microsoft JhengHei", 16, 'bold'))
        # Button 樣式
        self.style.configure('TButton', padding=8, relief='flat', background=p['panel'], foreground=p['fg'], font=("Microsoft JhengHei", 12))
        self.style.map('TButton', background=[('active', p['border'])])
        self.style.configure('Primary.TButton', padding=8, relief='flat', background=p['primary'], foreground='#ffffff')
        self.style.map('Primary.TButton', background=[('active', p['primary_hover'])])
        self.style.configure('Danger.TButton', padding=8, relief='flat', background=p['danger'], foreground='#ffffff')
        # 輸入元件
        self.style.configure('TEntry', fieldbackground=p['input_bg'], foreground=p['fg'], bordercolor=p['border'], lightcolor=p['primary'])
        self.style.configure('TCombobox', fieldbackground=p['input_bg'], foreground=p['fg'], bordercolor=p['border'], lightcolor=p['primary'])
        # Notebook 樣式
        self.style.configure('TNotebook', background=p['bg'], bordercolor=p['border'])
        self.style.configure('TNotebook.Tab', padding=(14, 8), background=p['panel'], foreground=p['muted'])
        self.style.map('TNotebook.Tab', background=[('selected', p['primary'])], foreground=[('selected', '#ffffff')])
        # Root 背景
        self.root.configure(bg=p['bg'])
        # 套用至 tk 元件
        self._apply_tk_widget_colors(light=True)

    def apply_dark_theme(self):
        p = self.palette_dark
        # 現代化暗色主題
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=p['bg'])
        self.style.configure('TLabelframe', background=p['bg'], bordercolor=p['border'])
        self.style.configure('TLabelframe.Label', background=p['bg'], foreground=p['fg'], font=("Microsoft JhengHei", 12, 'bold'))
        self.style.configure('TLabel', background=p['bg'], foreground=p['fg'], font=("Microsoft JhengHei", 12))
        self.style.configure('Header.TLabel', background=p['bg'], foreground=p['fg'], font=("Microsoft JhengHei", 18, 'bold'))
        self.style.configure('Subtle.TLabel', background=p['bg'], foreground=p['muted'])
        self.style.configure('Cash.TLabel', background=p['bg'], foreground='#86efac', font=("Microsoft JhengHei", 16, 'bold'))
        self.style.configure('TButton', padding=8, relief='flat', background=p['panel'], foreground=p['fg'], font=("Microsoft JhengHei", 12))
        self.style.map('TButton', background=[('active', p['border'])])
        self.style.configure('Primary.TButton', padding=8, relief='flat', background=p['primary'], foreground='#0b1220')
        self.style.map('Primary.TButton', background=[('active', p['primary_hover'])])
        self.style.configure('Danger.TButton', padding=8, relief='flat', background=p['danger'], foreground='#0b1220')
        self.style.configure('TEntry', fieldbackground=p['input_bg'], foreground=p['fg'], bordercolor=p['border'], lightcolor=p['primary'])
        self.style.configure('TCombobox', fieldbackground=p['input_bg'], foreground=p['fg'], bordercolor=p['border'], lightcolor=p['primary'])
        self.style.configure('TNotebook', background=p['bg'], bordercolor=p['border'])
        self.style.configure('TNotebook.Tab', padding=(14, 8), background=p['panel'], foreground=p['muted'])
        self.style.map('TNotebook.Tab', background=[('selected', p['primary'])], foreground=[('selected', '#0b1220')])
        self.root.configure(bg=p['bg'])
        self._apply_tk_widget_colors(light=False)

    def auto_switch_theme(self):
        # 根據系統時間自動切換主題（18:00~6:00 為夜間模式）
        now = datetime.datetime.now().hour
        if 18 <= now or now < 6:
            if not self.is_dark_mode:
                self.is_dark_mode = True
                self.apply_dark_theme()
        else:
            if self.is_dark_mode:
                self.is_dark_mode = False
                self.apply_light_theme()
        # 每 10 分鐘自動檢查一次
        self.root.after(600000, self.auto_switch_theme)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    # 供 BankGame 在 UI 建立後呼叫，將 tk 元件也套用主題
    def apply_to_game(self, game):
        try:
            # 暴露 root 與 game 互通
            self.root.game = game
            self._apply_tk_widget_colors(light=not self.is_dark_mode)
        except Exception:
            pass

    def _apply_tk_widget_colors(self, light=True):
        p = self.palette_light if light else self.palette_dark
        root = self.root
        # event bar
        if hasattr(root, 'event_bar') and root.event_bar is not None:
            root.event_bar.config(bg=p['warning_bg'], fg=p['warning_fg'])
        # 交易歷史
        if hasattr(root, 'history_text') and root.history_text is not None:
            root.history_text.config(bg=p['panel'], fg=p['fg'], insertbackground=p['fg'])
        # 可用時套用 game 內其他 tk.Listbox/Text
        game = getattr(root, 'game', None)
        if game:
            # 支援 event_bar/history_text 定義在 game 上
            try:
                if hasattr(game, 'event_bar') and game.event_bar is not None:
                    game.event_bar.config(bg=p['warning_bg'], fg=p['warning_fg'])
            except Exception:
                pass
            try:
                if hasattr(game, 'history_text') and game.history_text is not None:
                    game.history_text.config(bg=p['panel'], fg=p['fg'], insertbackground=p['fg'])
            except Exception:
                pass
            for name in [
                'expense_listbox','business_list','inventory_list','store_subs_list','store_goods_list',
                'ach_listbox','rank_text'
            ]:
                w = getattr(game, name, None)
                try:
                    if w:
                        w.config(bg=p['panel'], fg=p['fg'])
                except Exception:
                    pass