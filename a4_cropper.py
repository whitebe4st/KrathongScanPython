from tkinter import Tk, filedialog

import cv2
import numpy as np


def crop_with_markers(image_path, output_path, debug=True):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"ไม่พบไฟล์รูป: {image_path}")

    # ย่อภาพเพื่อ process ไวขึ้น
    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image = cv2.resize(image, (int(image.shape[1] / ratio), 500))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # ใช้ adaptive threshold ให้ขอบชัดขึ้น
    edged = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    edged = cv2.Canny(edged, 75, 200)

    if debug:
        cv2.imshow("Edged", edged)
        cv2.waitKey(0)

    # หา contour
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    screenCnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            screenCnt = approx
            break

    if screenCnt is None:
        raise ValueError("ไม่เจอสี่เหลี่ยม A4")

    if debug:
        # โชว์ว่ากรอบที่เจอคือกรอบไหน
        debug_img = image.copy()
        cv2.drawContours(debug_img, [screenCnt], -1, (0, 255, 0), 2)
        cv2.imshow("Contour", debug_img)
        cv2.waitKey(0)

    # แปลงกลับเป็นขนาดจริง
    pts = screenCnt.reshape(4, 2) * ratio

    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    dst = np.array(
        [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
        dtype="float32",
    )

    M = cv2.getPerspectiveTransform(rect, dst)
    warp = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

    cv2.imwrite(output_path, warp)
    print(f"✅ บันทึกไฟล์ที่ {output_path}")


# -------------------
# Main program
# -------------------
if __name__ == "__main__":
    root = Tk()
    root.withdraw()

    input_file = filedialog.askopenfilename(
        title="เลือกไฟล์รูป", filetypes=[("Images", "*.jpg;*.png;*.jpeg")]
    )
    if not input_file:
        exit()

    output_file = filedialog.asksaveasfilename(
        title="บันทึกไฟล์เป็น",
        defaultextension=".png",
        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
    )
    if not output_file:
        exit()

    crop_with_markers(input_file, output_file, debug=True)
