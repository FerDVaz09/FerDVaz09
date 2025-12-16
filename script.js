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
        const slideWidth = slides[0].offsetWidth + 32; // width + gap
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

// Copy email to clipboard
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
    experiencia: `
        <p><strong>💼 Mi Experiencia:</strong></p>
        <p>Tengo más de 3 años de experiencia como QA Testing y Automation Engineer. He trabajado en:</p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>✅ Automatización de procesos (80% de eficiencia)</li>
            <li>✅ Desarrollo de bots y agentes inteligentes</li>
            <li>✅ Integración de APIs y sistemas</li>
            <li>✅ Testing automatizado con Selenium y Pytest</li>
        </ul>
    `,
    proyectos: `
        <p><strong>🚀 Proyectos Destacados:</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>📱 Bot de WhatsApp con IA y persistencia en Supabase</li>
            <li>💬 Sistema de tickets Discord con respuestas automáticas</li>
            <li>🎓 Agente de soporte académico con base de conocimiento</li>
            <li>📊 Asistente de trading en Telegram con journal automático</li>
            <li>🔗 Apps Slack + Thinkific para gestión de cursos</li>
            <li>📅 Agente de citas con Notion y Google Sheets</li>
        </ul>
    `,
    tecnologias: `
        <p><strong>💻 Stack Tecnológico:</strong></p>
        <p><strong>Lenguajes:</strong> Python, JavaScript, SQL</p>
        <p><strong>Backend:</strong> Flask, Evolution API, Redis, Supabase</p>
        <p><strong>Automatización:</strong> N8N, Selenium, Pytest</p>
        <p><strong>APIs:</strong> Slack, Discord, Telegram, WhatsApp, Thinkific</p>
        <p><strong>IA/ML:</strong> OpenAI, LangChain, RAG, Prompt Engineering</p>
        <p><strong>Testing:</strong> Postman, Selenium, Pytest, Automation</p>
    `,
    contacto: `
        <p><strong>📧 Contáctame:</strong></p>
        <p>📩 Email: <strong>ferdypruebass@gmail.com</strong></p>
        <p>📱 Teléfono: <strong>(809) 476-9759</strong></p>
        <p>💼 LinkedIn: <a href="https://linkedin.com/in/ferdy-vasquez-placencia-vasquez-7b0338315" target="_blank" style="color: var(--primary-color);">Ver perfil</a></p>
        <p>💻 GitHub: <a href="https://github.com/FerDVaz09" target="_blank" style="color: var(--primary-color);">@FerDVaz09</a></p>
        <p style="margin-top: 1rem;">¡Puedes usar los botones de contacto arriba para copiar mi email o abrir WhatsApp directamente! 📲</p>
    `,
    disponibilidad: `
        <p><strong>✅ Disponibilidad:</strong></p>
        <p>Actualmente trabajo como <strong>Especialista TI</strong> en Abacus Exchange, pero estoy abierto a nuevas oportunidades freelance y proyectos interesantes.</p>
        <p><strong>Puedo ayudarte con:</strong></p>
        <ul style="margin-left: 1.5rem; line-height: 1.8;">
            <li>🤖 Desarrollo de bots y automatizaciones</li>
            <li>🔗 Integración de APIs y sistemas</li>
            <li>🧪 Testing y QA automation</li>
            <li>🧠 Soluciones con IA y ML</li>
        </ul>
        <p style="margin-top: 1rem;">¡Contáctame y hablemos de tu proyecto! 🚀</p>
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
