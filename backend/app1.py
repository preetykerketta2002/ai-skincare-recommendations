from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image

app = Flask(__name__)
CORS(app)

model = load_model("skin_model_final.h5")

classes = [
    "acne_inflammatory",
    "acne_noninflammatory",
    "hyperpigmentation",
    "wrinkles"
]

# ---------------- ROUTINES ----------------
routines = {
    "acne_inflammatory": {
        "morning": ["Gentle cleanser", "Oil-free moisturizer", "Sunscreen SPF 50"],
        "night": ["Benzoyl peroxide", "Light moisturizer"]
    },
    "acne_noninflammatory": {
        "morning": ["Salicylic acid cleanser", "Niacinamide serum", "Sunscreen"],
        "night": ["Cleanser", "Niacinamide", "Moisturizer"]
    },
    "hyperpigmentation": {
        "morning": ["Vitamin C serum", "Sunscreen SPF 50"],
        "night": ["Niacinamide", "Moisturizer"]
    },
    "wrinkles": {
        "morning": ["Hyaluronic acid", "Sunscreen"],
        "night": ["Retinol", "Moisturizer"]
    }
}

products = {
    "acne_inflammatory": ["CeraVe Cleanser", "Benzoyl Peroxide Gel"],
    "acne_noninflammatory": ["Salicylic Acid Cleanser", "Niacinamide Serum"],
    "hyperpigmentation": ["Vitamin C Serum", "SPF 50 Sunscreen"],
    "wrinkles": ["Retinol Cream", "Hyaluronic Acid Serum"]
}

def get_severity(conf):
    if conf > 0.85:
        return "High"
    elif conf > 0.6:
        return "Moderate"
    return "Low"


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]
    img = Image.open(file).convert("RGB")
    img = img.resize((224, 224))
    img = np.array(img) / 255.0
    img = np.expand_dims(img, axis=0)

    preds = model.predict(img)[0]

    threshold = 0.30  # MULTI-LABEL

    detected = []
    all_morning = []
    all_night = []
    all_products = []

    for i, prob in enumerate(preds):
        if prob >= threshold:
            detected.append({
                "condition": classes[i],
                "confidence": float(prob)
            })

            all_morning += routines[classes[i]]["morning"]
            all_night += routines[classes[i]]["night"]
            all_products += products.get(classes[i], [])

    if not detected:
        top = int(np.argmax(preds))
        detected = [{
            "condition": classes[top],
            "confidence": float(preds[top])
        }]

        all_morning = routines[classes[top]]["morning"]
        all_night = routines[classes[top]]["night"]
        all_products = products.get(classes[top], [])

    return jsonify({
        "detected_conditions": detected,
        "confidence": float(max([d["confidence"] for d in detected])),
        "severity": get_severity(max([d["confidence"] for d in detected])),

        "routine": {
            "morning": list(set(all_morning)),
            "night": list(set(all_night))
        },

        "products": list(set(all_products))
    })


if __name__ == "__main__":
    app.run(debug=True)