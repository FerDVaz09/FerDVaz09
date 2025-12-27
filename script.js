// Mobile menu toggle
const burger = document.querySelector('.burger');
const navRight = document.querySelector('.nav-right');
const navLinks = document.querySelectorAll('.nav-links li');

burger.addEventListener('click', () => {
    navRight.classList.toggle('active');
    
    // Burger animation
    burger.classList.toggle('toggle');
});

// Close mobile menu when clicking on a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navRight.classList.remove('active');
        burger.classList.remove('toggle');
    });
});

// Projects Carousel
const track = document.querySelector('.projects-track');
const cards = Array.from(document.querySelectorAll('.project-card-link'));
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');

let currentIndex = 0;

function getCardsPerView() {
    if (window.innerWidth <= 640) return 1;
    if (window.innerWidth <= 1024) return 2;
    return 3;
}

function clampIndex() {
    const perView = getCardsPerView();
    const maxIndex = Math.max(0, cards.length - perView);
    currentIndex = Math.min(Math.max(currentIndex, 0), maxIndex);
}

function updateCarousel() {
    clampIndex();
    const perView = getCardsPerView();
    const stepPercent = 100 / perView;
    track.style.transform = `translateX(-${currentIndex * stepPercent}%)`;
    
    // Update button states
    const maxIndex = Math.max(0, cards.length - perView);
    prevBtn.style.opacity = currentIndex === 0 ? '0.5' : '1';
    prevBtn.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
    nextBtn.style.opacity = currentIndex >= maxIndex ? '0.5' : '1';
    nextBtn.style.pointerEvents = currentIndex >= maxIndex ? 'none' : 'auto';
}

nextBtn.addEventListener('click', () => {
    currentIndex += getCardsPerView();
    updateCarousel();
});

prevBtn.addEventListener('click', () => {
    currentIndex -= getCardsPerView();
    updateCarousel();
});

window.addEventListener('resize', () => {
    currentIndex = 0;
    updateCarousel();
});

// Initialize carousel
updateCarousel();

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background on scroll
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(10, 10, 10, 0.98)';
        navbar.style.boxShadow = '0 5px 20px rgba(0, 217, 255, 0.1)';
    } else {
        navbar.style.background = 'rgba(10, 10, 10, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Add animation to sections
document.querySelectorAll('section').forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(30px)';
    section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(section);
});

// Project cards hover effect
const projectCards = document.querySelectorAll('.project-card');
projectCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        card.style.setProperty('--mouse-x', `${x}px`);
        card.style.setProperty('--mouse-y', `${y}px`);
    });
});

// Skill items animation on hover
const skillItems = document.querySelectorAll('.skill-item');
skillItems.forEach((item, index) => {
    item.style.animationDelay = `${index * 0.05}s`;
});

// Typing effect for subtitle (optional enhancement)
const subtitle = document.querySelector('.subtitle');
const subtitleText = subtitle.textContent;
subtitle.textContent = '';
let charIndex = 0;

function typeWriter() {
    if (charIndex < subtitleText.length) {
        subtitle.textContent += subtitleText.charAt(charIndex);
        charIndex++;
        setTimeout(typeWriter, 100);
    }
}

// Start typing effect when page loads
window.addEventListener('load', () => {
    setTimeout(typeWriter, 500);
});

// Copy email to clipboard or handle contact actions
const contactItems = document.querySelectorAll('.contact-item');
contactItems.forEach(item => {
    item.addEventListener('click', (e) => {
        const action = item.getAttribute('data-action');
        const value = item.getAttribute('data-value');
        
        if (action === 'email') {
            // Copy email to clipboard
            navigator.clipboard.writeText(value).then(() => {
                showNotification('✓ Email copiado al portapapeles');
            });
        } else if (action === 'email-compose') {
            // Open email compose window
            window.location.href = `mailto:${value}?subject=Consulta sobre Automatización&body=Hola Ferdy,%0D%0A%0D%0AMe gustaría consultar sobre...`;
        } else if (action === 'whatsapp') {
            // Open WhatsApp
            window.open(value, '_blank');
        } else if (action === 'phone') {
            // Open phone dialer
            window.location.href = value;
        } else if (action === 'link') {
            // Open link in new tab
            window.open(value, '_blank');
        }
    });
});

