from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import os

app = Flask(__name__)

# User-Agent para evitar bloqueos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extraer_enlaces(url):
    """Extrae todos los enlaces de una URL"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        enlaces = []
        
        for tag in soup.find_all('a', href=True):
            enlace = tag['href']
            enlace_completo = urljoin(url, enlace)
            enlaces.append(enlace_completo)
        
        return list(set(enlaces))  # Eliminar duplicados
    except Exception as e:
        return []

def verificar_enlace(url):
    """Verifica si un enlace está roto"""
    try:
        response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        status_code = response.status_code
        
        if status_code >= 400:
            return {'url': url, 'status': status_code, 'estado': 'ROTO'}
        else:
            return {'url': url, 'status': status_code, 'estado': 'OK'}
    except requests.exceptions.Timeout:
        return {'url': url, 'status': 'TIMEOUT', 'estado': 'TIMEOUT'}
    except requests.exceptions.ConnectionError:
        return {'url': url, 'status': 'ERROR', 'estado': 'ERROR'}
    except Exception as e:
        return {'url': url, 'status': 'ERROR', 'estado': 'ERROR'}

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    """Analiza una URL y retorna los enlaces rotos"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'Por favor ingresa una URL válida'}), 400
    
    # Agregar http:// si no tiene protocolo
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Extraer enlaces
        print(f"📊 Analizando: {url}")
        enlaces = extraer_enlaces(url)
        
        if not enlaces:
            return jsonify({
                'error': 'No se pudieron extraer enlaces de esta URL',
                'url_analizada': url
            }), 400
        
        # Verificar enlaces (limitado a 50 para no sobrecargar)
        enlaces_limitados = enlaces[:50]
        resultados = []
        enlaces_rotos = []
        
        for i, enlace in enumerate(enlaces_limitados, 1):
            print(f"Verificando {i}/{len(enlaces_limitados)}: {enlace}")
            resultado = verificar_enlace(enlace)
            resultados.append(resultado)
            
            if resultado['estado'] in ['ROTO', 'TIMEOUT', 'ERROR']:
                enlaces_rotos.append(resultado)
        
        # Estadísticas
        total = len(resultados)
        rotos = len(enlaces_rotos)
        ok = total - rotos
        porcentaje_rotos = (rotos / total * 100) if total > 0 else 0
        
        return jsonify({
            'url_analizada': url,
            'total_enlaces': len(enlaces),
            'enlaces_analizados': total,
            'estadisticas': {
                'total': total,
                'ok': ok,
                'rotos': rotos,
                'porcentaje_rotos': round(porcentaje_rotos, 2)
            },
            'resultados': resultados,
            'enlaces_rotos': enlaces_rotos,
            'nota': f'Se analizaron los primeros {total} enlaces. Total encontrados: {len(enlaces)}'
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': f'Error al analizar la URL: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("🔗 EXTERMINADOR DE ENLACES ROTOS - WEB VERSION")
    print("="*60)
    print(f"📊 Servidor disponible en: http://0.0.0.0:{port}")
    print("⚡ Presiona CTRL+C para detener el servidor")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
