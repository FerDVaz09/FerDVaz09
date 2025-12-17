# app.py
from flask import Flask, request, make_response, jsonify
import os
import json
from dotenv import load_dotenv
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError
from datetime import datetime
import requests
import time
import unicodedata
import pandas as pd
from io import BytesIO
import threading
from concurrent.futures import ThreadPoolExecutor
import re

# ==========================
# CARGA ENTORNO Y CLIENTES
# ==========================
load_dotenv()

from thinkific_api import get_user_by_email, get_enrollments

# Instancias necesarias
app = Flask(__name__)
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
verifier = SignatureVerifier(signing_secret=os.getenv("SLACK_SIGNING_SECRET"))

# API Thinkific
THINKIFIC_API_KEY = os.getenv("THINKIFIC_API_KEY")
THINKIFIC_SUBDOMAIN = os.getenv("THINKIFIC_SUBDOMAIN", "axcampus")
BASE_URL = "https://api.thinkific.com/api/public/v1"

HEADERS = {
    "X-Auth-API-Key": THINKIFIC_API_KEY,
    "X-Auth-Subdomain": THINKIFIC_SUBDOMAIN,
    "Content-Type": "application/json",
}

# Canal operativo
THINKIFIC_CHANNEL_ID = "C088ADY7TNG"
THINKIFIC_CHANNEL_NAME = "#thinkific"

# Programas Premium
PREMIUM_PROGRAMS = [
    "abacus experience", "abacus experience-", "abacus pro", "abacus pro-",
    "portfolio hacking", "day trading dynamics", "programa de preparación",
    "option collision", "road to first 10k", "traders hub", "todos los programas (team abacus)",
]

# ===== MAPEOS ESTÁTICOS DE CURSOS (USADO EN /acceso y /acceso-masivo) =====
COURSE_IDS = {
    "abacus experience": 2058326,
    "abacus experience-": 3154898,
    "abacus pro": 2060571,
    "abacus pro-": 3158575,
    "portfolio hacking": 2078283,
    "day trading dynamics": 2837735,
    "option collision": 2292845,
    "abacus masterclasses": 1975914,
    "programa de preparación": 2195573,
    "bootcamp": 2056542,
    "traders_club": 3035597,
    "todos los programas (team abacus)": 2200738,
    "road to first 10k": 3097316,
    "traders hub": 3186759,
}

# Memoria en RAM
PENDING_MASS = {}

# ==========================
# PRE-CARGA DE CURSOS AL INICIO
# ==========================
def warmup_courses_cache():
    """Pre-carga el cache de cursos en background al iniciar la app"""
    print("🔥 Iniciando pre-carga de cursos en background...")
    time.sleep(2)  # Esperar a que la app esté lista
    try:
        courses = fetch_all_courses()
        if courses:
            COURSES_CACHE["data"] = courses
            COURSES_CACHE["last_updated"] = time.time()
            print(f"✅ Cache pre-cargado: {len(courses)} cursos disponibles")
        else:
            print("⚠️ No se pudieron pre-cargar cursos")
    except Exception as e:
        print(f"❌ Error en warmup_courses_cache: {e}")

# Lanzar warmup en thread separado al importar el módulo
warmup_thread = threading.Thread(target=warmup_courses_cache, daemon=True)
warmup_thread.start()

# ==========================
# HELPERS GENERALES
# ==========================
def _norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().strip().split())

def iso_from_datepicker(date_str):
    # Slack datepicker => 'YYYY-MM-DD'
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").isoformat() + "Z"
    except Exception:
        return None

def safe_name(val):
    """
    Thinkific exige first_name/last_name no vacíos. Si vienen vacíos/NaN,
    retornamos un espacio para pasar validación sin bloquear el proceso.
    """
    txt = (str(val or "")).strip()
    return txt if txt else " "

def format_expiry(raw):
    """Formatea fecha de expiración a YYYY-MM-DD o 'Sin fecha'"""
    if not raw:
        return "Sin fecha"
    try:
        if isinstance(raw, str) and len(raw) >= 10:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        return str(raw)[:10]
    except Exception:
        return "Sin fecha"

# Helper seguro para leer inputs Slack (evita None.strip())
def slack_input(values: dict, block_id: str, action_id: str) -> str:
    try:
        return (values.get(block_id, {}).get(action_id, {}).get("value") or "").strip()
    except Exception:
        return ""

# ==========================
# THINKIFIC API FUNCTIONS
# ==========================
def create_user_if_not_exists(email, first_name, last_name, telefono=None, pais=None, estado=None, max_retries=5):  # ← 5 reintentos
    """Crea usuario en Thinkific, saltando validación de custom fields si vienen vacíos."""
    email = (email or "").strip().lower()
    if not email:
        print("❌ Email vacío.")
        return None

    existing = get_user_by_email(email)
    if existing:
        print(f"✅ Usuario ya existe: {email} (id {existing.get('id')})")
        return existing

    # Preparar custom fields solo si vienen con valores
    custom_fields_payload = []
    has_custom_values = False
    
    # Si vienen teléfono, país o estado, obtener IDs de definiciones
    if telefono or pais or estado:
        defs = get_custom_field_definition_map()
        norm_defs = {_norm(k): v for k, v in defs.items()}
        tel_id = norm_defs.get(_norm("Telefono Personal"))
        pais_id = norm_defs.get(_norm("Pais de Residencia"))
        est_id = norm_defs.get(_norm("Estado o Provincia"))

        def _clean_val(v):
            txt = (str(v or "").strip())
            if txt.upper() in ("N/A", "NA", "N.A.", "N.A", ""):
                return None
            return txt

        cleaned_tel = _clean_val(telefono)
        cleaned_pais = _clean_val(pais)
        cleaned_estado = _clean_val(estado)

        if tel_id and cleaned_tel:
            custom_fields_payload.append({"custom_profile_field_definition_id": int(tel_id), "value": cleaned_tel})
            has_custom_values = True
        if pais_id and cleaned_pais:
            custom_fields_payload.append({"custom_profile_field_definition_id": int(pais_id), "value": cleaned_pais})
            has_custom_values = True
        if est_id and cleaned_estado:
            custom_fields_payload.append({"custom_profile_field_definition_id": int(est_id), "value": cleaned_estado})
            has_custom_values = True

    url = f"{BASE_URL}/users"
    base_payload = {
        "email": email,
        "first_name": safe_name(first_name),
        "last_name": safe_name(last_name),
        "skip_custom_fields_validation": not has_custom_values  # ← CLAVE: skip si no hay valores
    }
    
    if custom_fields_payload:
        base_payload["custom_profile_fields"] = custom_fields_payload

    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=HEADERS, json=base_payload, timeout=20)
            print(f"POST {url} -> {resp.status_code} | {resp.text[:500]}")
            
            if resp.status_code == 201:
                user = resp.json()
                print(f"✅ Creado usuario {email} (id {user.get('id')})")
                return user
            
            if resp.status_code == 422:
                error_msg = resp.text[:500]
                print(f"⚠️ 422 creando {email}: {error_msg}")
                time.sleep(1)
                return get_user_by_email(email)
            
            if resp.status_code == 429:
                wait = min((2 ** attempt) * 5, 60)  # ← CAP a 60s
                print(f"⏳ Rate limit creando {email} (intento {attempt+1}/{max_retries}). Esperar {wait}s.")
                time.sleep(wait)
                continue
            
            print(f"❌ Fallo creando {email}: {resp.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ Excepción creando {email}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
    
    return None

def enroll_user(user_id, course_id, expiry_date=None, max_retries=3):
    """Inscribe usuario con reintentos ante 429"""
    if not user_id or not course_id:
        print(f"❌ Faltan datos - user_id: {user_id}, course_id: {course_id}")
        return False

    url = f"{BASE_URL}/enrollments"
    data = {
        "user_id": user_id,
        "course_id": course_id,
        "is_free_trial": False
    }
    if expiry_date:
        data["expiry_date"] = expiry_date

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=HEADERS, json=data, timeout=15)
            
            if response.status_code == 429:
                wait = (2 ** attempt) * 2
                print(f"⏳ Rate limit enroll. Esperando {wait}s...")
                time.sleep(wait)
                continue
            
            if response.status_code == 201:
                enrollment = response.json()
                enrollment_id = enrollment["id"]
                activated_at = datetime.utcnow().isoformat() + "Z"
                put_url = f"{BASE_URL}/enrollments/{enrollment_id}"
                put_data = {"activated_at": activated_at}
                
                put_response = requests.put(put_url, headers=HEADERS, json=put_data, timeout=15)
                print(f"PUT {put_url} -> {put_response.status_code}")
                return put_response.status_code in (204, 200)
            else:
                print(f"❌ POST enroll falló: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error enroll (intento {attempt+1}): {e}")  # ← FIX: cerrar el f-string
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
    
    return False

