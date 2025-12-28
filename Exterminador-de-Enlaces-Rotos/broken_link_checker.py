"""
Exterminador de Enlaces Rotos
Broken Link Checker - Professional QA Tool
Autor: Senior QA Automation Engineer
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from colorama import init, Fore, Style
from urllib.parse import urljoin, urlparse

# Inicializar colores para la consola
init(autoreset=True)

def verificar_enlaces(url_objetivo):
    print(f"\n{Fore.CYAN}🔍 Iniciando escaneo en: {url_objetivo}...\n")
    
    # 1. Configurar Headers para parecer un navegador real (y no un bot)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 2. Obtener el HTML de la página principal
        response = requests.get(url_objetivo, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"{Fore.RED}❌ Error crítico: No se pudo acceder a la web. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        etiquetas_a = soup.find_all('a')
        
        print(f"{Fore.YELLOW}📦 Se encontraron {len(etiquetas_a)} enlaces. Verificando uno por uno...\n")

        enlaces_rotos = []

        # 3. Bucle para verificar cada enlace
        for etiqueta in etiquetas_a:
            link = etiqueta.get('href')
            
            # Filtrar enlaces vacíos o anclas internas (#)
            if not link or link.startswith('#') or link.startswith('javascript:'):
                continue

            # Convertir enlaces relativos (/contacto) a absolutos (https://miweb.com/contacto)
            link_completo = urljoin(url_objetivo, link)

            try:
                # Hacemos la petición al enlace
                r = requests.get(link_completo, headers=headers, timeout=5)
                
                # 4. Evaluación del Status Code
                if r.status_code == 200:
                    print(f"{Fore.GREEN}✅ [200 OK] {link_completo}")
                elif r.status_code == 404:
                    print(f"{Fore.RED}❌ [404 NOT FOUND] {link_completo}")
                    enlaces_rotos.append({'URL_Origen': url_objetivo, 'Link_Roto': link_completo, 'Error': '404 Not Found'})
                else:
                    print(f"{Fore.RED}⚠️ [{r.status_code}] {link_completo}")
                    enlaces_rotos.append({'URL_Origen': url_objetivo, 'Link_Roto': link_completo, 'Error': f'Status {r.status_code}'})

            except requests.exceptions.RequestException as e:
                print(f"{Fore.RED}💀 [ERROR CONEXIÓN] {link_completo}")
                enlaces_rotos.append({'URL_Origen': url_objetivo, 'Link_Roto': link_completo, 'Error': 'Fallo de Conexión'})

        # 5. Generar Reporte
        if enlaces_rotos:
            print(f"\n{Fore.RED}🚨 Se detectaron {len(enlaces_rotos)} enlaces rotos.")
            df = pd.DataFrame(enlaces_rotos)
            df.to_csv('reporte_errores_qa.csv', index=False)
            print(f"{Fore.WHITE}📄 Reporte guardado como: 'reporte_errores_qa.csv'")
        else:
            print(f"\n{Fore.GREEN}✨ ¡Felicidades! No se encontraron enlaces rotos.")

    except Exception as e:
        print(f"Error general: {e}")

# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    url_input = input("Introduce la URL a auditar (ej: https://the-internet.herokuapp.com): ")
    verificar_enlaces(url_input)
