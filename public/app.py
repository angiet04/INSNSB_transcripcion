# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ========= NLP =========
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
print("Cargando modelo NLP")
model = SentenceTransformer(MODEL_NAME)
print("Modelo NLP cargado correctamente")

# ====== Campos ======
FIELDS = {
    "edad": "edad años paciente",
    "sexo": "sexo masculino femenino varón mujer",
    "peso": "peso corporal kilogramos kilos",
    "talla": "talla altura estatura centímetros metros",
    "ta": "tensión arterial presión arterial mmhg",
    "fr": "frecuencia respiratoria respiraciones por minuto",
    "fc": "frecuencia cardiaca pulso latidos por minuto",
    "temp": "temperatura corporal fiebre grados celsius",
    "sat": "saturación de oxígeno spo2 porcentaje",
}
NEURO = {
    "pupilas": "pupilas reactivas isocóricas",
    "pares": "pares craneales conservados normales",
    "tono": "tono y reflejos normales conservados",
    "sensi": "sensibilidad intacta conservada",
    "coord": "coordinación adecuada normal",
    "marcha": "marcha estable normal",
    "mening": "signos meníngeos negativos",
}

ALL_KEYS = list(FIELDS.keys()) + list(NEURO.keys())
ALL_TEXTS = list(FIELDS.values()) + list(NEURO.values())
EMB_BASE = model.encode(ALL_TEXTS, convert_to_tensor=True)

# ====== Utilidades ======
SCALE = r'(?P<a>[0-5])\s*(?:\/|de)\s*(?P<b>[0-5])'  # 4/5, 4 / 5, 4 de 5

def muscle_patterns(name_variants):
    name_union = r'(?:' + '|'.join(name_variants) + r')'
    p1 = rf'\b{name_union}\b[^\d]{{0,20}}{SCALE}'   # deltoides 4/5
    p2 = rf'{SCALE}[^\w]{{0,20}}\b{name_union}\b'   # 4/5 deltoides
    return [p1, p2]

def add_result(results, field, value, score):
    """Guarda solo si hay valor y mejora score."""
    if value is None or value == "":
        return
    cur = results.get(field)
    if cur is None or score > cur["score"]:
        results[field] = {"value": value, "score": round(float(score), 3)}

