from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank_game import BankGame


class GameLogger:
    def __init__(self, game: 'BankGame'):
        self.game = game

    def debug_log(self, msg: str):
        try:
            if getattr(self.game, 'DEBUG', False) or os.environ.get('SG_DEBUG') == '1':
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[DEBUG {ts}] {msg}")
        except Exception:
            pass

    def log_transaction(self, message: str):
        g = self.game
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            g.data.transaction_history.append({'timestamp': timestamp, 'message': message})
            # 更新歷史訊息視窗（若存在）
            if hasattr(g, 'history_text') and g.history_text is not None:
                g.history_text.config(state='normal')
                g.history_text.insert('1.0', f"[{timestamp}] {message}\n")
                if int(g.history_text.index('end-1c').split('.')[0]) > 20:
                    g.history_text.delete('end-1c linestart', 'end-1c')
                g.history_text.config(state='disabled')
        except Exception:
            # 不阻斷遊戲流程
            pass
