import os
import time
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import logging

# Suprimir logs de webdriver-manager y Selenium
logging.getLogger('webdriver_manager').setLevel(logging.ERROR)
logging.getLogger('selenium').setLevel(logging.ERROR)


class QAGhostShopper:
    """
    Automatización de pruebas E2E para el flujo de compra en Sauce Demo.
    Captura evidencia en cada paso del proceso.
    """

    def __init__(self, evidence_path="static/evidence"):
        """Inicializa el bot con configuración de Chrome para producción."""
        self.evidence_path = evidence_path
        self.driver = None
        self.results = []
        self.step_count = 0

        # Crear directorio de evidencia si no existe
        if not os.path.exists(self.evidence_path):
            os.makedirs(self.evidence_path, exist_ok=True)

    def click_with_retry(self, locator, desc="", attempts=3, wait_visibility=15, wait_clickable=10):
        """Intenta hacer click con scroll y reintentos para evitar timeouts de Selenium."""
        for i in range(attempts):
            try:
                elem = WebDriverWait(self.driver, wait_visibility).until(
                    EC.presence_of_element_located(locator)
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                WebDriverWait(self.driver, wait_clickable).until(EC.element_to_be_clickable(locator))
                try:
                    elem.click()
                except Exception:
                    # Click alterno por JS si el click normal falla (overlay/focus)
                    self.driver.execute_script("arguments[0].click();", elem)
                return True
            except Exception as e:
                if i == attempts - 1:
                    print(f"[x] Fallo definitivo al clickear {desc}: {e}")
                    raise
                print(f"[!] Reintento {i+1}/{attempts} en {desc}: {e}")
                time.sleep(2)

    def fill_field_with_retry(self, locator, text, desc="campo", attempts=3, wait_visibility=15):
        """Escribe texto en un campo con reintentos para evitar stale/timeout."""
        for i in range(attempts):
            try:
                field = WebDriverWait(self.driver, wait_visibility).until(
                    EC.presence_of_element_located(locator)
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
                field.clear()
                field.send_keys(text)
                return True
            except Exception as e:
                if i == attempts - 1:
                    print(f"[x] Fallo definitivo al llenar {desc}: {e}")
                    raise
                print(f"[!] Reintento {i+1}/{attempts} llenando {desc}: {e}")
                time.sleep(2)

    def setup_chrome_driver(self):
        """
        Configura ChromeDriver inteligentemente según el SO.
        - Windows: Usa Gestor Nativo de Selenium (LIMPIO, sin opciones experimentales)
        - Linux (Render): Usa webdriver-manager + Service (headless + stealth)
        """
        chrome_options = ChromeOptions()
        os_type = platform.system()
        headless_flag = os.getenv("HEADLESS", "true").lower() in ["1", "true", "yes"]
        
        print(f"\n[*] SO detectado: {os_type}")
        
        # --- Opciones BÁSICAS (Seguras para todos) ---
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        
        if os_type == "Linux":
            # ========== RENDER (Linux) - Headless + Stealth ==========
            print("[*] Configurando para RENDER (Linux/Headless)")
            
            # Opciones "Stealth" (SOLO EN LINUX)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            try:
                print("[*] Descargando ChromeDriver con webdriver-manager...")
                driver_path = ChromeDriverManager().install()
                print(f"[+] Driver descargado: {driver_path}")
                
                service = Service(driver_path, verbose=False)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("[+] Chrome iniciado en RENDER (Headless)\n")
                
            except Exception as e:
                print(f"[-] Error en Linux: {e}")
                raise
        
        else:
            # ========== WINDOWS/MAC - Visual + Limpio (SIN opciones experimentales) ==========
            print("[*] Configurando para WINDOWS/MAC (Visual/Nativo)")
            
            # ¡IMPORTANTE! Aquí NO ponemos opciones experimentales ni excludeSwitches
            if headless_flag:
                print("[*] HEADLESS activado (default). Para ver el navegador: set HEADLESS=false")
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--window-size=1920,1080")
            else:
                chrome_options.add_argument("--start-maximized")
            
            try:
                print("[*] Usando Gestor Nativo de Selenium (Selenium Manager)...")
                # Selenium 4.10+ busca tu Chrome automáticamente SIN problemas
                self.driver = webdriver.Chrome(options=chrome_options)
                print("[+] Chrome iniciado en WINDOWS/MAC (Visual)\n")
                
            except Exception as e:
                print(f"[-] Error al iniciar Chrome: {e}")
                raise
        
        # Configurar timeouts globales
        if self.driver:
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)

    def hide_automation_banner(self):
        """Oculta el banner de automatización (opcional)"""
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        except:
            pass

    def take_screenshot(self, step_name):
        """Captura screenshot y guarda en el directorio de evidencia."""
        self.step_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.step_count:02d}_{step_name}_{timestamp}.png"
        filepath = os.path.join(self.evidence_path, filename)

        try:
            self.driver.save_screenshot(filepath)
            # Convertir ruta para que funcione en URL (Windows usa backslashes)
            relative_path = os.path.join("evidence", filename).replace(os.sep, "/")
            print(f"[+] Screenshot guardado: {filename}")
            return relative_path
        except Exception as e:
            print(f"[-] Error al capturar screenshot: {e}")
            return None

    def run(self, base_url="https://www.saucedemo.com"):
        """Ejecuta el flujo completo de la prueba de compra."""
        try:
            self.setup_chrome_driver()
            time.sleep(2)
            
            # Paso 1: Navegación
            print(f"\n[1] Navegando a {base_url}...")
            self.driver.get(base_url)
            time.sleep(3)
            self.hide_automation_banner()
            
            evidence_1 = self.take_screenshot("01_inicio_sitio")
            self.results.append({
                "step": 1,
                "descripcion": "Acceso a SauceDemo",
                "imagen": evidence_1,
                "estado": "[+] Completado"
            })

            # Paso 2: Login
            print("[2] Realizando login...")
            time.sleep(2)
            try:
                # Esperar y obtener el campo username
                username_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "user-name"))
                )
                time.sleep(1)
                username_field.clear()
                username_field.send_keys("standard_user")
                time.sleep(1)
                
                # Llenar contraseña
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys("secret_sauce")
                time.sleep(1)
                
                # Click en login
                login_btn = self.driver.find_element(By.ID, "login-button")
                login_btn.click()
                time.sleep(4)
                
                evidence_2 = self.take_screenshot("02_login_exitoso")
                self.results.append({
                    "step": 2,
                    "descripcion": "Login Exitoso",
                    "imagen": evidence_2,
                    "estado": "[+] Completado"
                })
            except Exception as e:
                print(f"[!] Error en login: {e}")
                raise

            # Paso 3: Agregar al Carrito
            print("[3] Agregando producto...")
            time.sleep(2)
            try:
                add_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "btn_inventory"))
                )
                time.sleep(1)
                add_btn.click()
                time.sleep(2)
                
                evidence_3 = self.take_screenshot("03_producto_agregado")
                self.results.append({
                    "step": 3,
                    "descripcion": "Producto Agregado",
                    "imagen": evidence_3,
                    "estado": "[+] Completado"
                })
            except Exception as e:
                print(f"[!] Error al agregar producto: {e}")
                raise

            # Paso 4: Ir al Carrito
            print("[4] Yendo al carrito...")
            time.sleep(2)
            try:
                cart_link = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "shopping_cart_link"))
                )
                time.sleep(1)
                cart_link.click()
                time.sleep(2)

                # Refuerzo: navegar directo a la URL del carrito para evitar estados raros
                try:
                    self.driver.get(f"{base_url}/cart.html")
                except Exception:
                    pass

                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, "checkout")))
                
                evidence_4 = self.take_screenshot("04_carrito_items")
                self.results.append({
                    "step": 4,
                    "descripcion": "Ver Carrito",
                    "imagen": evidence_4,
                    "estado": "[+] Completado"
                })
            except Exception as e:
                print(f"[!] Error al acceder al carrito: {e}")
                raise

            # Paso 5: Checkout y Información de Envío
            print("[5] Iniciando checkout...")
            time.sleep(3)  # Esperar a que cargue la página del carrito
            try:
                # Confirmar que estamos en la página de carrito
                WebDriverWait(self.driver, 10).until(EC.url_contains("cart"))

                print("[5a] Esperando botón checkout...")
                self.click_with_retry((By.ID, "checkout"), desc="checkout", attempts=3, wait_visibility=15, wait_clickable=10)
                time.sleep(2)

                # Refuerzo: ir directo a checkout-step-one por si el click no navegó
                try:
                    self.driver.get(f"{base_url}/checkout-step-one.html")
                except Exception:
                    pass

                # Esperar a que esté la página de checkout y los campos visibles
                WebDriverWait(self.driver, 15).until(EC.url_contains("checkout-step-one"))
                print("[5b] Esperando formulario de envío...")

                # Captura de evidencia para ver el estado real de la página antes de rellenar
                try:
                    evidence_5a = self.take_screenshot("05a_checkout_before_fill")
                    self.results.append({
                        "step": 5,
                        "descripcion": "Checkout - estado antes de rellenar",
                        "imagen": evidence_5a,
                        "estado": "[+] Captura previa"
                    })
                except Exception as e:
                    print(f"[!] No se pudo tomar captura previa: {e}")
                
                self.fill_field_with_retry((By.ID, "first-name"), "Test", desc="first-name", attempts=3, wait_visibility=20)
                time.sleep(1)
                self.fill_field_with_retry((By.ID, "last-name"), "User", desc="last-name", attempts=3, wait_visibility=15)
                time.sleep(1)
                self.fill_field_with_retry((By.ID, "postal-code"), "12345", desc="postal-code", attempts=3, wait_visibility=15)
                time.sleep(1)
                
                print("[5c] Click en continue...")
                self.click_with_retry((By.ID, "continue"), desc="continue", attempts=3, wait_visibility=10, wait_clickable=10)
                time.sleep(3)

                # Forzar estar en el resumen antes de intentar finish
                try:
                    self.driver.get(f"{base_url}/checkout-step-two.html")
                except Exception:
                    pass
                WebDriverWait(self.driver, 15).until(EC.url_contains("checkout-step-two"))
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, "finish")))
                
                evidence_5 = self.take_screenshot("05_informacion_envio")
                self.results.append({
                    "step": 5,
                    "descripcion": "Información de Envío",
                    "imagen": evidence_5,
                    "estado": "[+] Completado"
                })
            except Exception as e:
                print(f"[!] Error en checkout: {e}")
                raise

            # Paso 6: Finalizar compra
            print("[6] Finalizando orden...")
            time.sleep(3)
            try:
                print("[6a] Esperando botón finish...")
                WebDriverWait(self.driver, 15).until(EC.url_contains("checkout-step-two"))
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, "finish")))
                self.click_with_retry((By.ID, "finish"), desc="finish", attempts=3, wait_visibility=15, wait_clickable=10)
                time.sleep(3)
                
                evidence_6 = self.take_screenshot("06_orden_completada")
                self.results.append({
                    "step": 6,
                    "descripcion": "Orden Completada",
                    "imagen": evidence_6,
                    "estado": "[+] EXITOSO"
                })
            except Exception as e:
                print(f"[!] Error al finalizar: {e}")
                raise
            
            print("\n[✓] Flujo completado exitosamente\n")
            return self.results

        except Exception as e:
            print(f"\n[-] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "step": 99,
                "descripcion": "Error en proceso",
                "imagen": None,
                "estado": f"[-] {str(e)}"
            })
            return self.results
            
        finally:
            print("[*] Cerrando navegador...")
            if self.driver:
                try:
                    self.driver.quit()
                    print("[+] Navegador cerrado")
                except Exception as e:
                    print(f"[-] Error al cerrar: {e}")

def run_ghost_shopper_test(base_url="https://www.saucedemo.com"):
    bot = QAGhostShopper()
    return bot.run(base_url)

if __name__ == "__main__":
    run_ghost_shopper_test()
