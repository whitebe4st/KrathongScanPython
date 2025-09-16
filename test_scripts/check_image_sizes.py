import os

import cv2

test_dir = "data/test_images"
photos = [
    "real_photo_test.jpg",
    "test_real_photo.jpg",
    "sizing_test.jpg",
    "download.jpg",
]

for photo in photos:
    path = os.path.join(test_dir, photo)
    if os.path.exists(path):
        img = cv2.imread(path)
        if img is not None:
            print(f"{photo}: {img.shape}")
        else:
            print(f"{photo}: could not read")
    else:
        print(f"{photo}: not found")
