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

### Step 2: Start Both Servers (Single Command) ⚡

**Recommended - One command to rule them all!**

```bash
python run.py
```

This will start both the backend API (port 8000) and frontend server (port 3000) simultaneously.

You should see:
```
🚀 Starting Backend API on http://localhost:8000...
🌐 Starting Frontend Server on http://localhost:3000...

============================================================
✅ Servers are running!
============================================================
📊 Frontend:  http://localhost:3000
🔧 Backend:   http://localhost:8000
📚 API Docs:  http://localhost:8000/docs
============================================================

💡 Press Ctrl+C to stop both servers
```

Then open your browser to: **http://localhost:3000**

---

### Alternative: Manual Two-Terminal Setup

<details>
<summary>Click to expand if you prefer running servers separately</summary>

**Terminal 1 - Backend API:**

```bash
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: **http://localhost:8000**

**Terminal 2 - Frontend:**

```bash
cd src/frontend
python -m http.server 3000
```

Then open your browser to: **http://localhost:3000**

</details>

---

### Step 3: Load Sample Data

The project comes with 3 sample CSV files:

1. **sample.csv** - 2000 1-minute bars, moderate volatility
2. **crypto.csv** - 5000 1-minute bars, high volatility (crypto-like)
3. **stock.csv** - 1000 1-hour bars, low volatility (stock-like)

In the web interface:
1. Enter filename: `sample.csv`
2. Click **"Load Chart"**
3. Chart will render!

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

## 🎨 Example Workflows

### Workflow 1: Basic Chart

```
1. Enter: sample.csv
2. Click: Load Chart
3. Result: OHLCV candlestick chart
```

### Workflow 2: Chart with Indicators

```
1. Enter: crypto.csv
2. Select: RSI:14
3. Select: SMA:50
4. Select: EMA:12
5. Click: Load Chart
6. Result: Chart with 3 indicators
```

### Workflow 3: Resampled Chart

```
1. Enter: sample.csv
2. Select Timeframe: 5min
3. Select: SMA:20
4. Click: Load Chart
5. Result: 5-minute bars with SMA overlay
```

### Workflow 4: Complex Analysis

```
1. Enter: stock.csv
2. Select Timeframe: 4h
3. Add: RSI:14
4. Add: SMA:20
5. Add: SMA:50
6. Add: EMA:26
7. Click: Load Chart
8. Result: Multi-indicator analysis on 4-hour timeframe
```

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

# Generate daily data for 1 year
poetry run python scripts/generate_sample_data.py \
  --output data/yearly.csv \
  --periods 365 \
  --freq 1D \
  --price 500.0 \
  --volatility 0.01

# Generate 5-minute bars (high volatility)
poetry run python scripts/generate_sample_data.py \
  --output data/volatile.csv \
  --periods 3000 \
  --freq 5min \
  --price 1000.0 \
  --volatility 0.05
```

**Parameters:**
- `--output` / `-o`: Output file path
- `--periods` / `-p`: Number of data points
- `--freq` / `-f`: Frequency (1min, 5min, 1h, 1D, etc.)
- `--price`: Starting price
- `--volatility` / `-v`: Price volatility (0.02 = 2%)

## 🧪 Running Tests

Run the complete test suite (462 tests):

```bash
poetry run pytest
```

Run specific test files:

```bash
# Backend tests
poetry run pytest tests/test_api*.py -v

# Frontend tests
poetry run pytest tests/test_frontend*.py -v

# Integration tests
poetry run pytest tests/test_integration.py -v
```

## 📡 API Endpoints

### GET /chart-data

Fetch chart data with optional indicators and resampling.

**Query Parameters:**
- `filename` (required): CSV filename
- `indicators` (optional, multiple): Indicator specs (e.g., `RSI:14`, `SMA:20`)
- `timeframe` (optional): Resample timeframe (e.g., `5min`, `1h`, `1D`)
- `start_date` (optional): Filter start date
- `end_date` (optional): Filter end date
- `target_tz` (optional): Target timezone

