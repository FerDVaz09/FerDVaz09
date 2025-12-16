// Carousel functionality (only if elements exist)
const track = document.querySelector('.carousel-track');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const dotsContainer = document.getElementById('carouselDots');

if (track && prevBtn && nextBtn && dotsContainer) {
    let currentPage = 0;
    const slides = document.querySelectorAll('.carousel-track .project-card-link');
    const slidesPerPage = 3;
    const totalPages = Math.ceil(slides.length / slidesPerPage);

    // Create dots for pages
    for (let i = 0; i < totalPages; i++) {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        if (i === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToPage(i));
        dotsContainer.appendChild(dot);
    }

    const dots = document.querySelectorAll('.dot');

    function updateCarousel() {
        const slideWidth = slides[0].offsetWidth + 24; // width + gap (1.5rem = 24px)
        const offset = currentPage * slidesPerPage * slideWidth;
        track.style.transform = `translateX(-${offset}px)`;
        
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentPage);
        });
    }

    function goToPage(page) {
        currentPage = page;
        updateCarousel();
    }

    function nextPage() {
        currentPage = (currentPage + 1) % totalPages;
        updateCarousel();
    }

    function prevPage() {
        currentPage = (currentPage - 1 + totalPages) % totalPages;
        updateCarousel();
    }

    nextBtn.addEventListener('click', nextPage);
    prevBtn.addEventListener('click', prevPage);

    // Drag functionality - mueve de 3 en 3 con movimiento fluido
    let isDragging = false;
    let startPos = 0;
    let currentTranslate = 0;
    let prevTranslate = 0;

    track.addEventListener('mousedown', dragStart);
    track.addEventListener('mouseup', dragEnd);
    track.addEventListener('mouseleave', dragEnd);
    track.addEventListener('mousemove', drag);

    function dragStart(event) {
        // Solo si es clic izquierdo
        if (event.button !== 0) return;
        
        isDragging = true;
        startPos = event.pageX;
        
        // Guardar la posición actual traducida
        const slideWidth = slides[0].offsetWidth + 24; // 1.5rem = 24px
        prevTranslate = -currentPage * slidesPerPage * slideWidth;
        currentTranslate = prevTranslate;
        
        track.style.cursor = 'grabbing';
        track.style.transition = 'none';
        event.preventDefault();
    }

    function drag(event) {
        if (!isDragging) return;
        
        event.preventDefault();
        const currentPosition = event.pageX;
        const diff = currentPosition - startPos;
        
        // Mover el track mientras arrastra
        currentTranslate = prevTranslate + diff;
        track.style.transform = `translateX(${currentTranslate}px)`;
    }

    function dragEnd(event) {
        if (!isDragging) return;
        
        isDragging = false;
        track.style.cursor = 'grab';
        track.style.transition = 'transform 0.5s ease-in-out';

        const movedBy = currentTranslate - prevTranslate;

        // Si arrastró más de 100px, cambiar página
        if (movedBy < -100 && currentPage < totalPages - 1) {
            // Arrastró a la izquierda -> siguiente página (3 proyectos)
            nextPage();
        } else if (movedBy > 100 && currentPage > 0) {
            // Arrastró a la derecha -> página anterior (3 proyectos)
            prevPage();
        } else {
            // No arrastró suficiente, volver a la página actual
            updateCarousel();
        }
    }

    // Establecer cursor
    track.style.cursor = 'grab';

    // Auto-play carousel
    let autoplayInterval = setInterval(nextPage, 5000);

    // Pause autoplay on hover
    const carouselContainer = document.querySelector('.carousel-container');
    carouselContainer.addEventListener('mouseenter', () => {
        clearInterval(autoplayInterval);
    });

    carouselContainer.addEventListener('mouseleave', () => {
        autoplayInterval = setInterval(nextPage, 5000);
    });

    // Update carousel on window resize
    window.addEventListener('resize', updateCarousel);
}


// Mobile menu toggle
const burger = document.querySelector('.burger');
const nav = document.querySelector('.nav-links');
const navLinks = document.querySelectorAll('.nav-links li');

burger.addEventListener('click', () => {
    nav.classList.toggle('active');
    
    // Burger animation
    burger.classList.toggle('toggle');
});

// Close mobile menu when clicking on a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        nav.classList.remove('active');
        burger.classList.remove('toggle');
    });
});

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
        <p><strong>Testing Automatizado:</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>🐍 <strong>Selenium + Pytest</strong> - UI automation & regression testing</li>
            <li>📬 <strong>Postman + Newman</strong> - API testing & CI/CD integration</li>
            <li>🔄 <strong>N8N</strong> - Workflow automation & monitoring</li>
        </ul>
        <p><strong>Gestión QA & Tracking:</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>📋 <strong>Jira</strong> - Bug tracking, test management & sprint planning</li>
            <li>📊 <strong>TestRail</strong> - Test case documentation & reporting</li>
            <li>🐙 <strong>Git/GitHub</strong> - Version control & code review</li>
        </ul>
        <p><strong>Infraestructura & Deploy:</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>🖥️ <strong>VPS + EasyPanel</strong> - Deployment & environment management</li>
            <li>🌐 <strong>Hostinger</strong> - Web hosting & database management</li>
            <li>⚡ <strong>Redis</strong> - Cache testing & session management</li>
            <li>📊 <strong>Supabase</strong> - Database validation & logs</li>
        </ul>
        <p><strong>Integraciones & APIs:</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>💬 <strong>Evolution API</strong> - WhatsApp automation & testing</li>
            <li>📞 <strong>Chatwoot</strong> - Omnichannel support testing</li>
            <li>🔗 <strong>Slack, Discord, Telegram APIs</strong> - Bot testing & integration</li>
        </ul>
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
