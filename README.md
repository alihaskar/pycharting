# PyCharting

[![PyPI version](https://img.shields.io/pypi/v/pycharting.svg)](https://pypi.org/project/pycharting/)
[![Python versions](https://img.shields.io/pypi/pyversions/pycharting.svg)](https://pypi.org/project/pycharting/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

High‑performance financial charting library for OHLC data visualization with technical indicators.

## Overview

PyCharting lets you render large OHLC time series (hundreds of thousands to millions of candles) in the browser with a single Python call.  
It runs a lightweight FastAPI server locally, streams your data to a uPlot-based frontend, and gives you an interactive viewport with overlays and indicator subplots.

![PyCharting demo](demo.png?v=2)

## Features

- **Million‑point OHLC charts**: optimized for large datetime indices and dense intraday data.
- **Timeseries x‑axis**: pass a `pd.DatetimeIndex` or Unix‑ms timestamps and the chart renders proper date/time labels that adapt to the zoom level.
- **Overlays on price**: moving averages, EMAs, or any arbitrary overlay series.
- **Indicator subplots**: RSI, MACD, volume, or any series rendered as separate panels with synced crosshair. Supports line, bar, and scatter rendering per series.
- **Multi-series subplots**: a single panel can contain multiple series with mixed types — e.g., MACD line + signal line + histogram bars, or RSI with a moving-average overlay in a different color.
- **Trade markers**: plot buy/sell arrows directly on the price chart from a simple `+1`/`-1`/`0` signal array.
- **Viewport management**: server‑side slicing and caching for smooth pan/zoom on huge arrays.
- **Measurement tool**: Shift‑click to measure price delta, percentage change, and time between two points.
- **FastAPI + uPlot stack**: Python on the backend, ultra‑light JS on the frontend.
- **Simple Python API**: one main entry point, `plot(...)`, plus helpers to manage the server.

## Installation

### From PyPI

Install the latest released version from PyPI:

```bash
pip install pycharting
```

This will install the `pycharting` package along with its runtime dependencies (`numpy`, `pandas`, `fastapi`, `uvicorn`, and friends).

### From source

If you want to develop or run against `main`:

```bash
git clone https://github.com/alihaskar/pycharting.git
cd pycharting
pip install -e .
```

If you use Poetry instead of pip:

```bash
git clone https://github.com/alihaskar/pycharting.git
cd pycharting
poetry install
```

## Quick start

The primary API is a single `plot` function that takes OHLC arrays (plus optional overlays and subplots), starts a local server, and opens your default browser on the interactive chart.
You normally import everything you need like this:

```pycon
>>> from pycharting import plot, stop_server, get_server_status

```

When you run this script, PyCharting will:

- spin up a local FastAPI server on an available port,
- register your OHLC series and overlays in a session,
- open your default browser to a minimal full‑page chart UI showing price and overlays.

Nothing runs until the first `plot` call:

```pycon
>>> get_server_status()
{'running': False, 'server_info': None, 'active_sessions': 0}

```

and stopping a server that was never started is a harmless no-op:

```pycon
>>> stop_server()
ⓘ No active server to stop

```

The examples in this README are [doctest](https://docs.python.org/3/library/doctest.html) sessions, run by the test suite. To run them yourself: `python -m doctest README.md`.

## Overlays vs subplots

Once you have your OHLC series, you pass additional series to `plot` in two different ways:

```pycon
>>> import numpy as np
>>> import pandas as pd

>>> # Synthetic OHLC data — substitute your own series.
>>> n = 300
>>> rng = np.random.default_rng(0)
>>> index = pd.date_range("2024-01-01", periods=n, freq="h")
>>> close = 100 + np.cumsum(rng.normal(size=n))
>>> open_ = np.r_[close[0], close[:-1]]
>>> high = np.maximum(open_, close) + rng.uniform(0, 1, n)
>>> low = np.minimum(open_, close) - rng.uniform(0, 1, n)
>>> price = pd.Series(close)

>>> overlays = {
...     "SMA_50": price.rolling(50).mean().to_numpy(),  # rendered on top of price
...     "EMA_200": price.ewm(span=200).mean().to_numpy(),
... }
>>> subplots = {
...     "Momentum": price.diff(14).to_numpy(),  # rendered in its own panel below price
...     "Range": high - low,
... }

>>> result = plot(  # doctest: +ELLIPSIS
...     index,
...     open_,
...     high,
...     low,
...     close,
...     overlays=overlays,
...     subplots=subplots,
...     open_browser=False,  # just print the URL and return it in result["url"]
...     block=False,  # return straight away instead of waiting for the page to close
... )
<BLANKLINE>
✓ Chart created successfully!
  URL: http://127.0.0.1:.../static/viewport-demo.html?session=default&v=...
  Data points: 300
  Open the URL above in your browser to view the chart.
<BLANKLINE>

```

In a script you would normally drop the last two arguments: `plot` then opens your browser and waits until you close the page. They are here so the README's examples can run unattended.

- **Overlays** share the same y‑axis as price and are drawn directly on the candlestick chart (moving averages, bands, signals on price).
- **Subplots** are stacked independent charts below the main panel with their own y‑scales (oscillators, volume, breadth measures).

### Subplot series types

Each subplot value can be a plain array (line), a dict with options, or a list of dicts for multi-series panels:

```pycon
>>> # A few indicators derived from the data above.
>>> delta = price.diff()
>>> gain = delta.clip(lower=0).rolling(14).mean()
>>> loss = (-delta.clip(upper=0)).rolling(14).mean()
>>> rsi = (100 - 100 / (1 + gain / loss)).to_numpy()
>>> rsi_sma = pd.Series(rsi).rolling(20).mean().to_numpy()
>>> macd_line = (price.ewm(span=12).mean() - price.ewm(span=26).mean()).to_numpy()
>>> signal_line = pd.Series(macd_line).ewm(span=9).mean().to_numpy()
>>> histogram = macd_line - signal_line
>>> volume_array = rng.normal(0, 1000, n)
>>> events_array = np.where(rng.random(n) < 0.05, close, np.nan)

>>> subplots = {
...     # Simple line (default)
...     "RSI": rsi,
...     # Bar chart — green if value ≥ 0, red if < 0, centered at y=0
...     "Volume": {"data": volume_array, "type": "bar"},
...     # Scatter plot
...     "Events": {"data": events_array, "type": "scatter", "color": "#9C27B0"},
...     # Multi-series panel: two lines + histogram bars in one subplot
...     "MACD": [
...         {"data": macd_line, "type": "line", "color": "#2196F3", "label": "MACD"},
...         {"data": signal_line, "type": "line", "color": "#FF9800", "label": "Signal"},
...         {"data": histogram, "type": "bar", "label": "Histogram"},
...     ],
...     # RSI with its own moving average overlay
...     "RSI+SMA": [
...         {"data": rsi, "type": "line", "color": "#FF9800", "label": "RSI"},
...         {"data": rsi_sma, "type": "line", "color": "#2196F3", "label": "RSI SMA(20)"},
...     ],
... }

>>> result = plot(index, open_, high, low, close, subplots=subplots, open_browser=False, block=False)  # doctest: +ELLIPSIS
<BLANKLINE>
✓ Chart created successfully!
  URL: http://127.0.0.1:.../static/viewport-demo.html?session=default&v=...
  Data points: 300
  Open the URL above in your browser to view the chart.
<BLANKLINE>

```

Supported series types: `"line"` (default), `"bar"`, `"scatter"`. Each entry accepts optional `"color"` (hex string) and `"label"` (legend text).

## Trade markers

You can overlay buy/sell arrows on the price chart by passing a `trades` array aligned with your index. Values: `1` (buy), `-1` (sell), `0` (no trade).

```pycon
>>> trades = np.zeros(len(index), dtype=int)
>>> trades[42] = 1  # buy at bar 42
>>> trades[100] = -1  # sell at bar 100

>>> result = plot(  # doctest: +ELLIPSIS
...     index,
...     open=open_,
...     high=high,
...     low=low,
...     close=close,
...     trades=trades,
...     open_browser=False,
...     block=False,
... )
<BLANKLINE>
✓ Chart created successfully!
  URL: http://127.0.0.1:.../static/viewport-demo.html?session=default&v=...
  Data points: 300
  Open the URL above in your browser to view the chart.
<BLANKLINE>

```

Buy signals render as green upward arrows below the low; sell signals render as red downward arrows above the high.

See `demo.py` for a full example that generates synthetic data and wires up overlays, subplots, and trade markers.

Run the demo from the project root:

```bash
python demo.py
```

You should see something similar to the screenshot above: a price panel with overlays, plus RSI-like and stochastic-like subplots underneath.

## Python API

The public API is intentionally small and focused. All functions are available from the top-level `pycharting` package.

### `plot`

Every parameter, spelled out (array arguments accept a `np.ndarray`, `pd.Series` or `list`):

```pycon
>>> result = plot(  # doctest: +ELLIPSIS
...     index,
...     open=open_,
...     high=high,
...     low=low,
...     close=close,
...     overlays=None,
...     subplots=None,
...     trades=None,
...     session_id="default",
...     port=None,
...     open_browser=False,  # default: True
...     server_timeout=2.0,
...     block=False,  # default: True
... )
<BLANKLINE>
✓ Chart created successfully!
...
>>> sorted(result)
['data_points', 'server_running', 'server_url', 'session_id', 'status', 'url']
>>> stop_server()
✓ Chart server stopped

```

- **index**: datetime x-axis values — `pd.DatetimeIndex`, Unix timestamps in milliseconds (`np.int64`), or a numeric array.
- **open/high/low/close**: price series of identical length.
- **overlays**: mapping of overlay name to series (same length as `close`), rendered on the main price chart.
- **subplots**: mapping of subplot name to series data. Values can be a plain array (line chart), `{"data": array, "type": "bar"|"scatter"|"line", "color": "#hex"}` for a single series with options, or a list of such dicts for multi-series panels. Rendered as additional charts stacked vertically.
- **trades**: array of `+1` (buy), `-1` (sell), `0` (no trade) signals, same length as `index`. Renders arrows on the price chart.
- **session_id**: identifier for the data session; can be used to host multiple concurrent charts.
- **port**: optional port override; if `None`, PyCharting picks an available port.
- **open_browser**: if `False`, you get the URL back in `result["url"]` but the browser is not opened automatically.
- **server_timeout**: seconds to wait for a newly started server to come up before returning.
- **block**: if `True` (the default), `plot` waits until the chart page is closed and the server shuts down; pass `False` to return immediately.

The returned dict includes:

- `status`: `"success"` or `"error"`,
- `url`: full chart URL (including session query),
- `server_url`: base FastAPI server URL,
- `session_id`: the session identifier you passed in,
- `data_points`: number of OHLC rows,
- `server_running`: boolean.

### `stop_server`

Stops the active chart server if it is running, and says so when there is none (see [Quick start](#quick-start)). This is useful in long‑running processes and demos to clean up after you are done exploring charts.

### `get_server_status`

Returns a small dict (see [Quick start](#quick-start) for its value before any chart is plotted) with:

- `running`: whether the server is alive,
- `server_info`: host/port and other metadata if running,
- `active_sessions`: number of registered data sessions.

## How it works

For a detailed technical deep dive into the architecture, data flow, rendering pipeline, and internals, see [docs/how-it-works.md](docs/how-it-works.md).

## Project structure

The library follows a modern `src/` layout:

```text
pycharting/
├── src/
│   └── pycharting/
│       ├── core/         # Chart server lifecycle and internals
│       ├── data/         # Data ingestion, validation, and slicing
│       ├── api/          # FastAPI routes and Python API surface
│       └── web/          # Static frontend (HTML + JS for charts)
├── tests/                # Test suite, mirroring src/pycharting/
├── docs/                 # MkDocs sources, incl. how-it-works.md
└── pyproject.toml        # Project configuration
```

## Contributing

Contributions, bug reports, and feature suggestions are welcome. Please open an issue or pull request on GitHub.

Basic workflow:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Make changes and add tests.
4. Run the test suite.
5. Open a pull request against `main`.

## License

PyCharting is licensed under the MIT License.

## Links

- **PyPI**: `https://pypi.org/project/pycharting/`
- **Source**: `https://github.com/alihaskar/pycharting`
- **Issues**: `https://github.com/alihaskar/pycharting/issues`
- **Blog**: [aligrithm.com](https://aligrithm.com)
