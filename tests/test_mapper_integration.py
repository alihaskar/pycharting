"""
Integration tests for mapper module

Tests comprehensive workflows combining multiple functions:
- detect_columns() → map_columns()
- Various DataFrame sources (CSV, Excel, etc.)
- Real-world naming conventions
- Performance with large datasets
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestDetectAndMapIntegration:
    """Test integration of detect_columns() and map_columns()"""
    
    def test_detect_then_map_standard_names(self):
        """Should detect and map standard lowercase names"""
        from src.charting.mapper import detect_columns, map_columns
        
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0 + i for i in range(10)],
            'high': [105.0 + i for i in range(10)],
            'low': [99.0 + i for i in range(10)],
            'close': [103.0 + i for i in range(10)],
            'volume': [1000 + i*100 for i in range(10)]
        })
        df.set_index('timestamp', inplace=True)
        
        # Detect columns
        detected = detect_columns(df)
        assert len(detected) == 5  # open, high, low, close, volume
        
        # Map using detected columns
        # detected is {'open': 'open', 'high': 'high', ...}
        # We need to pass open='open', high='high', ...
        params = {v: k for k, v in detected.items()}  # Invert: {'open': 'open', ...}
        result = map_columns(df, **params)
        
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert len(result) == 10
    
    def test_detect_then_map_mixed_case(self):
        """Should handle mixed case column names"""
        from src.charting.mapper import detect_columns, map_columns
        
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': [100.0 + i for i in range(10)],
            'High': [105.0 + i for i in range(10)],
            'Low': [99.0 + i for i in range(10)],
            'Close': [103.0 + i for i in range(10)]
        })
        df.set_index('timestamp', inplace=True)
        
        detected = detect_columns(df)
        # Invert detected: {'Open': 'open', ...} → {'open': 'Open', ...}
        params = {v: k for k, v in detected.items()}
        result = map_columns(df, **params)
        
        assert list(result.columns) == ['open', 'high', 'low', 'close']
    
    def test_detect_then_map_abbreviations(self):
        """Should handle abbreviated column names"""
        from src.charting.mapper import detect_columns, map_columns
        
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'o': [100.0 + i for i in range(10)],
            'h': [105.0 + i for i in range(10)],
            'l': [99.0 + i for i in range(10)],
            'c': [103.0 + i for i in range(10)],
            'v': [1000 + i*100 for i in range(10)]
        })
        df.set_index('timestamp', inplace=True)
        
        detected = detect_columns(df)
        # Invert detected: {'o': 'open', ...} → {'open': 'o', ...}
        params = {v: k for k, v in detected.items()}
        result = map_columns(df, **params)
        
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']


class TestRealWorldDataFormats:
    """Test with real-world data formats and naming conventions"""
    
    @pytest.mark.parametrize("naming_style,columns", [
        ("yahoo_finance", ['Open', 'High', 'Low', 'Close', 'Volume']),
        ("alpha_vantage", ['1. open', '2. high', '3. low', '4. close', '5. volume']),
        ("binance", ['open', 'high', 'low', 'close', 'volume']),
        ("tradingview", ['Open', 'High', 'Low', 'Close', 'Volume']),
    ])
    def test_common_data_source_formats(self, naming_style, columns):
        """Should handle common data source naming conventions"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        data = {
            'timestamp': dates,
            columns[0]: [100.0, 101.0, 102.0, 103.0, 104.0],
            columns[1]: [105.0, 106.0, 107.0, 108.0, 109.0],
            columns[2]: [99.0, 100.0, 101.0, 102.0, 103.0],
            columns[3]: [103.0, 104.0, 105.0, 106.0, 107.0],
            columns[4]: [1000, 1200, 1100, 1300, 1250]
        }
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Should be able to map explicitly
        result = map_columns(
            df,
            open=columns[0],
            high=columns[1],
            low=columns[2],
            close=columns[3],
            volume=columns[4]
        )
        
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert len(result) == 5


