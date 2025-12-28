# 🔧 Exterminador de Enlaces Rotos

## 📋 Descripción
Herramienta profesional de QA para auditar sitios web y detectar enlaces rotos en segundos. Genera reportes en formato CSV/Excel listos para presentar.

## 🎯 Características
- ✅ Escaneo automático de todos los enlaces de una página
- ✅ Verificación de status codes (200, 404, 500, etc.)
- ✅ User-Agent falso para evitar bloqueos
- ✅ Interfaz colorida (Verde = OK, Rojo = Error)
- ✅ Reporte CSV con enlaces rotos
- ✅ Manejo robusto de errores (timeouts, SSL, conexión)

## 🛠️ Instalación

### 1. Instalar dependencias
```bash
pip install requests beautifulsoup4 colorama pandas
```

## 🚀 Uso

### Ejecutar el script
```bash
python broken_link_checker.py
```

### Ejemplo de uso
```
Ingresa la URL del sitio web a auditar: http://the-internet.herokuapp.com/status_codes
```

El script:
1. Extraerá todos los enlaces de la página
2. Verificará cada uno mostrando en tiempo real el estado
3. Generará un archivo `reporte_errores.csv` con los enlaces rotos

## 📊 Salida del reporte
El CSV generado incluye:
- **URL_Origen**: La página auditada
- **Link_Roto**: El enlace que falló
- **Status_Code**: Código de error (404, 500, TIMEOUT, etc.)

## 🧪 Sitios para probar
- http://the-internet.herokuapp.com/status_codes (Tiene errores a propósito)
- https://httpstat.us/ (Para simular diferentes códigos de estado)
- Tu propio sitio web

## 💡 Tips QA
- Úsalo antes de lanzar un sitio a producción
- Corre auditorías periódicas en tus proyectos
- Presenta el CSV a tu equipo/jefe como evidencia de calidad
- Modifica el código para auditar múltiples páginas (crawling)

## 🔮 Mejoras futuras
- [ ] Crawling recursivo (auditar todo el sitio)
- [ ] Interfaz gráfica (GUI)
- [ ] Exportar a Excel con formato
- [ ] Enviar reporte por email automáticamente
- [ ] Agregar análisis de imágenes rotas (src)

## 👨‍💻 Autor
QA Automation Engineer - Portfolio Project

---
**¿Te gustó?** Agrega esto a tu portafolio de GitHub y menciona en entrevistas: *"Tengo un script que audita toda la web en 30 segundos y entrega un Excel con los errores"* 🚀