def normalize_text(t: str) -> str:
    """
    Normaliza expresiones como '37 punto 2' / '37 coma 2' -> '37.2'.
    También compacta espacios repetidos.
    """
    t = t.lower()

    # 37 punto 2  -> 37.2   ;   37 coma 2 -> 37.2
    t = re.sub(r'(\d+)\s*(?:punto|coma)\s*(\d+)', r'\1.\2', t)

    # grados centigrados -> grados centígrados (unificar variantes)
    t = re.sub(r'centigrados', 'centígrados', t)

    # compactar espacios
    t = re.sub(r'\s+', ' ', t).strip()
    return t

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    tl = normalize_text(text)   # 🔧 usamos texto normalizado
    out = {}

    # ===== 1) Signos vitales (solo si se mencionan) =====
    # Edad
    m = re.search(r'(\d{1,3})\s*(?:años|año)\b', tl)
    if m: add_result(out, "edad", m.group(1), 0.99)

    # Sexo
    if re.search(r'\b(masculino|var[oó]n|hombre)\b', tl):
        add_result(out, "sexo", "Masculino", 0.99)
    elif re.search(r'\b(femenino|mujer)\b', tl):
        add_result(out, "sexo", "Femenino", 0.99)

    # Peso
    m = re.search(r'\b(\d{2,3})\s*(?:kg|kilos|kilogramos)\b', tl)
    if m: add_result(out, "peso", m.group(1), 0.98)

    # Talla (cm primero para evitar confusiones con 'm' de minuto)
    m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(?:cm|cent[ií]metros)\b', tl)
    if not m:
        m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(?:m|metros)\b', tl)
    if m:
        add_result(out, "talla", m.group(1).replace(",", "."), 0.98)

    # TA
    m = re.search(r'\b(\d{2,3})\s*(?:/|sobre|a)\s*(\d{2,3})\b', tl)
    if m: add_result(out, "ta", f"{m.group(1)}/{m.group(2)}", 0.98)

    # FC (más flexible)
    m = re.search(r'(?:\bfc\b|frecuencia\s*card[ií]aca)\s*(?:de\s*)?(\d{2,3})\b', tl)
    if not m:
        m = re.search(r'\b(\d{2,3})\s*(?:latidos(?:\s*por\s*minuto)?|/min|lpm|minuto|card[ií]aca)\b', tl)
    if m: add_result(out, "fc", m.group(1), 0.98)

    # FR (mucho más flexible)
    m = re.search(r'(?:\bfr\b|frecuencia\s*respiratoria)\s*(?:de\s*)?(\d{1,2})\b', tl)
    if not m:
        m = re.search(r'\b(\d{1,2})\s*(?:resp(?:iraciones)?(?:\s*por\s*minuto)?|rpm|r\/min|resp\/min)\b', tl)
    if m: add_result(out, "fr", m.group(1), 0.98)

    # ===== Temperatura =====
    # 1) Formatos con unidad (°C, °, grados, centígrados, celsius, 'c' pero NO 'cm')
    m = re.search(
        r'\b(\d{1,2}(?:[.,]\d)?)\s*'
        r'(?:'
            r'°\s*c'                                    # 37.2 °c / 37.2°c
            r'|°(?!\s*[a-z])'                           # 37.2° (sin letra luego)
            r'|grados?(?:\s*(?:cent[ií]grados?|c(?:el(?:sius)?)?))?'  # "grados", "grados centígrados", "grados celsius"
            r'|\bc\b(?!\s*m)'                           # "c" como unidad, pero NO "cm"
        r')\b',
        tl
    )
    if not m:
        # 2) "temperatura 37.2" (sin decir grados)
        m = re.search(r'\btemp(?:eratura)?\s*(?:de\s*)?(\d{1,2}(?:[.,]\d)?)\b', tl)
    if m:
        add_result(out, "temp", m.group(1).replace(",", "."), 0.98)

    # Saturación
    m = re.search(r'(?:saturaci[oó]n[^0-9%]{0,10}(\d{2,3}))|(\d{2,3})\s*%(\s*sato2|\s*spo2)?\b', tl)
    if m:
        val = m.group(1) or m.group(2)
        try:
            if val and 80 <= int(val) <= 100:
                add_result(out, "sat", val, 0.98)
        except:
            pass

    # ===== 2) Fuerza muscular (solo si se menciona) =====
    MUSCLE_VARIANTS = {
        "deltoides":   [r'deltoides?'],
        "biceps":      [r'b[ií]ceps'],
        "triceps":     [r'tr[ií]ceps'],
        "ext-muneca":  [r'extensores?\s+de\s+muñeca'],
        "interoseos":  [r'inter[oó]seos'],
        "psoas":       [r'psoas(?:\/|\s*)?iliopsoas', r'iliopsoas', r'psoas'],
        "cuadriceps":  [r'cu[aá]driceps'],
        "tibial-ant":  [r'tibial\s+anterior'],
        "gemelos":     [r'(?:gastrocnemio(?:-|\s*)s[oó]leo|gemelos|s[oó]leo)'],
        "ext-hallux":  [r'extensor\s+del\s+hallux'],
    }
    for key, variants in MUSCLE_VARIANTS.items():
        for pat in muscle_patterns(variants):
            m = re.search(pat, tl, flags=re.IGNORECASE)
            if m:
                add_result(out, key, f"{m.group('a')}/{m.group('b')}", 0.99)
                break  # si ya encontró una variante, no seguir

    # ===== 3) Neurológico (NLP) — solo si hay evidencia =====
    if text:
        emb_in = model.encode(text, convert_to_tensor=True)
        sims = util.cos_sim(emb_in, EMB_BASE)[0]
        for idx, label in enumerate(ALL_KEYS):
            score = float(sims[idx])
            if label in NEURO and score > 0.58:
                default_val = {
                    "pupilas": "Isocóricas y reactivas",
                    "pares":   "Conservados",
                    "tono":    "Normales",
                    "sensi":   "Intacta",
                    "coord":   "Adecuada",
                    "marcha":  "Estable",
                    "mening":  "Negativos",
                }[label]
                add_result(out, label, default_val, score)

    print("🧠 Texto recibido:", text)
    print("📊 Resultados enviados:", out)

    # 👉 devolvemos SOLO lo detectado
    return jsonify({
        "results": [{"field": k, "value": v["value"], "score": v["score"]} for k, v in out.items()]
    })

if __name__ == "__main__":
    print("🚀 Servidor Flask activo en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)