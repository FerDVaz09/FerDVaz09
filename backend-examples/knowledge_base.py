"""Memoria de respuestas para Abacus GPT."""
from __future__ import annotations

MEMORY_BLOB = """✅ 1. GUIA OPERATIVA COMPLETA DEL ESTUDIANTE
Apertura de cuenta TradeStation
1. ¿Con cuanto dinero puedo fondear mi cuenta?
- Puedes fondear con cualquier monto.
- Oferta: Si fondeas con $500, recibes $100 extra (20 x 5 meses).

2. ¿Para que sirve el codigo de promocion?
- Sin codigo → $5 por transaccion
- Con codigo → $0 comision acciones / $0.60 opciones

3. ¿Como aplicar el codigo de promocion?
- Si no se aplico: tradestation.com → Chat Online → Cuenta existente → Solicitar aplicar codigo ABCXAFWT.

4. ¿Como sigo mi aplicacion?
- https://getstarted2.tradestation.com/intro (Log In)

5. Reagendar cita o taller
- http://abacusexchange.org/creacion-de-cuenta

6. Acceso al Discord
- https://discord.gg/abacusexchange

7. Fondeo de cuenta
- Tutorial: Como depositar fondos en tu cuenta de inversion

8. Crear cuenta TradeStation
- Tutorial: Como abrir tu cuenta de inversion

9. Cuenta bloqueada
- tradestation.com → Chat Online → Cuenta nueva → Solicitar desbloqueo.

10. Cuentas para menores (18-21 anos)
- Tutorial: Apertura de cuenta para jovenes

11. Formulario DocuSign
- Link: Formulario de registro (DocuSign)

12. Reunion o taller (Zoom)
- Link: Enlace Zoom oficial

13. Recuperar usuario o contrasena
- Chat Online → New Account → Solicitar restablecer.

14. Reinicio Google Authenticator
- Chat Online → New Account → Solicitar reinicio → Escanear nuevo QR.

15. Credenciales olvidadas
- Chat Online → Cuenta nueva → Explicar situacion.

16. Acceso al simulador
- https://sim.webtrading.tradestation.com

17. Dashboard TradeStation
- https://my.tradestation.com/dashboard

18. Tiempo de aprobacion de cuenta
- Entre 1 y 3 dias laborables.

19. Retomar aplicacion
- https://getstarted2.tradestation.com/intro (Log In)

20. Cambiar de Margin a Cash
- Chat Online → Cuenta abierta → Solicitar cambio (24h)

21. Solicitud de correo
- Debe proporcionar el correo con que se registro.

✅ 2. LISTA MAESTRA DE ENLACES OFICIALES
Comunidad y acceso
- Discord Abacus: https://discord.gg/abacusexchange

TradeStation
- Dashboard: https://my.tradestation.com/dashboard
- Simulador: https://sim.webtrading.tradestation.com
- Aumento Nivel de Opciones: https://campus.abacusexchange.org/courses/take/BOOTCAMP/lessons/67383591-solicitar-aumento

Cuentas de jovenes (18-21 anos)
- Formulario Docusign menores: https://powerforms.docusign.net/647dddd7-cf95-4f7e-b8da-d5808bbf7581?env=na1&acct=7397d86f-8ce6-4029-966b-59a9d1a222d7
- Guia apertura menores: https://campus.abacusexchange.org/courses/take/BOOTCAMP/lessons/67383590-apertura-de-cuenta

Fondeo por banco (RD y USA)
- Banco Popular: https://campus.abacusexchange.org/courses/take/BOOTCAMP/pdfs/67594934-transferencia-desde-banco-popular-a-tradestation
- Banreservas: https://campus.abacusexchange.org/courses/take/BOOTCAMP/pdfs/58795335-transferencia-desde-banreservas-a-tradestation-paso-a-paso
- BHD Leon: https://campus.abacusexchange.org/courses/take/BOOTCAMP/pdfs/60960890-transferencia-desde-bhd-a-tradestation-guia-completa
- Guia W-8BEN: https://campus.abacusexchange.org/courses/take/BOOTCAMP/lessons/67383780-como-llenar-correctamente-w8ben
- Reagendar taller/cita: http://abacusexchange.org/creacion-de-cuenta
- Depositos banco USA: https://campus.abacusexchange.org/courses/take/BOOTCAMP/lessons/67383592-como-depositar-fondos-desde-banco-usa

✅ 3. INFORMACION INSTITUCIONAL DE ABACUS EXCHANGE
1. ¿Que es Abacus Exchange?
- Plataforma educativa enfocada en inversiones, trading y gestion financiera.
- Mision: Capacitar para tomar decisiones informadas y lograr independencia financiera.
- Enfoque: Educacion solida, practica y accesible para todos los niveles.

2. Programas de formacion
- Abacus Experience (Principiantes): Estrategias de inversion de valor + day trading, analisis tecnico y value investing, practica en simulador, 100% virtual (opcion presencial 4 semanas: Ma/Ju 8-10pm o Sab 9-12pm), duracion 8 semanas.
- Abacus PRO (Opciones): Trader de opciones avanzado, manejo del riesgo y disciplina, mentoria personalizada, duracion 6-8 semanas.
- Abacus Executive (Value Investing): Inversion a largo plazo, casos practicos, duracion 6 semanas.

3. Modalidad educativa
- 100% virtual: clases grabadas, sesiones en vivo, simuladores y soporte en Discord.

4. Horarios
- Flexibles; sesiones en vivo lunes y martes 11:00 a.m. - 12:00 p.m.

5. Ubicacion fisica
- Santo Domingo, RD. Calle Filomena de Cova, Edif. Corporativo 2015, Suite 906, Piantini. Visitas solo con cita.

6. Flujo con un especialista
- Inscripcion → Acceso a materiales → Sesiones en vivo → Mentoria → Certificacion.

7. ¿Por que elegir Abacus?
- Enfoque practico, mentoria experta, horarios flexibles, cuenta TradeStation sin costo + simulador + 0 comisiones en acciones, comunidad activa, pre-market meetings, conference call del CEO (portafolio 0-1M), podcast Tradetalks.

✅ 4. INFORMACION TECNICA Y ADMINISTRATIVA
1. Cancelar Traders Hub
- El usuario gestiona su suscripcion en https://billing.stripe.com/p/login/eVqdR872EetMf6L9Ok1Fe00

2. Cancelar Market Open
- No es automatico. Solicitar nombre completo, correo y telefono para escalar.

3. Nivel 2 de opciones (TradeStation)
- Demora 2 a 3 dias laborables.

4. Impedimentos graves en cuenta
- El usuario debe llamar a TradeStation al 954-652-7900.

5. Capital no disponible / regla de liquidacion (SEC)
- Acciones: T+1.
- Opciones: T+1.
"""


def build_context(_user_message: str) -> str:
    """Devuelve el contexto completo de memoria para cada consulta."""
    return MEMORY_BLOB
