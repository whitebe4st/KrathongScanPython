#  KrathongScanner

A comprehensive Python-based computer vision system for automatic krathong image processing with ArUco marker detection, multiple input modes, and mobile web interface.

##  Project Overview

KrathongScanner is an advanced image processing application that automatically detects krathong images using ArUco markers, applies perspective correction, and generates transparent PNG outputs. The system supports multiple input methods and provides both desktop GUI and mobile web interfaces.

###  Key Components

1. ** ArUco Detection System** - Real-time marker detection with 4X4_50 dictionary
2. ** Desktop GUI Application** - Tkinter-based interface with multiple processing modes
3. ** Auto-Directory Monitoring** - Real-time folder monitoring with automatic processing
4. ** Mobile Web Server** - Flask-based web interface for mobile upload and processing
5. ** Webcam Integration** - Live camera feed processing (advanced and basic modes)
6. ** Template Masking** - Automatic background removal with transparent output

##  Features

### Core Processing

- ** ArUco Marker Detection**: Automatic krathong detection using ArUco markers
- ** Perspective Correction**: Homography-based image rectification
- ** Template Masking**: Automatic background removal for clean transparent PNGs
- ** Batch Processing**: Process multiple images automatically
- ** Real-time Monitoring**: Live folder monitoring with instant processing

### Multiple Input Modes

- ** Import Mode**: Direct file selection and processing
- ** Auto-Directory Mode**: Monitor folders for automatic processing
- ** Webcam Mode**: Live camera feed processing
- ** Web Upload Mode**: Mobile-friendly web interface

### Advanced Features

- ** Mobile Web Interface**: Thai language interface optimized for mobile devices
- ** Public Access**: Optional ngrok tunneling for remote access
- ** Progress Tracking**: Real-time processing status and job monitoring
- ** Automatic Downloads**: Direct download of processed results
- ** Security Validation**: File type and size validation for uploads

##  Project Structure

```
KrathongScanner/
├── main.py                       # Main application entry point
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project configuration
├── KrathongScanner.spec         # PyInstaller configuration
├──
├── src/                         # Core source code
│   ├── aruco_detector/          # ArUco detection system
│   │   ├── detector.py          # Main detection logic
│   │   └── __init__.py
│   ├── mask_generator/          # Template mask generation
│   ├── ui/                      # Desktop GUI components
│   ├── utils/                   # Utility functions
│   └── websocket_api/           # WebSocket API for real-time features
├──
├── web/                         # Web server components
│   ├── server.py                # Flask web server
│   ├── templates/               # HTML templates
│   └── static/                  # CSS, JS, images
├──
├── tools/                       # Development and utility tools
│   ├── template_makers/         # Template creation tools
│   ├── image_processing/        # Image processing utilities
│   ├── qr_generation/          # QR code generation
│   ├── database/               # Database management tools
│   ├── webcam/                 # Webcam utilities
│   └── README.md               # Tools documentation
├──
├── scripts/                     # Batch files and scripts
│   ├── run_KrathongScanner.bat # Main launcher
│   ├── start_web_server.bat    # Web server launcher
│   ├── run_template_maker_gui.bat # Template maker GUI
│   └── README.md               # Scripts documentation
├──
├── test_scripts/               # Development test scripts
│   ├── test_*.py              # Various test scripts
│   ├── debug_*.py             # Debugging utilities
│   └── README.md              # Test scripts documentation
├──
├── docs/                       # Documentation
│   └── archive/                # Historical documentation
│       ├── *.md               # Feature development docs
│       └── README.md          # Archive documentation
├──
├── data/                       # Application data
│   ├── db/                    # Database files
│   ├── markers/               # ArUco marker templates
│   ├── test_images/           # Test images
│   └── extracted_krathong/    # Processing results
├──
├── test_outputs/              # Test and debug outputs
│   ├── images/                # Test result images
│   ├── json/                  # Test metadata files
│   └── README.md              # Test outputs documentation
├──
├── config/                    # Configuration files
├── models/                    # ML models (if any)
├── logs/                      # Application logs
├── temp/                      # Temporary files
├── output/                    # Processing outputs
└── build/                     # Build artifacts
│   ├── auto_directory_detector.py # Auto-directory monitoring
│   ├── mask_generator/           # Template masking system
│   │   ├── mask_generator.py     # Mask generation logic
│   │   └── __init__.py
│   ├── ui/                       # GUI components
│   │   ├── menu.py              # Main menu interface
│   │   └── __init__.py
│   ├── utils/                    # Shared utilities
│   │   ├── file_utils.py        # File handling utilities
│   │   └── __init__.py
│   ├── webcam_detector.py        # Webcam processing
│   ├── webcam_detector_advanced.py # Advanced webcam features
│   └── paper_detector.py         # Paper detection utilities
├── web/                          # Web server components
│   ├── server.py                 # Flask web server
│   ├── templates/                # HTML templates
│   │   ├── index.html           # Upload interface
│   │   └── status.html          # Server status
│   ├── uploads/                  # Upload directory
│   ├── results/                  # Processed results
│   └── README.md                # Web server documentation
├── data/                         # Data files and templates
│   ├── markers/                  # Marker templates and generation
│   │   ├── templates/           # Template masks
│   │   ├── generated/           # Generated markers
│   │   └── custom/              # Custom markers
│   ├── test_images/             # Test image samples
│   ├── processed_images/        # Processing output
│   └── calibration/             # Camera calibration data
├── tests/                        # Test files
├── config/                       # Configuration
│   └── settings.py              # Application settings
├── logs/                         # Application logs
├── build/                        # Build artifacts
├── dist/                         # Distribution files
├── main.py                       # Main application entry
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── KrathongScanner.spec         # PyInstaller specification
├── run_web_server.bat           # Web server launcher
├── run_KrathongScanner.bat      # Main application launcher
└── README.md                    # This file
```

