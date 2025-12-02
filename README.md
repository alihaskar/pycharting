# Financial Charting Tool

A high-performance financial charting application using uPlot and Python for visualizing OHLC (Open, High, Low, Close) data with technical indicators.

## Features

- **High Performance**: Render 500k+ data points at 60fps
- **Fast Loading**: Parse and display 100MB CSV files in under 2 seconds
- **Technical Indicators**: RSI, SMA, EMA, and more
- **Interactive**: Smooth zoom and pan with <16ms latency
- **Local Processing**: Work with local CSV files, no third-party uploads required

## Requirements

- Python 3.11 or higher
- Poetry (Python package manager)

## Setup

### 1. Install Poetry

If you don't have Poetry installed, follow the instructions at [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)

### 2. Clone the Repository

```bash
git clone <repository-url>
cd charting
```

### 3. Install Dependencies

Poetry will automatically create a virtual environment and install all dependencies:

```bash
poetry install
```

### 4. Activate the Virtual Environment

You have two options to work with the virtual environment:

#### Option A: Spawn a shell within the virtualenv

```bash
poetry shell
```

This activates the virtual environment in your current shell. You can then run commands directly:

```bash
python script.py
pytest
```

#### Option B: Run commands with `poetry run`

Without activating the shell, prefix your commands with `poetry run`:

```bash
poetry run python script.py
poetry run pytest
```

### 5. Verify Installation

Run the test suite to ensure everything is set up correctly:

```bash
poetry run pytest
```

All tests should pass.

## Quick Start

### Run the Application (Single Command)

After installation, start both backend and frontend servers with one command:

```bash
python run.py
```

This will start:
- **Server** on http://localhost:8000

Then open your browser to **http://localhost:8000** (it should open automatically) and load one of the sample files:
- `sample.csv` - Moderate volatility data
- `crypto.csv` - High volatility crypto-like data
- `stock.csv` - Low volatility stock-like data

Press `Ctrl+C` to stop both servers.

For more details, see [QUICK_START.md](QUICK_START.md).

## Project Structure

```
charting/
├── src/                    # Source code
│   ├── ingestion/         # CSV parsing and data loading
│   ├── processing/        # Technical indicators and data processing
│   ├── api/              # FastAPI backend
│   └── frontend/         # uPlot visualization (HTML/JS)
├── data/                  # CSV data storage
├── tests/                # Test suite
├── pyproject.toml        # Poetry configuration
└── README.md            # This file
```

## Development

### Running Tests

```bash
poetry run pytest              # Run all tests
poetry run pytest tests/path/to/test_file.py  # Run specific test file
poetry run pytest -v           # Verbose output
poetry run pytest -k test_name # Run specific test by name
```

### Adding Dependencies

```bash
poetry add package-name              # Add production dependency
poetry add --group dev package-name  # Add development dependency
```

## Usage

(Coming soon: Usage instructions will be added as features are implemented)

## Performance Targets

- **Render Performance**: 500k+ points at 60fps
- **Load Time**: 100MB CSV in < 2 seconds
- **Interaction Latency**: < 16ms for zoom/pan
- **Accuracy**: Indicators match TA-Lib output

## License

(Add your license here)

## Contributing

(Add contribution guidelines here)

