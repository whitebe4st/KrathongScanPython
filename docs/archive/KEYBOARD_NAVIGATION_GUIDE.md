# 🎯 Template Maker - Keyboard Navigation Guide

## ✅ **Fixed Issues**

### 1. **Template Creation Now Works Properly**

- **"Create Template"** button now saves BOTH template image AND mask
- **Success message** shows which files were created
- **Template file**: `{template_name}.png`
- **Mask file**: `{template_name}_mask.png`

### 2. **Keyboard Navigation Added**

#### **Scale Control (0.01 precision)**

- **Focus on scale entry field** and use:
  - `←` **Left Arrow**: Decrease by 0.01
  - `→` **Right Arrow**: Increase by 0.01
  - `↑` **Up Arrow**: Increase by 0.01
  - `↓` **Down Arrow**: Decrease by 0.01

#### **X Position Control (1 pixel precision)**

- **Focus on X offset entry field** and use:
  - `←` **Left Arrow**: Move left by 1 pixel
  - `→` **Right Arrow**: Move right by 1 pixel
  - `↑` **Up Arrow**: Move right by 1 pixel
  - `↓` **Down Arrow**: Move left by 1 pixel

#### **Y Position Control (1 pixel precision)**

- **Focus on Y offset entry field** and use:
  - `←` **Left Arrow**: Move down by 1 pixel
  - `→` **Right Arrow**: Move up by 1 pixel
  - `↑` **Up Arrow**: Move up by 1 pixel
  - `↓` **Down Arrow**: Move down by 1 pixel

## 🚀 **Complete Workflow**

### **Creating a Template with Custom Mask**

1. **Load Image**: Click "Browse Image" and select your Krathong image
2. **Enter Template Name**: Type a unique name (e.g., "my_custom_krathong")
3. **Set Marker IDs**: Use unique ArUco marker IDs (20-49 for custom templates)
4. **Preview**: Click "Preview & Adjust" to open the adjustment window

5. **In Preview Window**:

   - **Load Mask**: Click "Select Mask" to load your mask file
   - **Enable Overlay**: Check "Show Mask Overlay" to see the green overlay

6. **Fine-tune with Keyboard**:

   - **Click in Scale field** → Use arrow keys for 0.01 increments
   - **Click in X Offset field** → Use arrow keys for 1-pixel movement
   - **Click in Y Offset field** → Use arrow keys for 1-pixel movement

7. **Save Mask**: Click "Save Adjusted Mask" to apply settings
8. **Create Template**: Click "Create Template" to save both files

### **Result Files**

- ✅ **Template**: `data/templates/{name}.png` (with ArUco markers)
- ✅ **Mask**: `data/templates/{name}_mask.png` (adjusted with your settings)
- ✅ **Metadata**: `data/templates/{name}_metadata.json` (for CRUD import)

## 🎯 **Keyboard Tips**

- **Tab** between fields to change focus
- **Enter** confirms value changes
- **Arrow keys** work when field is focused (highlighted)
- **Scale precision**: Every arrow press = 0.01 change
- **Position precision**: Every arrow press = 1 pixel movement

## 🔧 **Button Controls Still Available**

- **Scale**: -0.1, -0.01, +0.01, +0.1 buttons
- **Position**: -10, -1, +1, +10 pixel buttons
- **Reset**: Return to default settings (1.0x scale, center position)
- **Sliders**: For approximate adjustments

---

_Now you have precise control with both keyboard AND mouse! 🎊_
