# KrathongScanner

A Python-based ArUco marker detection system with WebSocket API for Unity integration.

## Project Overview

This project consists of two main components:

1. **ArUco Detection Module** - Computer vision system for detecting and tracking ArUco markers
2. **WebSocket API Server** - Real-time communication interface for Unity clients

## Project Structure

```
KrathongScanner/
├── src/                    # Source code
│   ├── aruco_detector/    # ArUco detection module
│   ├── websocket_api/     # WebSocket API server
│   └── utils/             # Shared utilities
├── tests/                 # Test files
├── config/                # Configuration files
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Features

- **ArUco Marker Detection**: Real-time detection and pose estimation
- **WebSocket API**: Low-latency communication for Unity integration
- **Configurable**: Environment-based configuration
- **Tested**: Comprehensive test coverage
- **Documented**: API documentation and code comments

## Getting Started

### Prerequisites

- Python 3.8+
- OpenCV with ArUco support
- WebSocket library

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Copy `.env.example` to `.env`
2. Update environment variables as needed

### Running the Application

```bash
# Run ArUco detector
python -m src.aruco_detector.main

# Run WebSocket API server
python -m src.websocket_api.main

# Run both (development mode)
python -m src.main
```

## Development

### Code Quality

- **Formatting**: Black for code formatting
- **Linting**: Flake8 for style checking
- **Type Checking**: MyPy for static type analysis

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test module
pytest tests/test_aruco_detector.py
```

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pre-commit install
```

## API Documentation

The WebSocket API provides real-time communication for Unity clients. See `docs/api.md` for detailed API specifications.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Add your license here]

## Contact

[Add contact information]