**Example:**
```
http://localhost:8000/chart-data?filename=sample.csv&indicators=RSI:14&indicators=SMA:20&timeframe=5min
```

**Response:**
```json
{
  "data": [
    [timestamp1, timestamp2, ...],  // Unix milliseconds
    [open1, open2, ...],
    [high1, high2, ...],
    [low1, low2, ...],
    [close1, close2, ...],
    [volume1, volume2, ...],
    [rsi1, rsi2, ...],              // If RSI requested
    [sma1, sma2, ...]               // If SMA requested
  ],
  "metadata": {
    "filename": "sample.csv",
    "rows": 400,
    "columns": 8,
    "timeframe": "5min",
    "indicators": ["RSI:14", "SMA:20"]
  }
}
```

## 🐛 Troubleshooting

### Backend won't start

```bash
# Reinstall dependencies
poetry install

# Check Python version
python --version  # Should be 3.12+

# Check if port 8000 is in use
# Windows: netstat -ano | findstr :8000
# Kill process if needed
```

### Frontend can't connect to API

1. Make sure backend is running on port 8000
2. Check browser console for CORS errors
3. Use Python HTTP server instead of direct file open
4. Verify API URL in browser: http://localhost:8000/health

### Chart doesn't render

1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify CSV file exists in `data/` directory
4. Try a different sample file
5. Check network tab for API response

### Data file not found

- Ensure CSV file is in the `data/` directory
- Use relative path (just filename, not full path)
- Example: `sample.csv` not `data/sample.csv`

## 📚 Project Structure

```
charting/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # Application entry
│   │   ├── routes.py     # API endpoints
│   │   ├── models.py     # Pydantic models
│   │   ├── processor.py  # Data processing pipeline
│   │   └── exceptions.py # Custom exceptions
│   ├── ingestion/        # Data loading
│   │   ├── loader.py     # CSV loader & datetime parser
│   │   └── schema.py     # Validation schemas
│   ├── processing/       # Data processing
│   │   ├── indicators.py # Technical indicators
│   │   ├── resampler.py  # Timeframe conversion
│   │   └── pivot.py      # uPlot format conversion
│   └── frontend/         # Web interface
│       ├── index.html    # Main HTML
│       ├── data-client.js # API communication
│       ├── chart.js      # Chart management
│       └── app.js        # Application logic
├── data/                 # CSV data files
│   ├── sample.csv        # 2000 1-min bars
│   ├── crypto.csv        # 5000 1-min bars
│   └── stock.csv         # 1000 1-hour bars
├── tests/                # Test suite (462 tests)
└── scripts/              # Utility scripts
    └── generate_sample_data.py
```

## 🎯 Next Steps

1. **Explore the Data:**
   - Try all 3 sample files
   - Compare different timeframes
   - Experiment with indicator combinations

2. **Generate Custom Data:**
   - Create your own CSV files
   - Test with different volatilities
   - Try different time periods

3. **Customize:**
   - Modify chart colors in `chart.js`
   - Add more indicator options in `index.html`
   - Adjust API parameters

4. **Deploy:**
   - Deploy backend to Heroku/AWS
   - Host frontend on Netlify/Vercel
   - Configure production CORS

## 💡 Tips

- **Performance:** Sample.csv loads fastest (2000 points)
- **Crypto-like:** Use crypto.csv for high volatility testing
- **Stock-like:** Use stock.csv for smooth, realistic data
- **State Persistence:** Your selections are saved in localStorage
- **Keyboard Shortcut:** Press Enter in filename input to load
- **Multiple Indicators:** Add as many as you want!
- **Responsive:** Resize browser window to see chart adapt

## ✅ Verification Checklist

- [ ] Backend starts on port 8000
- [ ] Frontend accessible in browser
- [ ] sample.csv loads successfully
- [ ] Chart renders with OHLCV data
- [ ] Timeframe selection works
- [ ] Indicators can be added/removed
- [ ] Chart updates when selections change
- [ ] State persists after page reload

Enjoy exploring your Financial Charting Tool! 🎉📈

