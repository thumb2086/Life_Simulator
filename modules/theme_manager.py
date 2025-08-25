import platform
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
        self.apply_light_theme()
        self.auto_switch_theme() # 初始化時啟動自動切換

    def setup_chinese_font(self):
        system = platform.system()
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
        # 現代化亮色主題
        self.style.theme_use('default')
        self.style.configure('TButton', padding=6, relief="flat", background="#e0e7ef", foreground="#222", font=("Microsoft JhengHei", 12))
        self.style.configure('TLabel', background='#f8fafc', foreground='#222', font=("Microsoft JhengHei", 12))
        self.style.configure('TFrame', background='#f8fafc')
        self.style.configure('TLabelframe', background='#f8fafc')
        self.style.configure('TLabelframe.Label', background='#f8fafc', foreground='#222', font=("Microsoft JhengHei", 12))
        self.style.configure('TEntry', fieldbackground='#ffffff', foreground='#222')
        self.style.configure('TCombobox', fieldbackground='#ffffff', foreground='#222')
        self.root.configure(bg='#f8fafc')
        # 針對 tk 元件（如 event_bar、history_text、trade_log_label）
        if hasattr(self.root, 'event_bar'):
            self.root.event_bar.config(bg='#fffbe6', fg='#b36b00')
        if hasattr(self.root, 'history_text'):
            self.root.history_text.config(bg='#ffffff', fg='#222', insertbackground='#222')
        if hasattr(self.root, 'trade_log_label'):
            self.root.trade_log_label.config(bg='#f8fafc', fg='#888')

    def apply_dark_theme(self):
        # 現代化暗色主題
        self.style.theme_use('clam')
        self.style.configure('TButton', padding=6, relief="flat", background='#23272e', foreground='#f8fafc', font=("Microsoft JhengHei", 12))
        self.style.configure('TLabel', background='#23272e', foreground='#f8fafc', font=("Microsoft JhengHei", 12))
        self.style.configure('TFrame', background='#23272e')
        self.style.configure('TLabelframe', background='#23272e')
        self.style.configure('TLabelframe.Label', background='#23272e', foreground='#f8fafc', font=("Microsoft JhengHei", 12))
        self.style.configure('TEntry', fieldbackground='#23272e', foreground='#f8fafc')
        # 修正 TCombobox 顏色
        self.style.configure('TCombobox', fieldbackground='#ececec', foreground='#222', selectbackground='#444', selectforeground='#222')
        self.root.configure(bg='#23272e')
        # 針對 tk 元件（如 event_bar、history_text、trade_log_label）
        if hasattr(self.root, 'event_bar'):
            self.root.event_bar.config(bg='#23272e', fg='#ffe066')
        if hasattr(self.root, 'history_text'):
            self.root.history_text.config(bg='#23272e', fg='#f8fafc', insertbackground='#f8fafc')
        if hasattr(self.root, 'trade_log_label'):
            self.root.trade_log_label.config(bg='#23272e', fg='#ffe066')

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