def has_premium_access(user_id):
    enrollments = get_enrollments(user_id)
    for enrollment in enrollments:
        if (enrollment.get("course_name", "").lower()) in PREMIUM_PROGRAMS:
            return True
    return False

def fetch_all_courses(max_retries=3):
    """
    Devuelve lista de cursos activos en Thinkific como
    [{"id": int, "name": str}, ...]  (ordenados por nombre).
    """
    items = []
    page = 1
    while True:
        url = f"{BASE_URL}/courses?page={page}&limit=200&sort=name"
        
        for attempt in range(max_retries):
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                
                if r.status_code == 429:
                    wait = min((2 ** attempt) * 3, 30)
                    print(f"⏳ Rate limit courses (intento {attempt+1}/{max_retries}). Esperando {wait}s...")
                    time.sleep(wait)
                    continue
                
                if r.status_code != 200:
                    print(f"❌ No pude listar cursos: {r.status_code} {r.text}")
                    return items  # Retornar lo que se tenga hasta ahora
                
                data = r.json() or {}
                batch = data.get("items", []) or []
                
                # Transformar cada curso al formato necesario
                for it in batch:
                    items.append({"id": it.get("id"), "name": it.get("name", "")})
                
                if len(batch) < 200:
                    break  # No hay más páginas
                
                page += 1
                break  # Salir del loop de reintentos
                
            except Exception as e:
                print(f"❌ Excepción fetch_courses (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return items
        
        # Si agotó reintentos, salir del loop de páginas
        if attempt >= max_retries - 1:
            break
    
    items.sort(key=lambda x: _norm(x["name"]))
    print(f"✅ Cursos cargados: {len(items)}")
    return items

def get_custom_field_definition_map():
    """Obtiene mapa de nombres de custom fields a IDs."""
    url = f"{BASE_URL}/custom_profile_fields"  # ← FIX: endpoint correcto
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ No pude leer custom fields: {r.status_code} - {r.text[:300]}")
            return {}
        data = r.json() or {}
        items = data.get("items", []) or []
        out = {}
        for it in items:
            raw_name = (it.get("name") or "")
            fid = it.get("id")
            key = _norm(raw_name)
            if key and fid:
                out[key] = fid
        print(f"✅ Custom fields cargados: {len(out)} campos - {list(out.keys())}")  # ← Debug
        return out
    except Exception as e:
        print(f"❌ Excepción leyendo custom fields: {e}")
        return {}

def get_custom_field_value(user, label):
    if not user:
        return ""
    for f in (user.get("custom_profile_fields") or []):
        name = f.get("name") or ""
        if _norm(name) == _norm(label):
            return f.get("value") or ""
    return ""

def update_user_profile_with_custom_ids(user, first_name, last_name, email, tel, pais, estado):
    user_id = user["id"]
    url = f"{BASE_URL}/users/{user_id}"

    defs = get_custom_field_definition_map()
    defs_norm = {_norm(k): v for k, v in defs.items()}

    TEL_KEYS = [_norm("Telefono Personal"), _norm("Phone")]
    PAIS_KEYS = [_norm("Pais de Residencia"), _norm("Country")]
    EST_KEYS = [_norm("Estado o Provincia"), _norm("Province")]

    tel_id = next((defs_norm[k] for k in TEL_KEYS if k in defs_norm), None)
    pais_id = next((defs_norm[k] for k in PAIS_KEYS if k in defs_norm), None)
    est_id = next((defs_norm[k] for k in EST_KEYS if k in defs_norm), None)

    payload = {}
    payload["first_name"] = safe_name(first_name)
    payload["last_name"] = safe_name(last_name)

    current_email = (user.get("email") or "").strip().lower()
    if email and email.strip().lower() != current_email:
        payload["email"] = email.strip().lower()

    custom_payload = []
    if tel_id and tel and str(tel).strip():
        custom_payload.append({"custom_profile_field_definition_id": int(tel_id), "value": str(tel).strip()})
    if pais_id and pais and str(pais).strip():
        custom_payload.append({"custom_profile_field_definition_id": int(pais_id), "value": str(pais).strip()})
    if est_id and estado and str(estado).strip():
        custom_payload.append({"custom_profile_field_definition_id": int(est_id), "value": str(estado).strip()})
    
    if custom_payload:
        payload["custom_profile_fields"] = custom_payload

    try:
        r = requests.put(url, headers=HEADERS, json=payload, timeout=20)
        print(f"PUT {url} -> {r.status_code}")
        
        if r.status_code in (200, 204):
            g = requests.get(url, headers=HEADERS, timeout=15)
            if g.status_code == 200:
                return True, g.json()
            return True, {}
        
        return False, f"Thinkific {r.status_code}: {r.text[:300]}"
    except Exception as e:
        print(f"❌ Excepción actualizar perfil: {e}")
        return False, str(e)

# ==========================
# RUTAS BÁSICAS
# ==========================
@app.route("/")
def home():
    return "✅ Bot Thinkific corriendo."

# ===============================================================
# =================== COMANDO /ACCESO ===========================
# ===============================================================
@app.route("/slack/acceso", methods=["POST"])
def slack_acceso():
    raw_data = request.get_data(cache=True)
    if not verifier.is_valid_request(raw_data, request.headers):
        return make_response("Firma inválida", 403)

    form = request.form
    channel_id = form.get("channel_id")
    user_id = form.get("user_id")
    trigger_id = form.get("trigger_id")

    if channel_id != THINKIFIC_CHANNEL_ID:
        return make_response("❌ Comando solo permitido en #thinkific.", 200)

    course_ids = {
        "abacus experience": 2058326,
        "abacus experience-": 3154898,
        "abacus pro": 2060571,
        "abacus pro-": 3158575,
        "portfolio hacking": 2078283,
        "day trading dynamics": 2837735,
        "option collision": 2292845,
        "abacus masterclasses": 1975914,
        "programa de preparación": 2195573,
        "bootcamp": 2056542,
        "traders_club": 3035597,
        "todos los programas (team abacus)": 2200738,
        "road to first 10k": 3097316,
        "traders hub": 3186759,
    }

    options = [{
        "text": {"type": "plain_text", "text": k.title()},
        "value": k
    } for k in course_ids.keys()]

    view = {
        "type": "modal",
        "callback_id": "acceso_formulario",
        "title": {"type": "plain_text", "text": "Acceso Individual"},
        "submit": {"type": "plain_text", "text": "Otorgar"},
        "close": {"type": "plain_text", "text": "Cancelar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "email_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "email_input",
                    "placeholder": {"type": "plain_text", "text": "correo@dominio.com"}
                },
                "label": {"type": "plain_text", "text": "Correo del estudiante"}
            },
            {
                "type": "input",
                "block_id": "programa_block",
                "element": {
                    "type": "multi_static_select",
                    "action_id": "programa_input",
                    "placeholder": {"type": "plain_text", "text": "Selecciona uno o varios programas"},
                    "options": options
                },
                "label": {"type": "plain_text", "text": "Programas"}
            },
            {
                "type": "input",
                "optional": True,  # ← AHORA OPCIONAL
                "block_id": "fecha_block",
                "element": {
                    "type": "datepicker",
                    "action_id": "fecha_input",
                    "placeholder": {"type": "plain_text", "text": "Fecha de expiración (opcional)"}
                },
                "label": {"type": "plain_text", "text": "Fecha de expiración"},
                "hint": {"type": "plain_text", "text": "⚠️ Bootcamp y Masterclasses pueden dejarse sin fecha (acceso permanente)"}
            },
            {
                "type": "actions",
                "block_id": "acceso_actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "open_create_user",
                        "style": "primary",
                        "text": {"type": "plain_text", "text": "Crear cuenta"}
                    }
                ]
            }
        ]
    }

    try:
        slack_client.views_open(trigger_id=trigger_id, view=view)
        return make_response("", 200)
    except SlackApiError as e:
        print(f"❌ Error abriendo modal /acceso: {e.response.get('error')}")
        return make_response("Error modal", 500)

