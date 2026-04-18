import os
import numpy as np
import random
import cv2
# Assuming tensorflow and keras imports are valid
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from functools import wraps
from functools import lru_cache
from flask import Flask, request, render_template, jsonify, send_file, abort
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS
import logging
import re
import csv
import os
import pandas as pd
import json
from urllib import request as urllib_request
from urllib import error as urllib_error
from dotenv import load_dotenv

load_dotenv()

# -------------------- Logging Setup --------------------
def setup_logger():
    """Set up a simple console logger."""
    logger = logging.getLogger("TomatoApp")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger

# -------------------- Flask setup --------------------
app = Flask(__name__, template_folder='./templates', static_folder='./static')
CORS(app)
log = setup_logger()

# -------------------- Global variables --------------------
selected_language = 'en'
camera = cv2.VideoCapture()

# Load model once at startup (not inside the function)
MODEL_PATH = 'model/model_tomato.h5'

try:
    model = load_model(MODEL_PATH)
except Exception as e:
    log.error(f"Failed to load model at {MODEL_PATH}. Prediction will fail. Error: {e}")
    # Define a placeholder model to prevent app crash if model loading fails
    # In a real app, you would handle this more gracefully.
    class MockModel:
        def predict(self, x):
            return np.zeros((1, 10))
    model = MockModel()

# Class labels in the same order used during training
CLASS_NAMES = [
    "Tomato Mosaic Virus",
    "Target Spot",
    "Bacterial Spot",
    "Early Blight",
    "Late Blight",
    "Leaf Mold",
    "Septoria Leaf Spot",
    "Spider Mites",
    "Bacterial Speck",
    "Healthy"
]

def model_predict(img_bytes):
    """Predict tomato disease using the trained CNN model."""
    try:
        # Check if the model is a placeholder
        if not hasattr(model, 'predict'):
             raise RuntimeError("Model not loaded. Cannot predict.")
             
        # Convert bytes to OpenCV image
        npimg = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        # Use the correct training image size (64x64)
        img = cv2.resize(img, (64, 64))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        # Make prediction
        preds = model.predict(img)
        confidence = float(np.max(preds) * 100)
        label = CLASS_NAMES[np.argmax(preds)]

        return {"label": label, "confidence score": round(confidence, 2)}
    
    except Exception as e:
        log.error(f"Prediction error: {e}")
        return {"label": "Error in prediction", "confidence score": "None"}


