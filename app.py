import os
import base64
import numpy as np
import tensorflow as tf
import cv2
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dataset import IMG_SIZE, CLASS_NAMES
from explainability import get_img_array, make_gradcam_heatmap
from segmentation import load_segmentation_model, get_segmentation_mask, apply_mask_to_image

app = Flask(__name__)
CORS(app)

# Load Classification Model
MODEL_PATH = "best_model.keras"
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Classification model loaded successfully.")
except Exception as e:
    print(f"Error loading classification model: {e}")
    model = None

# Load Segmentation Model
try:
    seg_model = load_segmentation_model()
    print("Segmentation model initialized.")
except Exception as e:
    print(f"Error initializing segmentation model: {e}")
    seg_model = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded on server."}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    # Read image from request
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        return jsonify({"error": "Invalid image file."}), 400

    # Save temp original for processing
    temp_path = "temp_uploaded.png"
    cv2.imwrite(temp_path, img)

    # Prepare for model
    img_array = get_img_array(temp_path, size=IMG_SIZE)
    
    # 1. Segmentation Stage
    seg_mask_raw, seg_mask_binary = get_segmentation_mask(img_array, seg_model)
    segmented_viz = apply_mask_to_image(img, seg_mask_binary)
    
    # Encode segmentation visualization
    _, buffer_seg = cv2.imencode('.png', segmented_viz)
    base64_seg = base64.b64encode(buffer_seg).decode('utf-8')

    # --- Isolate ROI for Classification ---
    # Resize mask to match original image dimensions
    mask_resized = cv2.resize(seg_mask_binary, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    # Convert single channel mask to 3 channels
    mask_3d = cv2.merge([mask_resized, mask_resized, mask_resized])
    # Apply the mask: keep only tissue within the U-Net prediction, black out the rest
    isolated_img = cv2.bitwise_and(img, mask_3d)
    
    # Save temporarily to load through the standard get_img_array function
    isolated_path = "temp_isolated.png"
    cv2.imwrite(isolated_path, isolated_img)

    # 2. Classification Stage (using Grad-CAM for explainability)
    last_conv_layer_name = "top_activation" # For EfficientNetB0/B3
    
    # The classification model expects a specific size (e.g., 224) 
    # Pass the ISOLATED image to the classification model
    try:
        expected_size = model.input_shape[1]
        if expected_size is None:
            expected_size = 224
        img_array_class = get_img_array(isolated_path, size=expected_size)
    except Exception:
        img_array_class = get_img_array(isolated_path, size=224)
        
    heatmap, preds = make_gradcam_heatmap(img_array_class, model, last_conv_layer_name)
    
    pred_index = np.argmax(preds)
    raw_class = CLASS_NAMES[pred_index]
    confidence = float(np.max(preds))
    
    # Map raw classes to readable clinical names
    readable_mapping = {
        "Inter_Sph_Fistula": "Intersphincteric Fistula",
        "Inter_Sph_Abscess": "Intersphincteric Abscess",
        "Trans_Sph_Fistula": "Transsphincteric Fistula",
        "Supra_Sph_Fistla": "Suprasphincteric Fistula",
        "Pre_Anal_Abscess": "Pre-Anal Abscess",
        "Ischiorectal_Abscess": "Ischiorectal Abscess",
        "Supra_Levator_Abscess": "Supralevator Abscess"
    }
    
    pred_class = readable_mapping.get(raw_class, raw_class)
    
    # Generate Detection Result
    if "Fistula" in pred_class:
        detection_result = "Fistula Detected"
    elif "Abscess" in pred_class:
        detection_result = "Abscess Detected"
    else:
        detection_result = "Anomaly Detected"
        
    # Generate Clinical Summary
    conf_text = "high confidence" if confidence > 0.8 else ("moderate confidence" if confidence > 0.5 else "low confidence")
    summary = f"AI analysis suggests a {pred_class.lower()} with {conf_text}. The segmentation highlights the suspected anatomy, and the heatmap shows the classification focus."
    
    # 3. Grad-CAM Visualization
    heatmap_resized = cv2.resize(heatmap, (img.shape[1], img.shape[0]))
    heatmap_resized = np.uint8(255 * heatmap_resized)
    jet = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
    superimposed_img = cv2.addWeighted(img, 0.6, jet, 0.4, 0)
    
    # Encode superimposed image
    _, buffer_cam = cv2.imencode('.png', superimposed_img)
    base64_heatmap = base64.b64encode(buffer_cam).decode('utf-8')
    
    os.remove(temp_path)
    if os.path.exists(isolated_path):
        os.remove(isolated_path)
    
    return jsonify({
        "detection_result": detection_result,
        "class": pred_class,
        "confidence": round(confidence * 100, 2),
        "summary": summary,
        "segmentation_mask": f"data:image/png;base64,{base64_seg}",
        "heatmap": f"data:image/png;base64,{base64_heatmap}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