# ===============================================================
# =================== COMANDO /FIX ==============================
# ===============================================================
@app.route("/slack/fix", methods=["POST"])
def slack_fix():
    raw_data = request.get_data(cache=True)
    if not verifier.is_valid_request(raw_data, request.headers):
        return make_response("Invalid signature", 403)

    form = request.form
    payload = form.get("text", "").strip().lower()
    channel_id = form.get("channel_id")
    user_id_actor = form.get("user_id")
    trigger_id = form.get("trigger_id")

    if channel_id != THINKIFIC_CHANNEL_ID:
        return make_response("❌ Este comando solo funciona en #thinkific.", 200)

    if not payload:
        return make_response("❌ Uso: /fix correo@dominio.com", 200)

    email = payload
    user = get_user_by_email(email)
    if not user:
        return make_response(f"❌ Usuario `{email}` no encontrado.", 200)

    # Obtener inscripciones activas para mostrar en multi-select
    enrollments = get_enrollments(user["id"])
    active_enrollments = [e for e in enrollments if not e.get("expired")]

    remove_options = []
    for enr in active_enrollments:
        cname = enr.get("course_name", "Desconocido")
        cid = enr.get("course_id")
        eid = enr.get("id")
        remove_options.append({
            "text": {"type": "plain_text", "text": cname},
            "value": json.dumps({"enrollment_id": eid, "course_id": cid, "course_name": cname})
        })

    # Obtener valores actuales del perfil
    initial_tel = get_custom_field_value(user, "Telefono Personal")
    initial_pais = get_custom_field_value(user, "Pais de Residencia")
    initial_estado = get_custom_field_value(user, "Estado o Provincia")

    blocks = [
        {
            "type": "input",
            "optional": True,
            "block_id": "first_block",
            "element": {"type": "plain_text_input", "action_id": "first_input", "initial_value": (user.get("first_name") or "")},
            "label": {"type": "plain_text", "text": "Nombre (core)"}
        },
        {
            "type": "input",
            "optional": True,
            "block_id": "last_block",
            "element": {"type": "plain_text_input", "action_id": "last_input", "initial_value": (user.get("last_name") or "")},
            "label": {"type": "plain_text", "text": "Apellido (core)"}
        },
        {
            "type": "input",
            "optional": True,
            "block_id": "email_block_fix",
            "element": {"type": "plain_text_input", "action_id": "email_input_fix", "initial_value": (user.get("email") or "")},
            "label": {"type": "plain_text", "text": "Correo (core) - nuevo"}
        },
        {
            "type": "input",
            "optional": True,
            "block_id": "telefono_block",
            "element": {"type": "plain_text_input", "action_id": "telefono_input", "initial_value": initial_tel},
            "label": {"type": "plain_text", "text": "Teléfono Personal"}
        },
        {
            "type": "input",
            "optional": True,
            "block_id": "pais_block",
            "element": {"type": "plain_text_input", "action_id": "pais_input", "initial_value": initial_pais},
            "label": {"type": "plain_text", "text": "País de Residencia"}
        },
        {
            "type": "input",
            "optional": True,
            "block_id": "estado_block",
            "element": {"type": "plain_text_input", "action_id": "estado_input", "initial_value": initial_estado},
            "label": {"type": "plain_text", "text": "Estado o Provincia"}
        }
    ]

    # Agregar bloque de eliminación solo si hay programas activos
    if remove_options:
        blocks.append({
            "type": "input",
            "optional": True,
            "block_id": "remove_block",
            "element": {
                "type": "multi_static_select",
                "action_id": "remove_select",
                "placeholder": {"type": "plain_text", "text": "Selecciona programas"},
                "options": remove_options
            },
            "label": {"type": "plain_text", "text": "Gestionar Programas (opcional)"}
        })
        blocks.append({
            "type": "input",
            "optional": True,
            "block_id": "new_expiry_block",
            "element": {
                "type": "datepicker",
                "action_id": "new_expiry_input",
                "placeholder": {"type": "plain_text", "text": "Nueva fecha de expiración"}
            },
            "label": {"type": "plain_text", "text": "Nueva fecha (para cambiar expiración)"}
        })
        blocks.append({
            "type": "actions",
            "block_id": "remove_actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "expire_today",
                    "style": "danger",
                    "text": {"type": "plain_text", "text": "Expirar hoy"}
                },
                {
                    "type": "button",
                    "action_id": "change_expiry",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Cambiar fecha"}
                }
            ]
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":information_source: Sin programas activos para eliminar."}
        })

    # Contraseña y acciones rápidas
    blocks.extend([
        {
            "type": "input",
            "optional": True,
            "block_id": "password_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "password_input",
                "placeholder": {"type": "plain_text", "text": "Nueva contraseña"}
            },
            "label": {"type": "plain_text", "text": "Nueva contraseña (opcional)"},
            "hint": {"type": "plain_text", "text": "Usa el botón 'Cambiar contraseña'. No necesitas presionar Actualizar."}
        },
        {
            "type": "actions",
            "block_id": "user_actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "apply_password",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Cambiar contraseña"}
                },
                {
                    "type": "button",
                    "action_id": "delete_user",
                    "style": "danger",
                    "text": {"type": "plain_text", "text": "Eliminar usuario"},
                    "confirm": {
                        "title": {"type": "plain_text", "text": "¿Eliminar usuario?"},
                        "text": {"type": "mrkdwn", "text": "Esta acción es permanente."},
                        "confirm": {"type": "plain_text", "text": "Sí, eliminar"},
                        "deny": {"type": "plain_text", "text": "Cancelar"}
                    }
                }
            ]
        }
    ])

    try:
        slack_client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "fix_formulario",
                "title": {"type": "plain_text", "text": "Editar Información"},
                "submit": {"type": "plain_text", "text": "Actualizar"},
                "close": {"type": "plain_text", "text": "Cancelar"},
                "private_metadata": json.dumps({"anchor_email": email, "actor_id": user_id_actor}),
                "blocks": blocks
            }
        )
        return make_response("", 200)
    except SlackApiError as e:
        print(f"❌ Error al abrir modal de edición: {e.response.get('error')}")
        return make_response("Error modal", 500)

# ===============================================================
# =============== COMANDO /COURSES_INFO =========================
# ===============================================================
@app.route("/slack/courses_info", methods=["POST"])
def slack_courses_info():
    form = request.form
    payload = form.get("text")
    user_id = form.get("user_id") or form.get("user")

    if not payload:
        return make_response("❌ Debes proporcionar un correo después del comando /courses_info.", 200)

    email = payload.strip().lower()
    if not email:
        return make_response("❌ Correo electrónico no proporcionado.", 200)

    print(f"📧 Correo solicitado: {email} por <@{user_id}>")
    user = get_user_by_email(email)
    if not user:
        return make_response(f"❌ Usuario con correo `{email}` no encontrado en Thinkific. (Solicitado por: <@{user_id}>)", 200)

    try:
        # ========== FIX: Obtener detalles completos del usuario con GET /users/{id} ==========
        user_id_thinkific = user.get("id")
        user_detail_url = f"{BASE_URL}/users/{user_id_thinkific}"
        
        user_full = user  # Fallback a datos básicos
        try:
            print(f"🔍 Obteniendo detalles completos para user_id {user_id_thinkific}...")
            user_detail_resp = requests.get(user_detail_url, headers=HEADERS, timeout=15)
            print(f"GET {user_detail_url} -> {user_detail_resp.status_code}")
            
            if user_detail_resp.status_code == 200:
                user_full = user_detail_resp.json()
                print(f"✅ Detalles completos obtenidos: {user_full.keys()}")
            else:
                print(f"⚠️ No se pudieron obtener detalles completos: {user_detail_resp.status_code} - {user_detail_resp.text[:300]}")
        except Exception as e:
            print(f"⚠️ Error obteniendo detalles de usuario: {e}")

        enrollments = get_enrollments(user_id_thinkific)
        
        if not enrollments:
            slack_client.chat_postMessage(
                channel=THINKIFIC_CHANNEL_NAME,
                text=f"❌ El usuario `{email}` no tiene ningún programa asignado. (Solicitado por: <@{user_id}>)",
            )
            return make_response(f"❌ El usuario `{email}` no tiene ningún programa asignado.", 200)

        # Separar activos y expirados
        active_enrollments = [e for e in enrollments if not e.get("expired")]
        expired_enrollments = [e for e in enrollments if e.get("expired")]

        # ========== Usar user_full (con datos completos) ==========
        created_at = user_full.get("created_at")
        last_sign_in = user_full.get("last_sign_in_at")
        sign_in_count = user_full.get("sign_in_count")
        
        # Debug: imprimir valores crudos
        print(f"📊 Datos de acceso para {email}:")
        print(f"  • created_at: {created_at}")
        print(f"  • last_sign_in_at: {last_sign_in}")
        print(f"  • sign_in_count: {sign_in_count}")
        
        fecha_creacion = format_expiry(created_at) if created_at else "No disponible"
        
        # Manejo robusto de valores None/0
        if sign_in_count is None or sign_in_count == 0:
            ultimo_acceso = "Nunca ha ingresado"
            sign_in_count = 0
        else:
            ultimo_acceso = format_expiry(last_sign_in) if last_sign_in else "No disponible"

        # Mensaje PADRE con información de acceso
        resp = slack_client.chat_postMessage(
            channel=THINKIFIC_CHANNEL_NAME,
            text=(f"📚 *Información de Usuario* (Solicitado por: <@{user_id}>)\n\n"
                  f"• *Email:* <mailto:{email}|{email}>\n"
                  f"• *Cuenta creada:* {fecha_creacion}\n"
                  f"• *Último acceso:* {ultimo_acceso}\n"
                  f"• *Total accesos:* {sign_in_count}\n\n"
                  f"✅ *Programas activos:* {len(active_enrollments)}\n"
                  f"❌ *Programas expirados:* {len(expired_enrollments)}"),
        )
        thread_ts = resp["ts"]

        # HILOS con programas activos
        if active_enrollments:
            slack_client.chat_postMessage(
                channel=THINKIFIC_CHANNEL_NAME,
                thread_ts=thread_ts,
                text="*✅ PROGRAMAS ACTIVOS*"
            )
            for enrollment in active_enrollments:
                course_name = enrollment.get("course_name", "Desconocido")
                expiry_raw = enrollment.get("expiry_date")
                expiry_date = format_expiry(expiry_raw)
                
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    thread_ts=thread_ts,
                    text=f"• *{course_name}*\n  📅 Expira: {expiry_date}"
                )

        # HILOS con programas expirados
        if expired_enrollments:
            slack_client.chat_postMessage(
                channel=THINKIFIC_CHANNEL_NAME,
                thread_ts=thread_ts,
                text="\n*❌ PROGRAMAS EXPIRADOS*"
            )
            for enrollment in expired_enrollments:
                course_name = enrollment.get("course_name", "Desconocido")
                expiry_raw = enrollment.get("expiry_date")
                expiry_date = format_expiry(expiry_raw)
                
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    thread_ts=thread_ts,
                    text=f"• *{course_name}*\n  ⏱️ Expiró: {expiry_date}"
                )

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()  # Debug completo del error
        return make_response("❌ Hubo un error al procesar la solicitud.", 200)

    return make_response(f"✅ Información de `{email}` enviada en hilo. (Solicitado por: <@{user_id}>)", 200)

