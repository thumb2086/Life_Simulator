# 新股票銀行遊戲

這是一個結合股票交易、銀行理財和小遊戲的模擬經營遊戲。玩家可以透過存款、貸款、股票交易等多種方式來增加資產，並挑戰各種成就。

## 功能特點

### 🏦 銀行系統
- 存款/提款功能
- 貸款系統（基於資產的貸款額度）
- 自動計算利息（存款和貸款）

### 📈 股票交易
- 多檔股票選擇（科技業、一級產業、服務業）
- 即時股價走勢圖
- 股票配息機制
- 買賣紀錄追蹤

### 🎮 娛樂功能
- 拉霸機小遊戲
- 21點遊戲（開發中）
- 成就系統
- 排行榜系統

### 🌙 其他特色
- 主題切換（明亮/暗色）
- 交易歷史記錄
- 隨機事件系統
- 自動存檔功能

## 安裝需求

- Python 3.6+
- tkinter（Python 的 GUI 庫）
- matplotlib（繪製股票圖表）
- 其他依賴套件（請見 requirements.txt）

## 開始遊戲

1. 確保已安裝所有需要的 Python 套件
2. 執行 main.py：
```bash
python main.py
```

## 遊戲玩法

1. **開始遊戲**
   - 輸入帳號進行登入
   - 新帳號會獲得起始資金 $1,000

2. **基本操作**
   - 在銀行分頁進行存款、提款、貸款操作
   - 在各產業分頁進行股票買賣
   - 觀察股價走勢進行交易決策
   - 留意股票配息時間

3. **進階玩法**
   - 使用貸款槓桿操作（注意風險）
   - 透過股票配息獲取被動收入
   - 挑戰各種成就
   - 爭取排行榜名次

## 檔案結構

- `main.py`: 遊戲主程式
- `bank_game.py`: 遊戲核心邏輯
- `game_data.py`: 遊戲資料結構
- `ui_sections.py`: UI 介面元件
- `events.py`: 隨機事件系統
- `achievements.py`: 成就系統
- `leaderboard.py`: 排行榜功能
- `slot_machine.py`: 拉霸機遊戲
- `theme_manager.py`: 主題管理

## 版本更新

### v1.0
- 基礎銀行功能
- 股票交易系統
- 成就和排行榜
- 拉霸機小遊戲

### 開發中功能
- 21點遊戲
- 更多股票分析工具
- 更多隨機事件
- 更多成就挑戰

## 問題回報

如發現任何問題或有功能建議，請聯繫開發者。

## 作者

大拇哥

## 授權

本專案僅供學習使用，非商業用途。

---

## 架構與模組化總覽（v1.1）

為了提升可維護性與效能，專案已逐步模組化，將原本集中於 `BankGame` 的邏輯拆到對應的 Manager：

- `modules/bank_game.py`：核心遊戲流程與統籌排程（unified timer、UI 初始化、事件、持久化）
- `modules/dividend_manager.py`：股利與 DRIP 再投資的每日處理（`DividendManager.process_daily()`）
- `modules/crypto_manager.py`：加密貨幣 UI 與每日邏輯（`CryptoManager.on_daily_tick()`）
- `modules/job_manager.py`：工作系統與相關 UI/邏輯
- `modules/store_expenses.py`：商店與支出管理（新增/刪除/訂閱服務）
- `modules/reports_charts.py`：報表與圖表更新（集中 Matplotlib 更新）
- `modules/theme_manager.py`：主題/樣式統一（明亮/暗色、ttk 風格）
- `modules/logger.py`：統一日誌 `GameLogger`，避免使用 `print`
- `modules/config.py`：集中常數設定（計時器、加密貨幣參數等）

此設計能讓各職責獨立、易於維護與測試，並降低 `BankGame` 的複雜度。

## 設定與常數（`modules/config.py`）

集中遊戲中常見的參數，便於調整與一致性：

- 計時器（毫秒）
  - `UNIFIED_TICK_MS`：主迴圈節拍
  - `TIME_LABEL_MS`：時鐘標籤更新頻率
  - `LEADERBOARD_REFRESH_MS`：排行榜刷新間隔
  - `PERSIST_DEBOUNCE_MS`：存檔/排行榜的延遲合併寫入（防抖）
- 加密貨幣
  - `BTC_VOLATILITY`：每日高斯波動（標準差）
  - `BTC_MIN_PRICE`：最低價格下限
  - `CRYPTO_MINED_PER_HASHRATE`：每回合每單位算力的產出量

所有計時器與加密參數已於程式中引用此設定，避免「魔術數字」。

## 計時器與效能優化

- 統一計時器：`BankGame.unified_timer()` 以 `UNIFIED_TICK_MS` 節拍執行，集中處理每日/每 N 秒的任務。
- UI 防抖：新增 `BankGame.schedule_ui_update()`，將頻繁的 UI 刷新合併，避免 UI thrash。
- I/O 防抖：`BankGame.schedule_persist()` 改為延遲合併寫入（排行榜與存檔），間隔由 `PERSIST_DEBOUNCE_MS` 控制。
- 圖表更新：集中於 `ReportsChartsManager`，未來可持續優化為「差異更新」以提升效能。

## 加密貨幣與股利委派

- 加密貨幣（Bitcoin）
  - 每日邏輯移至 `CryptoManager.on_daily_tick()`：價格隨機波動、礦機產出、資訊更新。
  - `BankGame.unified_timer()` 僅負責呼叫委派方法，降低耦合。
- 股利與 DRIP
  - 每日配息與再投資邏輯集中在 `DividendManager.process_daily()`。
  - 遊戲每日結束時由 `BankGame` 委派呼叫。

## 開發規範與建議

- 日誌請使用 `GameLogger`（`self.debug_log()` / `self.log_transaction()`），避免直接 `print`。
- 參數/常數請集中到 `modules/config.py`，避免重複與魔術數字。
- UI 風格請使用 `ThemeManager` 提供的 ttk 樣式，保持視覺一致。
- 新功能盡量以 Manager 類別封裝邏輯，`BankGame` 只做協調與排程。
- 優先考慮非同步/延遲合併策略以降低 UI 卡頓（UI 更新、存檔、排行榜）。

## 快速開始（再次整理）

1. 安裝 Python 與必要套件（`tkinter`、`matplotlib` 等）
2. 執行遊戲：
   ```bash
   python main.py
   ```
3. 登入或建立新帳號後開始遊戲。

## 版本更新

### v1.1（模組化與效能優化）
- 新增 `modules/config.py` 統一設定常數。
- 新增 `CryptoManager.on_daily_tick()` 並由 `BankGame.unified_timer()` 委派呼叫。
- 新增 `DividendManager.process_daily()` 並由 `BankGame` 委派呼叫。
- 新增 `schedule_ui_update()` 與 `schedule_persist()` 防抖優化，降低 UI 與 I/O 負擔。
- 計時器與刷新間隔改由設定檔控制，移除硬編數值。

（舊版本資訊如下）
