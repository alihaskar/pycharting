"""
Generate sample OHLC data for testing the charting application.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse


def generate_ohlc_data(
    start_date: str = "2024-01-01",
    periods: int = 1000,
    freq: str = "1min",
    base_price: float = 100.0,
    volatility: float = 0.02
) -> pd.DataFrame:
    """
    Generate realistic OHLC data with random walk.
    
    Args:
        start_date: Starting date for the data
        periods: Number of data points to generate
        freq: Frequency (1min, 5min, 1h, 1D, etc.)
        base_price: Starting price
        volatility: Price volatility (0.02 = 2% average movement)
        
    Returns:
        DataFrame with OHLC data
    """
    # Generate timestamps
    timestamps = pd.date_range(start=start_date, periods=periods, freq=freq)
    
    # Generate price data using random walk
    np.random.seed(42)  # For reproducibility
    
    # Random returns
    returns = np.random.normal(0, volatility, periods)
    
    # Calculate close prices
    close_prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close prices
    data = []
    for i in range(periods):
        close = close_prices[i]
        
        # Generate high/low with realistic spreads
        spread = abs(np.random.normal(0, volatility * close, 1)[0])
        high = close + abs(np.random.uniform(0, spread))
        low = close - abs(np.random.uniform(0, spread))
        
        # Open is somewhere between previous close and current range
        if i == 0:
            open_price = base_price
        else:
            # Open near previous close with some gap
            prev_close = close_prices[i-1]
            gap = np.random.normal(0, volatility * prev_close / 2)
            open_price = prev_close + gap
            
            # Ensure open is within high/low range
            open_price = np.clip(open_price, low, high)
        
        # Ensure OHLC relationships are valid
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume (higher volume on bigger moves)
        price_change = abs(close - open_price)
        base_volume = np.random.uniform(1000, 5000)
        volume_multiplier = 1 + (price_change / open_price) * 10
        volume = int(base_volume * volume_multiplier)
        
        data.append({
            'timestamp': timestamps[i],
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # Add indicators
    df = add_indicators(df)
    
    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to the OHLC data.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with added indicator columns
    """
    # RSI (Relative Strength Index) - 14 period
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # SMA (Simple Moving Average) - 20 period
    df['sma_20'] = df['close'].rolling(window=20).mean()
    
    # EMA (Exponential Moving Average) - 12 period
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    
    return df


def main():
    parser = argparse.ArgumentParser(description='Generate sample OHLC data')
    parser.add_argument('--output', '-o', default='data/sample.csv',
                      help='Output CSV file path')
    parser.add_argument('--periods', '-p', type=int, default=1000,
                      help='Number of data points to generate')
    parser.add_argument('--freq', '-f', default='1min',
                      help='Frequency (1min, 5min, 1h, 1D)')
    parser.add_argument('--start', '-s', default='2024-01-01',
                      help='Start date (YYYY-MM-DD)')
    parser.add_argument('--price', type=float, default=100.0,
                      help='Starting price')
    parser.add_argument('--volatility', '-v', type=float, default=0.02,
                      help='Volatility (0.02 = 2%%)')
    
    args = parser.parse_args()
    
    print(f"Generating {args.periods} data points...")
    print(f"Frequency: {args.freq}")
    print(f"Start date: {args.start}")
    print(f"Base price: ${args.price}")
    print(f"Volatility: {args.volatility*100}%")
    
    # Generate data
    df = generate_ohlc_data(
        start_date=args.start,
        periods=args.periods,
        freq=args.freq,
        base_price=args.price,
        volatility=args.volatility
    )
    
    # Create output directory if needed
    import os
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    
    print(f"\n✅ Generated {len(df)} rows")
    print(f"📁 Saved to: {args.output}")
    print(f"\n📊 Data Summary:")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print(f"   Volume range: {df['volume'].min():,} - {df['volume'].max():,}")
    print(f"\n   First few rows:")
    print(df.head().to_string(index=False))


if __name__ == '__main__':
    main()