# ==========================
# CACHE DE CURSOS EN RAM
# ==========================
COURSES_CACHE = {
    "data": [],
    "last_updated": None
}
CACHE_TTL = 3600  # 1 hora

def get_cached_courses():
    """Devuelve cursos desde cache (no bloquea si está vacío)"""
    now = time.time()
    last_update = COURSES_CACHE.get("last_updated") or 0
    
    # Si cache está vacío, retornar inmediatamente (ya se está cargando en background)
    if not COURSES_CACHE["data"]:
        print("⏳ Cache aún no cargado, retornando lista vacía")
        return []
    
    # Si cache expiró, actualizar en background (no bloquear)
    if (now - last_update) > CACHE_TTL:
        print("🔄 Cache expirado, actualizando en background...")
        update_thread = threading.Thread(target=lambda: fetch_all_courses(), daemon=True)
        update_thread.start()
        # Retornar cache antiguo mientras se actualiza
        return COURSES_CACHE["data"]
    
    print(f"✅ Usando cache de cursos ({len(COURSES_CACHE['data'])} items)")
    return COURSES_CACHE["data"]

# ===============================================================
# =============== NUEVO FLUJO /ACCESO-MASIVO (2 PASOS) ==========
# ===============================================================
@app.route("/slack/acceso-masivo", methods=["POST"])
def slack_acceso_masivo():
    raw_data = request.get_data(cache=True)
    if not verifier.is_valid_request(raw_data, request.headers):
        return make_response("Invalid signature", 403)

    form = request.form
    user_id = form.get("user_id")
    channel_id = form.get("channel_id")
    trigger_id = form.get("trigger_id")

    if channel_id != THINKIFIC_CHANNEL_ID:
        return make_response("❌ Este comando solo funciona en #thinkific.", 200)

    # ==== USO DE LISTA ESTÁTICA (sin llamadas a Thinkific) ====
    options = [{
        "text": {"type": "plain_text", "text": f"{name.title()} (#{cid})"},
        "value": json.dumps({"id": cid, "name": name.title()})
    } for name, cid in COURSE_IDS.items()]

    view = {
        "type": "modal",
        "callback_id": "acceso_masivo_step1",
        "title": {"type": "plain_text", "text": "Acceso Masivo — Paso 1"},
        "submit": {"type": "plain_text", "text": "Siguiente"},
        "close": {"type": "plain_text", "text": "Cancelar"},
        "private_metadata": json.dumps({"channel_id": channel_id, "user_id": user_id}),
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": "*Sube la lista* (Excel/CSV) en este canal con columnas: `Nombre`, `Apellido(s)`, `Correo`.\nLuego selecciona los cursos."}
            },
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "courses_block",
                "element": {
                    "type": "multi_static_select",
                    "action_id": "courses_select",
                    "placeholder": {"type": "plain_text", "text": "Selecciona cursos"},
                    "options": options
                },
                "label": {"type": "plain_text", "text": "Cursos a asignar"}
            }
        ]
    }

    try:
        slack_client.views_open(trigger_id=trigger_id, view=view)
        return make_response("", 200)
    except SlackApiError as e:
        print(f"❌ Error modal paso 1: {e.response.get('error')}")
        return make_response("Error modal", 500)

