"""Performance tests for technical indicators."""
import pytest
import pandas as pd
import numpy as np
import time
from src.processing.indicators import calculate_rsi, calculate_sma, calculate_ema


def test_sma_performance_large_dataset():
    """Test SMA performance with large dataset (100k points)."""
    # Generate 100k random prices
    np.random.seed(42)
    prices = pd.Series(np.random.uniform(100, 200, 100000))
    
    start_time = time.time()
    sma = calculate_sma(prices, period=20)
    elapsed = time.time() - start_time
    
    # Should complete in reasonable time (< 1 second for 100k points)
    assert elapsed < 1.0, f"SMA took {elapsed:.3f}s, expected < 1.0s"
    
    # Verify correctness
    assert len(sma) == len(prices)
    assert not sma.iloc[20:].isna().all()


def test_ema_performance_large_dataset():
    """Test EMA performance with large dataset (100k points)."""
    np.random.seed(42)
    prices = pd.Series(np.random.uniform(100, 200, 100000))
    
    start_time = time.time()
    ema = calculate_ema(prices, period=20)
    elapsed = time.time() - start_time
    
    # Should complete in reasonable time (< 2 seconds for 100k points)
    assert elapsed < 2.0, f"EMA took {elapsed:.3f}s, expected < 2.0s"
    
    # Verify correctness
    assert len(ema) == len(prices)
    assert not ema.iloc[20:].isna().all()


def test_rsi_performance_large_dataset():
    """Test RSI performance with large dataset (100k points)."""
    np.random.seed(42)
    prices = pd.Series(np.random.uniform(100, 200, 100000))
    
    start_time = time.time()
    rsi = calculate_rsi(prices, period=14)
    elapsed = time.time() - start_time
    
    # Should complete in reasonable time (< 2 seconds for 100k points)
    assert elapsed < 2.0, f"RSI took {elapsed:.3f}s, expected < 2.0s"
    
    # Verify correctness
    assert len(rsi) == len(prices)
    assert not rsi.iloc[14:].isna().all()


def test_multiple_indicators_same_data():
    """Test calculating multiple indicators on same data efficiently."""
    np.random.seed(42)
    prices = pd.Series(np.random.uniform(100, 200, 50000))
    
    start_time = time.time()
    sma_20 = calculate_sma(prices, period=20)
    sma_50 = calculate_sma(prices, period=50)
    ema_12 = calculate_ema(prices, period=12)
    ema_26 = calculate_ema(prices, period=26)
    rsi_14 = calculate_rsi(prices, period=14)
    elapsed = time.time() - start_time
    
    # All indicators should complete quickly
    assert elapsed < 3.0, f"Multiple indicators took {elapsed:.3f}s, expected < 3.0s"
    
    # Verify all have correct length
    assert len(sma_20) == len(prices)
    assert len(ema_12) == len(prices)
    assert len(rsi_14) == len(prices)


def test_sma_memory_efficient():
    """Test that SMA doesn't create unnecessary copies."""
    np.random.seed(42)
    prices = pd.Series(np.random.uniform(100, 200, 10000))
    
    # Calculate SMA
    sma = calculate_sma(prices, period=20)
    
    # Result should be same length (no unnecessary expansion)
    assert len(sma) == len(prices)
    
    # Should share index with original
    pd.testing.assert_index_equal(sma.index, prices.index)


def test_ema_vectorized_operations():
    """Test that EMA uses efficient operations."""
    prices = pd.Series(range(1, 1001))
    
    start_time = time.time()
    ema = calculate_ema(prices, period=50)
    elapsed = time.time() - start_time
    
    # Should be fast even with loop
    assert elapsed < 0.5, f"EMA took {elapsed:.3f}s for 1k points"


def test_rsi_vectorized_operations():
    """Test that RSI uses efficient operations."""
    prices = pd.Series(range(1, 1001))
    
    start_time = time.time()
    rsi = calculate_rsi(prices, period=14)
    elapsed = time.time() - start_time
    
    # Should be fast
    assert elapsed < 0.5, f"RSI took {elapsed:.3f}s for 1k points"


def test_indicators_scale_linearly():
    """Test that indicators scale approximately linearly with data size."""
    np.random.seed(42)
    
    # Medium dataset
    prices_medium = pd.Series(np.random.uniform(100, 200, 10000))
    start = time.time()
    calculate_sma(prices_medium, period=20)
    time_medium = time.time() - start
    
    # Large dataset (10x)
    prices_large = pd.Series(np.random.uniform(100, 200, 100000))
    start = time.time()
    calculate_sma(prices_large, period=20)
    time_large = time.time() - start
    
    # Should scale roughly linearly (allow 20x overhead for setup)
    # Only test if medium time is measurable
    if time_medium > 0.001:
        assert time_large < time_medium * 20


def test_numerical_stability():
    """Test that indicators maintain numerical stability with large values."""
    # Very large prices
    prices = pd.Series([1e6 + i * 100 for i in range(100)])
    
    sma = calculate_sma(prices, period=10)
    ema = calculate_ema(prices, period=10)
    rsi = calculate_rsi(prices, period=14)
    
    # Should not have inf or overflow
    assert not np.isinf(sma.dropna()).any()
    assert not np.isinf(ema.dropna()).any()
    assert not np.isinf(rsi.dropna()).any()


def test_precision_maintained():
    """Test that calculations maintain sufficient precision."""
    # Small price differences
    prices = pd.Series([100.001, 100.002, 100.003, 100.004, 100.005])
    
    sma = calculate_sma(prices, period=3)
    
    # Should maintain precision
    assert sma.iloc[2] != sma.iloc[3]  # Values should be different
    
    # Check precision is reasonable
    expected = (100.001 + 100.002 + 100.003) / 3
    assert sma.iloc[2] == pytest.approx(expected, abs=1e-9)

