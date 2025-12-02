# 🚀 Quick Start Guide

## Option 1: Run in Separate Terminals (Recommended for Development)

### Terminal 1 - Backend API:
```bash
poetry run uvicorn src.api.main:app --reload
```

This will start the FastAPI backend on **http://localhost:8000**

### Terminal 2 - Frontend Server:
```bash
cd src/frontend
python -m http.server 3000
```

This will start the frontend on **http://localhost:3000**

---

## Option 2: Using run.py (May have issues on Windows)

```bash
poetry run python run.py
```

If this doesn't work or servers don't stay running, use Option 1 instead.

---

## 📊 Access the Application

Once both servers are running:

1. Open your browser to: **http://localhost:3000**
2. Enter a CSV filename in the input (e.g., `sample.csv`)
3. Select indicators (RSI, SMA, etc.) if desired
4. Click "Load Chart"
5. Enjoy your interactive chart! 📈

---

## 🧪 Test with Sample Data

Generate sample data first:
```bash
poetry run python scripts/generate_sample_data.py
```

This creates `sample.csv` in the `data/` directory.

---

## 📚 API Documentation

Visit **http://localhost:8000/docs** to see the FastAPI interactive docs.

---

## 🛑 Stopping Servers

Press `Ctrl+C` in each terminal window to stop the servers.

---

## 🐛 Troubleshooting

**"Failed to load chart" error:**
- Make sure both servers are running
- Check that the backend is on port 8000
- Check that the frontend is on port 3000
- Make sure the CSV file exists in the `data/` directory

**CORS errors:**
- The backend should automatically allow requests from localhost:3000
- Check the browser console for specific error messages

**Module not found errors:**
- Make sure you're in the project root directory
- Run `poetry install` to install dependencies

