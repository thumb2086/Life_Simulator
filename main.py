import tkinter as tk
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