# -------------------- Detailed Descriptions (Point-wise) --------------------
# ... (DISEASE_DESCRIPTIONS remains the same) ...
DISEASE_DESCRIPTIONS = {
    "Tomato Mosaic Virus": (
        "1. Symptoms: Mosaic patterns on leaves with alternating light and dark green areas. Leaves curl and distort; fruit may be malformed or mottled. Stunted growth and severe infection affecting the entire plant.\n"
        "2. Incubation/Progression: Symptoms appear within 7 to 10 days. Systemic infection can last the whole season; severely affected plants may die within 2 to 3 weeks.\n"
        "3. Yield Loss & Economic Impact: Yield reduction of 30 to 70 percent. Infected fruits often unsellable due to distortion or discoloration.\n"
        "4. Environmental Conditions Favoring Disease: Dry and warm weather; mechanical transmission through contaminated hands, tools, and equipment.\n"
        "5. Spread Mechanism / Vectors: Spread by aphids, thrips, insect vectors, seeds, tools, and physical contact.\n"
        "6. Treatment / Chemical Control: No chemical cure; infected plants must be removed immediately to prevent spread.\n"
        "7. Biological Control / Natural Predators: Limited biological control; controlling aphid populations can reduce virus transmission.\n"
        "8. Cultural & Agronomic Practices / Prevention: Use virus-free certified seeds, sanitize tools, avoid handling wet plants, remove infected debris.\n"
        "9. Resistant Varieties: 'Celebrity', 'Rutgers', 'Mountain Pride'.\n"
        "10. Post-Harvest Impact: Fruits may continue to show malformation and have reduced shelf life.\n"
        "11. Other Notes: Mechanical inoculation is a major infection source; early detection and sanitation critical.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>V Bind Viral Disease Special</a> (Effective against viral symptoms and spread)."
    ),
    "Target Spot": (
        "1. Symptoms: Dark circular lesions with concentric rings on leaves; yellow halo; lesions may occur on stems and fruit; premature leaf drop.\n"
        "2. Incubation/Progression: Appears within 5 to 7 days in humid conditions; spreads rapidly if uncontrolled.\n"
        "3. Yield Loss & Economic Impact: Causes 20 to 40 percent yield reduction.\n"
        "4. Environmental Conditions Favoring Disease: High humidity (>80%), wet leaves, poor air circulation.\n"
        "5. Spread Mechanism / Vectors: Spread by water splash and infected plant debris.\n"
        "6. Treatment / Chemical Control: Fungicides like chlorothalonil or mancozeb; apply every 7 to 10 days during high humidity.\n"
        "7. Biological Control / Natural Predators: Beneficial fungi such as Trichoderma species suppress inoculum.\n"
        "8. Cultural & Agronomic Practices / Prevention: Crop rotation, debris removal, pruning for airflow, avoid overhead irrigation.\n"
        "9. Resistant Varieties: 'Mountain Pride'.\n"
        "10. Post-Harvest Impact: Mostly affects foliage; minimal effect on fruit quality.\n"
        "11. Other Notes: Rapid fungicide intervention prevents epidemics; greenhouse seedlings vulnerable.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>Propi Propineb 70% WP Fungicide</a> (A broad-spectrum fungicide effective on spot diseases)."
    ),
    "Bacterial Spot": (
        "1. Symptoms: Small dark water-soaked lesions on leaves and fruit; yellow halos; leaf curling and fruit scarring.\n"
        "2. Incubation/Progression: Symptoms appear in 7 to 10 days; spread accelerated by wet weather.\n"
        "3. Yield Loss & Economic Impact: Causes 30 to 50 percent yield loss.\n"
        "4. Environmental Conditions Favoring Disease: Warm, humid conditions and rain splash.\n"
        "5. Spread Mechanism / Vectors: Spread by water splash, tools, hands, contaminated seeds.\n"
        "6. Treatment / Chemical Control: Copper-based bactericides; reapply every 7 to 10 days.\n"
        "7. Biological Control / Natural Predators: Bacillus subtilis can suppress pathogen growth.\n"
        "8. Cultural & Agronomic Practices / Prevention: Use resistant varieties, crop rotation, seed treatment, sanitize tools.\n"
        "9. Resistant Varieties: 'Bonny Best', 'Hawaii 7998'.\n"
        "10. Post-Harvest Impact: Cosmetic blemishes on fruit reducing marketability.\n"
        "11. Other Notes: Dense canopy and wetness increase severity; early sanitation important.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>CUREAL Best Fungicide & Bactericide</a> (Designed for effective bacterial control)."
    ),
    "Early Blight": (
        "1. Symptoms: Dark concentric rings on older leaves, yellowing, defoliation; lesions on stems and fruit.\n"
        "2. Incubation/Progression: Appears in 7 to 10 days; severe infections cause defoliation in 2 weeks.\n"
        "3. Yield Loss & Economic Impact: Yield losses between 30 and 60 percent common.\n"
        "4. Environmental Conditions Favoring Disease: Warm, humid environments; poor ventilation.\n"
        "5. Spread Mechanism / Vectors: Soil-borne spores and rain splash.\n"
        "6. Treatment / Chemical Control: Fungicides like chlorothalonil and mancozeb; repeat in wet conditions.\n"
        "7. Biological Control / Natural Predators: Trichoderma species and Bacillus subtilis suppress fungi.\n"
        "8. Cultural & Agronomic Practices / Prevention: Crop rotation, spacing, mulching, debris removal.\n"
        "9. Resistant Varieties: 'Plum Regal', 'Iron Lady'.\n"
        "10. Post-Harvest Impact: Fruit lesions reduce quality; earlier harvest may be needed.\n"
        "11. Other Notes: Integrated management best.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>NATIVO FUNGICIDE</a> (Known for efficacy against Early Blight)."
    ),
    "Late Blight": (
        "1. Symptoms: Irregular water-soaked lesions on leaves/stems; white fungal growth; fruit rot and rapid plant collapse.\n"
        "2. Incubation/Progression: Rapid onset in 3 to 5 days under cool, wet weather; can destroy crops quickly.\n"
        "3. Yield Loss & Economic Impact: Up to 100 percent yield loss in unmanaged fields.\n"
        "4. Environmental Conditions Favoring Disease: Cool, wet, and highly humid conditions.\n"
        "5. Spread Mechanism / Vectors: Airborne spores, rain splash, infected seedlings.\n"
        "6. Treatment / Chemical Control: Fungicides such as mefenoxam and metalaxyl; rotate chemicals to prevent resistance.\n"
        "7. Biological Control / Natural Predators: Limited biological options; ongoing research.\n"
        "8. Cultural & Agronomic Practices / Prevention: Use resistant varieties, drip irrigation, remove infected plants, rotate crops.\n"
        "9. Resistant Varieties: 'Defiant', 'Mountain Magic'.\n"
        "10. Post-Harvest Impact: Fruits decay rapidly; unsuitable for storage.\n"
        "11. Other Notes: Climate monitoring essential.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>ACROBAT FUNGICIDE</a> (A potent fungicide often used for Late Blight control)."
    ),
    "Leaf Mold": (
        "1. Symptoms: Yellow spots on leaf upper surface; olive-green mold underneath; leaf curling and defoliation.\n"
        "2. Incubation/Progression: Develops in 6 to 10 days; rapid spread in humid greenhouses.\n"
        "3. Yield Loss & Economic Impact: 20 to 40 percent yield loss.\n"
        "4. Environmental Conditions Favoring Disease: High humidity above 85% and poor air circulation.\n"
        "5. Spread Mechanism / Vectors: Airborne spores, contaminated tools and hands.\n"
        "6. Treatment / Chemical Control: Copper oxychloride or chlorothalonil fungicides; improve ventilation.\n"
        "7. Biological Control / Natural Predators: Bacillus subtilis biofungicides reduce fungal growth.\n"
        "8. Cultural & Agronomic Practices / Prevention: Drip irrigation, proper spacing, remove fallen leaves.\n"
        "9. Resistant Varieties: 'Heinz 1706', F1 hybrids with Cf genes.\n"
        "10. Post-Harvest Impact: Minimal; usually no fruit impact.\n"
        "11. Other Notes: Proper greenhouse humidity control most effective.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>Virus Special Set (Immuno 1L + Enviro 1L)</a> (Combination product for broad protection)."
    ),
    "Septoria Leaf Spot": (
        "1. Symptoms: Small circular spots with dark brown edges and gray centers; yellow halos; premature leaf drop.\n"
        "2. Incubation/Progression: Symptoms visible 5 to 8 days post infection; can cause severe defoliation in 3 weeks if humid.\n"
        "3. Yield Loss & Economic Impact: Up to 50 percent due to loss of photosynthetic area.\n"
        "4. Environmental Conditions Favoring Disease: Warm, humid (20-25°C), frequent rain or irrigation.\n"
        "5. Spread Mechanism / Vectors: Rain splash, infected debris, tools; spores survive in soil for months.\n"
        "6. Treatment / Chemical Control: Chlorothalonil or mancozeb fungicides every 7 to 10 days.\n"
        "7. Biological Control / Natural Predators: Trichoderma spp. and compost tea sprays suppress spores.\n"
        "8. Cultural & Agronomic Practices / Prevention: Crop rotation, avoid overhead irrigation, remove infected debris.\n"
        "9. Resistant Varieties: 'Iron Lady', 'Mountain Magic'.\n"
        "10. Post-Harvest Impact: Uneven fruit ripening; possible sun damage.\n"
        "11. Other Notes: Common but manageable with preventive fungicides.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>ROKO FUNGICIDE</a> (General-purpose fungicide effective against leaf spot)."
    ),
    "Spider Mites": (
        "1. Symptoms: Yellow/white speckling on leaf tops; fine webbing underneath; bronzing, curling, defoliation.\n"
        "2. Incubation/Progression: Life cycle 5-7 days in hot, dry climates; full infestation can defoliate in 2 weeks.\n"
        "3. Yield Loss & Economic Impact: 40 to 70 percent due to foliar damage.\n"
        "4. Environmental Conditions Favoring Disease: Hot, dry, dusty conditions; low humidity greenhouse.\n"
        "5. Spread Mechanism / Vectors: Wind, infested plants, equipment.\n"
        "6. Treatment / Chemical Control: Miticides like abamectin, sulfur sprays; target leaf undersides.\n"
        "7. Biological Control / Natural Predators: Predatory mites and lady beetles.\n"
        "8. Cultural & Agronomic Practices / Prevention: Maintain irrigation, clean leaves, remove infested foliage.\n"
        "9. Resistant Varieties: Some stress-tolerant hybrids.\n"
        "10. Post-Harvest Impact: Minimal direct fruit impact; lowers yield.\n"
        "11. Other Notes: Early detection key; pesticide resistance can develop.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>OMITE INSECTICIDE</a> (A potent miticide for controlling mites)."
    ),
    "Bacterial Speck": (
        "1. Symptoms: Small dark spots with yellow halos on leaves, stems, and fruit; spots may merge, causing leaf curling.\n"
        "2. Incubation/Progression: Appears 5 to 8 days after infection; can devastate foliage in 2 weeks.\n"
        "3. Yield Loss & Economic Impact: 20 to 40 percent, especially in wet seasons.\n"
        "4. Environmental Conditions Favoring Disease: Cool, wet weather; humidity > 85%.\n"
        "5. Spread Mechanism / Vectors: Contaminated seed, rain splash, equipment, wet plant handling.\n"
        "6. Treatment / Chemical Control: Copper bactericides, streptomycin sprays; hot water seed treatment.\n"
        "7. Biological Control / Natural Predators: Bacillus subtilis suppresses pathogen.\n"
        "8. Cultural & Agronomic Practices / Prevention: Disease-free seeds, crop rotation, avoid working when wet.\n"
        "9. Resistant Varieties: 'Hawaii 7981', 'Iron Lady'.\n"
        "10. Post-Harvest Impact: Fruit blemishes reduce appearance, fruit remains edible.\n"
        "11. Other Notes: Seed disinfection critical to prevention.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>CUREAL Best Fungicide & Bactericide</a> (Using the recommended bacterial control product)."
    ),
    "Healthy": (
        "1. Notes: Leaves show uniform green color with no lesions or discoloration; healthy plants maximize yield.\n"
        "2. Growth & Longevity: Fruit production for 3 to 5 months under good conditions.\n"
        "3. Yield & Economic Impact: Potential of 10–15 kg fruit per plant with good care.\n"
        "4. Environmental Conditions Favoring Growth: Moderate temperatures (20-28°C), well-drained organic soil, regular watering.\n"
        "5. Disease Prevention: Regular inspection, balanced fertilization, timely pruning, avoid stress.\n"
        "6. Cultural & Agronomic Practices: Disease-free seeds, proper spacing, crop rotation, sanitation.\n"
        "7. Resistant Varieties: 'Iron Lady', 'Mountain Magic', 'Roma VF'.\n"
        "8. Post-Harvest Impact: Uniform fruit ripening and longer shelf life.\n"
        "9. Other Notes: Optimal soil moisture and organic compost enhance plant health.\n"
        "12. Recommended Supplement/Product: <a href='/market' class='text-decoration-underline text-success fw-bold' target='_blank'>Tomato Organic Fertilizer (Home/Balcony)</a> (For maintaining optimal plant health and maximizing yield)."
    )
}

