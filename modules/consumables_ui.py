import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from bank_game import BankGame

class ConsumablesUI:
    def __init__(self, game: 'BankGame', parent_frame: tk.Frame):
        self.game = game
        self.parent_frame = parent_frame
        self.tab_control = ttk.Notebook(parent_frame)
        
        # Create tabs
        self.shop_tab = ttk.Frame(self.tab_control)
        self.inventory_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.shop_tab, text='商店')
        self.tab_control.add(self.inventory_tab, text='背包')
        self.tab_control.pack(expand=1, fill='both')
        
        # Initialize tabs
        self._setup_shop_tab()
        self._setup_inventory_tab()
        
    def _setup_shop_tab(self):
        # Shop header
        ttk.Label(self.shop_tab, text="消耗品商店", font=('Microsoft JhengHei', 14, 'bold')).pack(pady=10)
        
        # Shop items frame with scrollbar
        canvas = tk.Canvas(self.shop_tab)
        scrollbar = ttk.Scrollbar(self.shop_tab, orient="vertical", command=canvas.yview)
        self.shop_frame = ttk.Frame(canvas)
        
        self.shop_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.shop_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_shop_items()
    
    def _setup_inventory_tab(self):
        ttk.Label(self.inventory_tab, text="我的背包", font=('Microsoft JhengHei', 14, 'bold')).pack(pady=10)
        
        canvas = tk.Canvas(self.inventory_tab)
        scrollbar = ttk.Scrollbar(self.inventory_tab, orient="vertical", command=canvas.yview)
        self.inv_frame = ttk.Frame(canvas)
        
        self.inv_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.inv_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_inventory()
    
    def refresh_shop_items(self):
        for widget in self.shop_frame.winfo_children():
            widget.destroy()
        
        # Add shop items
        for item_id, item in self.game.data.consumables.items():
            frame = ttk.Frame(self.shop_frame)
            frame.pack(fill='x', pady=5, padx=5)
            
            ttk.Label(frame, text=item['name'], width=15).pack(side='left')
            ttk.Label(frame, text=f"${item['price']}", width=8).pack(side='left')
            
            daily_left = max(0, item['daily_limit'] - item['daily_bought'])
            ttk.Button(
                frame, 
                text=f"購買 ({daily_left}/{item['daily_limit']})",
                command=lambda iid=item_id: self.buy_item(iid),
                state='normal' if daily_left > 0 else 'disabled'
            ).pack(side='right', padx=5)
    
    def refresh_inventory(self):
        for widget in self.inv_frame.winfo_children():
            widget.destroy()
            
        # 添加表頭
        header_frame = ttk.Frame(self.inv_frame)
        header_frame.pack(fill='x', pady=5)
        ttk.Label(header_frame, text="物品", width=25, font=('Microsoft JhengHei', 10, 'bold')).pack(side='left')
        ttk.Label(header_frame, text="數量", width=10, font=('Microsoft JhengHei', 10, 'bold')).pack(side='left')
        ttk.Label(header_frame, text="效果", width=30, font=('Microsoft JhengHei', 10, 'bold')).pack(side='left')
        
        # 添加分隔線
        ttk.Separator(self.inv_frame, orient='horizontal').pack(fill='x', pady=2)
            
        has_items = False
        inventory = getattr(self.game.data, 'inventory', {})
        consumables = getattr(self.game.data, 'consumables', {})
        
        for item_id, quantity in inventory.items():
            if quantity > 0 and item_id in consumables:
                item = consumables[item_id]
                frame = ttk.Frame(self.inv_frame)
                frame.pack(fill='x', pady=2, padx=5)
                
                # 物品名稱
                ttk.Label(frame, text=item.get('name', '未知物品'), width=25, anchor='w').pack(side='left')
                
                # 數量
                ttk.Label(frame, text=str(quantity), width=10).pack(side='left')
                
                # 效果描述
                effects = []
                if 'restore' in item:
                    for stat, amount in item['restore'].items():
                        effects.append(f"恢復{stat} {amount}點")
                if 'buffs' in item:
                    for buff in item['buffs']:
                        stat = buff.get('stat', '')
                        amount = buff.get('amount', 0)
                        duration = buff.get('duration', 1)
                        effects.append(f"{stat}+{amount} ({duration}天)")
                
                effect_text = ", ".join(effects) if effects else "無特殊效果"
                ttk.Label(frame, text=effect_text, width=30, wraplength=300, justify='left').pack(side='left')
                
                # 使用按鈕
                ttk.Button(
                    frame, 
                    text="使用",
                    command=lambda iid=item_id: self.use_item(iid),
                    style='Accent.TButton' if item.get('important', False) else ''
                ).pack(side='right', padx=5)
                
                has_items = True
                
        if not has_items:
            empty_label = ttk.Label(
                self.inv_frame, 
                text="背包是空的，去商店購買物品吧！",
                font=('Microsoft JhengHei', 12),
                foreground='gray'
            )
            empty_label.pack(pady=20, expand=True)
    
    def buy_item(self, item_id: str):
        """購買指定物品"""
        if item_id not in self.game.data.consumables:
            messagebox.showerror("購買失敗", "找不到該物品")
            return
            
        item = self.game.data.consumables[item_id]
        item_name = item.get('name', item_id)
        price = item.get('price', 0)
        
        # 檢查每日限購
        if item.get('daily_bought', 0) >= item.get('daily_limit', 1):
            messagebox.showerror("購買失敗", f"{item_name} 今日已達限購數量")
            return
            
        # 檢查金錢是否足夠
        if self.game.data.cash < price:
            messagebox.showerror("購買失敗", f"現金不足，需要 ${price:.2f}")
            return
            
        # 執行購買
        success = self.game.buy_store_good(item_name, price)
        if success:
            self.refresh_shop_items()
            self.refresh_inventory()
            messagebox.showinfo("購買成功", f"成功購買 {item_name}")
        else:
            messagebox.showerror("購買失敗", "購買過程中發生錯誤")
    
    def use_item(self, item_id: str):
        """使用指定物品"""
        success, message = self.game.use_item(item_id)
        if success:
            self.refresh_inventory()
            self.game.show_event_message(message)
            messagebox.showinfo("使用成功", message)
        else:
            messagebox.showerror("使用失敗", message)
    
    def refresh_all(self):
        self.refresh_shop_items()
        self.refresh_inventory()
