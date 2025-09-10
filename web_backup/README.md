# 🌐 KrathongScanner Web Server Documentation

## 📖 Overview

The KrathongScanner Web Server provides a mobile-friendly interface for uploading and processing krathong images through a web browser. It leverages the existing Auto-Directory Mode for processing and includes real-time progress tracking, automatic file management, and optional public access via ngrok tunneling.

## 🚀 Features

### Core Functionality

- **📱 Mobile-Optimized Interface**: Thai language interface designed for mobile devices
- **🔄 Real-time Processing**: Live progress tracking with status updates
- **📤 Drag & Drop Upload**: Support for multiple upload methods
- **📥 Automatic Download**: Direct download of processed results
- **🎯 Auto-Processing**: Uses existing Auto-Directory Mode for consistent results

### Advanced Features

- **🌐 Public Access**: Optional ngrok tunnel for remote access
- **📱 QR Code Generation**: Easy mobile access via QR code
- **📊 Job Tracking**: Monitor all uploads and processing status
- **⚡ Background Processing**: Non-blocking file processing
- **🛡️ File Validation**: Secure file type and size validation

### Security & Validation

- **✅ File Type Validation**: Only image files (JPG, PNG, GIF, BMP)
- **📏 Size Limits**: 16MB maximum file size
- **🔒 Secure Filenames**: Automatic filename sanitization
- **⏰ Unique Timestamps**: Prevents filename conflicts

## 📁 File Structure

```
web/
├── server.py              # Main Flask server
├── templates/
│   ├── index.html         # Upload interface
│   └── status.html        # Server status page
├── static/                # Static assets (CSS, JS, images)
├── uploads/               # Uploaded files (input to Auto-Directory Mode)
├── results/               # Processed files (output from Auto-Directory Mode)
└── README.md             # This documentation
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.10+ with virtual environment
- KrathongScanner project dependencies
- Flask and related web dependencies

### Required Dependencies

```bash
pip install flask>=2.3.0 werkzeug>=2.3.0 requests>=2.31.0 qrcode>=7.4.0 pillow>=10.0.0
```

### Optional Dependencies

- **ngrok**: For public access tunneling
  - Download from https://ngrok.com/
  - **Easy Setup**: Place `ngrok.exe` in the `web/` directory (✅ **CONFIGURED**)
  - **Alternative**: Install globally and add to system PATH

## 🏃‍♂️ Running the Server

### Method 1: Using the Batch File (Recommended)

```cmd
# From KrathongScanner root directory
run_web_server.bat
```

### Method 2: Manual Start

```cmd
# Navigate to web directory
cd web

# Activate virtual environment
..\venv\Scripts\activate

# Start server
python server.py
```

### Method 3: Using Python Path

```cmd
# From any directory
G:/path/to/KrathongScanner/venv/Scripts/python.exe G:/path/to/KrathongScanner/web/server.py
```

## 🌐 Access Points

### Local Access

- **Primary Interface**: http://localhost:5000
- **Status Page**: http://localhost:5000/status
- **Job Listing**: http://localhost:5000/jobs

### Network Access

- **LAN Access**: http://[your-ip]:5000 (e.g., http://10.11.0.39:5000)
- **Public Access**: ✅ **ENABLED** - Automatic ngrok tunnel when server starts
  - Public URL: `https://[random].ngrok-free.app` (changes each restart)
  - QR Code: Available at http://localhost:5000/status for easy mobile access

## 📱 Mobile Usage

### QR Code Access

1. Start the server
2. Visit http://localhost:5000/status
3. Scan the QR code with your mobile device
4. Upload images directly from your phone

### Direct Mobile Access

1. Connect your mobile device to the same WiFi network
2. Find your computer's IP address
3. Open browser on mobile: http://[computer-ip]:5000
4. Upload and process images

## 🔧 API Endpoints

### Upload Endpoint

```http
POST /upload
Content-Type: multipart/form-data

Response:
{
  "success": true,
  "job_id": "uuid-string",
  "filename": "timestamped_filename.jpg",
  "message": "File uploaded successfully, processing started"
}
```

### Status Check

```http
GET /status/{job_id}

Response:
{
  "job_id": "uuid-string",
  "status": "completed|processing|pending|error",
  "filename": "original_filename.jpg",
  "created_at": "2024-01-01T12:00:00",
  "download_url": "/download/result_file.png",
  "preview_url": "/preview/result_file.png"
}
```

### File Download

