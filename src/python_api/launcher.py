"""
Single-Command Launcher for Financial Charting

Task 8: Provides a simple way to generate sample data and launch a chart.

Usage:
    python -m src.python_api.launcher
    
Or in code:
    from src.python_api.launcher import main
    main()
"""
import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict, List

from .charting import Charting

logger = logging.getLogger(__name__)


def generate_sample_data(
    rows: int = 500,
    start_price: float = 100.0,
    volatility: float = 0.02,
    include_indicators: bool = True
) -> pd.DataFrame:
    """
    Generate sample OHLC data with optional indicators.
    
    Args:
        rows: Number of data points to generate
        start_price: Starting price for the series
        volatility: Price volatility factor
        include_indicators: Whether to include technical indicators
        
    Returns:
        DataFrame with OHLC data and indicators
    """
    logger.info(f"Generating {rows} rows of sample data...")
    
    # Generate timestamps
    dates = pd.date_range(
        start='2024-01-01',
        periods=rows,
        freq='1h'
    )
    
    # Generate random walk prices
    np.random.seed(42)  # For reproducibility
    returns = np.random.randn(rows) * volatility
    prices = start_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close prices
    df = pd.DataFrame(index=dates)
    df['close'] = prices
    
    # Add some noise for OHLC
    daily_range = prices * volatility * 2
    df['high'] = prices + np.abs(np.random.randn(rows) * daily_range)
    df['low'] = prices - np.abs(np.random.randn(rows) * daily_range)
    df['open'] = df['close'].shift(1).fillna(start_price)
    
    # Ensure OHLC relationships are valid
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    
    # Generate volume
    df['volume'] = np.random.randint(1000, 10000, rows)
    
    # Reorder columns
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    if include_indicators:
        # Add SMA indicators
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Add EMA
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        
        # Add RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.inf)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Add Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        logger.info("Added technical indicators: SMA, EMA, RSI, Bollinger Bands")
    
    # Drop NaN rows from indicators
    df = df.dropna()
    
    logger.info(f"Generated DataFrame with {len(df)} rows and columns: {list(df.columns)}")
    return df


def launch_chart(
    df: pd.DataFrame,
    overlays: Optional[List[str]] = None,
    subplots: Optional[List[str]] = None,
    indicators: Optional[Dict[str, bool]] = None,
    port: int = 0,
    auto_open: bool = True
) -> str:
    """
    Launch a chart from DataFrame.
    
    Args:
        df: DataFrame with OHLC data
        overlays: List of overlay indicator column names
        subplots: List of subplot indicator column names
        indicators: Dict mapping indicator names to True (overlay) or False (subplot)
        port: Port for server (0 = auto-select)
        auto_open: Whether to open browser automatically
        
    Returns:
        URL of the chart
    """
    logger.info("Launching chart...")
    
    chart = Charting(port=port, auto_open=auto_open)
    
    url = chart.load(
        df,
        overlays=overlays,
        subplots=subplots,
        indicators=indicators
    )
    
    logger.info(f"Chart launched at: {url}")
    return url


def main(
    rows: int = 500,
    auto_open: bool = True,
    indicators: Optional[Dict[str, bool]] = None
) -> str:
    """
    Main entry point: Generate sample data and launch chart.
    
    Args:
        rows: Number of data points
        auto_open: Whether to open browser
        indicators: Custom indicator classification
        
    Returns:
        URL of the chart
    """
    print("📊 Financial Charting Tool - Single Command Launcher")
    print("=" * 50)
    
    # Generate sample data
    print("📈 Generating sample OHLC data with indicators...")
    df = generate_sample_data(rows=rows)
    print(f"   Generated {len(df)} data points")
    print(f"   Columns: {list(df.columns)}")
    
    # Default indicator classification if not provided
    if indicators is None:
        indicators = {
            'sma_20': True,    # overlay
            'sma_50': True,    # overlay
            'ema_12': True,    # overlay
            'bb_upper': True,  # overlay
            'bb_middle': True, # overlay
            'bb_lower': True,  # overlay
            'rsi_14': False    # subplot
        }
    
    # Launch chart
    print("\n🚀 Launching chart...")
    url = launch_chart(
        df,
        indicators=indicators,
        auto_open=auto_open
    )
    
    print(f"\n✅ Chart is ready at: {url}")
    print("=" * 50)
    print("Press Ctrl+C to close the chart server")
    
    return url


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch financial chart')
    parser.add_argument('--rows', type=int, default=500, help='Number of data points')
    parser.add_argument('--no-open', action='store_true', help='Don\'t open browser')
    
    args = parser.parse_args()
    
    try:
        main(rows=args.rows, auto_open=not args.no_open)
        
        # Keep running until Ctrl+C
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

