# KrathongScanner UI

A modern, user-friendly graphical interface for the KrathongScanner application.

## Features

The UI provides four main modes for processing krathong images:

### 1. 📁 Import Krathong from Picture

- **Purpose**: Process individual krathong images from files with preview and manual mask alignment
- **How it works**:
  - Click the button to open a file browser
  - Select any image file (PNG, JPG, JPEG, BMP, TIFF)
  - The app will automatically detect ArUco markers and identify the krathong template
  - **Supported Templates**:
    - **krathong1**: Traditional design (markers 0,1,2,3)
    - **krathong2**: Modern design (markers 4,5,6,7)
    - **krathong3**: Lotus design (markers 8,9,10,11)
    - **krathong4**: Royal design (markers 12,13,14,15)
  - **Perspective Correction Options**:
    - **Default Setting**: Toggle in main UI to choose homography or simple cropping
    - **Real-time Toggle**: Switch between methods in the preview window
    - **Homography**: Automatically corrects warped/perspective-distorted images
    - **Simple Cropping**: Direct cropping without perspective correction
  - A preview window opens showing the processed result
  - **NEW**: Manual mask alignment controls allow you to adjust:
    - **Mask Scale**: Resize the mask (0.5x to 2.0x)
    - **X/Y Offset**: Move the mask horizontally and vertically
    - **Reset**: Return to original settings
  - **Preview Features**:
    - Real-time preview of adjustments
    - Save, cancel, or re-process options
    - Scrollable image view for large images
- **Use case**: When you have individual krathong images to process and want fine control over the mask alignment

### 2. 📷 Use Webcam

- **Purpose**: Real-time krathong detection using your computer's camera
- **How it works**:
  - Opens a live webcam feed with ArUco marker detection
  - Shows real-time feedback with marker overlays and template information
  - Press 'c' to capture and process the current frame
  - Press 'q' to quit webcam mode
- **Features**:
  - Paper detection and auto-zoom for better accuracy
  - Template identification (shows which krathong template is detected)
  - Quality indicators and stabilization
    - **Perspective Correction**: Uses homography to automatically correct warped/perspective-distorted images
- **Use case**: For real-time scanning of physical krathong papers

### 3. 🔄 Auto-Directory Monitor

- **Purpose**: Automatically monitor a directory for new krathong images and process them
- **How it works**:
  - Click the button to select a directory to monitor
  - The system continuously scans for new image files
  - Automatically processes any new krathong images found
  - Uses the same detection and cropping pipeline as Import mode
- **Features**:
  - Real-time directory monitoring
  - Automatic file detection and processing
  - Supports multiple image formats (PNG, JPG, BMP, TIFF)
  - Metadata generation for each processed image
  - Background processing without blocking the UI
- **Use case**: For batch processing or automated workflows where images are regularly added to a folder

## Settings & Status Display

### Settings Panel

- **Default Perspective Correction**: Choose whether imported images use homography by default
  - **Use Homography**: Automatically corrects warped images (recommended for angled photos)
  - **Simple Cropping**: Direct cropping without perspective correction (faster processing)

### Status Display

The UI includes a real-time status display that shows:

- Timestamped log messages
- Processing status and results
- Error messages and notifications
- Auto-scrolling with the last 50 messages kept

## Image Preview & Processing Controls

### Preview Window Features

- **Real-time Preview**: See the processed image immediately after detection
- **Scrollable View**: Handle large images with horizontal and vertical scrollbars
- **Responsive Display**: Automatically scales images to fit the preview area

### Processing Controls

- **Perspective Correction Toggle**: Switch between homography and simple cropping in real-time
  - **Homography**: Automatically straightens warped images using perspective transformation
  - **Simple Cropping**: Direct rectangular cropping without perspective correction
- **Real-time Processing**: See changes immediately when toggling between methods

### Mask Alignment Controls

- **Scale Adjustment**: Resize the mask from 0.5x to 2.0x to match your image
- **Position Control**: Move the mask horizontally (X) and vertically (Y) with pixel precision
- **Real-time Updates**: See changes immediately as you adjust the controls
- **Reset Function**: Return to original settings with one click

### Action Buttons

- **💾 Save Image**: Save the current preview with all adjustments
- **❌ Cancel**: Close without saving
- **🔄 Re-process**: Start over with original settings

## Getting Started

### Running the UI

```bash
# Run with UI mode (default)
python main.py

# Or explicitly specify UI mode
python main.py --mode ui

# Other modes still available
python main.py --mode webcam
python main.py --mode webcam-advanced
python main.py --mode webcam-enhanced
```

### Requirements

Make sure you have the required dependencies installed:

```bash
pip install opencv-python python-dotenv pyyaml Pillow
```

## Technical Details

### Architecture

- **Framework**: Tkinter with ttk widgets for modern appearance
- **Threading**: Background processing to keep UI responsive
- **Integration**: Uses existing ArUco detector and webcam components

### File Structure

```
src/ui/
├── menu.py          # Main UI implementation
└── __init__.py      # Package initialization

data/
├── processed_images/    # Output for imported images
└── webcam_captures/     # Output for webcam captures
```

### Error Handling

- All operations run in background threads
- Errors are displayed in the status area
- User-friendly error messages with suggestions
- Graceful fallbacks for missing files or failed operations

## Troubleshooting

### Common Issues

1. **"No markers detected"**

   - Ensure the image contains valid ArUco markers (IDs 0-19)
   - Check that markers are clearly visible and not blurred
   - Try adjusting lighting or camera angle

2. **Webcam not working**

   - Check that your camera is not being used by another application
   - Try a different camera index if you have multiple cameras
   - Ensure camera drivers are properly installed

3. **Processing fails**
   - Check the status display for specific error messages
   - Ensure the image format is supported (PNG, JPG, etc.)
   - Verify that template masks exist in `data/markers/templates/`

### Testing

Run the UI test script to verify everything is working:

```bash
python test_ui.py
```

## Future Enhancements

Potential improvements for the UI:

- [x] ✅ Preview of processed images in the UI
- [x] ✅ Manual mask alignment controls
- [x] ✅ Batch processing for multiple files (Auto-Directory Mode)
- [ ] Settings panel for camera and processing options
- [ ] Export options for different formats
- [ ] Keyboard shortcuts for common actions
- [ ] Mask rotation controls
- [ ] Multiple mask template selection in preview
- [ ] Before/after comparison view