# ===============================================================
# ============== INTERACTIVIDAD (MODALES / BOTONES) =================
# ===============================================================
@app.route("/slack/interactividad", methods=["POST"])
def slack_interactividad():
    raw = request.get_data(cache=True)
    if not verifier.is_valid_request(raw, request.headers):
        return make_response("Firma inválida", 403)

    payload = request.form.get("payload")
    if not payload:
        return make_response("", 200)

    try:
        data = json.loads(payload)
    except Exception as e:
        print(f"❌ payload json error: {e}")
        return make_response("", 200)

    tipo = data.get("type")
    cbid = None
    if tipo == "view_submission":
        cbid = (data.get("view") or {}).get("callback_id")
    # (block_actions no lleva callback_id para botones)

    # ========== VIEW SUBMISSION (formularios enviados) ==========
    if tipo == "view_submission":
        # acceso individual
        if cbid == "acceso_formulario":
            values = data["view"]["state"]["values"]
            email = values["email_block"]["email_input"]["value"].strip().lower()
            selected_opts = values["programa_block"]["programa_input"].get("selected_options", []) or []
            fecha = values["fecha_block"]["fecha_input"].get("selected_date")  # ← puede ser None ahora
            user_id_actor = (data.get("user") or {}).get("id")
            channel_id = THINKIFIC_CHANNEL_NAME

            if not selected_opts:
                return jsonify({
                    "response_action": "errors",
                    "errors": {"programa_block": "Selecciona al menos un programa."}
                }), 200

            # ========== VALIDACIÓN DE FECHA SEGÚN PROGRAMA ==========
            PROGRAMAS_SIN_FECHA = ["bootcamp", "abacus masterclasses"]
            selected_program_names = [opt["value"] for opt in selected_opts]
            
            # Si hay programas que NO son Bootcamp/Masterclasses, exigir fecha
            requiere_fecha = any(prog not in PROGRAMAS_SIN_FECHA for prog in selected_program_names)
            
            if requiere_fecha and not fecha:
                return jsonify({
                    "response_action": "errors",
                    "errors": {"fecha_block": "La fecha es obligatoria para programas premium. Solo Bootcamp y Masterclasses pueden dejarse sin fecha."}
                }), 200

            course_ids = {
                "abacus experience": 2058326,
                "abacus experience-": 3154898,
                "abacus pro": 2060571,
                "abacus pro-": 3158575,
                "portfolio hacking": 2078283,
                "day trading dynamics": 2837735,
                "option collision": 2292845,
                "abacus masterclasses": 1975914,
                "programa de preparación": 2195573,
                "bootcamp": 2056542,
                "traders_club": 3035597,
                "todos los programas (team abacus)": 2200738,
                "road to first 10k": 3097316,
                "traders hub": 3186759,
            }

            selected_course_ids = [(name, COURSE_IDS.get(name)) for name in selected_program_names if COURSE_IDS.get(name)]

            user = get_user_by_email(email)
            if not user:
                # Usuario NO existe -> abrir modal "Crear y Asignar"
                resumen = "• " + "\n• ".join([n.title() for n, _ in selected_course_ids]) if selected_course_ids else "Ninguno"
                fecha_display = fecha if fecha else "Sin fecha límite"
                
                create_assign_view = {
                    "type": "modal",
                    "callback_id": "crear_usuario_asignar_form",
                    "title": {"type": "plain_text", "text": "Crear y Asignar"},
                    "submit": {"type": "plain_text", "text": "Crear y asignar"},
                    "close": {"type": "plain_text", "text": "Cancelar"},
                    "private_metadata": json.dumps({
                        "actor_id": user_id_actor,
                        "channel_id": channel_id,
                        "program_names": selected_program_names,
                        "fecha": fecha  # puede ser None
                    }),
                    "blocks": [
                        {"type": "section", "text": {"type": "mrkdwn", "text": "*Programas a asignar:*\n" + resumen}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Expira:* {fecha_display}"}]},
                        {"type": "divider"},
                        {"type": "input", "block_id": "cu_email_block", "element": {"type": "plain_text_input", "action_id": "cu_email_input", "initial_value": email}, "label": {"type": "plain_text", "text": "Correo"}},
                        {"type": "input", "block_id": "cu_first_block", "element": {"type": "plain_text_input", "action_id": "cu_first_input"}, "label": {"type": "plain_text", "text": "Nombre"}},
                        {"type": "input", "block_id": "cu_last_block", "element": {"type": "plain_text_input", "action_id": "cu_last_input"}, "label": {"type": "plain_text", "text": "Apellido"}},
                        {"type": "input", "optional": True, "block_id": "cu_tel_block", "element": {"type": "plain_text_input", "action_id": "cu_tel_input"}, "label": {"type": "plain_text", "text": "Teléfono"}},
                        {"type": "input", "optional": True, "block_id": "cu_pais_block", "element": {"type": "plain_text_input", "action_id": "cu_pais_input"}, "label": {"type": "plain_text", "text": "País"}},
                        {"type": "input", "optional": True, "block_id": "cu_estado_block", "element": {"type": "plain_text_input", "action_id": "cu_estado_input"}, "label": {"type": "plain_text", "text": "Estado/Provincia"}}
                    ]
                }
                print(f"🔄 Abriendo modal crear_usuario_asignar_form para {email}")
                return jsonify({"response_action": "update", "view": create_assign_view}), 200

            # Usuario existe -> asignar directamente
            had_premium_before = has_premium_access(user["id"])
            existing = get_enrollments(user["id"])
            already = set(e.get("course_id") for e in existing if not e.get("expired"))

            fecha_iso = iso_from_datepicker(fecha) if fecha else None  # ← puede ser None

            successes = []
            skipped = []
            for name, cid in selected_course_ids:
                if cid in already:
                    skipped.append(f"{name} (ya tiene acceso)")
                    continue
                ok = enroll_user(user["id"], cid, fecha_iso)  # ← pasa None si no hay fecha
                if ok:
                    successes.append(name)
                else:
                    skipped.append(f"{name} (error)")

            # Mensaje específico si todos ya estaban asignados (y sin errores)
            already_has = [s.replace(" (ya tiene acceso)", "") for s in skipped if "(ya tiene acceso)" in s]
            errors = [s for s in skipped if "(error)" in s]
            if not successes and already_has and not errors:
                fecha_display = fecha if fecha else "Sin fecha límite"
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=(f"ℹ️ El correo <mailto:{email}|{email}> ya tiene acceso a "
                          f"{', '.join([c.title() for c in already_has])}. "
                          f"Acceso dado por: <@{user_id_actor}>")
                )
                return jsonify({"response_action": "clear"}), 200

            premium_selected = any(n in PREMIUM_PROGRAMS for n in successes)

            msg_header = "✅ Accesos otorgados" if successes else "ℹ️ Sin accesos nuevos"
            cursos_ok = ", ".join([c.title() for c in successes]) if successes else "Ninguno"
            cursos_skip = ", ".join(skipped) if skipped else "Ninguno"
            fecha_display = fecha if fecha else "Sin fecha límite"

            parent = slack_client.chat_postMessage(
                channel=channel_id,
                text=(f"{msg_header}\n"
                      f"• Correo: <mailto:{email}|{email}>\n"
                      f"• Cursos asignados: {cursos_ok}\n"
                      f"• Omitidos: {cursos_skip}\n"
                      f"• Expira: {fecha_display}\n"
                      f"• Por: <@{user_id_actor}>")
            )

            if (not had_premium_before) and premium_selected:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=parent["ts"],
                    text=f":receipt: Adjunta prueba(s) de pago para los programas premium. <@{user_id_actor}>"
                )

            return jsonify({"response_action": "clear"}), 200

        if cbid == "crear_usuario_asignar_form":
            values = data["view"]["state"]["values"]
            # Recuperar metadata (programas seleccionados y fecha)
            try:
                meta = json.loads(data["view"].get("private_metadata") or "{}")
            except Exception:
                meta = {}
            actor_id = meta.get("actor_id") or (data.get("user") or {}).get("id")
            channel_id = meta.get("channel_id") or THINKIFIC_CHANNEL_NAME
            program_names = meta.get("program_names") or []
            fecha = meta.get("fecha")  # formato YYYY-MM-DD esperado desde datepicker

            email = values["cu_email_block"]["cu_email_input"]["value"].strip().lower()
            first = values["cu_first_block"]["cu_first_input"]["value"].strip()
            last  = values["cu_last_block"]["cu_last_input"]["value"].strip()
            tel   = (values.get("cu_tel_block", {}).get("cu_tel_input", {}).get("value") or "").strip()
            pais  = (values.get("cu_pais_block", {}).get("cu_pais_input", {}).get("value") or "").strip()
            estado= (values.get("cu_estado_block", {}).get("cu_estado_input", {}).get("value") or "").strip()

            # ========== FIX: Validar si usuario ya existe ANTES de intentar crear ==========
            existing_user = get_user_by_email(email)
            if existing_user:
                print(f"✅ Usuario ya existía: {email} (id {existing_user.get('id')})")
                user = existing_user
            else:
                user = create_user_if_not_exists(email, first, last, tel, pais, estado)
                if not user:
                    # ========== FIX: Retornar error en modal en lugar de mensaje en canal ==========
                    return jsonify({
                        "response_action": "errors",
                        "errors": {"cu_email_block": f"No se pudo crear la cuenta. Verifica los datos o contacta soporte."}
                    }), 200

            course_ids = {
                "abacus experience": 2058326,
                "abacus experience-": 3154898,
                "abacus pro": 2060571,
                "abacus pro-": 3158575,
                "portfolio hacking": 2078283,
                "day trading dynamics": 2837735,
                "option collision": 2292845,
                "abacus masterclasses": 1975914,
                "programa de preparación": 2195573,
                "bootcamp": 2056542,
                "traders_club": 3035597,
                "todos los programas (team abacus)": 2200738,
                "road to first 10k": 3097316,
                "traders hub": 3186759,
            }
            selected_course_ids = [(name, COURSE_IDS.get(name)) for name in program_names if COURSE_IDS.get(name)]

            fecha_iso = iso_from_datepicker(fecha) if fecha else None  # ← puede ser None

            successes, skipped = [], []
            for name, cid in selected_course_ids:
                ok = enroll_user(user["id"], cid, fecha_iso)
                if ok:
                    successes.append(name)
                else:
                    skipped.append(f"{name} (error)")

            premium_selected = any(n in PREMIUM_PROGRAMS for n in successes)

            header = "✅ Usuario creado y accesos otorgados" if successes else "👤 Usuario creado sin programas"
            cursos_ok = ", ".join([n.title() for n in successes]) if successes else "Ninguno"
            cursos_skip = ", ".join([n.title() for n in skipped]) if skipped else "Ninguno"
            fecha_display = fecha if fecha else "Sin fecha límite"

            parent = slack_client.chat_postMessage(
                channel=channel_id,
                text=(f"{header}\n"
                      f"• Correo: <mailto:{email}|{email}>\n"
                      f"• Cursos asignados: {cursos_ok}\n"
                      f"• Omitidos: {cursos_skip}\n"
                      f"• Expira: {fecha_display}\n"
                      f"• Por: <@{actor_id}>")
            )

            if premium_selected:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=parent["ts"],
                    text=f":receipt: Adjunta prueba(s) de pago para programas premium. <@{actor_id}>"
                )

            # ========== FIX: Cerrar modal correctamente ==========
            return jsonify({"response_action": "clear"}), 200

        if cbid == "fix_formulario":
            values = data["view"]["state"]["values"]
            meta = json.loads(data["view"]["private_metadata"])
            anchor_email = meta.get("anchor_email", "").strip().lower()
            actor_id = meta.get("actor_id") or data["user"]["id"]

            first_name = slack_input(values, "first_block", "first_input")
            last_name  = slack_input(values, "last_block", "last_input")
            new_email  = slack_input(values, "email_block_fix", "email_input_fix")
            telefono   = slack_input(values, "telefono_block", "telefono_input")
            pais       = slack_input(values, "pais_block", "pais_input")
            estado     = slack_input(values, "estado_block", "estado_input")

            remove_selected = []
            try:
                selected_options = values.get("remove_block", {}).get("remove_select", {}).get("selected_options", []) or []
                for opt in selected_options:
                    try:
                        payload = json.loads(opt.get("value"))
                        remove_selected.append(payload)
                    except Exception:
                        continue
            except Exception:
                remove_selected = []

            user = get_user_by_email(anchor_email)
            if not user:
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    text=f"❌ Usuario `{anchor_email}` no encontrado. Por: <@{actor_id}>"
                )
                return jsonify({"response_action": "clear"}), 200

            ok, updated = update_user_profile_with_custom_ids(
                user,
                first_name or user.get("first_name",""),
                last_name or user.get("last_name",""),
                new_email or user.get("email",""),
                telefono,
                pais,
                estado
            )
            removed = []
            remove_err = []
            for r in remove_selected:
                enrollment_id = r.get("enrollment_id")
                course_name = r.get("course_name") or str(r.get("course_id"))
                if not enrollment_id:
                    remove_err.append((course_name, "missing_enrollment_id"))
                    continue
                del_url = f"{BASE_URL}/enrollments/{enrollment_id}"
                try:
                    resp = requests.delete(del_url, headers=HEADERS, timeout=15)
                    if resp.status_code in (204, 200):
                        removed.append(course_name)
                    else:
                        remove_err.append((course_name, f"{resp.status_code}: {resp.text[:300]}"))
                except Exception as e:
                    remove_err.append((course_name, str(e)))

            if ok:
                text = f"✅ Perfil actualizado para <mailto:{new_email or anchor_email}|{new_email or anchor_email}>. Por: <@{actor_id}>"
                if removed:
                    text += "\n• Programas eliminados: " + ", ".join(removed)
                if remove_err:
                    text += "\n• Errores: " + "; ".join([f'{t}: {e}' for t, e in remove_err])
                slack_client.chat_postMessage(channel=THINKIFIC_CHANNEL_NAME, text=text)
            else:
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    text=f"❌ No se pudo actualizar `{new_email or anchor_email}`. {updated} Por: <@{actor_id}>"
                )

            return jsonify({"response_action": "clear"}), 200

        if cbid == "acceso_masivo_step1":
            meta = json.loads(data["view"]["private_metadata"])
            channel_id = meta["channel_id"]
            user_id = meta["user_id"]

            values = data["view"]["state"]["values"]
            selected = values["courses_block"]["courses_select"]["selected_options"]

            if not selected:
                return jsonify({
                    "response_action": "errors",
                    "errors": {"courses_block": "Selecciona al menos un curso."}
                }), 200

            selected_courses = [json.loads(opt["value"]) for opt in selected]

            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": "*Paso 2: Configurar fechas y confirmar*"}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": "⚠️ *Antes de presionar 'Procesar':*\n1. Cierra este modal\n2. Sube tu archivo Excel/CSV en #thinkific\n3. Vuelve a abrir `/acceso-masivo` y repite el proceso"}]},
                {"type": "divider"}
            ]
            
            for c in selected_courses:
                blocks.append({
                    "type": "input",
                    "optional": True,
                    "block_id": f"date_block_{c['id']}",
                    "element": {
                        "type": "datepicker",
                        "action_id": f"datepick_{c['id']}",
                        "placeholder": {"type": "plain_text", "text": "Sin fecha"}
                    },
                    "label": {"type": "plain_text", "text": f"Fecha para {c['name']}"}
                })

            new_view = {
                "type": "modal",
                "callback_id": "acceso_masivo_step2",
                "title": {"type": "plain_text", "text": "Acceso Masivo — Paso 2"},
                "submit": {"type": "plain_text", "text": "Procesar"},
                "close": {"type": "plain_text", "text": "Cancelar"},
                "private_metadata": json.dumps({
                    "channel_id": channel_id,
                    "user_id": user_id,
                    "selected_courses": selected_courses
                }),
                "blocks": blocks
            }

            return jsonify({"response_action": "update", "view": new_view}), 200

        if cbid == "acceso_masivo_step2":
            meta = json.loads(data["view"]["private_metadata"])
            channel_id = meta["channel_id"]
            actor_id = meta["user_id"]
            selected_courses = meta["selected_courses"]

            values = data["view"]["state"]["values"]

            # Obtener fechas por curso
            dates_per_course = {}
            for c in selected_courses:
                cid = c["id"]
                try:
                    fecha = values[f"date_block_{cid}"][f"datepick_{cid}"].get("selected_date")
                    if fecha:
                        dates_per_course[str(cid)] = fecha
                except Exception:
                    continue

            # Buscar archivo más reciente en el canal
            file_id = None
            try:
                history = slack_client.conversations_history(channel=channel_id, limit=20)
                for msg in history.get("messages", []):
                    files = msg.get("files", [])
                    for f in files:
                        mime = f.get("mimetype", "")
                        name = f.get("name", "").lower()
                        if any(x in mime for x in ["spreadsheet", "csv", "excel"]) or name.endswith((".xlsx", ".xls", ".csv")):
                            file_id = f.get("id")
                            break
                    if file_id:
                        break
            except Exception as e:
                print(f"❌ Error buscando archivo: {e}")

            if not file_id:
                return jsonify({
                    "response_action": "errors",
                    "errors": {"courses_block": "No se encontró archivo Excel/CSV reciente en el canal."}
                }), 200

            # Descargar archivo
            try:
                file_info = slack_client.files_info(file=file_id)
                url = file_info["file"]["url_private"]
                headers_dl = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
                
                with requests.get(url, headers=headers_dl, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    content = BytesIO(r.content)
                    
                    try:
                        df = pd.read_excel(content)
                    except Exception:
                        content.seek(0)
                        df = pd.read_csv(content)
                        
            except Exception as e:
                print(f"❌ Error descargando archivo: {e}")
                return jsonify({
                    "response_action": "errors",
                    "errors": {"courses_block": f"Error descargando archivo: {str(e)[:100]}"}
                }), 200

            # Validar columnas
            df.columns = df.columns.str.strip()
            
            col_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if "nombre" in col_lower and "apellido" not in col_lower:
                    col_map[col] = "Nombre"
                elif "apellido" in col_lower:
                    col_map[col] = "Apellido(s)"
                elif "correo" in col_lower or "email" in col_lower:
                    col_map[col] = "Correo"
            
            df.rename(columns=col_map, inplace=True)
            
            expected_cols = {"Nombre", "Apellido(s)", "Correo"}
            missing_cols = expected_cols - set(df.columns)
            if missing_cols:
                return jsonify({
                    "response_action": "errors",
                    "errors": {"courses_block": f"Faltan columnas: {', '.join(missing_cols)}"}
                }), 200

            # Limpiar datos
            df["Correo"] = df["Correo"].str.strip().str.lower()
            df["Nombre"] = df["Nombre"].apply(lambda x: str(x).strip())
            df["Apellido(s)"] = df["Apellido(s)"].apply(lambda x: str(x).strip())

            rows = df.to_dict(orient="records")

            # ======== PROCESAMIENTO EN SEGUNDO PLANO ========
            def background_process():
                BATCH_SIZE = 50
                total_users = len(rows)
                batches = [rows[i:i + BATCH_SIZE] for i in range(0, total_users, BATCH_SIZE)]

                # MENSAJE PADRE
                parent_msg = slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"🔄 *Acceso Masivo Iniciado*\n• Total: {total_users} usuarios\n• Lotes: {len(batches)}\n• Cursos: {', '.join([c['name'] for c in selected_courses])}\n• Por: <@{actor_id}>"
                )
                parent_ts = parent_msg["ts"]

                all_results = []
                
                for batch_num, batch in enumerate(batches, 1):
                    slack_client.chat_postMessage(
                        channel=channel_id,
                        thread_ts=parent_ts,
                        text=f"📦 *Lote {batch_num}/{len(batches)}* ({len(batch)} usuarios) - Procesando..."
                    )

                    def process_row(row):
                        nombre = row.get("Nombre", "").strip()
                        apellidos = row.get("Apellido(s)", "").strip()
                        email = row.get("Correo", "").strip().lower()

                        if not email or not nombre:
                            return {
                                "email": email or "N/A",
                                "nombre": nombre,
                                "apellidos": apellidos,
                                "estado": "❌ Faltan datos",
                                "cursos_ok": "",
                                "cursos_error": ""
                            }

                        user = get_user_by_email(email)
                        if not user:
                            user = create_user_if_not_exists(email, nombre, apellidos, "", "", "")
                            if not user:
                                return {
                                    "email": email,
                                    "nombre": nombre,
                                    "apellidos": apellidos,
                                    "estado": "❌ Error creando",
                                    "cursos_ok": "",
                                    "cursos_error": ""
                                }

                        existing = get_enrollments(user["id"])
                        already_enrolled = set(e.get("course_id") for e in existing if not e.get("expired"))

                        successes = []
                        errors = []

                        for course_data in selected_courses:
                            course_id = course_data.get("id")
                            course_name = course_data.get("name")
                            fecha_str = dates_per_course.get(str(course_id))
                            fecha_iso = iso_from_datepicker(fecha_str) if fecha_str else None

                            if course_id in already_enrolled:
                                continue

                            ok = enroll_user(user["id"], course_id, fecha_iso)
                            if ok:
                                successes.append(course_name)
                            else:
                                errors.append(course_name)

                        estado = "✅ OK" if successes else ("⚠️ Ya inscrito" if not errors else "❌ Error")
                        
                        return {
                            "email": email,
                            "nombre": nombre,
                            "apellidos": apellidos,
                            "estado": estado,
                            "cursos_ok": ", ".join(successes) if successes else "Ninguno",
                            "cursos_error": ", ".join(errors) if errors else "Ninguno"
                        }

                    # Procesar secuencialmente (sin ThreadPoolExecutor para evitar race conditions)
                    batch_results = [process_row(row) for row in batch]
                    all_results.extend(batch_results)

                    if batch_num < len(batches):
                        time.sleep(5) # Pausa entre lotes

                    slack_client.chat_postMessage(
                        channel=channel_id,
                        thread_ts=parent_ts,
                        text=f"✅ *Lote {batch_num}/{len(batches)}* completado"
                    )

                # Generar reporte
                df_report = pd.DataFrame(all_results)
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_report.to_excel(writer, index=False, sheet_name="Resultados")
                output.seek(0)

                filename = f"reporte_masivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                try:
                    slack_client.files_upload_v2(
                        channel=channel_id,
                        thread_ts=parent_ts,
                        file=output,
                        filename=filename,
                        title="📊 Reporte Final"
                    )
                except SlackApiError as e:
                    print(f"❌ Error subiendo reporte: {e.response.get('error')}")

                # Resumen final
                total_ok = sum(1 for r in all_results if "✅" in r["estado"])
                total_error = sum(1 for r in all_results if "❌" in r["estado"])
                total_ya = sum(1 for r in all_results if "⚠️" in r["estado"])

                slack_client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=parent_ts,
                    text=f"🎉 *Proceso Completado*\n• ✅ Exitosos: {total_ok}\n• ❌ Errores: {total_error}\n• ⚠️ Ya inscritos: {total_ya}\n• Total: {len(all_results)}"
                )

            # Lanzar en thread separado para no bloquear respuesta HTTP
            thread = threading.Thread(target=background_process)
            thread.start()

            # Responder inmediatamente a Slack
            return jsonify({"response_action": "clear"}), 200

    # ========== BLOCK ACTIONS (botones / selects dinámicos) ==========
    if tipo == "block_actions":
        actions = data.get("actions") or []
        action_id = actions[0].get("action_id") if actions else None
        view = data.get("view") or {}
        try:
            meta = json.loads(view.get("private_metadata") or "{}")
        except Exception:
            meta = {}

        anchor_email = (meta.get("anchor_email") or "").strip().lower()
        actor_id = meta.get("actor_id") or (data.get("user") or {}).get("id")

        def update_modal_notice(txt: str):
            try:
                original_blocks = view.get("blocks", []) or []
                notice = {"type": "section", "text": {"type": "mrkdwn", "text": txt}}
                slack_client.views_update(
                    view_id=view.get("id"),
                    view={
                        "type": "modal",
                        "callback_id": view.get("callback_id"),
                        "title": view.get("title"),
                        "close": view.get("close"),
                        "submit": view.get("submit"),
                        "private_metadata": view.get("private_metadata"),
                        "blocks": [notice, {"type": "divider"}] + original_blocks
                    }
                )
            except Exception as e:
                print(f"❌ views_update notice: {e}")

        # Botón cambiar contraseña
        if action_id == "apply_password":
            u = get_user_by_email(anchor_email) if anchor_email else None
            
            if not u:
                update_modal_notice(f":warning: Usuario `{anchor_email}` no encontrado.")
                return make_response("", 200)
            
            values = (view.get("state") or {}).get("values") or {}
            new_pass = ""
            try:
                new_pass = values["password_block"]["password_input"].get("value", "").strip()
            except Exception:
                pass
            
            if not new_pass or len(new_pass) < 6:
                update_modal_notice(":warning: La contraseña debe tener al menos 6 caracteres.")
                return make_response("", 200)

            ok = update_user_password(u["id"], new_pass)
            if ok:
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    text=f"🔐 Contraseña actualizada para <mailto:{anchor_email}|{anchor_email}>. Por: <@{actor_id}>"
                )
                update_modal_notice("✅ Contraseña actualizada.")
            else:
                update_modal_notice("❌ No se pudo actualizar la contraseña.")
            return make_response("", 200)

        # Botón eliminar usuario
        if action_id == "delete_user":
            u = get_user_by_email(anchor_email) if anchor_email else None
            
            if not u:
                update_modal_notice(f":warning: Usuario `{anchor_email}` no encontrado.")
                return make_response("", 200)
            
            ok = delete_user_by_id(u["id"])
            if ok:
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    text=f"🗑️ Usuario eliminado: <mailto:{anchor_email}|{anchor_email}>. Por: <@{actor_id}>"
                )
                try:
                    slack_client.views_update(
                        view_id=view.get("id"),
                        view={
                            "type": "modal",
                            "title": {"type": "plain_text", "text": "Resultado"},
                            "close": {"type": "plain_text", "text": "Cerrar"},
                            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": f"✅ Usuario `{anchor_email}` eliminado."}}]
                        }
                    )
                except Exception as e:
                    print(f"❌ views_update delete_user: {e}")
            else:
                update_modal_notice("❌ No se pudo eliminar el usuario.")
            return make_response("", 200)

        # Botón expirar hoy
        if action_id == "expire_today":
            u = get_user_by_email(anchor_email) if anchor_email else None
            
            if not u:
                update_modal_notice(f":warning: Usuario `{anchor_email}` no encontrado.")
                return make_response("", 200)

            values_state = (view.get("state") or {}).get("values") or {}
            selected_options = (values_state.get("remove_block", {})
                                             .get("remove_select", {})
                                             .get("selected_options", [])) or []
            if not selected_options:
                update_modal_notice(":warning: Selecciona programas y vuelve a intentar.")
                return make_response("", 200)

            today = datetime.utcnow().isoformat() + "Z"
            expired = []
            errors = []
            for opt in selected_options:
                try:
                    payload = json.loads(opt.get("value") or "{}")
                except Exception:
                    payload = {}
                enrollment_id = payload.get("enrollment_id")
                course_name = payload.get("course_name") or str(payload.get("course_id") or "")
                if not enrollment_id:
                    errors.append(f"{course_name}: id faltante")
                    continue
                put_url = f"{BASE_URL}/enrollments/{enrollment_id}"
                try:
                    r = requests.put(put_url, headers=HEADERS, json={"expiry_date": today}, timeout=15)
                    print(f"PUT {put_url} (expire) -> {r.status_code}")
                    if r.status_code in (200, 204):
                        expired.append(course_name)
                    else:
                        errors.append(f"{course_name}: {r.status_code}")
                except Exception as e:
                    errors.append(f"{course_name}: {e}")

            msg = []
            if expired:
                msg.append("✅ Expirados hoy: " + ", ".join(expired))
            if errors:
                msg.append("⚠️ Errores: " + "; ".join(errors))
            update_modal_notice("\n".join(msg) if msg else "Sin cambios.")

            if expired:
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    text=f"⏱️ Expirados hoy para <mailto:{anchor_email}|{anchor_email}>: {', '.join(expired)}. Por: <@{actor_id}>"
                )
            return make_response("", 200)

        # Botón cambiar fecha
        if action_id == "change_expiry":
            u = get_user_by_email(anchor_email) if anchor_email else None
            
            if not u:
                update_modal_notice(f":warning: Usuario `{anchor_email}` no encontrado.")
                return make_response("", 200)

            values_state = (view.get("state") or {}).get("values") or {}
            selected_options = (values_state.get("remove_block", {})
                                             .get("remove_select", {})
                                             .get("selected_options", [])) or []
            new_date_str = None
            try:
                new_date_str = values_state["new_expiry_block"]["new_expiry_input"].get("selected_date")
            except Exception:
                pass

            if not selected_options:
                update_modal_notice(":warning: Selecciona programas.")
                return make_response("", 200)
            if not new_date_str:
                update_modal_notice(":warning: Selecciona una nueva fecha de expiración.")
                return make_response("", 200)

            new_date_iso = iso_from_datepicker(new_date_str)
            if not new_date_iso:
                update_modal_notice(":warning: Fecha inválida.")
                return make_response("", 200)

            changed = []
            errors = []
            for opt in selected_options:
                try:
                    payload = json.loads(opt.get("value") or "{}")
                except Exception:
                    payload = {}
                enrollment_id = payload.get("enrollment_id")
                course_name = payload.get("course_name") or str(payload.get("course_id") or "")
                if not enrollment_id:
                    errors.append(f"{course_name}: id faltante")
                    continue
                put_url = f"{BASE_URL}/enrollments/{enrollment_id}"
                try:
                    r = requests.put(put_url, headers=HEADERS, json={"expiry_date": new_date_iso}, timeout=15)
                    print(f"PUT {put_url} (change expiry) -> {r.status_code}")
                    if r.status_code in (200, 204):
                        changed.append(course_name)
                    else:
                        errors.append(f"{course_name}: {r.status_code}")
                except Exception as e:
                    errors.append(f"{course_name}: {e}")

            msg = []
            if changed:
                msg.append(f"✅ Fecha cambiada a {new_date_str}: " + ", ".join(changed))



            if errors:
                msg.append("⚠️ Errores: " + "; ".join(errors))
            update_modal_notice("\n".join(msg) if msg else "Sin cambios.")

            if changed:
                slack_client.chat_postMessage(
                    channel=THINKIFIC_CHANNEL_NAME,
                    text=f"📅 Fecha cambiada a {new_date_str} para <mailto:{anchor_email}|{anchor_email}>: {', '.join(changed)}. Por: <@{actor_id}>"
                )
            return make_response("", 200)

        # Botón crear cuenta desde /acceso
        if action_id == "open_create_user":
            trigger_id = data.get("trigger_id")
            email_prefill = ""
            try:
                vals = (view.get("state") or {}).get("values") or {}
                email_prefill = vals["email_block"]["email_input"].get("value", "").strip().lower()
            except Exception:
                pass

            create_view = {
                "type": "modal",
                "callback_id": "crear_usuario_form",
                "title": {"type": "plain_text", "text": "Crear cuenta Thinkific"},
                "submit": {"type": "plain_text", "text": "Crear"},
                "close": {"type": "plain_text", "text": "Cancelar"},
                "private_metadata": json.dumps({"requester_id": (data.get("user") or {}).get("id")}),
                "blocks": [
                    {"type": "input", "block_id": "c_email_block", "element": {"type": "plain_text_input", "action_id": "c_email_input", "initial_value": email_prefill}, "label": {"type": "plain_text", "text": "Correo"}},
                    {"type": "input", "block_id": "c_first_block", "element": {"type": "plain_text_input", "action_id": "c_first_input"}, "label": {"type": "plain_text", "text": "Nombre"}},
                    {"type": "input", "block_id": "c_last_block", "element": {"type": "plain_text_input", "action_id": "c_last_input"}, "label": {"type": "plain_text", "text": "Apellido"}},
                    {"type": "input", "optional": True, "block_id": "c_tel_block", "element": {"type": "plain_text_input", "action_id": "c_tel_input"}, "label": {"type": "plain_text", "text": "Teléfono personal"}},
                    {"type": "input", "optional": True, "block_id": "c_pais_block", "element": {"type": "plain_text_input", "action_id": "c_pais_input"}, "label": {"type": "plain_text", "text": "País de residencia"}},
                    {"type": "input", "optional": True, "block_id": "c_estado_block", "element": {"type": "plain_text_input", "action_id": "c_estado_input"}, "label": {"type": "plain_text", "text": "Estado/Provincia"}}
                ]
            }
            try:
                slack_client.views_push(trigger_id=trigger_id, view=create_view)
            except SlackApiError as e:
                print(f"❌ views_push crear_usuario_form: {e.response.get('error')}")
            return make_response("", 200)

        # Fallback para acción desconocida
        return make_response("", 200)

    # ========== Otros tipos no manejados ==========
    return make_response("", 200)

