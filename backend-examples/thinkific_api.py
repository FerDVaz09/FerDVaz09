import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

THINKIFIC_API_KEY = os.getenv("THINKIFIC_API_KEY")
THINKIFIC_SUBDOMAIN = os.getenv("THINKIFIC_SUBDOMAIN", "axcampus")
BASE_URL = "https://api.thinkific.com/api/public/v1"

HEADERS = {
    "X-Auth-API-Key": THINKIFIC_API_KEY,
    "X-Auth-Subdomain": THINKIFIC_SUBDOMAIN,
    "Content-Type": "application/json",
}

def _norm(s):
    """Normaliza strings para comparación (lowercase, sin espacios extra)"""
    if not s:
        return ""
    return " ".join(str(s).lower().strip().split())

def safe_name(name):
    """Retorna nombre seguro (no vacío)"""
    if not name or not str(name).strip():
        return " "
    return str(name).strip()

# -------------------------
# Función de prueba de endpoints
# -------------------------
def test_endpoints():
    """Prueba diferentes endpoints para encontrar custom fields"""
    endpoints = [
        "/custom_profile_field_definitions",
        "/custom_fields",
        "/profile_fields",
        "/users/225684329"  # Obtener desde un usuario existente
    ]

    for endpoint in endpoints:
        url = BASE_URL + endpoint
        print(f"\n🔍 Probando: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"✅ Respuesta exitosa:")
                
                # Si es un usuario, mostrar custom_profile_fields
                if "custom_profile_fields" in data:
                    for field in data["custom_profile_fields"]:
                        print(f"  • {field.get('label')}: ID={field.get('custom_profile_field_definition_id')}, Value={field.get('value')}")
                else:
                    print(data)
        except Exception as e:
            print(f"❌ Error: {e}")

# -------------------------
# Funciones principales
# -------------------------
def get_user_by_email(email, max_retries=3):
    """Obtiene usuario por email con retry ante 429"""
    if not email:
        return None
    
    email = str(email).strip().lower()
    url = f"{BASE_URL}/users?page=1&limit=25&query[email]={email}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 429:
                wait = min((2 ** attempt) * 3, 30)  # 3s, 6s, 12s (max 30s)
                print(f"⏳ Rate limit get_user (intento {attempt+1}/{max_retries}). Esperando {wait}s...")
                time.sleep(wait)
                continue
            
            if response.status_code != 200:
                print(f"❌ Error al obtener usuario: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            users = data.get("items", [])
            
            if users:
                return users[0]
            else:
                print(f"❌ Usuario con correo '{email}' no encontrado.")
                return None
                
        except Exception as e:
            print(f"❌ Excepción en get_user_by_email (intento {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
    
    print(f"❌ No se pudo obtener usuario {email} después de {max_retries} intentos")
    return None

def enroll_user(user_id, course_id, expiry_date=None, max_retries=3):
    """Inscribe a un usuario en un curso con retry ante 429"""
    if not user_id or not course_id:
        print(f"❌ Error: Faltan datos requeridos - user_id: {user_id}, course_id: {course_id}")
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
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            print(f"POST {url} -> Status: {response.status_code} Response: {response.text}")
            
            if response.status_code == 429:
                wait = (2 ** attempt) * 2  # 2s, 4s, 8s
                print(f"⏳ Rate limit enroll. Esperando {wait}s...")
                time.sleep(wait)
                continue
            
            if response.status_code == 201:
                enrollment = response.json()
                enrollment_id = enrollment["id"]

                # Activar inscripción con la fecha actual
                activated_at = datetime.utcnow().isoformat() + "Z"
                put_url = f"{BASE_URL}/enrollments/{enrollment_id}"
                put_data = {"activated_at": activated_at}
                put_response = requests.put(put_url, headers=HEADERS, json=put_data, timeout=15)
                print(f"PUT {put_url} -> Status: {put_response.status_code} Response: {put_response.text}")

                return put_response.status_code == 204
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error al realizar la inscripción (intento {attempt+1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    return False

def get_enrollments(user_id, max_retries=3):
    """Obtiene TODAS las inscripciones de un usuario con paginación y retry ante 429"""
    url_base = f"{BASE_URL}/enrollments?query[user_id]={user_id}"
    all_enrollments = []
    page = 1
    
    while True:
        url = f"{url_base}&page={page}&limit=200"
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                print(f"GET {url} -> Status: {response.status_code}")
                
                if response.status_code == 429:
                    wait = min((2 ** attempt) * 2, 30)
                    print(f"⏳ Rate limit get_enrollments (intento {attempt+1}/{max_retries}). Esperando {wait}s...")
                    time.sleep(wait)
                    continue
                
                if response.status_code != 200:
                    print(f"❌ Error obteniendo enrollments: {response.status_code} - {response.text}")
                    return all_enrollments  # Retornar lo que se tiene hasta ahora
                
                data = response.json()
                batch = data.get("items", [])
                all_enrollments.extend(batch)
                
                print(f"✅ Página {page}: {len(batch)} enrollments obtenidos")
                
                # Si hay menos de 200, ya no hay más páginas
                if len(batch) < 200:
                    print(f"✅ Total enrollments obtenidos: {len(all_enrollments)}")
                    return all_enrollments
                
                page += 1
                break  # Salir del loop de reintentos
                
            except Exception as e:
                print(f"❌ Excepción obteniendo enrollments (página {page}, intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return all_enrollments
        
        # Si agotó reintentos, salir del loop de páginas
        if attempt >= max_retries - 1:
            break
    
    print(f"✅ Total enrollments obtenidos: {len(all_enrollments)}")
    return all_enrollments

def get_custom_field_definition_map():
    """Devuelve map normalizado name -> id de custom_profile_fields"""
    candidates = [
        f"{BASE_URL}/custom_profile_field_definitions?limit=200",
        f"{BASE_URL}/custom_profile_fields?limit=200",
        f"{BASE_URL}/custom_profile_field_definitions",
        f"{BASE_URL}/custom_profile_fields"
    ]
    for url in candidates:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"GET {url} -> Status: {r.status_code}")
            if r.status_code != 200:
                print(f"❌ No pude leer definiciones desde {url}: {r.status_code} {r.text[:1000]}")
                continue
            data = r.json() or {}
            items = data.get("items") if isinstance(data, dict) else data
            if items is None:
                if isinstance(data, list):
                    items = data
                else:
                    items = []
            out = {}
            for it in items:
                raw_name = (it.get("name") or it.get("label") or it.get("title") or "").strip()
                fid = it.get("id") or it.get("custom_profile_field_definition_id")
                if raw_name and fid:
                    out[_norm(raw_name)] = fid
            if out:
                print(f"🔎 Custom fields disponibles (normalizados): {list(out.keys())}")
                return out
            else:
                print(f"❌ No se encontraron definiciones útiles en {url}.")
        except Exception as e:
            print(f"❌ Excepción leyendo definiciones desde {url}: {e}")
            continue
    print("❌ No pude obtener definiciones de custom_profile_fields desde la API de Thinkific.")
    return {}

def update_user_profile_with_custom_ids(user_id, first_name=None, last_name=None, email=None, tel=None, pais=None, estado=None):
    """
    Actualiza el usuario (PUT /users/{id}) enviando custom_profile_fields con
    custom_profile_field_definition_id. Devuelve True si OK.
    """
    if not user_id:
        print("❌ update_user_profile_with_custom_ids: falta user_id")
        return False

    url = f"{BASE_URL}/users/{user_id}"
    payload = {}
    if first_name is not None:
        payload["first_name"] = safe_name(first_name)
    if last_name is not None:
        payload["last_name"] = safe_name(last_name)
    if email is not None:
        payload["email"] = email

    defs = get_custom_field_definition_map() or {}
    custom_fields = []
    if tel and defs.get(_norm("Telefono Personal")):
        custom_fields.append({
            "custom_profile_field_definition_id": defs[_norm("Telefono Personal")],
            "value": tel
        })
    if pais and defs.get(_norm("Pais de Residencia")):
        custom_fields.append({
            "custom_profile_field_definition_id": defs[_norm("Pais de Residencia")],
            "value": pais
        })
    if estado and defs.get(_norm("Estado o Provincia")):
        custom_fields.append({
            "custom_profile_field_definition_id": defs[_norm("Estado o Provincia")],
            "value": estado
        })

    if custom_fields:
        payload["custom_profile_fields"] = custom_fields

    try:
        print(f"➡️ PUT {url} payload: {payload}")
        r = requests.put(url, headers=HEADERS, json=payload, timeout=30)
        print(f"PUT {url} -> {r.status_code} | {r.text}")
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"❌ Excepción actualizando usuario {user_id}: {e}")
        return False

def create_user_if_not_exists(email, first_name, last_name, tel=None, pais=None, estado=None, max_retries=3):
    """
    Crea el usuario en Thinkific si no existe con retry ante 429.
    """
    email = str(email).strip().lower()

    existing_user = get_user_by_email(email)
    if existing_user:
        print(f"✅ Usuario {email} ya existe con ID {existing_user.get('id')}")
        return existing_user

    url = f"{BASE_URL}/users"

    payload_base = {
        "email": email,
        "first_name": safe_name(first_name),
        "last_name": safe_name(last_name),
        "send_welcome_email": False
    }

    # Valores por defecto si no se proporcionan
    tel = tel or "+1-000-000-0000"
    pais = pais or "Dominican Republic"
    estado = estado or "Santo Domingo"

    payload_with_top = dict(payload_base)
    payload_with_top.update({
        "phone_number": tel,
        "country": pais,
        "province": estado
    })

    def do_post(p, attempt=0):
        try:
            r = requests.post(url, headers=HEADERS, json=p, timeout=30)
            print(f"POST {url} -> {r.status_code} | {r.text[:500]}")
            
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = (2 ** attempt) * 3
                print(f"⏳ Rate limit create_user. Esperando {wait}s...")
                time.sleep(wait)
                return do_post(p, attempt + 1)
            
            return r
        except Exception as e:
            print(f"❌ Excepción POST {url}: {e}")
            return None

    # 1) intento simple
    r = do_post(payload_base)
    if r and r.status_code in (200, 201):
        return r.json()

    # 2) intento con campos top-level
    r = do_post(payload_with_top)
    if r and r.status_code in (200, 201):
        return r.json()

    # Si recibimos 422 -> crear con skip y luego PUT
    if r and r.status_code == 422:
        try:
            err = r.json().get("errors", {})
        except Exception:
            err = {}
        keys = { _norm(k) for k in (err.keys() if isinstance(err, dict) else []) }
        needed = {"telefono personal", "pais de residencia", "estado o provincia"}
        if needed.intersection(keys):
            print("🔁 Thinkific exige custom fields -> crear con skip_custom_fields_validation y luego actualizar via PUT")
            payload_skip = dict(payload_with_top)
            payload_skip["skip_custom_fields_validation"] = True
            payload_skip["send_welcome_email"] = False
            rskip = do_post(payload_skip)
            if rskip and rskip.status_code in (200, 201):
                created = rskip.json()
                user_id = created.get("id")
                if user_id:
                    ok = update_user_profile_with_custom_ids(
                        user_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        tel=tel,
                        pais=pais,
                        estado=estado
                    )
                    if ok:
                        user = get_user_by_email(email)
                        if user:
                            return user
                        return created
                    else:
                        print("❌ Falló actualización custom fields después de crear con skip_custom_fields_validation.")
                        return created

    # Reintentar buscar usuario por si se creó en background
    time.sleep(1)
    user = get_user_by_email(email)
    if user:
        return user

    print(f"❌ No se pudo crear usuario {email}")
    return None

# -------------------------
# Ejecutar prueba si se corre directamente
# -------------------------
if __name__ == "__main__":
    print("🧪 Ejecutando prueba de endpoints...")
    test_endpoints()