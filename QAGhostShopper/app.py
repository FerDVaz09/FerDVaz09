import os
from flask import Flask, render_template, jsonify, request
from bot import run_ghost_shopper_test
from datetime import datetime
import sys
import threading
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import platform

# Forzar flush de stdout para ver logs en tiempo real
sys.stdout = sys.stderr

# Configuración de Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Ruta especial para servir imágenes de evidence
@app.route('/evidence/<filename>')
def serve_evidence(filename):
    """Sirve imágenes desde static/evidence"""
    from flask import send_from_directory
    return send_from_directory(os.path.join('static', 'evidence'), filename)

# Variables globales
test_results = None
test_execution_time = None


@app.route('/', methods=['GET'])
def index():
    """
    Renderiza la página principal con el botón para ejecutar el test.
    """
    return render_template('report.html', 
                         results=test_results,
                         execution_time=test_execution_time,
                         status='ready')


@app.route('/test', methods=['GET'])
def test_auto():
    """
    Ejecuta el test automáticamente (para debugging) en background.
    """
    global test_results, test_execution_time
    
    def run_test_bg():
        try:
            print("\n" + "="*50)
            print("Iniciando ejecución automática del test")
            print("="*50)
            
            start_time = datetime.now()
            test_results = run_ghost_shopper_test('https://www.saucedemo.com')
            end_time = datetime.now()
            
            test_execution_time = str(end_time - start_time)
            
            print("="*50)
            print("✓ Test ejecutado exitosamente")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"[✗] Error: {str(e)}\n")
    
    # Ejecutar en thread separado para no bloquear Flask
    thread = threading.Thread(target=run_test_bg, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Test iniciado en background',
        'status': 'running'
    }), 202


@app.route('/run_test', methods=['POST'])
def run_test():
    """
    Ejecuta el bot de pruebas y retorna los resultados.
    Captura la URL desde el formulario del usuario.
    """
    global test_results, test_execution_time
    
    try:
        # Capturar la URL enviada por el usuario
        target_url = request.form.get('target_url') or 'https://www.saucedemo.com'
        
        print("\n" + "="*50)
        print(f"Iniciando ejecución del test en: {target_url}")
        print("="*50)
        
        start_time = datetime.now()
        test_results = run_ghost_shopper_test(target_url)
        end_time = datetime.now()
        
        test_execution_time = str(end_time - start_time)
        
        print("="*50)
        print("✓ Test ejecutado exitosamente")
        print("="*50 + "\n")
        
        # Validar que los resultados no sean None
        if test_results is None:
            test_results = []
        
        return jsonify({
            'success': True,
            'message': 'Test ejecutado correctamente',
            'results': test_results,
            'execution_time': test_execution_time,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        print(f"\n✗ Error al ejecutar el test: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al ejecutar el test: {str(e)}',
            'error': str(e)
        }), 500


@app.route('/api/results', methods=['GET'])
def get_results():
    """
    Endpoint para obtener los resultados del último test en formato JSON.
    """
    if test_results is None:
        return jsonify({
            'success': False,
            'message': 'No hay resultados disponibles. Ejecuta un test primero.'
        }), 404

    return jsonify({
        'success': True,
        'results': test_results,
        'execution_time': test_execution_time,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado de la aplicación.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'QA Ghost Shopper',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Manejo de rutas no encontradas."""
    return jsonify({
        'error': 'Ruta no encontrada',
        'message': str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejo de errores internos del servidor."""
    return jsonify({
        'error': 'Error interno del servidor',
        'message': str(error)
    }), 500


if __name__ == '__main__':
    # Development mode (no usar en producción - Render usa Gunicorn)
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

if __name__ == '__main__':
    # Para desarrollo local
    app.run(debug=False, host='0.0.0.0', port=5000)

    # Para producción en Render, usar: gunicorn -w 4 -b 0.0.0.0:5000 app:app
