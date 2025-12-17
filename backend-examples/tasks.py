from redis import Redis
from rq import Queue, get_current_job
import time
import json
from concurrent.futures import ThreadPoolExecutor
import os

BATCH_SIZE = 50  # procesar 50 usuarios a la vez
SLEEP_BETWEEN = float(os.getenv("BATCH_SLEEP_SECONDS", "0.5"))  # medio segundo entre batches
MAX_WORKERS = int(os.getenv("BATCH_MAX_WORKERS", "5"))
MAX_RETRIES = int(os.getenv("ENROLL_MAX_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("ENROLL_BACKOFF_FACTOR", "1.5"))

# intentar importar la función real que hace el POST/PUT a Thinkific
try:
    from thinkific_api import enroll_user_and_activate  # nombre esperado en tu proyecto
except Exception as e:
    enroll_user_and_activate = None
    print(f"⚠️ thinkific_api.enroll_user_and_activate no disponible: {e}")

def enroll_user(email, course_id, expiry_date):
    """
    Wrapper hacia la implementación real. Lanza RuntimeError si no está disponible.
    """
    if not enroll_user_and_activate:
        raise RuntimeError("thinkific_api.enroll_user_and_activate no disponible")
    return enroll_user_and_activate(email=email, course_id=course_id, expiry_date=expiry_date)

def enroll_with_retry(email, course_id, expiry_date, max_retries=MAX_RETRIES, backoff=BACKOFF_FACTOR):
    """
    Intenta inscribir un usuario con reintentos exponenciales.
    Retorna dict con keys: success(bool), email, result/error.
    """
    attempt = 0
    while True:
        try:
            result = enroll_user(email, course_id, expiry_date)
            return {"success": True, "email": email, "result": result}
        except Exception as e:
            attempt += 1
            err = str(e)
            if attempt > max_retries:
                return {"success": False, "email": email, "error": err, "attempts": attempt}
            sleep_for = backoff ** attempt
            time.sleep(sleep_for)

def process_batch_enrollments(emails, course_id, expiry_date):
    """Procesa lista grande de emails en batches pequeños"""
    job = get_current_job()
    results = []
    total = len(emails)
    processed = 0

    # Partir en batches de BATCH_SIZE
    for i in range(0, total, BATCH_SIZE):
        batch = emails[i:i + BATCH_SIZE]
        batch_results = process_small_batch(batch, course_id, expiry_date)
        results.extend(batch_results)
        
        processed += len(batch)
        if job:
            job.meta['progress'] = {
                'total': total,
                'processed': processed,
                'current_batch': i // BATCH_SIZE + 1,
                'total_batches': (total + BATCH_SIZE - 1) // BATCH_SIZE
            }
            job.save_meta()
        
        # Dormir entre batches para no sobrecargar API
        time.sleep(SLEEP_BETWEEN)
    
    return results

def process_small_batch(emails, course_id, expiry_date):
    """Procesa batch pequeño con retry y control de errores"""
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for email in emails:
            futures.append(
                executor.submit(enroll_with_retry, email, course_id, expiry_date)
            )
        
        for f in futures:
            try:
                result = f.result(timeout=60)
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e)
                })
    
    return results