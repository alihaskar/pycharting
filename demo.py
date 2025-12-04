"""
PyCharting Demo Script.

This script demonstrates the full capabilities of the PyCharting library.
It generates a large synthetic dataset (1 million points) representing financial OHLC data
and calculates common technical indicators (SMA, EMA, RSI-like, Stochastic-like).

It then launches the interactive chart server to visualize this data.
This serves as both a usage example and a performance benchmark.
"""

import numpy as np
from src.pycharting import plot, stop_server


def sma(values: np.ndarray, window: int) -> np.ndarray:
    """
    Calculate Simple Moving Average (SMA).

    Args:
        values (np.ndarray): Input data array.
        window (int): The rolling window size.

    Returns:
        np.ndarray: The SMA series.
    """
    kernel = np.ones(window, dtype=float) / float(window)
    return np.convolve(values, kernel, mode="same")


def ema(values: np.ndarray, span: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).

    Args:
        values (np.ndarray): Input data array.
        span (int): The span (N) for the EMA calculation.

    Returns:
        np.ndarray: The EMA series.
    """
    alpha = 2.0 / (span + 1.0)
    out = np.empty_like(values, dtype=float)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def rsi_like(values: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate an RSI-like oscillator (Relative Strength Index approximation).

    Note: This is a simplified calculation using SMA instead of the traditional Wilder's smoothing
    for performance demonstration purposes.

    Args:
        values (np.ndarray): Input price data (typically Close).
        period (int): The lookback period.

    Returns:
        np.ndarray: The RSI values (0-100).
    """
    # Lightweight SMA-style RSI approximation
    delta = np.diff(values, prepend=values[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    avg_gain = sma(gain, period)
    avg_loss = sma(loss, period)

    rs = np.divide(
        avg_gain,
        avg_loss,
        out=np.zeros_like(avg_gain),
        where=avg_loss != 0,
    )
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def stochastic_like(
    close: np.ndarray, low: np.ndarray, high: np.ndarray, period: int = 14
) -> np.ndarray:
    """
    Calculate a Stochastic-like oscillator.

    This estimates the position of the close price relative to the recent high-low range.
    It uses smoothed bands for a cleaner visual in this demo.

    Args:
        close (np.ndarray): Closing prices.
        low (np.ndarray): Low prices.
        high (np.ndarray): High prices.
        period (int): The lookback period.

    Returns:
        np.ndarray: The oscillator values (0-100).
    """
    # Cheap "stochastic-looking" oscillator using rolling min/max approximation.
    # We normalize close into [0, 100] over a slowly-varying band.
    band_low = sma(low, period)
    band_high = sma(high, period)
    span = np.maximum(band_high - band_low, 1e-8)
    k = (close - band_low) / span
    k = np.clip(k, 0.0, 1.0) * 100.0
    return k


def main() -> None:
    # Generate sample OHLC data
    n = 1_000_000
    index = np.arange(n, dtype=float)

    base = 10_000.0
    noise = np.random.randn(n).astype(float)
    close = np.cumsum(noise) + base
    open_ = close + np.random.randn(n).astype(float) * 0.5
    high = np.maximum(open_, close) + np.abs(np.random.randn(n).astype(float))
    low = np.minimum(open_, close) - np.abs(np.random.randn(n).astype(float))

    # Overlays on price
    ma_window = 50
    ema_window = 200
    ma_close = sma(close, ma_window)
    ema_close = ema(close, ema_window)

    # Oscillator-style series for subplots
    rsi_series = rsi_like(close, period=14)
    stoch_series = stochastic_like(close, low, high, period=14)

    overlays = {
        f"SMA_{ma_window}": ma_close,
        f"EMA_{ema_window}": ema_close,
    }
    subplots = {
        "RSI_like": rsi_series,
        "Stoch_like": stoch_series,
    }

    print("plotting with overlays + subplots...")
    plot(index, open_, high, low, close, overlays=overlays, subplots=subplots)

    # KEEP PROCESS ALIVE SO SERVER THREADS DON'T DIE
    input("Press Enter to stop the chart server...")
    stop_server()


if __name__ == "__main__":
    main()
