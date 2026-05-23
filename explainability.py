import os
import glob
import numpy as np
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
from dataset import IMG_SIZE, CLASS_NAMES, apply_noise_reduction

def get_img_array(img_path, size):
    img = cv2.imread(img_path)
    if img is None: return None
    img = cv2.resize(img, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = apply_noise_reduction(img)
    array = tf.cast(tf.expand_dims(img, axis=0), tf.float32)
    return array

def make_gradcam_heatmap(img_array, model, last_conv_layer_name, pred_index=None):
    last_conv_layer = model.get_layer(last_conv_layer_name)
    last_conv_layer_model = tf.keras.Model(model.inputs, last_conv_layer.output)

    classifier_input = tf.keras.Input(shape=last_conv_layer.output.shape[1:])
    x = classifier_input

    layer_idx = model.layers.index(last_conv_layer)
    for layer in model.layers[layer_idx+1:]:
        x = layer(x)

    classifier_model = tf.keras.Model(classifier_input, x)

    with tf.GradientTape() as tape:
        last_conv_layer_output = last_conv_layer_model(img_array)
        tape.watch(last_conv_layer_output)

        preds = classifier_model(last_conv_layer_output)
        if pred_index is None:
            pred_index = tf.argmax(preds[0])
        class_channel = preds[:, pred_index]

    grads = tape.gradient(class_channel, last_conv_layer_output)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    last_conv_layer_output = last_conv_layer_output[0]
    heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-10)
    return heatmap.numpy(), preds[0]

def save_and_display_gradcam(img_path, heatmap, preds, cam_path="cam.jpg", alpha=0.4):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

    heatmap = np.uint8(255 * heatmap)
    jet = plt.cm.get_cmap("jet")
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap]

    jet_heatmap = tf.keras.utils.array_to_img(jet_heatmap)
    jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
    jet_heatmap = tf.keras.utils.img_to_array(jet_heatmap)

    superimposed_img = jet_heatmap * alpha + img
    superimposed_img = tf.keras.utils.array_to_img(superimposed_img)

    pred_class = CLASS_NAMES[np.argmax(preds)]
    confidence = np.max(preds) * 100

    cv_img = np.array(superimposed_img)
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
    cv2.putText(cv_img, f"{pred_class} ({confidence:.1f}%)", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imwrite(cam_path, cv_img)
    print(f"Saved Grad-CAM to {cam_path}")

def run_explainability():
    try:
        model = tf.keras.models.load_model("best_model.keras")
    except Exception as e:
        print(f"Could not load model: {e}")
        return

    image_dir = '../3D_EUS_PAF_v1_Images'
    image_paths = glob.glob(os.path.join(image_dir, '*.[pP][nN][gG]'))

    if not image_paths:
        print("No images found.")
        return

    os.makedirs("gradcam_results", exist_ok=True)

    last_conv_layer_name = "top_activation"

    for i, img_path in enumerate(image_paths[:5]):
        img_array = get_img_array(img_path, size=IMG_SIZE)
        if img_array is None:
            continue

        heatmap, preds = make_gradcam_heatmap(img_array, model, last_conv_layer_name)

        base_name = os.path.basename(img_path)
        save_path = os.path.join("gradcam_results", f"cam_{base_name}")

        save_and_display_gradcam(img_path, heatmap, preds, cam_path=save_path)

def generate_gradcam_batch(model, images, labels, output_dir="gradcam_batch"):
    """Generate Grad-CAM for a batch of images for evaluation purposes."""
    os.makedirs(output_dir, exist_ok=True)
    last_conv_layer_name = "top_activation"

    for idx, (img, label) in enumerate(zip(images[:10], labels[:10])):
        img_expanded = np.expand_dims(img, axis=0).astype(np.float32)

        heatmap, preds = make_gradcam_heatmap(img_expanded, model, last_conv_layer_name)

        heatmap = np.uint8(255 * heatmap)
        jet = plt.cm.get_cmap("jet")
        jet_colors = jet(np.arange(256))[:, :3]
        jet_heatmap = jet_colors[heatmap]

        jet_heatmap_img = tf.keras.utils.array_to_img(jet_heatmap)
        jet_heatmap_img = jet_heatmap_img.resize((IMG_SIZE, IMG_SIZE))
        jet_heatmap_arr = tf.keras.utils.img_to_array(jet_heatmap_img)

        superimposed = jet_heatmap_arr * 0.4 + img
        superimposed_img = tf.keras.utils.array_to_img(superimposed)

        cv_img = np.array(superimposed_img)
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)

        pred_class = CLASS_NAMES[np.argmax(preds)]
        true_class = CLASS_NAMES[label]
        confidence = np.max(preds) * 100

        text = f"Pred: {pred_class} ({confidence:.1f}%) | True: {true_class}"
        cv2.putText(cv_img, text, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        out_path = os.path.join(output_dir, f"sample_{idx:03d}_{true_class}.png")
        cv2.imwrite(out_path, cv_img)

    print(f"Generated {min(10, len(images))} Grad-CAM visualizations in {output_dir}/")

if __name__ == "__main__":
    run_explainability()
