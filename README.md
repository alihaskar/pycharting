# PyCharting

A Python library for interactive charting and data visualization.

## Overview

PyCharting is a comprehensive library designed to simplify the creation of interactive charts and data visualizations. It provides a clean API for working with various data sources and creating beautiful, interactive visualizations.

## Features

- 📊 Interactive charting capabilities
- 🔄 Data processing and transformation
- 🌐 Web-based visualization interface
- 🚀 FastAPI-powered REST API
- 📈 Support for multiple chart types
- 🔧 Easy-to-use configuration

## Installation

### From Source

Clone the repository and install in editable mode with development dependencies:

```bash
git clone https://github.com/yourusername/pycharting.git
cd pycharting
pip install -e ".[dev]"
```

### Requirements

- Python >= 3.8
- pandas >= 2.0.0
- numpy >= 1.24.0
- fastapi >= 0.104.0
- uvicorn >= 0.24.0

## Project Structure

```
pycharting/
├── src/
│   ├── core/         # Core functionality
│   ├── data/         # Data processing and management
│   ├── api/          # API endpoints
│   └── web/          # Web interface
├── tests/            # Test suite
├── data/             # Data files
└── pyproject.toml    # Project configuration
```

## Quick Start

```python
from pycharting import Chart

# Create a simple chart
chart = Chart(data=your_data)
chart.render()
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

### Running the API Server

```bash
# Start the development server
uvicorn src.api.main:app --reload

# The API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

## Testing

The project uses pytest for testing with the following features:

- Unit tests for all core functionality
- Integration tests for API endpoints
- Code coverage reporting
- Async test support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Authors

- PyCharting Team

## Links

- Homepage: https://github.com/yourusername/pycharting
- Documentation: https://pycharting.readthedocs.io
- Issues: https://github.com/yourusername/pycharting/issues
