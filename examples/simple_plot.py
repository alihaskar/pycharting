import pandas as pd
import numpy as np
import charting
import os
import sys

# Setup path to data file
data_path = "data/sample.csv"
if not os.path.exists(data_path):
    data_path = "../data/sample.csv"
    if not os.path.exists(data_path):
         if os.path.exists("data/sample.csv"):
             data_path = "data/sample.csv"

if not os.path.exists(data_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "sample.csv")
    
    if not os.path.exists(data_path):
        print(f"❌ Error: Could not find sample.csv")
        print(f"   Searched in: {data_path}")
        print("   Please run from project root.")
        sys.exit(1)

print(f"📂 Loading data from {data_path}...")
df = pd.read_csv(data_path)

# Parse timestamp as index
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

print("📊 Adding technical indicators...")

# === OVERLAY INDICATORS (on price chart) ===
# Multiple Moving Averages
df['sma_10'] = df['close'].rolling(window=10).mean()
df['sma_20'] = df['close'].rolling(window=20).mean()
df['sma_50'] = df['close'].rolling(window=50).mean()
df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()

# Bollinger Bands
bb_middle = df['close'].rolling(window=20).mean()
bb_std = df['close'].rolling(window=20).std()
df['bb_upper'] = bb_middle + (bb_std * 2)
df['bb_lower'] = bb_middle - (bb_std * 2)

# === SUBPLOT INDICATORS (separate panels) ===

# RSI (Relative Strength Index)
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss.replace(0, np.inf)
df['rsi_14'] = 100 - (100 / (1 + rs))

# Stochastic Oscillator
low_14 = df['low'].rolling(window=14).min()
high_14 = df['high'].rolling(window=14).max()
df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()

# MACD
ema_12 = df['close'].ewm(span=12, adjust=False).mean()
ema_26 = df['close'].ewm(span=26, adjust=False).mean()
df['macd'] = ema_12 - ema_26
df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
df['macd_hist'] = df['macd'] - df['macd_signal']

# Volume indicator
df['volume_sma'] = df['volume'].rolling(window=20).mean()

# Drop NaN rows from indicators
df = df.dropna()

print(f"✅ Added indicators to {len(df)} data points")
print(f"   Overlays: SMA(10,20,50), EMA(9,21), Bollinger Bands")
print(f"   Subplots: RSI, Stochastic, MACD, Volume SMA")

print("\n📊 Plotting data with indicators...")
# Specify which indicators are overlays vs subplots
charting.plot(df, indicators={
    # Overlays (on price chart)
    'sma_10': True,
    'sma_20': True,
    'sma_50': True,
    'ema_9': True,
    'ema_21': True,
    'bb_upper': True,
    'bb_lower': True,
    
    # Subplots (separate panels)
    'rsi_14': False,
    'stoch_k': False,
    'stoch_d': False,
    'macd': False,
    'macd_signal': False,
    'macd_hist': False,
    'volume_sma': False,
})
