# Project Structure Documentation

## Overview

This document provides a detailed breakdown of the KrathongScanner project structure, explaining the purpose and organization of each component.

## Directory Structure

```
KrathongScanner/
├── 📁 src/                          # Source code package
│   ├── 📁 aruco_detector/           # ArUco detection module
│   │   ├── __init__.py              # Module initialization
│   │   ├── detector.py              # Main ArUco detector class
│   │   ├── camera.py                # Camera management
│   │   └── marker.py                # Marker data structures
│   ├── 📁 websocket_api/            # WebSocket API module
│   │   ├── __init__.py              # Module initialization
│   │   ├── server.py                # WebSocket server
│   │   ├── client.py                # Client connection management
│   │   └── handlers.py              # Message handlers
│   ├── 📁 utils/                    # Shared utilities
│   │   ├── __init__.py              # Module initialization
│   │   ├── config.py                # Configuration management
│   │   ├── logger.py                # Logging utilities
│   │   └── validators.py            # Data validation
│   └── __init__.py                  # Main package initialization
├── 📁 tests/                        # Test suite
│   ├── __init__.py                  # Test package initialization
│   ├── conftest.py                  # Pytest configuration and fixtures
│   ├── test_aruco_detector.py       # ArUco detector tests
│   ├── test_websocket_api.py        # WebSocket API tests
│   └── test_utils.py                # Utility function tests
├── 📁 config/                       # Configuration files
│   └── settings.py                  # Main configuration settings
├── 📁 docs/                         # Documentation
│   └── api.md                       # WebSocket API documentation
├── 📁 scripts/                      # Utility scripts
│   └── setup_dev.py                 # Development environment setup
├── 📁 logs/                         # Application logs (auto-created)
├── 📁 temp/                         # Temporary files (auto-created)
├── 📁 output/                       # Output files (auto-created)
├── 📁 data/                         # Data files (auto-created)
│   ├── aruco_markers/               # ArUco marker images
│   ├── calibration/                 # Camera calibration data
│   └── test_images/                 # Test images
├── 📄 main.py                       # Main application entry point
├── 📄 requirements.txt              # Production dependencies
├── 📄 requirements-dev.txt          # Development dependencies
├── 📄 pyproject.toml               # Modern Python project configuration
├── 📄 .pre-commit-config.yaml      # Pre-commit hooks configuration
├── 📄 .gitignore                   # Git ignore rules
├── 📄 env.example                  # Environment variables template
├── 📄 README.md                    # Project documentation
└── 📄 PROJECT_STRUCTURE.md         # This file
```

## Module Descriptions

### 1. ArUco Detector Module (`src/aruco_detector/`)

**Purpose**: Handles all computer vision operations related to ArUco marker detection.

**Key Components**:

- **`detector.py`**: Main detection logic, marker identification, and pose estimation
- **`camera.py`**: Camera initialization, frame capture, and camera management
- **`marker.py`**: Data structures for marker information and pose data

**Responsibilities**:

- Real-time camera feed processing
- ArUco marker detection and identification
- Pose estimation and 3D positioning
- Marker tracking and validation
- Performance optimization for real-time processing

### 2. WebSocket API Module (`src/websocket_api/`)

**Purpose**: Provides real-time communication interface for Unity clients.

**Key Components**:

- **`server.py`**: WebSocket server implementation and connection management
- **`client.py`**: Client connection handling and lifecycle management
- **`handlers.py`**: Message processing and routing

**Responsibilities**:

- WebSocket connection establishment and maintenance
- Real-time data transmission to Unity clients
- Message serialization and validation
- Connection pooling and load management
- Heartbeat monitoring and connection health

### 3. Utilities Module (`src/utils/`)

**Purpose**: Provides shared functionality and common utilities across the project.

**Key Components**:

- **`config.py`**: Centralized configuration management
- **`logger.py`**: Structured logging with rotation and formatting
- **`validators.py`**: Data validation and sanitization

**Responsibilities**:

- Environment-based configuration
- Structured logging and monitoring
- Data validation and type checking
- Common helper functions

### 4. Configuration (`config/`)

**Purpose**: Centralized configuration management for all project components.

**Key Features**:

- Environment variable support
- Type-safe configuration classes
- Default value management
- Configuration validation

### 5. Testing (`tests/`)

**Purpose**: Comprehensive test coverage for all project components.

**Test Types**:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Performance Tests**: Performance and load testing
- **Mock Fixtures**: Test data and mock objects

### 6. Documentation (`docs/`)

**Purpose**: Comprehensive documentation for developers and users.

**Contents**:

- API documentation with examples
- Integration guides
- Performance considerations
- Troubleshooting guides

### 7. Scripts (`scripts/`)

**Purpose**: Automation and development workflow tools.

**Available Scripts**:

- **`setup_dev.py`**: Development environment setup
- **Future scripts**: Testing, deployment, monitoring

## Data Flow Architecture

```
Camera Input → ArUco Detector → Marker Data → WebSocket API → Unity Client
     ↓              ↓              ↓            ↓
  Frame Capture → Detection → Pose Estimation → Real-time Transmission
```

## Development Workflow

### 1. Setup Phase

```bash
# Clone repository
git clone <repository-url>
cd KrathongScanner

# Run setup script
python scripts/setup_dev.py

# Activate virtual environment
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
```

### 2. Development Phase

```bash
# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Check code quality
pre-commit run --all-files

# Run specific test modules
pytest tests/test_aruco_detector.py -v
```

### 3. Code Quality

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style checking
- **mypy**: Type checking
- **bandit**: Security analysis

## File Naming Conventions

- **Python files**: snake_case (e.g., `aruco_detector.py`)
- **Test files**: `test_<module_name>.py`
- **Configuration files**: lowercase with underscores
- **Documentation**: lowercase with hyphens
- **Directories**: lowercase with underscores

## Import Structure

```python
# Main package imports
from src.aruco_detector import ArUcoDetector
from src.websocket_api import WebSocketServer
from src.utils import Config, setup_logger

# Module-specific imports
from src.aruco_detector.detector import ArUcoDetector
from src.websocket_api.server import WebSocketServer
```

## Environment Configuration

The project uses environment variables for configuration:

1. Copy `env.example` to `.env`
2. Update values according to your environment
3. Configuration is automatically loaded by the `Config` class

## Testing Strategy

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Performance Tests**: Ensure real-time performance requirements
- **Mock Testing**: Use mock objects for external dependencies

## Deployment Considerations

- **Environment Variables**: Use `.env` files for different environments
- **Logging**: Structured logging with rotation
- **Monitoring**: Health checks and performance metrics
- **Security**: Input validation and authentication (for production)

## Collaboration Guidelines

1. **Branch Strategy**: Feature branches for new development
2. **Code Review**: All changes require review
3. **Testing**: Maintain high test coverage
4. **Documentation**: Update docs with code changes
5. **Pre-commit**: Automated quality checks before commits

## Future Enhancements

- **Docker Support**: Containerization for deployment
- **CI/CD Pipeline**: Automated testing and deployment
- **Performance Monitoring**: Real-time performance metrics
- **API Versioning**: Backward compatibility management
- **Plugin System**: Extensible architecture for custom detectors
