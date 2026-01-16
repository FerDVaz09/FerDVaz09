from flask import Flask, render_template, jsonify, request
from datetime import datetime
import os
import random

app = Flask(__name__)

# Nombre del archivo de log
LOG_FILE = 'server.log'

# Asegurar que el archivo de log existe al iniciar
def init_log_file():
    """Crea el archivo de log si no existe"""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] QA Log Sentinel initialized\n")
            print(f"✅ Archivo '{LOG_FILE}' creado exitosamente")
    else:
        print(f"✅ Archivo '{LOG_FILE}' ya existe")

# Función para escribir en el log
def write_log(level, message):
    """Escribe una línea en el archivo de log"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    
    return log_entry

# Función para leer las últimas líneas del log
def read_last_logs(n=15):
    """Lee las últimas N líneas del archivo de log"""
    if not os.path.exists(LOG_FILE):
        return []
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    # Retorna las últimas N líneas (sin el salto de línea)
    return [line.strip() for line in lines[-n:]]

# Ruta principal - Dashboard
@app.route('/')
def index():
    """Renderiza el dashboard principal"""
    return render_template('dashboard.html')

# Ruta para obtener logs (Polling)
@app.route('/get_logs', methods=['GET'])
def get_logs():
    """Devuelve las últimas 15 líneas del log como JSON"""
    logs = read_last_logs(15)
    return jsonify({'logs': logs, 'count': len(logs)})

# Ruta para simular un error crítico
@app.route('/simulate_error', methods=['POST'])
def simulate_error():
    """Genera un error crítico en el log"""
    error_id = random.randint(1000, 9999)
    error_messages = [
        f"Critical Database Connection Failed #DB{error_id}",
        f"Memory Overflow Detected #MEM{error_id}",
        f"API Authentication Failed #AUTH{error_id}",
        f"Disk Space Critical Alert #DISK{error_id}",
        f"Network Timeout Exception #NET{error_id}",
        f"File System Access Denied #FS{error_id}",
        f"SSL Certificate Validation Failed #SSL{error_id}",
        f"Service Unavailable Error #SVC{error_id}"
    ]
    
    message = random.choice(error_messages)
    log_entry = write_log('ERROR', message)
    
    return jsonify({
        'status': 'success',
        'message': 'Error simulado correctamente',
        'log_entry': log_entry.strip()
    })

# Ruta para simular información normal
@app.route('/simulate_info', methods=['POST'])
def simulate_info():
    """Genera un mensaje de información en el log"""
    info_messages = [
        "User login successful",
        "Data backup completed",
        "Cache cleared successfully",
        "Session started for user admin",
        "Configuration reloaded",
        "Health check passed",
        "API request processed successfully",
        "Database sync completed",
        "Email notification sent",
        "Report generated successfully"
    ]
    
    message = random.choice(info_messages)
    log_entry = write_log('INFO', message)
    
    return jsonify({
        'status': 'success',
        'message': 'Información registrada correctamente',
        'log_entry': log_entry.strip()
    })

# Ruta para simular warning
@app.route('/simulate_warning', methods=['POST'])
def simulate_warning():
    """Genera un mensaje de advertencia en el log"""
    warning_messages = [
        "High CPU usage detected (85%)",
        "Low memory available (150MB free)",
        "Slow database query detected (5.2s)",
        "Rate limit approaching threshold",
        "Deprecated API endpoint accessed",
        "Unusual traffic pattern detected",
        "Cache miss rate high (45%)",
        "Response time degradation (2.5s avg)"
    ]
    
    message = random.choice(warning_messages)
    log_entry = write_log('WARNING', message)
    
    return jsonify({
        'status': 'success',
        'message': 'Advertencia registrada correctamente',
        'log_entry': log_entry.strip()
    })

# Ruta para limpiar logs
@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    """Limpia el archivo de logs"""
    try:
        with open(LOG_FILE, 'w') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] [INFO] Logs cleared by user\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Logs limpiados correctamente'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al limpiar logs: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Inicializar el archivo de log
    init_log_file()
    
    # Obtener puerto desde variable de entorno (para Render/Heroku)
    port = int(os.environ.get('PORT', 5000))
    
    # Ejecutar la aplicación
    print("\n" + "="*60)
    print("🛡️  QA LOG SENTINEL - LIVE MONITOR")
    print("="*60)
    print(f"📊 Dashboard disponible en: http://0.0.0.0:{port}")
    print("📝 Archivo de logs: server.log")
    print("⚡ Presiona CTRL+C para detener el servidor")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
