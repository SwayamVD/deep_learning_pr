"""
Flask backend for Devanagari Character Classifier.
Serves prediction API for the ResNet-18 model trained in the notebook.
"""

import os
import io
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image

# --------------------------------------------------------------------------- #
# App setup
# --------------------------------------------------------------------------- #
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)  # Allow requests from the frontend

# --------------------------------------------------------------------------- #
# Devanagari class labels (46 classes — matches notebook training order)
# --------------------------------------------------------------------------- #
CLASS_LABELS = [
    "character_01_ka",
    "character_02_kha",
    "character_03_ga",
    "character_04_gha",
    "character_05_kna",
    "character_06_cha",
    "character_07_chha",
    "character_08_ja",
    "character_09_jha",
    "character_10_yna",
    "character_11_taamatar",
    "character_12_thaa",
    "character_13_daa",
    "character_14_dhaa",
    "character_15_adna",
    "character_16_tabala",
    "character_17_tha",
    "character_18_da",
    "character_19_dha",
    "character_20_na",
    "character_21_pa",
    "character_22_pha",
    "character_23_ba",
    "character_24_bha",
    "character_25_ma",
    "character_26_yaw",
    "character_27_ra",
    "character_28_la",
    "character_29_waw",
    "character_30_motosaw",
    "character_31_petchiryakha",
    "character_32_patalosaw",
    "character_33_ha",
    "character_34_chhya",
    "character_35_tra",
    "character_36_gya",
    "digit_0",
    "digit_1",
    "digit_2",
    "digit_3",
    "digit_4",
    "digit_5",
    "digit_6",
    "digit_7",
    "digit_8",
    "digit_9",
]

# Human-readable display names
DISPLAY_NAMES = {
    "character_01_ka": "क (Ka)",
    "character_02_kha": "ख (Kha)",
    "character_03_ga": "ग (Ga)",
    "character_04_gha": "घ (Gha)",
    "character_05_kna": "ङ (Kna)",
    "character_06_cha": "च (Cha)",
    "character_07_chha": "छ (Chha)",
    "character_08_ja": "ज (Ja)",
    "character_09_jha": "झ (Jha)",
    "character_10_yna": "ञ (Yna)",
    "character_11_taamatar": "ट (Taamatar)",
    "character_12_thaa": "ठ (Thaa)",
    "character_13_daa": "ड (Daa)",
    "character_14_dhaa": "ढ (Dhaa)",
    "character_15_adna": "ण (Adna)",
    "character_16_tabala": "त (Tabala)",
    "character_17_tha": "थ (Tha)",
    "character_18_da": "द (Da)",
    "character_19_dha": "ध (Dha)",
    "character_20_na": "न (Na)",
    "character_21_pa": "प (Pa)",
    "character_22_pha": "फ (Pha)",
    "character_23_ba": "ब (Ba)",
    "character_24_bha": "भ (Bha)",
    "character_25_ma": "म (Ma)",
    "character_26_yaw": "य (Yaw)",
    "character_27_ra": "र (Ra)",
    "character_28_la": "ल (La)",
    "character_29_waw": "व (Waw)",
    "character_30_motosaw": "श (Motosaw)",
    "character_31_petchiryakha": "ष (Petchiryakha)",
    "character_32_patalosaw": "स (Patalosaw)",
    "character_33_ha": "ह (Ha)",
    "character_34_chhya": "क्ष (Chhya)",
    "character_35_tra": "त्र (Tra)",
    "character_36_gya": "ज्ञ (Gya)",
    "digit_0": "० (0)",
    "digit_1": "१ (1)",
    "digit_2": "२ (2)",
    "digit_3": "३ (3)",
    "digit_4": "४ (4)",
    "digit_5": "५ (5)",
    "digit_6": "६ (6)",
    "digit_7": "७ (7)",
    "digit_8": "८ (8)",
    "digit_9": "९ (9)",
}

# --------------------------------------------------------------------------- #
# Model loading — lazy, on first request
# --------------------------------------------------------------------------- #
model = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "devanagari_resnet18.h5")


