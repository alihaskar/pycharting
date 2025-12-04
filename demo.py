"""
PyCharting Interactive Demo Suite.

This script provides multiple scenarios to demonstrate the flexibility of PyCharting:
1. Various Index Types (Numeric, Pandas Datetime, Unix Timestamps).
2. Chart Types (Candlestick vs Line).
3. Performance (Stress Test).
"""

import sys
import time
import numpy as np
import pandas as pd
from pycharting import plot, stop_server


def sma(values: np.ndarray, window: int) -> np.ndarray:
    """Calculate Simple Moving Average."""
    kernel = np.ones(window, dtype=float) / float(window)
    return np.convolve(values, kernel, mode="same")


def ema(values: np.ndarray, span: int) -> np.ndarray:
    """Calculate Exponential Moving Average."""
    alpha = 2.0 / (span + 1.0)
    out = np.empty_like(values, dtype=float)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def rsi_like(values: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate RSI-like oscillator."""
    delta = np.diff(values, prepend=values[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = sma(gain, period)
    avg_loss = sma(loss, period)
    rs = np.divide(avg_gain, avg_loss, out=np.zeros_like(avg_gain), where=avg_loss != 0)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def generate_ohlc(n: int = 1000):
    """Generate synthetic OHLC data with indicators."""
    base = 100.0
    noise = np.random.randn(n)
    close = np.cumsum(noise) + base
    open_ = close + np.random.randn(n) * 0.5
    high = np.maximum(open_, close) + np.abs(np.random.randn(n))
    low = np.minimum(open_, close) - np.abs(np.random.randn(n))
    
    # Calculate overlays
    sma_50 = sma(close, 50)
    ema_20 = ema(close, 20)
    
    # Calculate subplots
    rsi = rsi_like(close, 14)
    volume = np.abs(np.random.randn(n)) * 10000 + 5000
    
    overlays = {
        "SMA 50": sma_50,
        "EMA 20": ema_20,
    }
    
    subplots = {
        "RSI": rsi,
        "Volume": volume,
    }
    
    return open_, high, low, close, overlays, subplots


def run_demo(choice: str):
    n = 5000  # Default size
    
    open_, high, low, close, overlays, subplots = generate_ohlc(n)
    numeric_index = np.arange(n)
    
    if choice == "1":
        print("\n--- Demo: Full OHLC (Numeric Index) with Indicators ---")
        plot(numeric_index, open=open_, high=high, low=low, close=close, 
             overlays=overlays, subplots=subplots)
        
    elif choice == "2":
        print("\n--- Demo: Full OHLC (Pandas DatetimeIndex) with Indicators ---")
        date_index = pd.date_range(start="2024-01-01", periods=n, freq="h")
        plot(date_index, open=open_, high=high, low=low, close=close,
             overlays=overlays, subplots=subplots)
        
    elif choice == "3":
        print("\n--- Demo: Full OHLC (Unix Timestamps) with Indicators ---")
        # Milliseconds since epoch
        start_ts = int(time.time() * 1000)
        # 1 hour steps
        ts_index = np.array([start_ts + i * 3600000 for i in range(n)], dtype=np.int64)
        plot(ts_index, open=open_, high=high, low=low, close=close,
             overlays=overlays, subplots=subplots)
        
    elif choice == "4":
        print("\n--- Demo: Line Chart (Close Only) - Numeric Index with Indicators ---")
        # Only passing 'close' triggers line chart mode
        plot(numeric_index, close=close, overlays=overlays, subplots=subplots)
        
    elif choice == "5":
        print("\n--- Demo: Line Chart (Close Only) - Datetime Index with Indicators ---")
        date_index = pd.date_range(start="2024-01-01", periods=n, freq="h")
        plot(date_index, close=close, overlays=overlays, subplots=subplots)
    
    elif choice == "6":
        print("\n--- Demo: Single Array (Open Only) as Line with Indicators ---")
        # Should treat 'open' as the main line if it's the only one
        plot(numeric_index, open=open_, overlays=overlays, subplots=subplots)

    elif choice == "7":
        print("\n--- Stress Test (1 Million Points) with Indicators ---")
        n_stress = 1_000_000
        o, h, l, c, ovr, sub = generate_ohlc(n_stress)
        idx = np.arange(n_stress)
        plot(idx, open=o, high=h, low=l, close=c, overlays=ovr, subplots=sub)

    else:
        print("Invalid choice.")


def main():
    try:
        while True:
            print("\n" + "="*40)
            print("PyCharting Feature Demos")
            print("="*40)
            print("1. Candlesticks - Numeric Index (0, 1, 2...)")
            print("2. Candlesticks - Pandas DatetimeIndex")
            print("3. Candlesticks - Unix Timestamps (ms)")
            print("4. Line Chart   - Numeric Index (Close only)")
            print("5. Line Chart   - Datetime Index (Close only)")
            print("6. Line Chart   - Open Price only (Flexible Input)")
            print("7. Stress Test  - 1 Million Candles")
            print("0. Exit")
            print("="*40)
            
            choice = input("Select a demo (0-7): ").strip()
            
            if choice == "0":
                break
            
            run_demo(choice)
            input("\nPress Enter to return to menu (Server keeps running)...")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_server()


if __name__ == "__main__":
    main()
