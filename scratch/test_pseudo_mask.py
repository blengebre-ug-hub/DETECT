import cv2
import numpy as np
import glob
import os

def generate_pseudo_mask(img_path, save_path):
    # Read grayscale
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return False
    
    # Resize for consistency
    img = cv2.resize(img, (300, 300))
    
    # Blur to reduce speckle
    blurred = cv2.GaussianBlur(img, (9, 9), 0)
    
    # The fistula/abscess is usually hypoechoic (dark)
    # We invert the threshold so dark areas become white (255)
    # Use Otsu's thresholding on the lower intensity pixels
    _, binary = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Morphological operations to remove noise
    kernel = np.ones((5, 5), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=3)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create an empty mask
    mask = np.zeros_like(img)
    
    if contours:
        # Sort contours by area, keep the largest ones (often the main anomaly)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # Keep top 1 or 2 contours if they are reasonably large
        for cnt in contours[:2]:
            if cv2.contourArea(cnt) > 1000:  # Minimum size threshold
                cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)
                
    cv2.imwrite(save_path, mask)
    return True

if __name__ == "__main__":
    os.makedirs("test_masks", exist_ok=True)
    images = glob.glob("../3D_EUS_PAF_v1_Images/*.[pP][nN][gG]")
    for i, path in enumerate(images[:5]):
        print(f"Processing {path}")
        generate_pseudo_mask(path, f"test_masks/mask_{i}.png")
