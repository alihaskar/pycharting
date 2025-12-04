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


def generate_ohlc(n: int = 1000):
    """Generate synthetic OHLC data."""
    base = 100.0
    noise = np.random.randn(n)
    close = np.cumsum(noise) + base
    open_ = close + np.random.randn(n) * 0.5
    high = np.maximum(open_, close) + np.abs(np.random.randn(n))
    low = np.minimum(open_, close) - np.abs(np.random.randn(n))
    return open_, high, low, close


def run_demo(choice: str):
    n = 5000  # Default size
    
    open_, high, low, close = generate_ohlc(n)
    numeric_index = np.arange(n)
    
    if choice == "1":
        print("\n--- Demo: Full OHLC (Numeric Index) ---")
        plot(numeric_index, open=open_, high=high, low=low, close=close)
        
    elif choice == "2":
        print("\n--- Demo: Full OHLC (Pandas DatetimeIndex) ---")
        date_index = pd.date_range(start="2024-01-01", periods=n, freq="h")
        plot(date_index, open=open_, high=high, low=low, close=close)
        
    elif choice == "3":
        print("\n--- Demo: Full OHLC (Unix Timestamps) ---")
        # Milliseconds since epoch
        start_ts = int(time.time() * 1000)
        # 1 hour steps
        ts_index = np.array([start_ts + i * 3600000 for i in range(n)], dtype=np.int64)
        plot(ts_index, open=open_, high=high, low=low, close=close)
        
    elif choice == "4":
        print("\n--- Demo: Line Chart (Close Only) - Numeric Index ---")
        # Only passing 'close' triggers line chart mode
        plot(numeric_index, close=close)
        
    elif choice == "5":
        print("\n--- Demo: Line Chart (Close Only) - Datetime Index ---")
        date_index = pd.date_range(start="2024-01-01", periods=n, freq="h")
        plot(date_index, close=close)
    
    elif choice == "6":
        print("\n--- Demo: Single Array (Open Only) as Line ---")
        # Should treat 'open' as the main line if it's the only one
        plot(numeric_index, open=open_)

    elif choice == "7":
        print("\n--- Stress Test (1 Million Points) ---")
        n_stress = 1_000_000
        o, h, l, c = generate_ohlc(n_stress)
        idx = np.arange(n_stress)
        plot(idx, open=o, high=h, low=l, close=c)

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
