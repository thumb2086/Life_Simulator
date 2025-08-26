# Centralized configuration constants for BankGame
# Timers (milliseconds)
UNIFIED_TICK_MS = 1000            # unified timer loop cadence
TIME_LABEL_MS = 1000              # clock label refresh
LEADERBOARD_REFRESH_MS = 10000    # leaderboard refresh period
PERSIST_DEBOUNCE_MS = 8000        # debounce for batched persistence (save + leaderboard)

# Crypto
BTC_VOLATILITY = 0.03             # daily gaussian sigma for BTC price movement
BTC_MIN_PRICE = 10000             # floor price to avoid collapsing to zero
CRYPTO_MINED_PER_HASHRATE = 0.01  # BTC mined per round per khashrate unit

# Stocks / Calendar
STOCK_UPDATE_TICKS = 15           # how many unified ticks per stock price update
MONTH_DAYS = 30                   # days per in-game month