class TestEdgeCasesIntegration:
    """Test edge cases in integrated workflows"""
    
    def test_dataframe_with_extra_indicator_columns(self):
        """Should preserve extra indicator columns"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': [100.0 + i for i in range(10)],
            'High': [105.0 + i for i in range(10)],
            'Low': [99.0 + i for i in range(10)],
            'Close': [103.0 + i for i in range(10)],
            'Volume': [1000 + i*100 for i in range(10)],
            'RSI': [50.0 + i for i in range(10)],
            'SMA_20': [101.0 + i for i in range(10)]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(
            df,
            open='Open',
            high='High',
            low='Low',
            close='Close',
            volume='Volume'
        )
        
        # Should preserve indicator columns
        assert 'RSI' in result.columns
        assert 'SMA_20' in result.columns
    
    def test_dataframe_with_nan_values(self):
        """Should handle NaN values gracefully"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=10, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': [100.0, np.nan, 102.0, 103.0, np.nan, 105.0, 106.0, 107.0, 108.0, 109.0],
            'High': [105.0, 106.0, 107.0, np.nan, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0, np.nan, 105.0, 106.0, 107.0, 108.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, np.nan, 111.0, 112.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df, open='Open', high='High', low='Low', close='Close')
        
        # Should preserve NaN values
        assert result['open'].isna().sum() == 2
        assert result['high'].isna().sum() == 1
        assert result['low'].isna().sum() == 1
        assert result['close'].isna().sum() == 1
    
    def test_dataframe_with_different_numeric_types(self):
        """Should handle int, float, float32, float64"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': np.array([100, 101, 102, 103, 104], dtype=np.int64),
            'high': np.array([105.0, 106.0, 107.0, 108.0, 109.0], dtype=np.float32),
            'low': np.array([99.0, 100.0, 101.0, 102.0, 103.0], dtype=np.float64),
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]  # Python float
        })
        df.set_index('timestamp', inplace=True)
        
        # All numeric types should work
        result = map_columns(df, open='open', high='high', low='low', close='close')
        
        assert len(result) == 5
        assert all(pd.api.types.is_numeric_dtype(result[col]) for col in result.columns)


class TestPerformance:
    """Test performance with large DataFrames"""
    
    def test_large_dataframe_10k_rows(self):
        """Should handle 10k rows efficiently"""
        from src.charting.mapper import map_columns
        import time
        
        dates = pd.date_range('2024-01-01', periods=10000, freq='1min')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': np.random.uniform(100, 200, 10000),
            'High': np.random.uniform(100, 200, 10000),
            'Low': np.random.uniform(100, 200, 10000),
            'Close': np.random.uniform(100, 200, 10000),
            'Volume': np.random.randint(1000, 10000, 10000)
        })
        df.set_index('timestamp', inplace=True)
        
        start = time.time()
        result = map_columns(df, open='Open', high='High', low='Low', close='Close', volume='Volume')
        elapsed = time.time() - start
        
        assert len(result) == 10000
        assert elapsed < 1.0  # Should complete in under 1 second
    
    def test_large_dataframe_100k_rows(self):
        """Should handle 100k rows efficiently"""
        from src.charting.mapper import map_columns
        import time
        
        dates = pd.date_range('2024-01-01', periods=100000, freq='1min')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': np.random.uniform(100, 200, 100000),
            'High': np.random.uniform(100, 200, 100000),
            'Low': np.random.uniform(100, 200, 100000),
            'Close': np.random.uniform(100, 200, 100000)
        })
        df.set_index('timestamp', inplace=True)
        
        start = time.time()
        result = map_columns(df, open='Open', high='High', low='Low', close='Close')
        elapsed = time.time() - start
        
        assert len(result) == 100000
        assert elapsed < 2.0  # Should complete in under 2 seconds
    
    def test_detect_columns_performance(self):
        """detect_columns() should be fast even with many columns"""
        from src.charting.mapper import detect_columns
        import time
        
        dates = pd.date_range('2024-01-01', periods=1000, freq='1min')
        # Create DataFrame with many indicator columns
        data = {
            'timestamp': dates,
            'open': np.random.uniform(100, 200, 1000),
            'high': np.random.uniform(100, 200, 1000),
            'low': np.random.uniform(100, 200, 1000),
            'close': np.random.uniform(100, 200, 1000),
        }
        # Add 50 indicator columns
        for i in range(50):
            data[f'indicator_{i}'] = np.random.uniform(0, 100, 1000)
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        start = time.time()
        detected = detect_columns(df)
        elapsed = time.time() - start
        
        assert len(detected) == 4  # Should find open, high, low, close
        assert elapsed < 0.1  # Should be very fast


class TestParametricNaming:
    """Parametric tests for various naming conventions"""
    
    @pytest.mark.parametrize("open_name", ['open', 'Open', 'OPEN', 'o', 'O'])
    @pytest.mark.parametrize("high_name", ['high', 'High', 'HIGH', 'h', 'H'])
    def test_various_naming_combinations(self, open_name, high_name):
        """Should handle any combination of naming styles"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            open_name: [100.0, 101.0, 102.0, 103.0, 104.0],
            high_name: [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(
            df,
            open=open_name,
            high=high_name,
            low='low',
            close='close'
        )
        
        assert list(result.columns) == ['open', 'high', 'low', 'close']
        assert len(result) == 5

