# 🚀 Quick Start Guide - Financial Charting Tool

## 📋 Prerequisites

- Python 3.12+
- Poetry (installed globally)
- Modern web browser (Chrome, Firefox, Edge)

## 🏃 Running the Project

### Step 1: Install Dependencies

```bash
poetry install
```

### Step 2: Start the Application ⚡

**Single command to start everything!**

```bash
poetry run python run.py
```

This will:
1. Start the server on port 8000
2. Open your default web browser automatically

You should see:
```
🚀 Starting Financial Charting Tool on port 8000...

============================================================
✅ Server running at: http://localhost:8000
📊 Chart URL:       http://localhost:8000
============================================================

💡 Press Ctrl+C to stop the server
🌐 Opening browser...
```

### Option: Load Data Immediately

You can pass a CSV file path to load it immediately:

```bash
poetry run python run.py data/sample.csv
```

---

### Step 3: Load Sample Data (Web Interface)

If you didn't specify a file in the command, you can load data from the web interface.

The project comes with 3 sample CSV files (in `data/` folder):

1. **sample.csv** - 2000 1-minute bars, moderate volatility
2. **crypto.csv** - 5000 1-minute bars, high volatility (crypto-like)
3. **stock.csv** - 1000 1-hour bars, low volatility (stock-like)

In the web interface:
1. Enter filename: `sample.csv`
2. Click **"Load Chart"**
3. Chart will render!

## 🐍 Using from Python

You can also use the tool directly from your Python scripts:

```python
import pandas as pd
import charting

# Create or load your DataFrame
df = pd.DataFrame(...) 

# Plot it with a single command!
charting.plot(df)
```

Or load a CSV file directly:

```python
import charting
charting.plot("data/crypto.csv")
```

## 🎮 Using the Application

### Basic Operations:

1. **Load Chart:**
   - Enter filename (e.g., `sample.csv`, `crypto.csv`, `stock.csv`)
   - Click "Load Chart"

2. **Change Timeframe:**
   - Select timeframe from dropdown (1min, 5min, 15min, 1h, 4h, 1D)
   - Chart will automatically reload with resampled data

3. **Add Indicators:**
   - Select indicator from dropdown (RSI:14, SMA:20, EMA:12, etc.)
   - Indicator will be added to the chart
   - Multiple indicators supported!

4. **Remove Indicators:**
   - Click the **×** button on any indicator badge
   - Chart will reload without that indicator

### Supported Indicators:

- **RSI (14, 20)** - Relative Strength Index (oscillator, separate axis)
- **SMA (20, 50, 200)** - Simple Moving Average (overlay)
- **EMA (12, 26)** - Exponential Moving Average (overlay)

### Supported Timeframes:

- **Original** - No resampling
- **1 Minute** (1min)
- **5 Minutes** (5min)
- **15 Minutes** (15min)
- **1 Hour** (1h)
- **4 Hours** (4h)
- **1 Day** (1D)

## 📊 Generating Custom Data

Want more sample data? Use the data generator:

```bash
# Generate 10,000 1-minute bars
poetry run python scripts/generate_sample_data.py \
  --output data/custom.csv \
  --periods 10000 \
  --freq 1min \
  --price 100.0 \
  --volatility 0.02
```

## 📚 Project Structure

```
charting/
├── run.py                # Main launcher script
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # Application entry & frontend serving
│   │   └── ...
│   ├── python_api/       # Python client API
│   │   ├── charting.py   # Main Charting class
│   │   └── ...
│   └── frontend/         # Web interface
│       ├── index.html    # Main HTML
│       └── ...
├── data/                 # CSV data files
└── tests/                # Test suite
```
