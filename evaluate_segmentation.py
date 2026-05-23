import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score, roc_curve
from dataset import get_segmentation_datasets, IMG_SIZE
from segmentation import load_segmentation_model

# Enable memory efficiency
tf.config.run_functions_eagerly(False)

def calculate_dice(y_true, y_pred):
    intersection = np.sum(y_true * y_pred)
    return (2. * intersection) / (np.sum(y_true) + np.sum(y_pred) + 1e-7)

def evaluate():
    print("Loading datasets...")
    image_dir = '../3D_EUS_PAF_v1_Images'
    mask_dir = '../3D_EUS_PAF_v1_Masks'
    
    if not os.path.exists(image_dir) or not os.path.exists(mask_dir):
        print(f"Error: Could not find image or mask directory.")
        return
        
    _, val_ds = get_segmentation_datasets(image_dir, mask_dir, batch_size=8)
    
    print("Loading segmentation model...")
    model = load_segmentation_model()
    if model is None:
        print("Error: Could not load segmentation model!")
        return
        
    print("Evaluating model (this may take a minute depending on dataset size)...")
    y_true_all = []
    y_pred_prob_all = []
    
    for images, masks in val_ds:
        preds = model.predict(images, verbose=0)
        y_true_all.append(masks.numpy().flatten())
        y_pred_prob_all.append(preds.flatten())
        
    y_true_all = np.concatenate(y_true_all)
    y_pred_prob_all = np.concatenate(y_pred_prob_all)
    
    # Binarize predictions
    y_pred_bin = (y_pred_prob_all > 0.5).astype(np.uint8)
    y_true_bin = (y_true_all > 0.5).astype(np.uint8)
    
    print("Calculating metrics...")
    
    # 1. Confusion Matrix
    cm = confusion_matrix(y_true_bin, y_pred_bin)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        # Edge case if all pixels are background or foreground
        print("Warning: Confusion matrix is not 2x2. Skipping some metrics.")
        tn, fp, fn, tp = 0, 0, 0, 0
    
    # 2. Precision
    precision = precision_score(y_true_bin, y_pred_bin, zero_division=0)
    
    # 3. Sensitivity (Recall)
    sensitivity = recall_score(y_true_bin, y_pred_bin, zero_division=0)
    
    # 4. Specificity
    specificity = tn / (tn + fp + 1e-7)
    
    # 5. F1 Score
    f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
    
    # 6. Dice Coefficient
    dice = calculate_dice(y_true_bin, y_pred_bin)
    
    # 7. AUC-ROC
    try:
        auc_roc = roc_auc_score(y_true_bin, y_pred_prob_all)
    except ValueError:
        auc_roc = 0.5 # if only one class exists in true mask
        print("Warning: AUC-ROC calculation failed (likely only one class present in masks).")
        
    # Plot Confusion Matrix
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Segmentation Confusion Matrix (Pixels)')
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ['Background', 'Anomaly'])
    plt.yticks(tick_marks, ['Background', 'Anomaly'])
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    
    # Add text annotations
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
                     
    plt.tight_layout()
    plt.savefig('segmentation_confusion.png')
    plt.close()
    
    # Plot ROC Curve
    try:
        fpr, tpr, _ = roc_curve(y_true_bin, y_pred_prob_all)
        plt.figure()
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {auc_roc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.savefig('segmentation_roc.png')
        plt.close()
    except Exception as e:
        print(f"Skipping ROC plot: {e}")

    print("\n" + "="*50)
    print("SEGMENTATION EVALUATION RESULTS")
    print("="*50)
    print(f"Confusion Matrix: \n{cm}")
    print(f"Precision:         {precision:.4f}")
    print(f"Sensitivity:       {sensitivity:.4f}")
    print(f"Specificity:       {specificity:.4f}")
    print(f"F1 Score:          {f1:.4f}")
    print(f"Dice Coefficient:  {dice:.4f}")
    print(f"AUC-ROC:           {auc_roc:.4f}")
    print("="*50)
    print("Saved plots: segmentation_confusion.png, segmentation_roc.png")

if __name__ == "__main__":
    evaluate()
