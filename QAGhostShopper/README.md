# QA Ghost Shopper - Automatización E2E en Render.com

Proyecto de automatización de pruebas end-to-end para validar el flujo de compra en SauceDemo usando Selenium WebDriver, Flask y Gunicorn, desplegado en Render.com.

## 🚀 Características

- ✅ Automatización completa del flujo de compra (Login → Carrito → Checkout → Confirmación)
- 📸 Captura de pantallas en cada paso para evidencia
- 🌐 Interfaz web moderna y responsiva con Flask
- 🐳 Optimizado para Linux/Render.com (Chrome headless)
- 📊 Reporte interactivo con galerías de imágenes y zoom
- 🔧 Configuración de Gunicorn para producción

## 📋 Requisitos

- Python 3.10+
- Chrome/Chromium (se instala automáticamente en Render)
- pip

## 📦 Instalación Local

```bash
# Clonar o descargar el proyecto
cd QA-Ghost-Shopper

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## ▶️ Ejecución

### Local (Desarrollo)
```bash
python app.py
```
Luego visita: `http://localhost:5000`

### Producción (Render.com)
El despliegue se ejecuta automáticamente usando:
- `render.yaml` - Configuración de despliegue
- `render-build.sh` - Script de instalación de Chrome y dependencias
- `gunicorn` - Servidor WSGI de producción

## 📁 Estructura del Proyecto

```
QA-Ghost-Shopper/
├── app.py                 # Servidor Flask
├── bot.py                 # Lógica de Selenium
├── requirements.txt       # Dependencias Python
├── render.yaml           # Configuración Render
├── render-build.sh       # Script de instalación
├── .gitignore           # Archivos a ignorar
├── templates/
│   └── report.html      # Template HTML con interfaz
├── static/
│   └── evidence/        # Screenshots (generados)
└── README.md            # Este archivo
```

## 🔌 Endpoints de la API

### GET `/`
Página principal con botón para ejecutar el test.

### POST `/run_test`
Ejecuta el bot de pruebas y retorna los resultados en JSON.

**Response:**
```json
{
  "success": true,
  "message": "Test ejecutado correctamente",
  "results": [
    {
      "step": 1,
      "descripcion": "Acceso a SauceDemo",
      "imagen": "evidence/01_inicio_sitio_20260101_120000.png",
      "estado": "✓ Completado"
    }
  ],
  "execution_time": "0:05:30.123456",
  "timestamp": "2026-01-01T12:00:30.123456"
}
```

### GET `/api/results`
Obtiene los resultados del último test ejecutado.

### GET `/health`
Verificación de estado de la aplicación.

## 🔧 Flujo de Automatización

1. **Navegación** → Accede a https://www.saucedemo.com
2. **Login** → standard_user / secret_sauce
3. **Agregar Producto** → Sauce Labs Backpack al carrito
4. **Ver Carrito** → Verifica productos agregados
5. **Checkout** → Inicia proceso de pago
6. **Información** → Completa datos de envío
7. **Resumen** → Revisa orden
8. **Confirmación** → Finaliza compra

Cada paso genera una captura de pantalla para validación visual.

## 🎨 Características de la Interfaz

- Diseño moderno con gradientes
- Tabla responsiva con resultados
- Galería de imágenes con zoom
- Modal para ver imágenes en grande
- Indicadores de progreso y estado
- Compatible con dispositivos móviles

## 🚢 Despliegue en Render.com

1. Conecta tu repositorio GitHub
2. Crea un nuevo Web Service
3. Selecciona Python como entorno
4. Asegúrate de que `render.yaml` esté en la raíz
5. Render detectará automáticamente la configuración y desplegará

### Variables de Entorno (Opcional)

```
FLASK_ENV=production
PYTHON_VERSION=3.10.0
```

## 📝 Notas Importantes

- Chrome se instala automáticamente en Render mediante `render-build.sh`
- El bot corre en modo `--headless` (sin interfaz gráfica)
- Las imágenes se guardan en `static/evidence/`
- El servidor escucha en puerto `5000` (Render asigna el puerto dinámicamente)
- Timeout de página: 30 segundos
- Esperas implícitas: 10 segundos

## 🐛 Solución de Problemas

### Error: "Chrome no encontrado"
✓ Esto es normal en Render. El script `render-build.sh` lo instala automáticamente.

### Error: "Elemento no encontrado"
- Verifica que SauceDemo esté disponible
- Revisa los timeouts en `bot.py`
- Aumenta las esperas si los servidores están lentos

### Error: "No se puede escribir en static/evidence"
- Verifica permisos de carpetas
- Asegúrate de que `static/evidence` existe

## 📊 Información de Versiones

- Flask: 2.3.3
- Selenium: 4.13.0
- webdriver-manager: 4.0.1
- Gunicorn: 21.2.0
- Python: 3.10.0

## 📄 Licencia

Uso libre para fines educativos y comerciales.

---

**Creado para despliegue en Render.com | 2026**
