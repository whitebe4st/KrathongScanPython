# KrathongScanner - Distribution Guide

## 📁 **How to Distribute the Application**

When sharing the KrathongScanner with others, provide them with a **single folder** containing everything they need.

## 🗂️ **Distribution Folder Structure**

```
KrathongScanner/
├── KrathongScanner.exe          # Main application
├── data/
│   ├── markers/
│   │   └── templates/           # Template mask files
│   │       ├── mask1_final.png  # Krathong template 1
│   │       ├── mask2_final.png  # Krathong template 2
│   │       ├── mask3_final.png  # Krathong template 3
│   │       └── mask4_final.png  # Krathong template 4
│   └── processed_images/        # Output folder (empty)
├── README.txt                   # User instructions
└── run_KrathongScanner.bat     # Easy launcher (optional)
```

## 📋 **Step-by-Step User Instructions**

### **Option 1: Simple Setup (Recommended)**

1. **Download** the `KrathongScanner` folder
2. **Extract** it anywhere on your computer (Desktop, Documents, etc.)
3. **Double-click** `KrathongScanner.exe` to start
4. **That's it!** The app will automatically find all required files

### **Option 2: Manual Setup**

1. **Create** a new folder called `KrathongScanner`
2. **Copy** `KrathongScanner.exe` into it
3. **Create** the folder structure:
   ```
   KrathongScanner/
   ├── KrathongScanner.exe
   └── data/
       ├── markers/
       │   └── templates/
       └── processed_images/
   ```
4. **Copy** the mask files into `data/markers/templates/`
5. **Run** the executable

## 🚀 **How to Run**

- **Double-click** `KrathongScanner.exe`
- **Or** use the batch file: `run_KrathongScanner.bat`
- **Or** from command line: `KrathongScanner.exe --mode ui`

## ⚠️ **Important Notes**

- **Keep the folder structure intact** - Don't move files around
- **Don't delete** the `data` folder - It contains essential mask files
- **The app creates** the `processed_images` folder automatically if it doesn't exist
- **You can move** the entire `KrathongScanner` folder to any location

## 🔧 **Troubleshooting**

### **"Masks not found" Error**

- Ensure `data/markers/templates/` folder exists
- Check that all 4 mask PNG files are present
- Verify the folder structure matches exactly

### **App won't start**

- Check that `KrathongScanner.exe` is in the same folder as the `data` folder
- Ensure no antivirus is blocking the executable
- Try running as administrator

### **Webcam issues**

- Make sure your camera isn't being used by another application
- Check camera permissions in Windows settings

## 📱 **Portable Usage**

The entire `KrathongScanner` folder is **portable**:

- Copy it to a USB drive
- Move it between computers
- Run it from any location

## 🔄 **Updates**

To update the application:

1. **Replace** `KrathongScanner.exe` with the new version
2. **Update** mask files in `data/markers/templates/` if needed
3. **Keep** the folder structure the same

## 📞 **Support**

If you encounter issues:

1. Check this README first
2. Verify the folder structure matches exactly
3. Ensure all files are present and not corrupted
4. Try running from a different location

---

**Remember**: The key is keeping the `data` folder in the same directory as the executable!
