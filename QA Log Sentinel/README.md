# 🛡️ QA Log Sentinel

**Sistema de Monitoreo de Logs en Tiempo Real para QA Testing**

Herramienta profesional de monitoreo visual de logs con interfaz tipo terminal/hacker, diseñada para simular y visualizar eventos del sistema en tiempo real.

## 📋 Descripción

QA Log Sentinel es una aplicación web construida con Flask que permite:
- ✅ Monitoreo en tiempo real de logs del servidor (polling cada 2 segundos)
- 🚨 Simulación de errores críticos con IDs únicos
- ⚠️ Generación de advertencias del sistema
- ✅ Registro de información de tráfico normal
- 📊 Estadísticas visuales de tipos de logs
- 🎨 Interfaz tipo terminal con estética Matrix/Hacker
- 🗑️ Limpieza de logs con confirmación

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.8+ con Flask
- **Frontend:** HTML5, CSS3, JavaScript Vanilla
- **Diseño:** Tema Matrix/Terminal (Negro + Verde Fosforescente)
- **Comunicación:** Fetch API (Polling cada 2 segundos)

## 🚀 Instalación y Uso

### 1. Clona el repositorio
```bash
git clone https://github.com/FerDVaz09/QA-Log-Sentinel.git
cd QA-Log-Sentinel
```

### 2. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecuta la aplicación
```bash
python app.py
```

### 4. Abre el navegador
Visita: `http://localhost:5000`

## 📊 Características Principales

### Monitoreo en Tiempo Real
- **Polling automático:** La aplicación consulta el servidor cada 2 segundos para obtener las últimas 15 líneas del log
- **Auto-scroll:** El contenedor de logs se desplaza automáticamente al final cuando llegan nuevos mensajes
- **Colores diferenciados:**
  - 🔴 **[ERROR]** - Rojo brillante con efecto glow
  - 🟠 **[WARNING]** - Naranja con efecto glow
  - 🔵 **[INFO]** - Cyan con efecto glow

### Panel de Control
- **Generar Tráfico:** Simula mensajes INFO normales (login, backups, etc.)
- **Simular Fallo Crítico:** Genera errores críticos con IDs aleatorios
- **Generar Advertencia:** Crea advertencias del sistema (CPU alto, memoria baja, etc.)
- **Limpiar Logs:** Elimina todos los logs con confirmación del usuario

### Estadísticas en Tiempo Real
- **Total Logs:** Contador de todas las entradas
- **Critical Errors:** Número de errores en pantalla
- **Warnings:** Cantidad de advertencias
- **Info Messages:** Mensajes informativos

## 💻 Estructura del Proyecto

```
qa_sentinel/
│
├── app.py                  # Servidor Flask con rutas y lógica
├── server.log              # Archivo de logs (se crea automáticamente)
├── requirements.txt        # Dependencias de Python
├── README.md              # Documentación
│
└── templates/
    └── dashboard.html      # Interfaz del dashboard con CSS/JS
```

## 🎨 Interfaz Visual

### Tema Matrix/Terminal
- **Fondo:** Negro absoluto (#000)
- **Texto principal:** Verde fosforescente (#0f0)
- **Efectos especiales:**
  - Scanlines tipo CRT
  - Efecto de flicker
  - Glow animado en títulos
  - Scrollbar personalizada
  - Notificaciones con animación

### Responsive Design
- Adaptable a diferentes tamaños de pantalla
- Grid flexible para estadísticas y botones
- Scrollbar personalizado en área de logs

## 🔧 API Endpoints

### `GET /`
Renderiza el dashboard principal

### `GET /get_logs`
Devuelve las últimas 15 líneas del log como JSON
```json
{
  "logs": ["[2025-12-28 10:30:15] [INFO] User login successful"],
  "count": 1
}
```

### `POST /simulate_error`
Genera un error crítico en el log
```json
{
  "status": "success",
  "message": "Error simulado correctamente",
  "log_entry": "[2025-12-28 10:30:15] [ERROR] Critical Database Connection Failed #DB1234"
}
```

### `POST /simulate_info`
Genera un mensaje INFO en el log

### `POST /simulate_warning`
Genera una advertencia en el log

### `POST /clear_logs`
Limpia el archivo de logs

## 📈 Casos de Uso en QA

1. **Simulación de Escenarios:** Genera diferentes tipos de eventos para probar dashboards de monitoreo
2. **Testing de Logs:** Valida que los sistemas de logging funcionen correctamente
3. **Demostración Visual:** Muestra en tiempo real cómo se manejan los logs en producción
4. **Entrenamiento:** Herramienta educativa para aprender sobre sistemas de logs
5. **Debugging:** Interfaz visual para analizar patrones de logs

## ⚠️ Notas Importantes

- El archivo `server.log` se crea automáticamente si no existe
- Los logs se acumulan, usa "Limpiar Logs" para resetear
- El polling consume recursos, úsalo en entornos de testing
- Perfecto para demos y presentaciones de QA

## 🎯 Mejoras Futuras

- [ ] Filtros por tipo de log (ERROR/WARNING/INFO)
- [ ] Exportación de logs a CSV
- [ ] Búsqueda en tiempo real
- [ ] WebSockets en lugar de polling
- [ ] Múltiples archivos de log
- [ ] Alertas sonoras para errores críticos

## 👨‍💻 Desarrollado por

**Ferdy Placencia Vásquez**
- Portfolio: [ferdvaz09.github.io](https://ferdvaz09.github.io/FerDVaz09/)
- LinkedIn: [linkedin.com/in/ferdyplacencia](https://linkedin.com/in/ferdyplacencia)

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**¡Disfruta monitoreando logs como un verdadero hacker! 🛡️💚**
