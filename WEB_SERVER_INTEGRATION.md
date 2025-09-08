# 🌐 Web Server Integration - New Feature Added!

## 📋 What's New

The KrathongScanner application now includes integrated web server functionality! You can now start the mobile upload web server directly from the main application.

## 🚀 How to Use

### Method 1: Command Line

```bash
# Start web server directly
python main.py --mode web-server

# Available at http://localhost:5000
```

### Method 2: GUI Button

1. Run the main application: `python main.py`
2. Click the **🌐 Start Web Server** button
3. Confirm the dialog to start the server
4. Access the mobile interface at http://localhost:5000

### Method 3: Standalone (Original)

```bash
# Direct web server execution
python web/server.py

# Or use batch file
run_web_server.bat
```

## ✨ Features

### 🎯 Integrated Functionality

- **One-Click Launch**: Start web server directly from GUI
- **Shared Output Directory**: Uses the same output folder as GUI
- **Consistent Processing**: Same ArUco detection and processing pipeline
- **Real-time Status**: Status updates in the main application

### 📱 Mobile Interface

- **Thai Language Interface**: Fully localized for Thai users
- **Responsive Design**: Works perfectly on mobile devices
- **Progress Tracking**: Real-time upload and processing status
- **QR Code Access**: Easy mobile access via QR codes (with ngrok)

### 🔄 Processing Pipeline

- **Auto-Directory Integration**: Uses existing Auto-Directory Mode
- **Same Quality Results**: Identical processing to desktop application
- **Background Processing**: Non-blocking file processing
- **Automatic Cleanup**: Manages uploads and results automatically

## 🛠️ Technical Details

### Command Line Arguments

```bash
python main.py --mode web-server    # Start web server mode
python main.py --mode ui            # Start GUI (default)
python main.py --mode auto-directory # Auto-directory monitoring
python main.py --mode webcam        # Webcam mode
```

### GUI Integration

- New button added to main menu: **🌐 Start Web Server**
- Background thread execution to avoid blocking GUI
- Error handling with user-friendly messages
- Automatic dependency checking

### File Structure

```
main.py                    # ✅ Added web-server mode support
src/ui/menu.py            # ✅ Added Start Web Server button
web/server.py             # ✅ Flask server (unchanged)
web/templates/            # ✅ Web interface (unchanged)
run_web_server.bat        # ✅ Standalone launcher (unchanged)
```

## 🎊 Benefits

### For Users

- **Unified Interface**: All features accessible from one application
- **Easy Mobile Access**: Quick setup for mobile image processing
- **Consistent Experience**: Same quality across all input methods
- **No Separate Setup**: No need to manage multiple applications

### For Developers

- **Code Reuse**: Leverages existing processing pipeline
- **Modular Design**: Clean separation of concerns
- **Easy Maintenance**: Single codebase for all features
- **Extensible**: Easy to add more server features

## 📊 Usage Examples

### Starting from GUI

1. **Launch Application**: `python main.py`
2. **Click Web Server Button**: "🌐 Start Web Server"
3. **Confirm Dialog**: Click "Yes" to start server
4. **Access Interface**: Open http://localhost:5000 in browser
5. **Mobile Access**: Use your computer's IP for network access

### Starting from Command Line

```bash
# Quick start
python main.py --mode web-server

# Server automatically starts on:
# - http://localhost:5000 (local)
# - http://[your-ip]:5000 (network)
# - [ngrok-url] (public, if ngrok installed)
```

### Integration Benefits

- **Shared Settings**: Uses GUI output directory setting
- **Consistent Quality**: Same ArUco detection and processing
- **Error Handling**: User-friendly error messages
- **Resource Management**: Proper cleanup on exit

## 🔧 Configuration

### Server Settings

- **Port**: 5000 (default)
- **Host**: 0.0.0.0 (accessible from network)
- **Output Directory**: Matches GUI setting
- **Processing Settings**: Inherited from main application

### Dependencies

The web server requires additional packages:

```bash
pip install flask werkzeug requests qrcode pillow
```

These are automatically checked when starting the server.

## 🎯 Use Cases

### Personal Use

- **Mobile Processing**: Process images from phone/tablet
- **Remote Access**: Access from anywhere in the house
- **Batch Upload**: Multiple images from mobile device
- **Instant Results**: Immediate download of processed images

### Team/Business Use

- **Team Collaboration**: Multiple users can upload images
- **Event Processing**: Mobile uploads during events
- **Public Access**: Share processing capability via ngrok
- **Workflow Integration**: API endpoints for automation

## ⚡ Quick Reference

### All Available Modes

```bash
python main.py                           # GUI with all features
python main.py --mode web-server         # Web server only
python main.py --mode auto-directory     # Folder monitoring
python main.py --mode webcam             # Live camera
python main.py --mode webcam-advanced    # Advanced webcam
```

### Access Points

- **Local**: http://localhost:5000
- **Network**: http://[computer-ip]:5000
- **Status**: http://localhost:5000/status
- **Jobs**: http://localhost:5000/jobs

## 🎉 Success!

The web server is now fully integrated into the main KrathongScanner application! Users can now:

✅ **Start web server from GUI** with one click
✅ **Use command line** for direct server launch
✅ **Access from mobile** devices seamlessly
✅ **Get consistent results** across all input methods
✅ **Manage everything** from one application

The mobile upload feature is now even more accessible and user-friendly! 🚀

---

_Updated on September 8, 2025 - Web Server Integration Complete_
