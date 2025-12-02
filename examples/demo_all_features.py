#!/usr/bin/env python3
"""
Financial Charting Tool - Complete Feature Demo
================================================

This script demonstrates ALL features of the charting library:

1. Sample OHLC data generation with multiple indicators
2. Explicit column mapping (custom column names → standard OHLC)
3. Indicator classification (overlay vs subplot)
4. Multi-subplot support (RSI, MACD, etc.)
5. Single-command chart launch

Usage:
    python examples/demo_all_features.py
    
Press Ctrl+C to stop the server when done.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from src.python_api.charting import Charting


def generate_realistic_ohlc(rows: int = 500, start_price: float = 100.0) -> pd.DataFrame:
    """
    Generate realistic OHLC data with custom column names.
    
    This simulates a scenario where your data source uses
    non-standard column names (PriceOpen, PriceHigh, etc.)
    """
    print("📊 Generating realistic OHLC data...")
    
    np.random.seed(42)
    
    # Generate timestamps
    dates = pd.date_range(start='2024-01-01', periods=rows, freq='1h')
    
    # Generate price series with trend and volatility
    trend = np.linspace(0, 0.3, rows)  # Slight upward trend
    volatility = 0.02
    returns = np.random.randn(rows) * volatility + trend / rows
    
    close_prices = start_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC with realistic intrabar movements
    df = pd.DataFrame(index=dates)
    
    # Use CUSTOM column names (not standard 'open', 'high', 'low', 'close')
    df['PriceClose'] = close_prices
    df['PriceOpen'] = df['PriceClose'].shift(1).fillna(start_price)
    
    # High/Low with random range
    range_pct = np.abs(np.random.randn(rows) * 0.01) + 0.005
    df['PriceHigh'] = df[['PriceOpen', 'PriceClose']].max(axis=1) * (1 + range_pct)
    df['PriceLow'] = df[['PriceOpen', 'PriceClose']].min(axis=1) * (1 - range_pct)
    
    # Volume with some correlation to price movement
    base_volume = 10000
    df['TradeVolume'] = (base_volume * (1 + np.abs(returns) * 10)).astype(int)
    
    print(f"   ✅ Generated {len(df)} rows with columns: {list(df.columns)}")
    return df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add various technical indicators to the DataFrame.
    
    Note: We're using the CUSTOM column names here.
    """
    print("📈 Adding technical indicators...")
    
    close = df['PriceClose']
    
    # === OVERLAY INDICATORS (displayed on main price chart) ===
    
    # Simple Moving Averages
    df['sma_20'] = close.rolling(window=20).mean()
    df['sma_50'] = close.rolling(window=50).mean()
    
    # Exponential Moving Average
    df['ema_12'] = close.ewm(span=12, adjust=False).mean()
    df['ema_26'] = close.ewm(span=26, adjust=False).mean()
    
    # Bollinger Bands
    bb_middle = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    df['bb_upper'] = bb_middle + (bb_std * 2)
    df['bb_middle'] = bb_middle
    df['bb_lower'] = bb_middle - (bb_std * 2)
    
    # === SUBPLOT INDICATORS (displayed in separate panels) ===
    
    # RSI (Relative Strength Index)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.inf)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD
    macd_line = df['ema_12'] - df['ema_26']
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    df['macd'] = macd_line
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_line - macd_signal
    
    # Stochastic Oscillator
    low_14 = df['PriceLow'].rolling(window=14).min()
    high_14 = df['PriceHigh'].rolling(window=14).max()
    df['stoch_k'] = 100 * (close - low_14) / (high_14 - low_14)
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    
    # ATR (Average True Range)
    high = df['PriceHigh']
    low = df['PriceLow']
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_14'] = tr.rolling(window=14).mean()
    
    # Drop NaN rows
    df = df.dropna()
    
    print(f"   ✅ Added indicators: SMA, EMA, Bollinger Bands, RSI, MACD, Stochastic, ATR")
    print(f"   📊 Final DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    return df


def demo_explicit_column_mapping():
    """
    Demo 1: Using explicit column mapping
    
    When your data has non-standard column names, you can
    explicitly map them to the standard OHLC format.
    """
    print("\n" + "="*60)
    print("DEMO 1: Explicit Column Mapping")
    print("="*60)
    
    # Generate data with custom column names
    df = generate_realistic_ohlc(rows=300)
    df = add_technical_indicators(df)
    
    print("\n🔧 Column names in our data:")
    print(f"   PriceOpen, PriceHigh, PriceLow, PriceClose, TradeVolume")
    print(f"   (These are NOT standard 'open', 'high', 'low', 'close', 'volume')")
    
    # Create chart with EXPLICIT column mapping
    chart = Charting(auto_open=True)
    
    url = chart.load(
        df,
        # Explicit column mapping: map custom names → standard OHLC
        open='PriceOpen',
        high='PriceHigh',
        low='PriceLow',
        close='PriceClose',
        volume='TradeVolume',
        
        # Indicator classification using dict
        # True = overlay (on main chart), False = subplot (separate panel)
        indicators={
            # Overlays (on price chart)
            'sma_20': True,
            'sma_50': True,
            'bb_upper': True,
            'bb_middle': True,
            'bb_lower': True,
            
            # Subplots (separate panels)
            'rsi_14': False,
            'macd': False,
            'stoch_k': False,
        }
    )
    
    print(f"\n✅ Chart launched at: {url}")
    return chart


def demo_auto_detection():
    """
    Demo 2: Auto-detection with standard column names
    
    If your data uses standard column names, the library
    will auto-detect them without any configuration.
    """
    print("\n" + "="*60)
    print("DEMO 2: Auto-Detection (Standard Column Names)")
    print("="*60)
    
    # Generate data with STANDARD column names
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    np.random.seed(123)
    
    df = pd.DataFrame({
        'open': 100 + np.random.randn(200).cumsum(),
        'high': 102 + np.random.randn(200).cumsum(),
        'low': 98 + np.random.randn(200).cumsum(),
        'close': 100 + np.random.randn(200).cumsum(),
        'volume': np.random.randint(1000, 10000, 200),
        'sma_20': 100 + np.random.randn(200).cumsum() * 0.9,
        'rsi_14': 50 + np.random.randn(200) * 10,
    }, index=dates)
    
    # Fix OHLC relationships
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    df['rsi_14'] = df['rsi_14'].clip(0, 100)
    
    print("\n🔧 Using standard column names:")
    print(f"   open, high, low, close, volume (auto-detected!)")
    
    # Create chart - no explicit mapping needed!
    chart = Charting(auto_open=True)
    
    url = chart.load(
        df,
        # No column mapping needed - auto-detection works!
        # Just classify indicators
        indicators={
            'sma_20': True,   # overlay
            'rsi_14': False,  # subplot
        }
    )
    
    print(f"\n✅ Chart launched at: {url}")
    return chart


def demo_multi_subplot():
    """
    Demo 3: Multiple subplots (4+ indicators)
    
    The library supports 10+ synchronized subplots
    with automatic layout management.
    """
    print("\n" + "="*60)
    print("DEMO 3: Multiple Subplots (4 indicators)")
    print("="*60)
    
    # Generate comprehensive data
    df = generate_realistic_ohlc(rows=500)
    df = add_technical_indicators(df)
    
    print("\n🔧 Creating chart with 4 subplot indicators:")
    print("   Main chart: Price + SMA + Bollinger Bands")
    print("   Subplot 1: RSI")
    print("   Subplot 2: MACD")
    print("   Subplot 3: Stochastic")
    print("   Subplot 4: ATR")
    
    chart = Charting(auto_open=True)
    
    url = chart.load(
        df,
        open='PriceOpen',
        high='PriceHigh',
        low='PriceLow',
        close='PriceClose',
        volume='TradeVolume',
        indicators={
            # Overlays
            'sma_20': True,
            'sma_50': True,
            'bb_upper': True,
            'bb_lower': True,
            
            # 4 Subplots!
            'rsi_14': False,
            'macd': False,
            'stoch_k': False,
            'atr_14': False,
        }
    )
    
    print(f"\n✅ Chart launched at: {url}")
    print("\n💡 TIP: Drag the dividers between panels to resize them!")
    return chart


def demo_using_launcher():
    """
    Demo 4: Using the launcher module (simplest approach)
    
    The launcher module provides the simplest way to
    generate data and display a chart.
    """
    print("\n" + "="*60)
    print("DEMO 4: Using the Launcher Module (Simplest)")
    print("="*60)
    
    from src.python_api.launcher import generate_sample_data, launch_chart
    
    # Generate sample data with indicators
    df = generate_sample_data(rows=400)
    
    print(f"\n📊 Generated data with columns:")
    for col in df.columns:
        print(f"   - {col}")
    
    # Launch chart with default indicator classification
    url = launch_chart(
        df,
        indicators={
            'sma_20': True,
            'sma_50': True,
            'ema_12': True,
            'bb_upper': True,
            'bb_lower': True,
            'rsi_14': False,
        }
    )
    
    print(f"\n✅ Chart launched at: {url}")
    return None  # launcher manages its own chart instance


def main():
    """
    Main entry point - run all demos or select one.
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║     Financial Charting Tool - Complete Feature Demo          ║
╠══════════════════════════════════════════════════════════════╣
║  Features demonstrated:                                      ║
║  1. Explicit column mapping (custom → standard OHLC)         ║
║  2. Auto-detection (standard column names)                   ║
║  3. Indicator classification (overlay vs subplot)            ║
║  4. Multi-subplot support (4+ synchronized panels)           ║
║  5. Single-command launcher                                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("Select a demo to run:")
    print("  1. Explicit Column Mapping")
    print("  2. Auto-Detection")
    print("  3. Multiple Subplots (4 indicators)")
    print("  4. Launcher Module (simplest)")
    print("  5. Run Demo 3 (recommended)")
    print()
    
    choice = input("Enter choice (1-5) or press Enter for Demo 3: ").strip()
    
    if choice == '1':
        chart = demo_explicit_column_mapping()
    elif choice == '2':
        chart = demo_auto_detection()
    elif choice == '3' or choice == '':
        chart = demo_multi_subplot()
    elif choice == '4':
        demo_using_launcher()
        chart = None
    elif choice == '5':
        chart = demo_multi_subplot()
    else:
        print("Invalid choice. Running Demo 3...")
        chart = demo_multi_subplot()
    
    print("\n" + "="*60)
    print("🎉 Demo running! The chart should open in your browser.")
    print("="*60)
    print("\n💡 Features to try in the chart:")
    print("   • Mouse wheel to zoom in/out")
    print("   • Click and drag to pan")
    print("   • Hover to see OHLC values")
    print("   • Drag dividers to resize panels")
    print("   • All subplots are synchronized!")
    print("\n⏹️  Press Ctrl+C to stop the server")
    
    try:
        # Keep running until Ctrl+C
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        if chart:
            chart.close()
        print("✅ Done!")


if __name__ == "__main__":
    main()

