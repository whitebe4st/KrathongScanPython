# Auto-Directory Mode

The Auto-Directory Mode automatically monitors a specified directory for new krathong images and processes them using the same pipeline as the Import and Webcam modes.

## Features

- **Automatic Detection**: Monitors a directory for new image files
- **Real-time Processing**: Processes images as soon as they are detected
- **Same Pipeline**: Uses the same ArUco detection and cropping logic as other modes
- **Metadata Generation**: Creates JSON metadata files for each processed image
- **Multiple Formats**: Supports JPG, PNG, BMP, TIFF image formats
- **Configurable Interval**: Adjustable check interval for directory scanning

## Usage

### 1. Command Line

```bash
# Interactive mode (will prompt for directories)
python main.py --mode auto-directory

# With specified directories
python main.py --mode auto-directory --input-dir "C:\MyKrathongs" --output-dir "C:\Processed"

# With custom check interval
python main.py --mode auto-directory --input-dir "C:\MyKrathongs" --output-dir "C:\Processed" --check-interval 5.0
```

### 2. GUI Mode

1. Start the application: `python main.py`
2. Click "🔄 Auto-Directory Monitor"
3. Select the directory to monitor
4. Confirm the output directory
5. The system will start monitoring automatically

### 3. Standalone Script

```bash
python run_auto_directory.py
```

## How It Works

1. **Directory Monitoring**: The system continuously scans the input directory for new image files
2. **File Detection**: When a new image file is found, it's added to the processing queue
3. **Automatic Processing**: Each image is processed using the ArUco detection pipeline:
   - Detects ArUco markers (IDs 0-3)
   - Applies perspective correction if needed
   - Applies template mask for cropping
   - Saves transparent PNG output
4. **Metadata Creation**: A JSON file is created with processing details
5. **Continuous Operation**: The system continues monitoring until stopped

## File Structure

```
Input Directory/           # Directory being monitored
├── krathong1.jpg         # New image file (will be processed)
├── krathong2.png         # Another image file
└── ...

Output Directory/         # Processed images
├── processed_krathong1.png      # Processed image
├── processed_krathong1.json     # Metadata file
├── processed_krathong2.png
├── processed_krathong2.json
└── ...
```

## Configuration

### Command Line Arguments

- `--input-dir`: Directory to monitor for new images
- `--output-dir`: Directory to save processed images (default: data/processed_images)
- `--check-interval`: Time in seconds between directory checks (default: 2.0)

### Supported Image Formats

- JPG/JPEG
- PNG
- BMP
- TIFF/TIF

## Status and Monitoring

The system provides real-time status updates including:

- Number of files processed
- Number of files failed
- Current directories being monitored
- Running time statistics

## Error Handling

- **Missing Mask Templates**: The system will automatically look for mask templates in standard locations
- **Processing Failures**: Failed images are logged but don't stop the monitoring process
- **Directory Issues**: Clear error messages for missing or inaccessible directories

## Best Practices

1. **Organize Input**: Keep the input directory clean and organized
2. **Monitor Logs**: Check the console output for processing status
3. **Backup Originals**: The system doesn't modify original files, but it's good practice to backup
4. **Disk Space**: Monitor disk space in the output directory for long-running operations

## Stopping the Monitor

- **Command Line**: Press `Ctrl+C`
- **GUI Mode**: Close the application window
- **Standalone Script**: Press `Ctrl+C`

## Troubleshooting

### Common Issues

1. **No mask templates found**

   - Ensure mask files exist in `data/markers/templates/`
   - Check for `krathong1_mask_final.png` or similar files

2. **Permission errors**

   - Ensure the application has read access to input directory
   - Ensure the application has write access to output directory

3. **No images being processed**
   - Check that image files are supported formats
   - Verify the input directory path is correct
   - Check console output for error messages

### Debug Mode

For detailed debugging, check the log files in the `logs/` directory or enable verbose console output.