// Notification function
function showNotification(message) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--primary-color);
        color: var(--dark-bg);
        padding: 15px 25px;
        border-radius: 50px;
        font-weight: 600;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Add CSS animation for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const heroContent = document.querySelector('.hero-content');
    if (heroContent) {
        heroContent.style.transform = `translateY(${scrolled * 0.5}px)`;
        heroContent.style.opacity = 1 - scrolled / 600;
    }
});

// Stats counter animation
const stats = document.querySelectorAll('.stat-item h3');
const statsSection = document.querySelector('.stats');

const animateStats = (entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            stats.forEach(stat => {
                const target = parseInt(stat.textContent);
                let count = 0;
                const increment = target / 50;
                
                const updateCount = () => {
                    if (count < target) {
                        count += increment;
                        stat.textContent = Math.ceil(count) + (stat.textContent.includes('+') ? '+' : '%');
                        setTimeout(updateCount, 30);
                    } else {
                        stat.textContent = target + (stat.textContent.includes('+') ? '+' : '%');
                    }
                };
                
                updateCount();
            });
            
            statsObserver.unobserve(entry.target);
        }
    });
};

const statsObserver = new IntersectionObserver(animateStats, observerOptions);
if (statsSection) {
    statsObserver.observe(statsSection);
}

// Easter egg: Konami code
let konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
let konamiIndex = 0;

document.addEventListener('keydown', (e) => {
    if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
            activateEasterEgg();
            konamiIndex = 0;
        }
    } else {
        konamiIndex = 0;
    }
});

function activateEasterEgg() {
    document.body.style.animation = 'rainbow 2s linear infinite';
    setTimeout(() => {
        document.body.style.animation = '';
    }, 5000);
}

const rainbowStyle = document.createElement('style');
rainbowStyle.textContent = `
    @keyframes rainbow {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }
`;
document.head.appendChild(rainbowStyle);

console.log('%c¡Hola Developer! 👋', 'font-size: 20px; font-weight: bold; color: #00d9ff;');
console.log('%c¿Buscando algo interesante? Prueba el Konami Code 🎮', 'font-size: 14px; color: #7b2cbf;');

// Chatbot functionality
const chatbotToggle = document.getElementById('chatbot-toggle');
const chatbotWindow = document.getElementById('chatbot-window');
const chatbotClose = document.getElementById('chatbot-close');
const chatbotReset = document.getElementById('chatbot-reset');
const menuOptions = document.querySelectorAll('.menu-option');
const chatbotResponse = document.getElementById('chatbot-response');
const chatbotMenu = document.querySelector('.chatbot-menu');

