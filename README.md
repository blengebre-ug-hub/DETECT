# Enhanced 3D EUS AI System Pipeline Guide

## Overview
Your system now includes:
- ✅ **Noise Reduction** (bilateral filtering post-augmentation)
- ✅ **2000+ Augmented Images** (286 per class)
- ✅ **Comprehensive Evaluation Metrics** (ROC-AUC, Precision, Recall, F1-score)
- ✅ **Grad-CAM Explainability** (visual attention maps)
- ✅ **Training Curves** (phase 1 & phase 2)

---

## Step 1: Data Augmentation

Generate 2000+ augmented images from your original dataset:

```bash
cd 3D_EUS_AI_System
python augment_data.py
```

**Output:** `augmented_dataset/` directory with ~2000 balanced images
- 286 images per class (7 classes)
- Original images + augmented variations
- Includes: rotation, flipping, zooming, shifting, shearing

---

## Step 2: Training

Train the model with transfer learning (2 phases):

```bash
python train.py
```

**Output Files:**
- `best_model.keras` - Best model checkpoint
- `phase1_history.png` - Feature extraction phase curves
- `phase2_history.png` - Fine-tuning phase curves

**What happens:**
- **Phase 1:** Freeze EfficientNetB0, train classification head (20 epochs)
- **Phase 2:** Unfreeze top 20 layers, fine-tune entire model (15 epochs)
- **Noise Reduction:** Applied during training augmentation
- **Early Stopping:** Stops if val_loss doesn't improve (patience=5)

---

## Step 3: Evaluation

Comprehensive evaluation with all metrics:

```bash
python evaluate.py
```

**Output Files:**
- `confusion_matrix.png` - Confusion matrix heatmap
- `roc_curves.png` - ROC curves for each class
- `gradcam_evaluation/` - 10 sample Grad-CAM visualizations

**Metrics Reported:**
- Test Accuracy & Loss
- Per-class: Precision, Recall, F1-score
- Macro-averaged: Precision, Recall, F1-score
- ROC-AUC score for each class

---

## Step 4: Explainability

Generate Grad-CAM visualizations:

```bash
python explainability.py
```

**Output:** `gradcam_results/` directory with attention maps

---

## Pipeline Architecture

```
Raw Ultrasound Images (224×224)
        ↓
[Preprocessing: Resize + RGB Conversion]
        ↓
[Data Augmentation: Rotate, Flip, Zoom, Shift]
        ↓
[Noise Reduction: Bilateral Filtering] ← NEW
        ↓
[Batch Processing]
        ↓
[EfficientNetB0 Feature Extraction]
        ↓
[Global Average Pooling]
        ↓
[Dense + Softmax Classification Layer]
        ↓
[Predictions + Probabilities]
        ↓
[Grad-CAM Visualization] ← NEW
```

## Sample Prediction Grid
Run batch prediction and save a sample grid of predictions:
```bash
python predict.py --image-dir ../3D_EUS_PAF_v1_Images --output-dir predictions --grid
```
This creates `predictions/sample_prediction_grid.png` with labeled sample tiles.

---

## Key Improvements

| Component | Improvement |
|-----------|------------|
| **Dataset Size** | 160 → 2000+ images |
| **Image Quality** | Added noise reduction filter |
| **Evaluation** | Basic → Comprehensive metrics |
| **Interpretability** | No explanation → Grad-CAM heatmaps |
| **Visualization** | Training curves + evaluation plots |

---

## Augmentation Parameters

Located in `augment_data.py`:
```python
datagen = ImageDataGenerator(
    rotation_range=30,          # ±30° rotation
    width_shift_range=0.1,      # 10% horizontal shift
    height_shift_range=0.1,     # 10% vertical shift
    shear_range=0.15,           # 15% shearing
    zoom_range=0.15,            # 15% zoom in/out
    horizontal_flip=True,       # Random horizontal flip
)
```

---

## Noise Reduction Parameters

Located in `dataset.py`:
```python
cv2.bilateralFilter(
    image,
    d=9,              # Diameter of pixel neighborhood
    sigmaColor=75,    # Filter sigma in color space
    sigmaSpace=75     # Filter sigma in coordinate space
)
```

---

## Troubleshooting

**Issue:** Augmented dataset not being used
- Check if `augmented_dataset/` has >500 files
- Run `augment_data.py` again

**Issue:** Grad-CAM visualization fails
- Ensure `best_model.keras` exists
- Check if EfficientNetB0 layer names are correct

**Issue:** Out of memory
- Reduce batch_size in `train.py` (currently 16)
- Or reduce augmentation target in `augment_data.py`

---

## Next Steps

For your thesis, ensure you include:
1. ✅ Test Accuracy
2. ✅ Test Loss
3. ✅ Confusion Matrix
4. ✅ Precision/Recall/F1-score
5. ✅ ROC-AUC
6. ✅ Grad-CAM Visualizations
7. ✅ Accuracy/Loss Curves
# detect_final_pro
# detect_final_pro
# detect_final_pro
# DETECT
# DETECT
# DETECT
# DETECT
