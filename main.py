import tkinter as tk
import os
import sys

# 確保可以匯入 modules/ 內的檔案
BASE_DIR = os.path.dirname(__file__)
MODULE_DIR = os.path.join(BASE_DIR, 'modules')
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# 設定 matplotlib 後端為 TkAgg（在其他匯入之前）
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.ioff()  # 關閉互動模式，避免阻塞

from bank_game import BankGame
from game_data import GameData


if __name__ == "__main__":
    root = tk.Tk()
    root.title("新股票銀行遊戲")
    root.geometry("1200x900")
    data = GameData()
    game = BankGame(root, data)
    root.protocol("WM_DELETE_WINDOW", game.on_close)
    root.mainloop() 