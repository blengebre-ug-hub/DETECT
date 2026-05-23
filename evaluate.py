import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score, roc_curve, auc
from sklearn.preprocessing import label_binarize
from dataset import get_datasets, CLASS_NAMES
from explainability import generate_gradcam_batch

# Enable memory efficiency
tf.config.run_functions_eagerly(False)

def evaluate():
    image_dir = '../3D_EUS_PAF_v1_Images'
    _, _, test_ds, paths_test, y_test, _, _ = get_datasets(image_dir, batch_size=8)

    try:
        model = tf.keras.models.load_model("best_model.keras")
        print("Loaded best_model.keras successfully.")
    except Exception as e:
        print(f"Could not load model: {e}")
        return

    print("Evaluating model...")
    test_loss, test_acc = model.evaluate(test_ds, verbose=0)
    print(f"\n{'='*60}")
    print(f"TEST SET PERFORMANCE")
    print(f"{'='*60}")
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Test Loss: {test_loss:.4f}")

    y_pred_probs = model.predict(test_ds)
    y_pred = np.argmax(y_pred_probs, axis=1)

    y_true = []
    for images, labels in test_ds:
        y_true.extend(labels.numpy())
    y_true = np.array(y_true)

    unique_labels = np.unique(y_true)
    target_names = [CLASS_NAMES[i] for i in unique_labels]

    print(f"\n{'='*60}")
    print(f"CLASSIFICATION REPORT")
    print(f"{'='*60}")
    print(classification_report(y_true, y_pred, labels=unique_labels, target_names=target_names))

    precision_macro = precision_score(y_true, y_pred, labels=unique_labels, average='macro', zero_division=0)
    recall_macro = recall_score(y_true, y_pred, labels=unique_labels, average='macro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, labels=unique_labels, average='macro', zero_division=0)

    print(f"\n{'='*60}")
    print(f"AGGREGATED METRICS (Macro Average)")
    print(f"{'='*60}")
    print(f"Precision (Macro): {precision_macro:.4f}")
    print(f"Recall (Macro):    {recall_macro:.4f}")
    print(f"F1-Score (Macro):  {f1_macro:.4f}")

    cm = confusion_matrix(y_true, y_pred, labels=unique_labels)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=target_names, yticklabels=target_names, cbar_kws={'label': 'Count'})
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    plt.title('Confusion Matrix', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=300)
    print("\nSaved confusion_matrix.png")

    try:
        y_true_bin = label_binarize(y_true, classes=unique_labels)
        if len(unique_labels) > 2:
            roc_auc_scores = []
            plt.figure(figsize=(10, 8))

            for i, label_idx in enumerate(unique_labels):
                fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_pred_probs[:len(y_true), label_idx])
                roc_auc = auc(fpr, tpr)
                roc_auc_scores.append(roc_auc)
                plt.plot(fpr, tpr, label=f'{CLASS_NAMES[label_idx]} (AUC = {roc_auc:.3f})')

            plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
            plt.xlabel('False Positive Rate', fontsize=12)
            plt.ylabel('True Positive Rate', fontsize=12)
            plt.title('ROC Curves (One-vs-Rest)', fontsize=14, fontweight='bold')
            plt.legend(loc='lower right')
            plt.tight_layout()
            plt.savefig('roc_curves.png', dpi=300)
            print("Saved roc_curves.png")

            print(f"\n{'='*60}")
            print(f"ROC-AUC SCORES (One-vs-Rest)")
            print(f"{'='*60}")
            for label_idx, auc_score in zip(unique_labels, roc_auc_scores):
                print(f"{CLASS_NAMES[label_idx]}: {auc_score:.4f}")
            print(f"Mean ROC-AUC: {np.mean(roc_auc_scores):.4f}")
    except Exception as e:
        print(f"ROC-AUC computation skipped: {e}")

    print(f"\n{'='*60}")
    print(f"GENERATING GRAD-CAM VISUALIZATIONS")
    print(f"{'='*60}")
    try:
        images, labels = next(iter(test_ds))
        X_test_batch = images.numpy()
        y_test_batch = labels.numpy()
        generate_gradcam_batch(model, X_test_batch, y_test_batch, output_dir="gradcam_evaluation")
    except Exception as e:
        print(f"Grad-CAM generation skipped: {e}")

    plt.close('all')
    print("\nEvaluation complete!")

if __name__ == "__main__":
    evaluate()
