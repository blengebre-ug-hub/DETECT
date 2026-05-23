import os
import glob
import cv2
import numpy as np

def generate_pseudo_mask(img_path, save_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None: 
        return False
        
    img = cv2.resize(img, (300, 300))
    blurred = cv2.GaussianBlur(img, (9, 9), 0)
    
    # Adaptive thresholding or simple inverted thresholding for dark hypoechoic areas
    _, binary = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
    
    kernel = np.ones((5, 5), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=3)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(img)
    
    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # Keep top contours that are reasonably sized
        for cnt in contours[:2]:
            if cv2.contourArea(cnt) > 800:
                cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)
                
    cv2.imwrite(save_path, mask)
    return True

if __name__ == "__main__":
    src_dir = "../3D_EUS_PAF_v1_Images"
    dest_dir = "../3D_EUS_PAF_v1_Masks"
    
    os.makedirs(dest_dir, exist_ok=True)
    images = glob.glob(os.path.join(src_dir, '*.[pP][nN][gG]'))
    
    print(f"Found {len(images)} images to process.")
    
    for i, path in enumerate(images):
        basename = os.path.basename(path)
        save_path = os.path.join(dest_dir, basename)
        success = generate_pseudo_mask(path, save_path)
        
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(images)}")
            
    print("Finished generating pseudo-masks.")
