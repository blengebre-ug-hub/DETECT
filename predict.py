import os
import glob
import numpy as np
import tensorflow as tf
import cv2
from dataset import IMG_SIZE, CLASS_NAMES, apply_noise_reduction
from explainability import make_gradcam_heatmap
from segmentation import load_segmentation_model, get_segmentation_mask, apply_mask_to_image

def load_classification_model(model_path="best_model.keras"):
    """Load trained classification model."""
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"✓ Classification model loaded: {model_path}")
        return model
    except Exception as e:
        print(f"✗ Error loading classification model: {e}")
        return None

def preprocess_image(img_path):
    """Load and preprocess image for both models."""
    try:
        img = cv2.imread(img_path)
        if img is None:
            print(f"  ✗ Could not read image: {img_path}")
            return None

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_rgb = apply_noise_reduction(img_rgb)
        img_normalized = img_rgb.astype(np.float32)
        img_batch = np.expand_dims(img_normalized, axis=0)

        return img, img_rgb, img_batch
    except Exception as e:
        print(f"  ✗ Error preprocessing: {e}")
        return None

def predict_image(img_path, clf_model, seg_model, save_dir="predictions"):
    """Run classification and segmentation on single image."""
    os.makedirs(save_dir, exist_ok=True)

    result = preprocess_image(img_path)
    if result is None:
        return None

    img, img_rgb, img_batch = result
    basename = os.path.basename(img_path)

    predictions = {}

    # CLASSIFICATION
    if clf_model:
        clf_probs = clf_model.predict(img_batch, verbose=0)[0]
        clf_pred = np.argmax(clf_probs)
        clf_confidence = clf_probs[clf_pred] * 100

        predictions['classification'] = {
            'class': CLASS_NAMES[clf_pred],
            'confidence': clf_confidence,
            'probabilities': {CLASS_NAMES[i]: float(clf_probs[i]) for i in range(len(CLASS_NAMES))}
        }

        print(f"  Classification: {CLASS_NAMES[clf_pred]} ({clf_confidence:.2f}%)")

    # SEGMENTATION
    if seg_model:
        seg_probs, seg_binary = get_segmentation_mask(img_batch, seg_model)
        predictions['segmentation'] = {
            'mask_path': os.path.join(save_dir, f"seg_{basename}"),
            'anomaly_percentage': float(np.mean(seg_binary / 255.0) * 100)
        }

        cv2.imwrite(predictions['segmentation']['mask_path'], seg_binary)
        print(f"  Segmentation: {predictions['segmentation']['anomaly_percentage']:.2f}% anomaly detected")

        # Save overlay
        overlay = apply_mask_to_image(img, seg_binary, alpha=0.4)
        overlay_path = os.path.join(save_dir, f"overlay_{basename}")
        cv2.imwrite(overlay_path, overlay)
        predictions['segmentation']['overlay_path'] = overlay_path

    # GRAD-CAM (Classification Explainability)
    if clf_model:
        try:
            heatmap, preds = make_gradcam_heatmap(img_batch, clf_model, "top_activation")

            heatmap = np.uint8(255 * heatmap)
            jet = tf.keras.utils.get_file.__class__.__bases__[0].__dict__.get('cm')
            if jet is None:
                import matplotlib.pyplot as plt
                jet = plt.cm.get_cmap("jet")

            jet_colors = jet(np.arange(256))[:, :3]
            jet_heatmap = jet_colors[heatmap]
            jet_heatmap_img = tf.keras.utils.array_to_img(jet_heatmap)
            jet_heatmap_img = jet_heatmap_img.resize((IMG_SIZE, IMG_SIZE))
            jet_heatmap_arr = tf.keras.utils.img_to_array(jet_heatmap_img)

            superimposed = jet_heatmap_arr * 0.4 + img_rgb
            superimposed_img = tf.keras.utils.array_to_img(superimposed)

            gradcam_path = os.path.join(save_dir, f"gradcam_{basename}")
            gradcam_bgr = cv2.cvtColor(np.array(superimposed_img), cv2.COLOR_RGB2BGR)
            cv2.imwrite(gradcam_path, gradcam_bgr)

            predictions['explainability'] = {
                'gradcam_path': gradcam_path,
                'explanation': 'Red regions show areas the model focused on for classification'
            }
        except Exception as e:
            print(f"  Note: Grad-CAM generation skipped ({e})")

    return predictions

def batch_predict(image_dir, clf_model, seg_model, save_dir="predictions", pattern="*.[pP][nN][gG]"):
    """Run predictions on multiple images."""
    image_paths = sorted(glob.glob(os.path.join(image_dir, pattern)))

    if not image_paths:
        print(f"✗ No images found in {image_dir}")
        return []

    print(f"\nProcessing {len(image_paths)} images...")
    all_predictions = []

    for i, img_path in enumerate(image_paths, 1):
        print(f"\n[{i}/{len(image_paths)}] {os.path.basename(img_path)}")
        pred = predict_image(img_path, clf_model, seg_model, save_dir)
        if pred:
            all_predictions.append({
                'image': os.path.basename(img_path),
                'predictions': pred
            })

    return all_predictions

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch prediction on ultrasound images")
    parser.add_argument('--image-dir', type=str, default='../3D_EUS_PAF_v1_Images',
                       help='Directory with images to predict on')
    parser.add_argument('--clf-model', type=str, default='best_model.keras',
                       help='Path to classification model')
    parser.add_argument('--seg-model', type=str, default='segmentation_model.keras',
                       help='Path to segmentation model')
    parser.add_argument('--output-dir', type=str, default='predictions',
                       help='Directory to save predictions')
    parser.add_argument('--single', type=str, default=None,
                       help='Predict on single image (if provided, image-dir is ignored)')

    args = parser.parse_args()

    print("="*60)
    print("3D EUS AI System - Batch Prediction")
    print("="*60)

    # Load models
    clf_model = load_classification_model(args.clf_model)
    seg_model = load_segmentation_model()

    if not clf_model and not seg_model:
        print("✗ No models loaded. Exiting.")
        return

    # Run predictions
    if args.single:
        print(f"\nPredicting on single image: {args.single}")
        result = predict_image(args.single, clf_model, seg_model, args.output_dir)
        if result:
            print("\n✓ Prediction complete!")
            import json
            print(json.dumps(result, indent=2))
    else:
        results = batch_predict(args.image_dir, clf_model, seg_model, args.output_dir)
        print(f"\n✓ Processed {len(results)} images")
        print(f"✓ Results saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
