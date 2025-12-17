# Configuración Web3Forms para Formularios de Contacto

## ⚠️ ACCIÓN REQUERIDA

Para que los formularios funcionen, necesitas obtener una **Access Key** de Web3Forms:

## Pasos:

1. **Ir a Web3Forms**: https://web3forms.com/

2. **Crear cuenta gratis**:
   - Ingresa tu email: **ferdyv59@gmail.com**
   - Confirma tu email
   - Plan gratuito: 250 envíos/mes

3. **Obtener Access Key**:
   - Dashboard → Create New Form
   - Nombre: "Portfolio Contact Forms"
   - Email destino: **ferdyv59@gmail.com**
   - Copiar el **Access Key** (ejemplo: `abc123def-4567-89gh-ijkl-mnopqrstuvwx`)

4. **Reemplazar en el código**:
   Buscar en `projects/whatsapp-bot.html`:
   ```html
   <input type="hidden" name="access_key" value="YOUR_ACCESS_KEY_HERE">
   ```
   
   Reemplazar `YOUR_ACCESS_KEY_HERE` con tu Access Key real.

## Alternativa: FormSubmit.co (sin registro)

Si prefieres no registrarte, puedes usar FormSubmit:

1. Cambiar el action del form:
   ```html
   <form action="https://formsubmit.co/ferdyv59@gmail.com" method="POST">
   ```

2. Eliminar la línea del access_key

3. Primera vez te llegará un email de confirmación

## Características del formulario actual:

✅ Modal con animación suave
✅ Validación de campos requeridos
✅ Feedback visual al enviar
✅ Cierra automáticamente después de enviar
✅ Responsive (móvil y desktop)
✅ Tecla ESC para cerrar
✅ Click fuera del modal para cerrar

## Campos del formulario:

- Nombre (requerido)
- Email (requerido)
- Teléfono (opcional)
- Mensaje (requerido)
- Subject: "Consulta desde Bot WhatsApp - Portfolio"