def load_model():
    """Load the Keras model once and cache it in `model` global."""
    global model
    if model is not None:
        return model, None

    if not os.path.exists(MODEL_PATH):
        return None, (
            f"Model file not found at {MODEL_PATH}. "
            "Please run the notebook and save the model first — "
            "add `model.save('devanagari_resnet18.h5')` after training, "
            "then copy the .h5 file to the backend/ folder."
        )

    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(MODEL_PATH)
        return model, None
    except Exception as exc:
        return None, f"Failed to load model: {str(exc)}"


# --------------------------------------------------------------------------- #
# Image preprocessing — matches exactly what the notebook does
# --------------------------------------------------------------------------- #
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Convert raw image bytes into a (1, 32, 32, 1) float32 array,
    normalized to [0, 1].

    Training data format: white characters on BLACK background.
    Canvas now draws: white strokes on BLACK background — matches training data directly.

    Pipeline:
      1. Convert to grayscale
      2. Crop to the bounding box of the bright stroke pixels (+ padding)
      3. Make crop square (preserve aspect ratio)
      4. Resize to 32x32
      5. Normalize to [0, 1]
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale

    # The character strokes are bright (white on black).
    # Crop tightly to the bright region so the character fills the frame,
    # exactly like the training images.
    bbox = img.getbbox()  # bounding box of non-zero (bright) pixels
    if bbox:
        pad = 4
        w, h = img.size
        x0 = max(0, bbox[0] - pad)
        y0 = max(0, bbox[1] - pad)
        x1 = min(w, bbox[2] + pad)
        y1 = min(h, bbox[3] + pad)

        # Make the crop square so resize doesn't squash the character
        cw = x1 - x0
        ch = y1 - y0
        if cw > ch:
            diff = cw - ch
            y0 = max(0, y0 - diff // 2)
            y1 = min(h, y0 + cw)
        elif ch > cw:
            diff = ch - cw
            x0 = max(0, x0 - diff // 2)
            x1 = min(w, x0 + ch)

        img = img.crop((x0, y0, x1, y1))

    # Resize to 32x32 — same as training
    img = img.resize((32, 32), Image.LANCZOS)

    arr = np.array(img, dtype=np.float32) / 255.0  # normalize to [0, 1]
    arr = arr.reshape(1, 32, 32, 1)
    return arr


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #

@app.route("/favicon.svg", methods=["GET"])
def favicon():
    """Serve the SVG favicon."""
    return send_from_directory(FRONTEND_DIR, "favicon.svg", mimetype="image/svg+xml")


@app.route("/", methods=["GET"])
def index():
    """Serve the frontend."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>", methods=["GET"])
def frontend_files(filename):
    """Serve any frontend static file (CSS, JS)."""
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/api/status", methods=["GET"])
def status():
    """Health check — also reports whether the model is loaded."""
    m, err = load_model()
    if err:
        return jsonify({"status": "no_model", "message": err}), 200
    return jsonify({"status": "ready", "num_classes": len(CLASS_LABELS)}), 200


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Accepts a multipart/form-data upload with key `image`.
    Returns JSON with the top-5 predictions.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    m, err = load_model()
    if err:
        return jsonify({"error": err}), 503

    try:
        image_bytes = image_file.read()
        input_arr = preprocess_image(image_bytes)
        predictions = m.predict(input_arr, verbose=0)[0]  # shape (46,)

        # Build top-5 results
        top5_idx = np.argsort(predictions)[::-1][:5]
        results = []
        for idx in top5_idx:
            label = CLASS_LABELS[idx]
            results.append(
                {
                    "rank": int(len(results) + 1),
                    "class_id": int(idx),
                    "label": label,
                    "display_name": DISPLAY_NAMES.get(label, label),
                    "confidence": float(predictions[idx]),
                    "confidence_pct": f"{predictions[idx]*100:.2f}%",
                }
            )

        return jsonify(
            {
                "success": True,
                "prediction": results[0],
                "top5": results,
                "all_probs": {
                    CLASS_LABELS[i]: float(predictions[i])
                    for i in range(len(CLASS_LABELS))
                },
            }
        )

    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {str(exc)}"}), 500


@app.route("/api/classes", methods=["GET"])
def get_classes():
    """Return the full list of class labels."""
    return jsonify(
        {
            "classes": [
                {"id": i, "label": CLASS_LABELS[i], "display": DISPLAY_NAMES.get(CLASS_LABELS[i], CLASS_LABELS[i])}
                for i in range(len(CLASS_LABELS))
            ]
        }
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