# ==========================
# Thinkific helpers extra (password y delete)
# ==========================
def update_user_password(user_id: int, new_password: str) -> bool:
    """Actualiza la contraseña de un usuario en Thinkific."""
    if not user_id or not new_password:
        return False
    
    user_url = f"{BASE_URL}/users/{user_id}"
    try:
        # Obtener usuario completo para extraer IDs de custom fields
        user_resp = requests.get(user_url, headers=HEADERS, timeout=15)
        if user_resp.status_code != 200:
            print(f"❌ No se pudo obtener usuario {user_id}: {user_resp.status_code}")
            return False
        
        user = user_resp.json()
        
        # ========== FIX: Extraer IDs de custom_profile_fields existentes ==========
        existing_custom = user.get("custom_profile_fields", []) or []
        custom_payload = []
        
        for field in existing_custom:
            field_id = field.get("custom_profile_field_definition_id")
            value = field.get("value")
            
            if field_id:
                # Si está vacío, poner "N/A" para pasar validación
                custom_payload.append({
                    "custom_profile_field_definition_id": int(field_id),
                    "value": value if value else "N/A"
                })
        
        # Construir payload
        payload = {
            "password": new_password,
            "first_name": user.get("first_name") or " ",
            "last_name": user.get("last_name") or " "
        }
        
        if custom_payload:
            payload["custom_profile_fields"] = custom_payload
        
        # Actualizar usuario
        r = requests.put(user_url, headers=HEADERS, json=payload, timeout=20)
        print(f"PUT {user_url} (password) -> {r.status_code} | {r.text[:300]}")
        
        return r.status_code in (200, 204)
        
    except Exception as e:
        print(f"❌ Excepción update_user_password: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_user_by_id(user_id: int) -> bool:
    """Elimina un usuario de Thinkific por ID."""
    if not user_id:
        return False
    url = f"{BASE_URL}/users/{user_id}"
    try:
        r = requests.delete(url, headers=HEADERS, timeout=20)
        print(f"DELETE {url} -> {r.status_code} | {r.text[:300]}")
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"❌ Excepción delete_user_by_id: {e}")
        return False