```http
GET /download/{filename}
# Downloads the processed file
```

### Job Listing

```http
GET /jobs
# Returns JSON array of all jobs
```

## ⚙️ Configuration

### Server Settings

```python
# In server.py
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
```

### Auto-Directory Settings

```python
# Auto-detector configuration
AutoDirectoryDetector(
    input_directory=UPLOAD_FOLDER,
    output_directory=RESULTS_FOLDER,
    use_homography=True,  # Enable perspective correction
    check_interval=2.0    # Check every 2 seconds
)
```

## 🔄 Processing Pipeline

### Upload Flow

1. **File Upload**: User uploads via web interface
2. **Validation**: File type and size validation
3. **Storage**: Secure filename generation and storage in uploads/
4. **Job Creation**: Unique job ID generated for tracking
5. **Processing**: Auto-Directory Mode detects and processes file
6. **Monitoring**: Real-time status updates via polling
7. **Completion**: Download link provided when ready

### File Processing

- Uses identical pipeline to Import and Auto-Directory modes
- ArUco marker detection with 4X4_50 dictionary
- Perspective correction (homography) applied
- Template masking for transparent background
- Output: `{filename}_transparent.png`

## 🐛 Troubleshooting

### Common Issues

#### Server Won't Start

```bash
# Check Python environment
G:/path/to/venv/Scripts/python.exe --version

# Install missing dependencies
pip install flask werkzeug requests qrcode pillow

# Check file permissions
ls -la web/server.py
```

#### Upload Fails

```bash
# Check upload directory permissions
mkdir web/uploads
chmod 755 web/uploads

# Verify file size (max 16MB)
# Check file type (JPG, PNG, GIF, BMP only)
```

#### Processing Timeout

```bash
# Check Auto-Directory Mode configuration
# Verify marker templates exist in data/markers/templates/
# Check output directory permissions
mkdir web/results
chmod 755 web/results
```

#### ngrok Not Found

```bash
# Download ngrok from https://ngrok.com/
# Add ngrok to system PATH
# Or disable ngrok by commenting out start_ngrok_tunnel()
```

### Log Files

- Server logs to console
- Auto-Directory logs available in logs/
- Check for ArUco detector initialization errors

## 🔧 Development

### Adding Features

1. **New Routes**: Add to server.py
2. **Templates**: Create in templates/
3. **Static Assets**: Add to static/
4. **Processing Logic**: Extend AutoDirectoryDetector

### Customization

- **UI Styling**: Modify CSS in templates/
- **Language**: Update Thai text in templates/
- **Processing**: Adjust AutoDirectoryDetector parameters
- **Security**: Enhance file validation in server.py

## 🚦 Production Deployment

### Security Considerations

- Use production WSGI server (not Flask dev server)
- Implement proper authentication
- Add HTTPS support
- Configure firewall rules
- Set up proper logging

### Recommended Setup

```bash
# Use Gunicorn for production
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app

# Or use nginx + uWSGI
# Configure reverse proxy for HTTPS
```

## 🎯 Integration with KrathongScanner

### Consistency

- Uses same ArUco detection as main application
- Identical processing pipeline to Auto-Directory Mode
- Same output format and quality
- Shared configuration and settings

### Benefits

- **Unified Processing**: All modes use same core logic
- **Consistent Results**: Same quality across all input methods
- **Easy Maintenance**: Single codebase for processing
- **Feature Parity**: Web mode has same capabilities as desktop modes

## 📊 Performance

### Benchmarks

- **Upload Speed**: Limited by network bandwidth
- **Processing Time**: Same as Auto-Directory Mode (~2-5 seconds per image)
- **Concurrent Users**: Limited by Python GIL (consider async framework for production)
- **File Size**: 16MB limit prevents memory issues

### Optimization Tips

- Use SSD for faster file I/O
- Increase check_interval for better CPU usage
- Consider Redis for job queue in production
- Implement file cleanup for old uploads

## 🤝 Support

### Getting Help

1. Check this documentation
2. Review console logs
3. Test with Auto-Directory Mode first
4. Verify file permissions and dependencies

### Known Limitations

- Single-threaded processing (Python GIL)
- Dev server not suitable for production
- ngrok requires separate installation
- Limited to local network without ngrok

## 🎉 Success!

Your KrathongScanner Web Server is now ready to provide mobile-friendly image processing! Users can upload krathong images from any device and receive professionally processed transparent PNG files automatically.

---

_Made with ❤️ for the KrathongScanner project_
