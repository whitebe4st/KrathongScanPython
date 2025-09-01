# KrathongScanner Executable

## 🚀 Quick Start

### Option 1: Double-click to run

Simply double-click `KrathongScanner.exe` to start the application in UI mode.

### Option 2: Use the batch file

Run `run_KrathongScanner.bat` for a guided startup.

### Option 3: Command line

```bash
# UI Mode (default)
KrathongScanner.exe

# Webcam Mode
KrathongScanner.exe --mode webcam

# Auto Directory Mode
KrathongScanner.exe --mode auto
```

## 📁 File Structure

The executable includes all necessary files:

- **KrathongScanner.exe** - Main executable (62MB)
- **data/markers/templates/** - Template mask files
- **data/processed_images/** - Output directory for processed images

## 🎯 Features

### UI Mode (Default)

- **Import from Picture**: Browse and process image files
- **Use Webcam**: Real-time scanning with paper detection
- **Auto Directory Mode**: Monitor folder for new images
- **Output Directory Selection**: Choose where to save processed images

### Output Directory Management

- **Custom Output Location**: Choose where to save processed images
- **Directory Selection**: Use "📁 Select Directory" to browse folders
- **Reset to Default**: Use "🔄 Reset to Default" to return to default location
- **Universal Setting**: Applies to both import and webcam modes

### Enhanced Mask Adjustment

- **Draggable Transform Box**: Click and drag to reposition masks
- **Interactive Handles**: Resize masks with corner handles
- **Large Preview Window**: 1400x1000 pixel preview area
- **Real-time Processing**: See changes instantly

## 🔧 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB free space
- **Camera**: Required for webcam mode

## 📝 Usage Instructions

### Processing Images

1. Click "Import from Picture"
2. Select an image file with ArUco markers
3. (Optional) Choose output directory using "📁 Select Directory"
4. Adjust mask position and size in the preview window
4. Click "Save Image" when satisfied

### Webcam Mode

1. Click "Use Webcam"
2. (Optional) Choose output directory using "📁 Select Directory"
3. Position krathong with markers visible
4. Press 'c' to capture and process
4. Press 'q' to quit

### Auto Directory Mode

1. Click "Auto Directory Mode"
2. Select a folder to monitor
3. Place new images in the folder
4. Images will be processed automatically

## 🐛 Troubleshooting

### Common Issues

- **"No markers detected"**: Ensure ArUco markers are clearly visible
- **"Camera not found"**: Check camera permissions and connections
- **"File not found"**: Ensure image files are in supported formats (PNG, JPG, etc.)

### Supported Image Formats

- PNG, JPG, JPEG, BMP, TIFF

### Performance Tips

- Use good lighting for better marker detection
- Keep markers clean and unobstructed
- Close other applications for better performance

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Ensure all files are in the correct locations
3. Try running in command line mode for error messages

## 🔄 Updates

To update the application:

1. Download the new executable
2. Replace the old `KrathongScanner.exe`
3. Keep your `data/processed_images/` folder for your work

---

**KrathongScanner v1.0.0** - Traditional Krathong Detection and Processing
