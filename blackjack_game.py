import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

# --- 遊戲邏輯核心 ---
class BlackjackLogic:
    def __init__(self):
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        
        # --- 新增：幸運值和牌的副數 ---
        self.lucky_streak = 0  # 幸運連敗計數器
        self.num_decks = 4     # 使用 4 副牌進行遊戲
        # --- 修改結束 ---

    def _create_deck(self):
        """創建指定副數的撲克牌"""
        self.deck = [(rank, suit) for _ in range(self.num_decks) for rank in self.ranks for suit in self.suits]

    def _card_value(self, card):
        """計算單張牌的點數"""
        rank = card[0]
        if rank in ['J', 'Q', 'K']:
            return 10
        if rank == 'A':
            return 11
        return int(rank)

    def calculate_hand_value(self, hand):
        """計算一手牌的總點數，並處理 Ace 的情況"""
        value = sum(self._card_value(card) for card in hand)
        num_aces = sum(1 for card in hand if card[0] == 'A')
        
        while value > 21 and num_aces > 0:
            value -= 10
            num_aces -= 1
        return value

    def _draw_card(self, is_lucky=False):
        """
        抽一張牌。如果處於幸運時刻，提高拿到好牌的機率。
        """
        if not self.deck: # 如果牌用完了就重新洗牌
            self._create_deck()
            random.shuffle(self.deck)

        # "好牌" 的定義
        good_ranks = ['10', 'J', 'Q', 'K', 'A']

        # 如果幸運值觸發，且牌堆中還有好牌
        if is_lucky and any(card[0] in good_ranks for card in self.deck):
            # 50% 的機率強制抽一張好牌
            if random.random() < 0.5:
                # 找到所有好牌的索引
                good_card_indices = [i for i, card in enumerate(self.deck) if card[0] in good_ranks]
                if good_card_indices:
                    # 隨機選一張好牌並從牌堆中移除
                    chosen_index = random.choice(good_card_indices)
                    return self.deck.pop(chosen_index)
        
        # 正常抽牌
        return self.deck.pop()


    def start_round(self):
        """開始新的一局：洗牌、發牌"""
        if len(self.deck) < 52: # 如果牌太少，就重新洗一副新牌
            self._create_deck()
            random.shuffle(self.deck)

        # 根據幸運值決定玩家第一張牌是否幸運
        is_player_lucky = self.lucky_streak >= 2 # 連敗2場後開始有幸運加成

        self.player_hand = [self._draw_card(is_lucky=is_player_lucky), self._draw_card()]
        self.dealer_hand = [self._draw_card(), self._draw_card()]

    def player_hit(self):
        """玩家要牌，也加入幸運機制"""
        is_player_lucky = self.lucky_streak >= 3 # 連敗3場後，要牌也有幸運加成
        self.player_hand.append(self._draw_card(is_lucky=is_player_lucky))
        return self.calculate_hand_value(self.player_hand) > 21

