import os
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np


def process_image():
    file_path = filedialog.askopenfilename(
        title="เลือกไฟล์รูป", filetypes=[("Image files", ".jpg.jpeg .png.bmp")]
    )
    if not file_path:
        return

    # โหลดรูป
    img = cv2.imread(file_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # หา Contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # สร้าง canvas สีดำ
    mask = np.zeros_like(gray)

    # วาด contour เติมขาวทึบ
    cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

    # บันทึกไฟล์
    save_path = os.path.splitext(file_path)[0] + "_output.png"
    cv2.imwrite(save_path, mask)

    messagebox.showinfo("สำเร็จ", f"รูปถูกแปลงแล้ว!\nไฟล์บันทึกที่:\n{save_path}")