# ===============================================================
# =================== COMANDO /HELP =============================
# ===============================================================
@app.route("/slack/help", methods=["POST"])
def slack_help():
    raw_data = request.get_data(cache=True)
    if not verifier.is_valid_request(raw_data, request.headers):
        return make_response("Firma inválida", 403)

    form = request.form
    channel_id = form.get("channel_id")
    user_id = form.get("user_id")

    if channel_id != THINKIFIC_CHANNEL_ID:
        return make_response("❌ Este comando solo funciona en #thinkific.", 200)

    help_text = """
*📚 Comandos disponibles del Bot Thinkific*

*1. `/acceso`*
• *Qué hace:* Abre un formulario para otorgar acceso individual a uno o varios programas.
• *Cómo usar:* Escribe `/acceso` en el canal.
• *Funciones:*
  - Selecciona múltiples programas y fecha de expiración.
  - Si el usuario no existe, abre un formulario para crear la cuenta con datos personales (nombre, apellido, teléfono, país, estado).
  - Si el usuario existe, asigna los programas directamente.
  - Si incluye programas premium, pide prueba de pago en hilo.

*2. `/fix correo@dominio.com`*
• *Qué hace:* Abre un formulario para editar información de un usuario existente.
• *Cómo usar:* Escribe `/fix correo@usuario.com`
• *Funciones:*
  - Editar nombre, apellido, correo, teléfono, país y estado.
  - *Cambiar contraseña:* Ingresa nueva contraseña y presiona "Cambiar contraseña".
  - *Expirar programas hoy:* Selecciona programas y presiona "Expirar hoy" (pone fecha de expiración al día actual).
  - *Cambiar fecha de expiración:* Selecciona programas, elige nueva fecha y presiona "Cambiar fecha".
  - *Eliminar usuario:* Botón "Eliminar usuario" (acción permanente).

*3. `/courses_info correo@dominio.com`*
• *Qué hace:* Lista todos los programas activos de un usuario.
• *Cómo usar:* Escribe `/courses_info correo@usuario.com`
• *Funciones:*
  - Envía mensaje padre con lista de programas.
  - Cada programa se detalla en un hilo con nombre y fecha de expiración.

*4. `/acceso-masivo`*
• *Qué hace:* Asigna programas a múltiples usuarios desde un archivo Excel/CSV.
• *Cómo usar:* Escribe `/acceso-masivo`
• *Funciones:*
  - *Paso 1:* Selecciona los cursos a asignar.
  - *Paso 2:* Elige fechas de expiración por curso (opcional).
  - Sube archivo Excel/CSV con columnas: `Nombre`, `Apellido(s)`, `Correo`.
  - Procesa inscripciones masivas en paralelo.
  - Genera reporte Excel con resultados (exitosos/fallidos).

*5. `/help`*
• *Qué hace:* Muestra esta ayuda con todos los comandos disponibles.
• *Cómo usar:* Escribe `/help`

---
*Notas importantes:*
• Todos los comandos solo funcionan en el canal #thinkific.
• Los programas premium requieren adjuntar prueba de pago en el hilo.
• Programas premium: Abacus Experience, Abacus Pro, Portfolio Hacking, Day Trading Dynamics, Option Collision, Road to First 10K, Traders Hub, Programa de Preparación.

*¿Dudas?* Etiqueta a Ferdy. 🚀
"""

    try:
        slack_client.chat_postEphemeral(

            channel=channel_id,
            user=user_id,
            text=help_text
        )
        return make_response("", 200)
    except SlackApiError as e:
        print(f"❌ Error enviando /help: {e.response.get('error')}")
        return make_response("Error al enviar ayuda", 500)