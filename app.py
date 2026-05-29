import os
import base64
import numpy as np
import tensorflow as tf
import cv2
import smtplib
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from dataset import IMG_SIZE, CLASS_NAMES
from explainability import get_img_array, make_gradcam_heatmap
from segmentation import load_segmentation_model, get_segmentation_mask, apply_mask_to_image

app = Flask(__name__)
CORS(app)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "best_model.keras")
_model_cache = None
_seg_model_cache = None


def get_classification_model():
    global _model_cache
    if _model_cache is None:
        try:
            _model_cache = tf.keras.models.load_model(MODEL_PATH)
            print("Classification model loaded successfully.")
        except Exception as e:
            print(f"Error loading classification model: {e}")
            _model_cache = None
    return _model_cache


def get_segmentation_model():
    global _seg_model_cache
    if _seg_model_cache is None:
        try:
            _seg_model_cache = load_segmentation_model()
            print("Segmentation model initialized.")
        except Exception as e:
            print(f"Error initializing segmentation model: {e}")
            _seg_model_cache = None
    return _seg_model_cache

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    model = get_classification_model()
    seg_model = get_segmentation_model()

    if model is None or seg_model is None:
        return jsonify({"error": "Models are not available on the server."}), 500

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

    # Use system temp directory for temporary files
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "temp_uploaded.png")
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
    isolated_path = os.path.join(temp_dir, "temp_isolated.png")
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

@app.route("/send_email", methods=["POST"])
def send_email():
    data = request.json
    if not data or 'email' not in data:
        return jsonify({"error": "No email provided."}), 400
        
    recipient = data['email']
    detection_result = data.get('detection_result', 'N/A')
    pred_class = data.get('pred_class', 'N/A')
    confidence = data.get('confidence', 'N/A')
    summary = data.get('summary', 'N/A')
    
    # Environment variables for SMTP
    # If not set, we'll log it as a simulation (useful for testing without real creds)
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('SENDER_PASSWORD')
    
    # Create HTML Email Content
    html_content = f"""
    <html>
      <body style="font-family: 'Inter', Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #050508; padding: 20px; border-radius: 12px 12px 0 0; text-align: center;">
            <h2 style="color: #00d2ff; margin: 0; font-family: 'Outfit', sans-serif;">EUS-AI Vision</h2>
            <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">Diagnostic Analysis Report</p>
        </div>
        <div style="background-color: #ffffff; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none;">
            <p style="font-size: 16px; margin-top: 0;">Hello,</p>
            <p style="font-size: 16px;">Your AI Diagnostic Analysis is complete. Here are the detailed results of the scan:</p>
            
            <div style="background: linear-gradient(135deg, rgba(0, 210, 255, 0.05), rgba(58, 123, 213, 0.05)); padding: 25px; border-left: 4px solid #00d2ff; border-radius: 8px; margin: 25px 0;">
                <p style="margin: 0 0 15px 0; font-size: 15px;"><strong style="color: #64748b; text-transform: uppercase; font-size: 12px; display: block; margin-bottom: 5px;">Detection Result</strong> <span style="font-size: 18px; font-weight: 600; color: #0f172a;">{detection_result}</span></p>
                <p style="margin: 0 0 15px 0; font-size: 15px;"><strong style="color: #64748b; text-transform: uppercase; font-size: 12px; display: block; margin-bottom: 5px;">Classification</strong> <span style="display: inline-block; background-color: #f1f5f9; padding: 6px 12px; border-radius: 6px; font-weight: 600; color: #3b82f6;">{pred_class}</span></p>
                <p style="margin: 0 0 15px 0; font-size: 15px;"><strong style="color: #64748b; text-transform: uppercase; font-size: 12px; display: block; margin-bottom: 5px;">AI Confidence Score</strong> <span style="font-size: 20px; font-weight: 700; color: #10b981;">{confidence}%</span></p>
                <p style="margin: 0; font-size: 15px;"><strong style="color: #64748b; text-transform: uppercase; font-size: 12px; display: block; margin-bottom: 5px;">Clinical Summary</strong> <span style="color: #334155;">{summary}</span></p>
            </div>
            
            <p style="font-size: 13px; color: #64748b; font-style: italic; background-color: #f8fafc; padding: 15px; border-radius: 6px;">
                <strong>Disclaimer:</strong> This is an AI-assisted analysis intended to support, not replace, professional medical judgment. All results should be reviewed by a clinical professional.
            </p>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
            <p style="font-size: 14px; color: #64748b; margin: 0;">Best regards,<br><strong style="color: #0f172a;">3D EUS AI System</strong></p>
        </div>
      </body>
    </html>
    """
    
    if not sender_email or not sender_password:
        # Simulate sending if credentials are not configured
        print(f"\n--- SIMULATED EMAIL TO {recipient} ---")
        print("No SENDER_EMAIL or SENDER_PASSWORD environment variables found. Simulating email.")
        print(f"Subject: Your 3D EUS AI Diagnostic Report")
        print(html_content)
        print("--------------------------------------\n")
        return jsonify({"message": "Email simulation successful (credentials not configured)."})
        
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "Your 3D EUS AI Diagnostic Report"
        
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return jsonify({"message": "Email sent successfully!"})
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host="0.0.0.0", port=port, debug=debug)