const responses = {
    perfil: `
        <p><strong>📄 Perfil Profesional Completo:</strong></p>
        <div style="background: rgba(0, 217, 255, 0.05); padding: 1rem; border-radius: 8px; border-left: 3px solid var(--primary-color); line-height: 1.8;">
            <p><strong>Automation Engineer & QA Tester</strong> con más de 3 años de experiencia en el desarrollo de soluciones automatizadas, aseguramiento de la calidad de software y mejora continua de procesos tecnológicos.</p>
            
            <p>Cuento con un enfoque integral que combina <strong>pensamiento analítico, visión técnica y orientación al negocio</strong>, lo que me permite identificar fallos, optimizar flujos y construir sistemas más eficientes y confiables.</p>
            
            <p>Tengo amplia experiencia en <strong>automatización de procesos operativos y de soporte, integración de APIs, desarrollo de bots y flujos inteligentes</strong>, así como en testing funcional, UAT y validación de sistemas. He trabajado con plataformas como <strong>Slack, WhatsApp (Evolution API), Discord, Telegram y Chatwoot</strong>, implementando soluciones que conectan múltiples servicios, reducen la carga manual y mejoran significativamente los tiempos de respuesta.</p>
            
            <p>A lo largo de mi carrera he liderado iniciativas que lograron <strong>reducir procesos que tomaban horas a ejecuciones de minutos</strong>, automatizar un alto porcentaje de tareas repetitivas y fortalecer la estabilidad de los sistemas mediante pruebas estructuradas, detección temprana de errores y documentación clara.</p>
            
            <p>Me caracterizo por mi capacidad de <strong>traducir necesidades del negocio en soluciones técnicas</strong>, trabajar de forma autónoma y adaptarme rápidamente a nuevos entornos y tecnologías.</p>
            
            <p style="margin-top: 1rem; color: var(--primary-color); font-weight: 600;">Apasionado por la automatización, la calidad y la mejora de la experiencia del usuario, busco seguir creciendo como profesional aportando soluciones escalables, confiables y orientadas a resultados. 🚀</p>
        </div>
    `,
    metodologia: `
        <p><strong>🧪 Mi Metodología QA:</strong></p>
        <p><strong>1. Análisis de Requisitos</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>📋 Revisión detallada de user stories en <strong>Jira</strong></li>
            <li>🎯 Identificación de criterios de aceptación</li>
            <li>❓ Clarificación de casos edge y escenarios negativos</li>
        </ul>
        <p><strong>2. Diseño de Test Cases</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>✍️ Test cases manuales con precondiciones y pasos detallados</li>
            <li>🔄 Test de regresión, smoke testing, UAT</li>
            <li>⚡ Scripts automatizados con <strong>Selenium + Pytest</strong></li>
            <li>🧪 Testing de integración API con <strong>Postman + Newman</strong></li>
        </ul>
        <p><strong>3. Ejecución y Reporte</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>🐞 Documentación de bugs en <strong>Jira</strong> (severidad/prioridad)</li>
            <li>📸 Screenshots + logs + pasos de reproducción detallados</li>
            <li>📊 Métricas: cobertura, pass rate, defect density</li>
            <li>✅ Validación en ambientes VPS (EasyPanel) y hosting (Hostinger)</li>
        </ul>
    `,
    bugs: `
        <p><strong>🐞 Ejemplo Real de Bug Detectado:</strong></p>
        <div style="background: rgba(255, 0, 0, 0.1); padding: 1rem; border-radius: 8px; border-left: 3px solid #e74c3c; margin: 1rem 0;">
            <p><strong>ID:</strong> BUG-2024-0157</p>
            <p><strong>Severidad:</strong> 🔴 CRÍTICA</p>
            <p><strong>Módulo:</strong> Sistema de pagos - Slack App + Thinkific</p>
            <p><strong>Plataforma:</strong> VPS con EasyPanel + Hostinger</p>
        </div>
        <p><strong>📝 Descripción:</strong></p>
        <p>El comando /acceso permite otorgar accesos a cursos sin validar si el usuario ya tiene un acceso activo, causando duplicación de registros en Thinkific y cobros dobles.</p>
        <p><strong>🔄 Pasos de Reproducción:</strong></p>
        <ol style="margin-left: 1.5rem; line-height: 1.8;">
            <li>Ejecutar <code>/acceso</code> en Slack para usuario existente</li>
            <li>Seleccionar curso ya asignado en Thinkific</li>
            <li>Sistema NO valida duplicación (falla en API validation)</li>
            <li>Se crea segundo enrollment → cobro doble detectado en logs</li>
        </ol>
        <p><strong>🛠️ Ambiente de Testing:</strong></p>
        <p>Reproducido en VPS (EasyPanel) + base de datos en Hostinger. Logs capturados con Python logging.</p>
        <p><strong>✅ Solución Implementada:</strong></p>
        <p>Agregué validación previa que verifica enrollments activos antes de crear nuevos accesos. Tiempo de fix: 2 horas. <strong>Impacto: evitó ~$2,400 en cobros erróneos</strong> en el primer mes.</p>
    `,
    proyectos: `
        <p><strong>🚀 Proyectos Testeados y Automatizados:</strong></p>
        <div style="background: rgba(0, 217, 255, 0.05); padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
            <p><strong>📱 Bot de WhatsApp - Evolution API</strong></p>
            <p style="font-size: 0.9rem; color: #999;">Testing de integración Evolution API, manejo de sesiones Redis, validación de persistencia en Supabase. Deploy en VPS con EasyPanel.</p>
        </div>
        <div style="background: rgba(0, 217, 255, 0.05); padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
            <p><strong>💬 Sistema de Tickets Discord + Chatwoot</strong></p>
            <p style="font-size: 0.9rem; color: #999;">Automatización UI con Selenium, validación de hilos Discord, integración con Chatwoot para soporte omnicanal. Testing end-to-end.</p>
        </div>
        <div style="background: rgba(0, 217, 255, 0.05); padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
            <p><strong>🔗 Slack + Thinkific Integration</strong></p>
            <p style="font-size: 0.9rem; color: #999;">Test cases para comandos slash, validación de enrollments, testing de edge cases. API testing con Postman. Hosting en Hostinger.</p>
        </div>
        <div style="background: rgba(0, 217, 255, 0.05); padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
            <p><strong>🎓 Agente IA Soporte Académico</strong></p>
            <p style="font-size: 0.9rem; color: #999;">UAT de flujos N8N, validación de respuestas IA, testing de escalamiento automático. Documentación en Jira.</p>
        </div>
        <p style="margin-top: 1rem;"><strong>🧪 Cobertura promedio:</strong> 85% | <strong>🤖 Automatización:</strong> 80% | <strong>📊 Gestión:</strong> Jira + TestRail</p>
    `,
    herramientas: `
        <p><strong>🛠️ Herramientas QA y Automatización:</strong></p>
        
        <div style="background: rgba(0, 217, 255, 0.08); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 3px solid var(--primary-color);">
            <p><strong>🔌 API Testing & Postman:</strong></p>
            <ul style="margin-left: 1.5rem; line-height: 1.8;">
                <li>📬 <strong>Postman</strong> - Colecciones automatizadas, variables de entorno, tests scripts</li>
                <li>⚡ <strong>Newman</strong> - Ejecución de tests en CLI y CI/CD pipelines</li>
                <li>🔗 <strong>Thunder Client</strong> - Testing integrado en VS Code</li>
                <li>✅ Validación de status codes, headers, JSON responses y schemas</li>
                <li>🔐 Testing de autenticación OAuth 2.0, JWT y API Keys</li>
                <li>📊 Reportes automáticos HTML con métricas de ejecución</li>
            </ul>
        </div>

        <div style="background: rgba(0, 217, 255, 0.08); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 3px solid var(--primary-color);">
            <p><strong>🔧 Web Dev Tools & Debugging:</strong></p>
            <ul style="margin-left: 1.5rem; line-height: 1.8;">
                <li>🌐 <strong>Chrome DevTools</strong> - Network, Console, Elements, Performance</li>
                <li>🦊 <strong>Firefox Developer Tools</strong> - Inspector, Debugger, Storage</li>
                <li>💡 <strong>Lighthouse</strong> - Auditorías de performance, SEO y accesibilidad</li>
                <li>🐞 Debugging avanzado de JavaScript, CSS y requests HTTP</li>
                <li>📡 Análisis de Network waterfall y tiempos de carga</li>
                <li>🎯 Inspección de LocalStorage, Cookies y Session Storage</li>
            </ul>
        </div>

        <div style="background: rgba(0, 217, 255, 0.08); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 3px solid var(--primary-color);">
            <p><strong>🤖 Pruebas Automatizadas:</strong></p>
            <ul style="margin-left: 1.5rem; line-height: 1.8;">
                <li>🐍 <strong>Selenium WebDriver</strong> - Testing end-to-end cross-browser</li>
                <li>🎭 <strong>Playwright</strong> - Automatización moderna para Chrome, Firefox, Safari</li>
                <li>🧪 <strong>Pytest</strong> - Framework de testing con fixtures y parametrización</li>
                <li>📝 <strong>Page Object Model (POM)</strong> - Arquitectura escalable de tests</li>
                <li>⚙️ Scripts de smoke tests, regression y validación de flujos críticos</li>
                <li>🔄 Integración con CI/CD (GitHub Actions, Jenkins)</li>
            </ul>
        </div>

        <div style="background: rgba(0, 217, 255, 0.08); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 3px solid var(--primary-color);">
            <p><strong>📊 Gestión QA & Performance:</strong></p>
            <ul style="margin-left: 1.5rem; line-height: 1.8;">
                <li>📋 <strong>Jira</strong> - Bug tracking, test cases y seguimiento de sprints</li>
                <li>📈 <strong>TestRail</strong> - Gestión de test plans y matriz de trazabilidad</li>
                <li>⚡ <strong>JMeter</strong> - Load testing y stress testing de APIs</li>
                <li>🔄 <strong>N8N</strong> - Workflow automation y testing de integraciones</li>
                <li>📊 <strong>Grafana + Prometheus</strong> - Monitoreo de performance en tiempo real</li>
            </ul>
        </div>

        <p style="margin-top: 1.5rem; padding: 1rem; background: rgba(123, 44, 191, 0.1); border-radius: 8px;">
            <strong>🎯 Metodologías:</strong> Agile/Scrum • Test-Driven Development (TDD) • Behavior-Driven Development (BDD) • Continuous Testing en CI/CD
        </p>
    `,
    experiencia: `
        <p><strong>💼 Experiencia Profesional QA:</strong></p>
        <p><strong>Especialista TI - Abacus Exchange</strong> (Actual)</p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>🧪 Testing de sistemas de pago y transferencias</li>
            <li>🤖 Automatización de procesos (80% eficiencia)</li>
            <li>🐞 Detección proactiva de bugs críticos</li>
        </ul>
        <p><strong>QA & Automation Engineer</strong> (3+ años)</p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>✅ +10 proyectos testeados end-to-end</li>
            <li>🔧 Desarrollo de frameworks de testing custom</li>
            <li>📊 Implementación de CI/CD con Pytest + GitHub Actions</li>
            <li>🧠 Integration testing con APIs REST y WebSockets</li>
        </ul>
        <p><strong>📈 Logros clave:</strong></p>
        <p>• Reducción 60% en bugs de producción<br>• 80% de cobertura automatizada<br>• Ahorro de $5k+ detectando bugs críticos pre-launch</p>
    `,
    contacto: `
        <p><strong>📧 Contáctame:</strong></p>
        <p>📩 Email: <strong>ferdyv59@gmail.com</strong></p>
        <p>📱 Teléfono: <strong>(809) 476-9759</strong></p>
        <p>💼 LinkedIn: <a href="https://linkedin.com/in/ferdy-vasquez-placencia-vasquez-7b0338315" target="_blank" style="color: var(--primary-color);">Ver perfil</a></p>
        <p>💻 GitHub: <a href="https://github.com/FerDVaz09" target="_blank" style="color: var(--primary-color);">@FerDVaz09</a></p>
        <p style="margin-top: 1rem;">¡Puedes usar los botones de contacto arriba para copiar mi email o abrir WhatsApp directamente! 📲</p>
        <p style="margin-top: 1rem; padding: 0.8rem; background: rgba(0, 217, 255, 0.05); border-radius: 8px;">
            <strong>💡 ¿Buscas un QA Engineer o Automation specialist?</strong><br>
            Estoy disponible para proyectos freelance y oportunidades full-time. ¡Hablemos! 🚀
        </p>
    `
};

// Toggle chatbot
chatbotToggle.addEventListener('click', () => {
    chatbotWindow.classList.toggle('active');
});

// Close chatbot
chatbotClose.addEventListener('click', () => {
    chatbotWindow.classList.remove('active');
});

// Reset to menu
chatbotReset.addEventListener('click', () => {
    chatbotResponse.classList.remove('active');
    chatbotResponse.innerHTML = '';
    chatbotMenu.style.display = 'flex';
});

// Handle menu options
menuOptions.forEach(option => {
    option.addEventListener('click', () => {
        const question = option.getAttribute('data-question');
        const answer = responses[question];
        
        // Hide menu and show response
        chatbotMenu.style.display = 'none';
        chatbotResponse.innerHTML = answer;
        chatbotResponse.classList.add('active');
        
        // Scroll to top of response
        chatbotResponse.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
});

// Close chatbot when clicking outside
document.addEventListener('click', (e) => {
    if (!chatbotWindow.contains(e.target) && !chatbotToggle.contains(e.target)) {
        chatbotWindow.classList.remove('active');
    }
});