# --- UI 介面 ---
class BlackjackWindow:
    # ... (__init__, _create_widgets, _format_hand, _update_ui, _deal, _hit, _stand 維持不變) ...
    # ... 只需要修改 _end_round 來處理幸運值 ...
    def __init__(self, master, main_game):
        self.main_game = main_game
        self.logic = BlackjackLogic()
        self.bet_amount = 0

        self.window = tk.Toplevel(master)
        self.window.title("21點 (Blackjack)")
        self.window.geometry("600x480") # 稍微增加高度以容納賠率說明
        self.window.resizable(False, False)
        
        # 設定主題樣式
        style = ttk.Style(self.window)
        style.theme_use('clam')

        is_dark = self.main_game.theme.is_dark_mode
        bg_color = '#23272e' if is_dark else '#f8fafc'
        fg_color = '#f8fafc' if is_dark else '#222'
        
        self.window.configure(bg=bg_color)
        style.configure('.', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=("Microsoft JhengHei", 12))
        style.configure('TButton', font=("Microsoft JhengHei", 11))
        style.configure('TLabelframe', background=bg_color, bordercolor=fg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color, font=("Microsoft JhengHei", 12))


        self._create_widgets()
        self.window.transient(master)
        self.window.grab_set()

    def _create_widgets(self):
        # 莊家區
        dealer_frame = ttk.LabelFrame(self.window, text="莊家")
        dealer_frame.pack(pady=10, padx=10, fill="x")
        self.dealer_cards_label = ttk.Label(dealer_frame, text="", style='TLabel')
        self.dealer_cards_label.pack()
        self.dealer_score_label = ttk.Label(dealer_frame, text="分數: ?", style='TLabel')
        self.dealer_score_label.pack()

        # 玩家區
        player_frame = ttk.LabelFrame(self.window, text="玩家")
        player_frame.pack(pady=10, padx=10, fill="x")
        self.player_cards_label = ttk.Label(player_frame, text="", style='TLabel')
        self.player_cards_label.pack()
        self.player_score_label = ttk.Label(player_frame, text="分數: 0", style='TLabel')
        self.player_score_label.pack()

        # 狀態訊息
        self.status_label = ttk.Label(self.window, text="請下注後按「發牌」開始", font=("Microsoft JhengHei", 14, "bold"))
        self.status_label.pack(pady=10)

        # --- 新增：賠率說明 ---
        rules_text = "賠率：Blackjack 3:2, 一般獲勝 1:1, 平手退回本金"
        ttk.Label(self.window, text=rules_text, font=("Microsoft JhengHei", 10)).pack(pady=5)
        # --- 修改結束 ---
        
        # 控制區
        control_frame = ttk.Frame(self.window)
        control_frame.pack(pady=10)

        # 下注區
        self.bet_frame = ttk.Frame(control_frame)
        self.bet_frame.pack(side="left", padx=10)
        ttk.Label(self.bet_frame, text="賭注:").pack(side="left")
        self.bet_entry = ttk.Entry(self.bet_frame, width=10)
        self.bet_entry.pack(side="left", padx=5)
        self.bet_entry.insert(0, "100")
        self.deal_button = ttk.Button(self.bet_frame, text="發牌 (Deal)", command=self._deal)
        self.deal_button.pack(side="left")

        # 遊戲按鈕區
        self.game_buttons_frame = ttk.Frame(control_frame)
        self.hit_button = ttk.Button(self.game_buttons_frame, text="要牌 (Hit)", command=self._hit, state="disabled")
        self.hit_button.pack(side="left", padx=5)
        self.stand_button = ttk.Button(self.game_buttons_frame, text="停牌 (Stand)", command=self._stand, state="disabled")
        self.stand_button.pack(side="left", padx=5)

    def _format_hand(self, hand, is_dealer_hidden=False):
        suit_map = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
        if is_dealer_hidden:
            first_card = hand[0]
            return f"{first_card[0]}{suit_map[first_card[1]]}  [??]"
        return "  ".join(f"{card[0]}{suit_map[card[1]]}" for card in hand)

    def _update_ui(self, reveal_dealer=False):
        player_score = self.logic.calculate_hand_value(self.logic.player_hand)
        self.player_cards_label.config(text=self._format_hand(self.logic.player_hand))
        self.player_score_label.config(text=f"分數: {player_score}")

        if reveal_dealer:
            dealer_score = self.logic.calculate_hand_value(self.logic.dealer_hand)
            self.dealer_cards_label.config(text=self._format_hand(self.logic.dealer_hand))
            self.dealer_score_label.config(text=f"分數: {dealer_score}")
        else:
            first_card_score = self.logic._card_value(self.logic.dealer_hand[0])
            self.dealer_cards_label.config(text=self._format_hand(self.logic.dealer_hand, is_dealer_hidden=True))
            self.dealer_score_label.config(text=f"分數: {first_card_score}")
        self.window.update_idletasks()

    def _deal(self):
        try:
            self.bet_amount = int(self.bet_entry.get())
            if self.bet_amount <= 0:
                messagebox.showwarning("錯誤", "賭注必須是正整數！", parent=self.window)
                return
            if self.main_game.data.cash < self.bet_amount:
                messagebox.showwarning("現金不足", f"你的現金不足 ${self.bet_amount}", parent=self.window)
                return
        except ValueError:
            messagebox.showwarning("錯誤", "請輸入有效的數字賭注！", parent=self.window)
            return

        self.main_game.data.cash -= self.bet_amount
        self.main_game.log_transaction(f"21點下注 ${self.bet_amount}")
        self.main_game.update_display()
        
        self.logic.start_round()
        self._update_ui()
        
        self.status_label.config(text="輪到你了。要牌或停牌？")
        self.bet_frame.pack_forget()
        self.game_buttons_frame.pack(side="left", padx=10)
        self.hit_button.config(state="normal")
        self.stand_button.config(state="normal")

        player_score = self.logic.calculate_hand_value(self.logic.player_hand)
        dealer_score = self.logic.calculate_hand_value(self.logic.dealer_hand)
        
        if player_score == 21:
            self._update_ui(reveal_dealer=True)
            if dealer_score == 21:
                self._end_round("push", "雙方都是Blackjack！平手。")
            else:
                self._end_round("player_blackjack", "Blackjack! 贏得 1.5 倍獎金！")
                
    def _hit(self):
        if self.logic.player_hit():
            self._update_ui()
            self._end_round("dealer_win", "你爆了！莊家獲勝。")
        else:
            self._update_ui()

    def _stand(self):
        self.hit_button.config(state="disabled")
        self.stand_button.config(state="disabled")
        
        self._update_ui(reveal_dealer=True)
        self.status_label.config(text="莊家回合...")
        self.window.update_idletasks()
        time.sleep(1)

        dealer_score = self.logic.calculate_hand_value(self.logic.dealer_hand)
        while dealer_score < 17:
            self.logic.dealer_hand.append(self.logic._draw_card()) # 莊家正常抽牌
            dealer_score = self.logic.calculate_hand_value(self.logic.dealer_hand)
            self._update_ui(reveal_dealer=True)
            time.sleep(1)

        if dealer_score > 21:
            self._end_round("player_win", "莊家爆了！你贏了！")
        else:
            player_score = self.logic.calculate_hand_value(self.logic.player_hand)
            if player_score > dealer_score:
                self._end_round("player_win", "你贏了！")
            elif dealer_score > player_score:
                self._end_round("dealer_win", "莊家獲勝。")
            else:
                self._end_round("push", "平手！")


    def _end_round(self, result, message):
        net_winnings = 0
        total_payout = 0

        if result == "player_win":
            net_winnings = self.bet_amount
            total_payout = self.bet_amount * 2
            self.logic.lucky_streak = 0  # 贏了，重置幸運值
        elif result == "player_blackjack":
            net_winnings = int(self.bet_amount * 1.5)
            total_payout = self.bet_amount + net_winnings
            self.logic.lucky_streak = 0  # 贏了，重置幸運值
        elif result == "push":
            net_winnings = 0
            total_payout = self.bet_amount
            # 平手不清空幸運值
        else: # dealer_win or player_bust
            net_winnings = -self.bet_amount
            total_payout = 0
            self.logic.lucky_streak += 1 # 輸了，增加幸運值
        
        self.main_game.data.cash += total_payout
        
        if net_winnings > 0:
            self.main_game.log_transaction(f"21點獲勝，淨賺 ${net_winnings:,.2f}")
        elif net_winnings == 0:
            self.main_game.log_transaction(f"21點平手，退回本金 ${self.bet_amount:,.2f}")
        else:
            self.main_game.log_transaction(f"21點失敗，輸了 ${self.bet_amount:,.2f}")
        
        self.status_label.config(text=message + " 請下新賭注。")
        self.main_game.update_display()
        
        self.hit_button.config(state="disabled")
        self.stand_button.config(state="disabled")
        self.game_buttons_frame.pack_forget()
        self.bet_frame.pack(side="left", padx=10)