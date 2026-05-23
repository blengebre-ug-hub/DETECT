import os
import numpy as np
import tensorflow as tf
import cv2
from model import build_unet
from dataset import IMG_SIZE

# Path to the segmentation model weights
SEG_MODEL_PATH = "segmentation_model.keras"

def load_segmentation_model():
    model = build_unet(img_size=IMG_SIZE)
    if os.path.exists(SEG_MODEL_PATH):
        try:
            model.load_weights(SEG_MODEL_PATH)
            print("Segmentation model weights loaded.")
        except Exception as e:
            print(f"Error loading segmentation weights: {e}")
            print("Using untrained U-Net as placeholder.")
    else:
        print(f"Segmentation weights not found at {SEG_MODEL_PATH}. Using untrained U-Net as placeholder.")
    return model

def get_segmentation_mask(img_array, model):
    """
    Returns a binary mask and a colorized overlay.
    """
    preds = model.predict(img_array, verbose=0)
    mask = preds[0]
    
    # Threshold the mask
    binary_mask = (mask > 0.5).astype(np.uint8) * 255
    
    return mask, binary_mask

def apply_mask_to_image(img, mask, alpha=0.5):
    """
    Applies a blue-tinted mask overlay to the image for visualization.
    """
    # Resize mask to original image size
    mask_resized = cv2.resize(mask, (img.shape[1], img.shape[0]))
    
    # Create a blue overlay
    overlay = img.copy()
    overlay[mask_resized > 127] = [255, 0, 0] # Blue in BGR
    
    # Blend
    blended = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    return blended
