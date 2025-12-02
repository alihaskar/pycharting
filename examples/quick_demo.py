#!/usr/bin/env python3
"""
Quick Demo - Runs immediately without prompts
Usage: poetry run python examples/quick_demo.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from src.python_api.charting import Charting

# Generate sample data
print("📊 Generating data...")
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=300, freq='1h')
close = 100 * np.exp(np.cumsum(np.random.randn(300) * 0.02))

df = pd.DataFrame({
    'open': np.roll(close, 1),
    'high': close * (1 + np.abs(np.random.randn(300) * 0.01)),
    'low': close * (1 - np.abs(np.random.randn(300) * 0.01)),
    'close': close,
    'volume': np.random.randint(1000, 10000, 300),
    'sma_20': pd.Series(close).rolling(20).mean(),
    'rsi_14': 50 + np.random.randn(300) * 15,
}, index=dates)
df['high'] = df[['open', 'close', 'high']].max(axis=1)
df['low'] = df[['open', 'close', 'low']].min(axis=1)
df = df.dropna()

print(f"✅ {len(df)} rows ready")

# Launch chart
print("🚀 Launching chart...")
chart = Charting()
url = chart.load(df, indicators={'sma_20': True, 'rsi_14': False})

print(f"\n📈 Chart: {url}")
print("⏹️  Press Ctrl+C to stop")

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    chart.close()
    print("\n👋 Done!")