# -------------------- API Key Setup --------------------
API_KEY = os.getenv('API_KEY', 'free-access-key')

def require_apikey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function

# -------------------- Error Response Helper --------------------
def create_error_response(message, status_code=400):
    resp = jsonify(error=message)
    resp.status_code = status_code
    return resp

# -------------------- SUPPLEMENT DATA --------------------

# load supplements CSV at startup into a dict keyed by disease short name (normalized)
SUPPLEMENTS = {}
SUPP_CSV = os.path.join(os.path.dirname(__file__), "supplement_info.csv")
if os.path.exists(SUPP_CSV):
    try:
        with open(SUPP_CSV, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = (row.get('disease_name') or "").strip()
                if not key:
                    continue
                SUPPLEMENTS[key] = {
                    "sname": (row.get('supplement name') or "").strip(),
                    "simage": (row.get('supplement image') or "").strip(),
                    "buy_link": (row.get('buy link') or "").strip()
                }
    except Exception as e:
        log.debug(f"Failed to load supplements CSV: {e}")

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    # Since your current about.html handles the contact section via an anchor, 
    # we can simplify the contact route to also render about.html or use a separate contact.html
    # For now, keeping it as is, which renders 'about.html'
    return render_template('about.html')

@app.route('/set_language', methods=['POST'])
def set_language():
    global selected_language
    data = request.json
    selected_language = data.get('language', 'en')
    return jsonify({"message": f"Language set to {selected_language}"})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'file' not in request.files:
            return create_error_response("No file uploaded", 400)

        uploaded = request.files['file']
        img_bytes = uploaded.read()

        try:
            preds = model_predict(img_bytes)
        except Exception as e:
            log.debug(f"model_predict error: {e}")
            preds = None

        if isinstance(preds, list) and preds:
            best = max(preds, key=lambda x: x.get('confidence', 0))
            out = {"label": best.get("label", "Unknown"), "confidence score": round(best.get("confidence", 0) * 100, 2)}
        elif isinstance(preds, dict):
            out = preds
        else:
            out = {"label": "Unknown", "confidence score": 0}

        # Attempt to attach supplement suggestion (if available)
        try:
            # normalize label variants and try several lookups
            label = out.get("label", "") or ""
            candidates = [label, label.replace(" ", "_"), label.replace(" ", "").lower()]
            supplement = None
            for cand in candidates:
                if cand in SUPPLEMENTS:
                    supplement = SUPPLEMENTS[cand]
                    break
            # fallback substring match
            if not supplement:
                for k, v in SUPPLEMENTS.items():
                    if k.lower() in label.lower() or label.lower() in k.lower():
                        supplement = v
                        break

            if supplement:
                # create UI-friendly supplement object
                out["supplement"] = {
                    "title": label,
                    "image_url": supplement.get("simage"),
                    "desc": "",       # optional: populate from DISEASE_DESCRIPTIONS if available
                    "prevent": "",
                    "simage": supplement.get("simage"),
                    "sname": supplement.get("sname"),
                    "buy_link": supplement.get("buy_link"),
                    "summary": ""
                }
        except Exception:
            log.debug("Failed to attach supplement", exc_info=True)

        return jsonify(out)
    except Exception as e:
        log.exception("Prediction error")
        return create_error_response("Error during prediction", 500)

# small cached translator wrapper
@lru_cache(maxsize=2048)
def _translate_cached(text: str, target_lang: str) -> str:
    if not text or target_lang == 'en':
        return text
    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except Exception as e:
        log.debug(f"_translate_cached error: {e}")
        return text


YOUTUBE_LANGUAGE_URLS = {
    "en": "https://youtu.be/S9-5_Y-Bb30?si=ZC0r9htaXCnMWfRD",
    "te": "https://youtu.be/8ZIl8srx52k?si=elwI6VmRaqwcD50N",
    "kn": "https://youtu.be/ENddaeTYRK4?si=96mgmXTSmq8ravHC",
    "hi": "https://youtu.be/CE8y9jhHghU?si=GvrawlbkeGy-E8mG",
    "ta": "https://www.youtube.com/watch?v=etupF7L_L_A",
}


YOUTUBE_POINT_COPY = {
    "en": {"title": "Video Guide", "cta": "Watch on YouTube"},
    "hi": {"title": "वीडियो मार्गदर्शिका", "cta": "यूट्यूब पर देखें"},
    "kn": {"title": "ವೀಡಿಯೊ ಮಾರ್ಗದರ್ಶಿ", "cta": "YouTube ನಲ್ಲಿ ನೋಡಿ"},
    "te": {"title": "వీడియో మార్గదర్శిని", "cta": "YouTube లో చూడండి"},
    "ta": {"title": "வீடியோ வழிகாட்டி", "cta": "YouTube-ல் பார்க்க"},
}


def build_youtube_point(lang: str) -> str:
    normalized_lang = (lang or "en").split("-")[0].lower()
    copy = YOUTUBE_POINT_COPY.get(normalized_lang, YOUTUBE_POINT_COPY["en"])
    youtube_url = YOUTUBE_LANGUAGE_URLS.get(normalized_lang, YOUTUBE_LANGUAGE_URLS["en"])
    return (
        f"13. {copy['title']}: "
        f"<a href='{youtube_url}' class='text-decoration-underline text-danger fw-bold' "
        f"target='_blank' rel='noopener noreferrer'>{copy['cta']}</a>."
    )


def translate_text_preserve_links(html_text: str, target_lang: str) -> str:
    """Translate html_text while preserving anchor tags."""
    if not html_text or target_lang == 'en':
        return html_text
    try:
        link_pattern = r"(<a\b[^>]*>.*?<\/a>)"
        matches = re.findall(link_pattern, html_text, flags=re.IGNORECASE)
        tmp = html_text
        placeholders = []
        for i, m in enumerate(matches):
            ph = f"__LINK_{i}__"
            placeholders.append((ph, m))
            tmp = tmp.replace(m, ph, 1)
        translated_tmp = _translate_cached(tmp, target_lang)
        for ph, original_html in placeholders:
            translated_tmp = translated_tmp.replace(ph, original_html)
        return translated_tmp
    except Exception as e:
        log.debug(f"translate_text_preserve_links error: {e}")
        return html_text

@app.route('/describe', methods=['POST'])
def describe_disease():
    try:
        data = request.json or {}
        disease = data.get('disease') or data.get('disease_key')
        lang = (data.get('lang') or 'en').split('-')[0].lower()
        if not disease:
            return create_error_response('No disease provided', 400)

        description = DISEASE_DESCRIPTIONS.get(disease)
        if description is None:
            return jsonify({"description": f"No detailed description available for {disease}.", "is_html": False})

        translated_body = translate_text_preserve_links(description, lang)
        youtube_point = build_youtube_point(lang)
        translated_html = f"{translated_body}\n{youtube_point}"

        translated_points = re.split(r'(?:^|\n)\d+\.\s', translated_body)
        translated_points = [p.strip() for p in translated_points if p.strip()]
        if not translated_points:
            translated_points = re.split(r'\d+\.\s', description)
            translated_points = [p.strip() for p in translated_points if p.strip()]
        translated_points.append(youtube_point.split("13. ", 1)[1])

        return jsonify({
            "description": translated_points,
            "description_points": translated_points,
            "description_html": translated_html,
            "is_html": True
        })
    except Exception as e:
        log.exception("describe_disease failed")
        return create_error_response("Failed to describe disease", 500)


# --- app.py (REQUIRED UPDATE FOR /translate_content) ---

@app.route('/translate_content', methods=['POST'])
def translate_content():
    try:
        data = request.json
        page = data.get('page')
        lang = data.get('lang', 'en')
        
        contents_map = {
            # Map of ID -> {en: 'English Text'}
            "about_hero_h2": {"en": "Tomato Disease Prediction"},
            "about_hero_p": {"en": "This intelligent system leverages deep learning to help farmers and gardeners quickly identify tomato leaf diseases with just an image. Our mission is to promote healthier crops and sustainable farming through AI innovation."},
            "about_hero_link": {"en": "Learn More"},
            "about_section_h1": {"en": "About the Project"},
            "about_section_p": {"en": "Our deep learning model is trained using a tomato leaf dataset from Kaggle. Images were resized to 64x64 pixels and enhanced through data augmentation techniques like flipping, zooming, and brightness adjustment. The model is built with convolutional neural networks (CNNs), enabling accurate classification of 9 common tomato diseases and healthy leaves."},
            "feature_1_h5": {"en": "AI-Powered Detection"},
            "feature_1_p": {"en": "Utilizes deep learning to automatically detect tomato leaf diseases from uploaded images."},
            "feature_2_h5": {"en": "Rich Dataset"},
            "feature_2_p": {"en": "Trained on thousands of images collected from trusted agricultural datasets for high accuracy."},
            "feature_3_h5": {"en": "Farmer Friendly"},
            "feature_3_p": {"en": "Designed to assist farmers and home gardeners in maintaining healthy tomato crops."},
            "tech_stack_h2": {"en": "Technology Stack"},
            "tech_stack_p": {"en": "The project is powered by <strong>TensorFlow</strong>, <strong>Keras</strong>, and <strong>OpenCV</strong>. The web interface is built using <strong>Flask</strong> and <strong>Bootstrap</strong>. All components work seamlessly to deliver real-time disease predictions."},
            "contact_h2": {"en": "Contact Me"},
            "contact_p": {"en": "Feel free to reach out for collaboration, suggestions, or queries."},
            "contact_location": {"en": "Bangalore, Karnataka, India"},
            "contact_phone_link": {"en": "+91 7483367339"},
            "contact_email_link": {"en": "harshithdn27@gmail.com"},
            "footer_p": {"en": "© 2025 Tomato Disease Prediction | All rights reserved"},

            # Add new translations for prevention section
            "prevent_title": {
                "en": "Prevent Plant Disease: Steps to Follow"
            },
            "prevent_steps": {
                "en": '''<ol class="list-unstyled">
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Follow Good Sanitation Practices.</li>
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Fertilize to Keep Your Plants Healthy.</li>
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Inspect Plants Before You Bring Them Home.</li>
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Allow the Soil to Warm Before Planting.</li>
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Rotate Crops for a Healthy Vegetable Garden.</li>
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Provide Good Air Circulation.</li>
                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> Remove Diseased Stems and Foliage promptly.</li>
                </ol>'''
            },
            "prevent_more": {
                "en": "More Info"
            },
            
            # Add translations for why detection section
            "why_title": {
                "en": "Why is it Necessary to Detect Disease?"
            },
            "why_content": {
                "en": "Accurate diagnosis is the most important aspect of plant pathology. Without proper identification of the disease and the causal agent, control measures are often ineffective, wasting resources and leading to further crop losses. This system provides the transparency needed to detect diseases early, often before symptoms are clearly visible, ensuring timely and effective intervention."
            }
        }
        
        translated_texts = {}
        if page == "about":
            if lang == 'en':
                # Return English text immediately
                for key, val in contents_map.items():
                    translated_texts[key] = val['en']
            else:
                # Translate all blocks
                translator = GoogleTranslator(source='en', target=lang)
                for key, val in contents_map.items():
                    english_text = val['en']
                    try:
                        # Special handling for prevent_steps to maintain HTML structure
                        if key == "prevent_steps":
                            # Extract just the text content to translate
                            steps = re.findall(r'</i>\s*(.*?)\.</li>', english_text)
                            translated_steps = []
                            for step in steps:
                                translated_step = translator.translate(step)
                                translated_steps.append(translated_step)
                            
                            # Reconstruct HTML with translated content
                            translated_html = '''<ol class="list-unstyled">'''
                            for step in translated_steps:
                                translated_html += f'''
                                    <li><i class="fa-solid fa-circle-check text-success me-2"></i> {step}.</li>'''
                            translated_html += '</ol>'
                            translated_texts[key] = translated_html
                        else:
                            translated_text = translator.translate(english_text)
                            translated_texts[key] = translated_text
                    except Exception as e:
                        log.debug(f"Translation error for {key}: {e}")
                        translated_texts[key] = english_text  # Fallback to English

            return jsonify(translated_texts)
        else:
            # Handle other pages (like contact, if separate)
            return create_error_response("Page content not found", 404)

    except Exception as e:
        log.debug(e)
        return create_error_response("Failed to translate content", 500)

@app.route('/speak', methods=['POST'])
def speak_description():
    try:
        data = request.json
        text = data.get('text')
        lang = data.get('lang', 'en')

        if not text:
            return create_error_response("No text provided for speech", 400)

        lang_map = {
            'en': 'en',
            'hi': 'hi',
            'ta': 'ta',
            'te': 'te',
            'kn': 'kn'
        }
        gtts_lang = lang_map.get(lang, 'en')

        # Since the frontend will manage the loading indicator, we keep the blocking
        # calls here for simplicity, assuming the frontend handles the UX.
        tts = gTTS(text=text, lang=gtts_lang)
        output_path = os.path.join("static", "speech_output.mp3")
        tts.save(output_path)

        return send_file(output_path, mimetype='audio/mpeg')

    except Exception as e:
        log.debug(f"Speech error: {e}")
        return create_error_response("Failed to generate speech", 500)


def build_chatbot_reply(message: str, lang: str) -> str:
    text = (message or "").lower()
    normalized_lang = (lang or "en").split("-")[0].lower()
    agriculture_responses = [
        (
            ["agriculture", "farming", "farmer", "cultivation", "krishi", "agri"],
            "Agriculture is the science and practice of growing crops and raising animals for food, fiber, and income. Good agriculture depends on proper land preparation, healthy soil, quality seeds, balanced fertilizer use, timely irrigation, pest and disease control, weed management, and harvesting at the correct stage. Farmers also need to understand weather, market demand, storage, and post-harvest handling. Modern agriculture combines traditional knowledge with improved methods such as soil testing, drip irrigation, resistant varieties, mulching, bio-inputs, and better crop planning. Sustainable farming is important because it protects soil fertility, saves water, reduces unnecessary chemical use, and improves long-term productivity and farmer income. If you want, I can also explain agriculture in detail topic by topic like soil, irrigation, fertilizer, pests, diseases, or crop planning."
        ),
        (
            ["hello", "hi", "hey", "namaste"],
            "Hello. I can help with crop diseases, fertilizers, irrigation, soil health, pests, weather, market planning, and general farming tips."
        ),
        (
            ["disease", "blight", "spot", "mold", "virus", "leaf", "wilt", "rot", "yellow leaf", "fungus"],
            "Check the affected leaves and stems closely, remove badly infected parts, avoid overhead watering, and keep good airflow. If symptoms continue, use the prediction page and follow crop-specific disease control."
        ),
        (
            ["fertilizer", "manure", "npk", "urea", "dap", "potash", "micronutrient", "zinc", "boron", "nutrient"],
            "Use balanced fertilizer based on crop stage and soil condition. Avoid excess nitrogen, add organic matter when possible, and split fertilizer doses instead of applying everything at once."
        ),
        (
            ["water", "irrigation", "drip", "moisture", "watering", "sprinkler"],
            "Keep soil moisture even but avoid waterlogging. Drip irrigation is usually better for vegetables because it saves water and reduces leaf wetness and disease spread."
        ),
        (
            ["pest", "insect", "aphid", "mites", "thrips", "whitefly", "caterpillar", "worm", "hopper", "borer"],
            "Inspect the underside of leaves and growing tips, isolate badly affected plants, and begin with safer control such as field sanitation, sticky traps, neem-based spray, or crop-specific pest management."
        ),
        (
            ["weather", "rain", "humidity", "temperature", "summer", "winter", "climate", "forecast"],
            "Weather strongly affects crops. High humidity and long leaf wetness increase disease risk, while heat and dry wind increase water stress. Adjust irrigation, scouting, and spraying based on local conditions."
        ),
        (
            ["soil", "ph", "salinity", "organic carbon", "compost", "mulch", "mulching"],
            "Healthy soil should have good drainage, enough organic matter, and a crop-suitable pH. Add compost, avoid overwatering, and test soil when possible before major fertilizer decisions."
        ),
        (
            ["seed", "germination", "nursery", "seedling", "transplant", "tray"],
            "Use clean, high-quality seed, well-drained nursery media, and avoid overcrowding. During transplanting, water lightly, reduce stress, and protect young seedlings from damping-off and extreme heat."
        ),
        (
            ["flower", "fruit", "yield", "production", "harvest", "ripening"],
            "Good yield depends on balanced nutrition, timely irrigation, pest control, and healthy flowering. Avoid stress during flowering and fruit set, and harvest at the correct maturity stage for better quality."
        ),
        (
            ["weed", "weeds", "grass", "herbicide"],
            "Control weeds early because they compete for water and nutrients. Mulching, timely hand weeding, and crop-safe herbicides can help depending on the crop and growth stage."
        ),
        (
            ["market", "price", "sell", "selling", "mandi", "profit", "income"],
            "For better profit, track local market prices, sort produce by quality, reduce post-harvest loss, and plan harvest timing carefully. Selling clean, graded produce usually improves returns."
        ),
        (
            ["organic", "natural farming", "bio", "jeevamrutham", "vermicompost"],
            "Organic farming works best with compost, crop rotation, mulching, bio-inputs, and preventive pest management. Nutrient release is slower, so planning and regular soil improvement are important."
        ),
        (
            ["spray", "pesticide", "fungicide", "insecticide", "dose", "dosage"],
            "Always follow the label dose, spray during calm weather, and wear protection. Do not mix chemicals unless they are compatible, and rotate products to reduce resistance."
        ),
        (
            ["tomato", "brinjal", "chilli", "paddy", "rice", "wheat", "cotton", "maize", "onion", "potato"],
            "For crop-specific advice, focus on stage, symptoms, water status, and pest pressure. Share the crop name and problem clearly, and I can guide you with more targeted farming advice."
        ),
    ]

    reply = None
    best_match_score = 0
    wants_long_answer = any(word in text for word in ["long", "detail", "detailed", "explain", "full", "complete", "format"])
    for keywords, response in agriculture_responses:
        match_score = sum(1 for word in keywords if word in text)
        if wants_long_answer and any(word in keywords for word in ["agriculture", "farming", "farmer", "cultivation", "krishi", "agri"]):
            match_score += 2
        if match_score > best_match_score:
            best_match_score = match_score
            reply = response

    if best_match_score == 0 or reply is None:
        if wants_long_answer:
            reply = (
                "Agriculture includes soil preparation, seed selection, sowing or transplanting, irrigation, fertilizer management, weed control, pest and disease protection, harvesting, storage, and marketing. "
                "A successful farmer chooses crops based on soil type, season, climate, water availability, and market demand. Healthy agriculture also depends on balanced plant nutrition, proper spacing, good drainage, timely field observation, and reducing crop stress during critical stages such as flowering and fruiting. "
                "Good farming practices improve yield, quality, and profit while sustainable farming helps protect soil, water, and long-term income."
            )
        else:
            reply = (
                "I can answer agriculture questions about crops, soil, fertilizer, irrigation, pests, diseases, weather, yield, harvesting, markets, and organic farming. "
                "Please ask your farming question with the crop name or problem."
            )

    if normalized_lang != "en":
        return _translate_cached(reply, normalized_lang)
    return reply


def query_chatbot_llm(message: str, lang: str) -> str | None:
    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("CHATBOT_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
    )
    if not api_key:
        return None

    normalized_lang = (lang or "en").split("-")[0].lower()
    api_url = os.getenv("CHATBOT_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("CHATBOT_MODEL", "openai/gpt-4o-mini")

    system_prompt = (
        "You are AgriBot, a helpful agriculture assistant. "
        "Answer farming, crop, soil, irrigation, fertilizer, pest, disease, weather, market, and harvest questions clearly and accurately. "
        f"Reply only in language code '{normalized_lang}'. "
        "Keep answers practical and directly useful for farmers."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "temperature": 0.4,
    }

    req = urllib_request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return reply or None
    except urllib_error.HTTPError as e:
        log.debug(f"Chatbot API HTTP error: {e}")
    except urllib_error.URLError as e:
        log.debug(f"Chatbot API URL error: {e}")
    except Exception as e:
        log.debug(f"Chatbot API error: {e}")

    return None


@app.route('/chat-bot/api', methods=['POST'])
def chat_bot_api():
    data = request.json or {}
    message = (data.get('message') or '').strip()
    lang = data.get('lang', 'en')

    if not message:
        return jsonify({"reply": "Please enter a question."}), 400

    llm_reply = query_chatbot_llm(message, lang)
    if llm_reply:
        return jsonify({"reply": llm_reply, "source": "api"})

    return jsonify({"reply": build_chatbot_reply(message, lang), "source": "fallback"})

# Quick routes to serve chat and market pages so navbar links don't 404.
@app.route('/chat-bot')
def chat_bot():
    return render_template('chat-bot.html')

@app.route('/market')
def market():
    # locate CSV (support common locations)
    base = os.path.dirname(__file__)
    candidates = [
        os.path.join(base, "data", "supplements.csv"),
        os.path.join(base, "supplement_info.csv"),
        os.path.join(base, "supplement_info.csv".replace("/", os.sep))
    ]
    csv_path = next((p for p in candidates if os.path.exists(p)), None)

    # safe fallback: render page with empty lists instead of raising error
    if not csv_path:
        log.debug("Market CSV not found, rendering empty market page.")
        return render_template('market.html', supplement_name=[], supplement_image=[], disease=[], buy=[])

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        log.exception("Failed to read market CSV")
        return render_template('market.html', supplement_name=[], supplement_image=[], disease=[], buy=[])

    # robust column detection (allow common variants)
    cols = {c.lower(): c for c in df.columns}
    def find_col(variants):
        for v in variants:
            if v in cols:
                return cols[v]
        return None

    supplement_col = find_col(['supplement name', 'supplement_name', 'sname', 'supplement'])
    image_col = find_col(['supplement image', 'supplement_image', 'simage', 'image', 'product image'])
    buy_col = find_col(['buy link', 'buy_link', 'buylink', 'buy', 'link'])
    disease_col = find_col(['disease_name', 'disease name', 'disease', 'disease_name'])

    # if required columns missing, return empty lists (avoids NameError)
    if not (supplement_col and image_col and buy_col and disease_col):
        log.debug(f"Market CSV missing expected columns. Found: {list(df.columns)}")
        return render_template('market.html', supplement_name=[], supplement_image=[], disease=[], buy=[])

    # drop rows missing required values
    df = df.dropna(subset=[supplement_col, image_col, buy_col, disease_col])

    supplement_name_list = df[supplement_col].astype(str).tolist()
    supplement_image_list = df[image_col].astype(str).tolist()
    disease_list = df[disease_col].astype(str).tolist()
    buy_links_list = df[buy_col].astype(str).tolist()

    return render_template(
        'market.html',
        supplement_name=supplement_name_list,
        supplement_image=supplement_image_list,
        disease=disease_list,
        buy=buy_links_list
    )


# -------------------- MAIN --------------------
if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(host="0.0.0.0", port=5002, debug=True)