##  Getting Started

### Prerequisites

- **Python 3.10+** with virtual environment support
- **OpenCV** with ArUco support
- **Modern web browser** for web interface
- **Webcam** (optional, for live processing)
- **ngrok** (optional, for public web access)

###  Installation

1. **Clone the repository**

   ```bash
   git clone [repository-url]
   cd KrathongScanner
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python main.py --help
   ```

###  Quick Start

#### Desktop Application

```bash
# GUI mode (recommended for beginners)
python main.py

# Import mode (direct file processing)
python main.py --mode import --input-dir "path/to/images" --output-dir "path/to/results"

# Auto-directory mode (real-time monitoring)
python main.py --mode auto-directory --input-dir "path/to/monitor" --output-dir "path/to/results"

# Using batch files (Windows)
run_KrathongScanner.bat
```

#### Web Server (Mobile Interface)

```bash
# Start web server
python web/server.py

# Or use batch file
run_web_server.bat

# Access via browser
http://localhost:5000
```

#### Webcam Mode

```bash
# Basic webcam processing
python run_webcam.py

# Advanced webcam features
python run_webcam_advanced.py
```

##  Usage Modes

### 1. Desktop GUI Mode

- **Launch**: `python main.py` or `run_KrathongScanner.bat`
- **Features**: Point-and-click interface, batch processing, real-time preview
- **Best for**: Desktop users, batch processing, testing

### 2. Auto-Directory Mode

- **Launch**: Choose "Auto-Directory Mode" in GUI or use command line
- **Features**: Real-time folder monitoring, automatic processing
- **Best for**: Continuous processing, integration with other systems

### 3.  Web Upload Mode

- **Launch**: `python web/server.py` or `run_web_server.bat`
- **Features**: Mobile-friendly interface, progress tracking, public access
- **Best for**: Mobile users, remote processing, team collaboration

### 4.  Webcam Mode

- **Launch**: `python run_webcam.py`
- **Features**: Live camera feed, real-time processing, instant preview
- **Best for**: Live demonstrations, immediate processing

## 🔧 Configuration

### Application Settings

Edit `config/settings.py`:

```python
# ArUco Detection
ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_SIZE = 0.05  # meters

# Processing
USE_HOMOGRAPHY = True
OUTPUT_FORMAT = "transparent_png"

# Directories
DEFAULT_INPUT_DIR = "data/test_images"
DEFAULT_OUTPUT_DIR = "data/processed_images"
```

### Web Server Configuration

Edit `web/server.py`:

```python
# Server settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'

# Processing settings
USE_HOMOGRAPHY = True
CHECK_INTERVAL = 2.0  # seconds
```

##  Processing Pipeline

### 1. **Input Stage**

- Image upload/import/capture
- File validation and preprocessing
- Format conversion if needed

### 2. **Detection Stage**

- ArUco marker detection using 4X4_50 dictionary
- Marker validation and filtering
- Corner point extraction

### 3. **Correction Stage**

- Homography calculation from detected markers
- Perspective correction and image rectification
- Size and orientation normalization

### 4. **Masking Stage**

- Template mask loading from `data/markers/templates/`
- Background removal using template matching
- Transparent PNG generation

### 5. **Output Stage**

- File saving with timestamp naming
- Result delivery (download/display)
- Cleanup and logging

##  Development & Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src

# Run specific test
python test_detector.py
```

### Code Quality

- **Formatting**: Follow PEP 8 guidelines
- **Type Hints**: Use type annotations where possible
- **Documentation**: Document all public functions and classes
- **Logging**: Use proper logging levels

### Building Executable

```bash
# Create standalone executable
python -m PyInstaller KrathongScanner.spec

# Output will be in dist/KrathongScanner_V2/
```

### Desktop Application

1. **Development**: Run directly with Python
2. **Distribution**: Use PyInstaller to create executable
3. **Installation**: Copy executable and data folders

### Web Server

1. **Development**: Use Flask development server
2. **Production**: Deploy with Gunicorn + Nginx
3. **Public Access**: Configure ngrok or similar tunneling service


## 📚 Documentation

### API Documentation

- **ArUco Detector**: `src/aruco_detector/README.md`
- **Web Server**: `web/README.md`
- **Mask Generator**: `src/mask_generator/README.md`


**🎉 Ready to start processing krathong images? Choose your preferred mode and begin scanning!**

_Made with ❤️ for automatic krathong image processing_
