// DOM Elements
const langZhBtn = document.getElementById('lang-zh');
const langEnBtn = document.getElementById('lang-en');
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navList = document.querySelector('.nav-list');
const galleryFilters = document.querySelectorAll('.filter-btn');
const galleryItems = document.querySelectorAll('.gallery-item');
const contactForm = document.querySelector('.contact-form form');

// Language switching functionality
function switchLanguage(lang) {
    const zhElements = document.querySelectorAll('.zh-content');
    const enElements = document.querySelectorAll('.en-content');
    
    if (lang === 'zh') {
        zhElements.forEach(el => el.style.display = 'block');
        enElements.forEach(el => el.style.display = 'none');
        langZhBtn.classList.add('active');
        langEnBtn.classList.remove('active');
        document.documentElement.lang = 'zh-HK';
    } else {
        zhElements.forEach(el => el.style.display = 'none');
        enElements.forEach(el => el.style.display = 'block');
        langEnBtn.classList.add('active');
        langZhBtn.classList.remove('active');
        document.documentElement.lang = 'en';
    }
    
    // Save language preference
    localStorage.setItem('preferred-language', lang);
}

// Initialize language based on saved preference or default to Chinese
function initializeLanguage() {
    const savedLang = localStorage.getItem('preferred-language') || 'zh';
    switchLanguage(savedLang);
}

// Navigation functionality
function showSection(targetId) {
    // Hide all sections
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Show target section
    const targetSection = document.getElementById(targetId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update active nav link
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-tab="${targetId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    // Close mobile menu if open
    navList.classList.remove('mobile-open');
    mobileMenuToggle.classList.remove('active');
}

// Gallery filtering functionality
function filterGallery(filter) {
    galleryItems.forEach(item => {
        const category = item.getAttribute('data-category');
        if (filter === 'all' || category === filter) {
            item.style.display = 'block';
            item.style.animation = 'fadeIn 0.5s ease-in-out';
        } else {
            item.style.display = 'none';
        }
    });
    
    // Update active filter button
    galleryFilters.forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeFilter = document.querySelector(`[data-filter="${filter}"]`);
    if (activeFilter) {
        activeFilter.classList.add('active');
    }
}

// Mobile menu toggle
function toggleMobileMenu() {
    navList.classList.toggle('mobile-open');
    mobileMenuToggle.classList.toggle('active');
}

// Smooth scrolling for anchor links
function smoothScroll(target) {
    const element = document.getElementById(target);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Form submission handler
function handleFormSubmission(e) {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // Simple validation
    if (!data.name || !data.email || !data.message) {
        alert('請填寫所有必填欄位 / Please fill in all required fields');
        return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        alert('請輸入有效的電郵地址 / Please enter a valid email address');
        return;
    }
    
    // Simulate form submission
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 發送中... / Sending...';
    submitBtn.disabled = true;
    
    setTimeout(() => {
        alert('訊息已發送！我們會盡快回覆您。\nMessage sent! We will reply to you as soon as possible.');
        e.target.reset();
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }, 2000);
}

// Intersection Observer for animations
function initializeAnimations() {
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
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.feature-card, .event-card, .team-card, .membership-card, .facility-item, .training-class, .contact-item, .links-category');
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Initialize hero buttons functionality
function initializeHeroButtons() {
    const learnMoreBtn = document.querySelector('.btn-primary');
    const joinUsBtn = document.querySelector('.btn-secondary');
    
    if (learnMoreBtn) {
        learnMoreBtn.addEventListener('click', () => {
            showSection('about');
        });
    }
    
    if (joinUsBtn) {
        joinUsBtn.addEventListener('click', () => {
            showSection('membership');
        });
    }
}

// Add CSS for mobile menu
function addMobileMenuStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @media (max-width: 768px) {
            .nav-list {
                position: fixed;
                top: 80px;
                right: -100%;
                width: 80%;
                max-width: 300px;
                height: calc(100vh - 80px);
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(10px);
                flex-direction: column;
                justify-content: flex-start;
                align-items: stretch;
                padding: 2rem 0;
                transition: right 0.3s ease;
                box-shadow: -5px 0 20px rgba(0, 0, 0, 0.1);
                z-index: 998;
            }
            
            .nav-list.mobile-open {
                right: 0;
            }
            
            .nav-list li {
                margin: 0;
                width: 100%;
            }
            
            .nav-link {
                display: block;
                padding: 1rem 2rem;
                color: #333 !important;
                border-radius: 0;
                border-bottom: 1px solid #eee;
            }
            
            .nav-link:hover,
            .nav-link.active {
                background: #007bff;
                color: white !important;
                transform: none;
            }
            
            .mobile-menu-toggle.active span:nth-child(1) {
                transform: rotate(45deg) translate(5px, 5px);
            }
            
            .mobile-menu-toggle.active span:nth-child(2) {
                opacity: 0;
            }
            
            .mobile-menu-toggle.active span:nth-child(3) {
                transform: rotate(-45deg) translate(7px, -6px);
            }
        }
    `;
    document.head.appendChild(style);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize language
    initializeLanguage();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize hero buttons
    initializeHeroButtons();
    
    // Add mobile menu styles
    addMobileMenuStyles();
    
    // Language switching
    langZhBtn.addEventListener('click', () => switchLanguage('zh'));
    langEnBtn.addEventListener('click', () => switchLanguage('en'));
    
    // Navigation
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-tab');
            showSection(targetId);
            
            // Update URL hash
            window.history.pushState(null, null, `#${targetId}`);
        });
    });
    
    // Mobile menu toggle
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Gallery filtering
    galleryFilters.forEach(filter => {
        filter.addEventListener('click', () => {
            const filterValue = filter.getAttribute('data-filter');
            filterGallery(filterValue);
        });
    });
    
    // Contact form submission
    if (contactForm) {
        contactForm.addEventListener('submit', handleFormSubmission);
    }
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', () => {
        const hash = window.location.hash.substring(1);
        if (hash) {
            showSection(hash);
        } else {
            showSection('home');
        }
    });
    
    // Initialize based on URL hash
    const initialHash = window.location.hash.substring(1);
    if (initialHash && document.getElementById(initialHash)) {
        showSection(initialHash);
    } else {
        showSection('home');
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav') && navList.classList.contains('mobile-open')) {
            toggleMobileMenu();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navList.classList.contains('mobile-open')) {
            toggleMobileMenu();
        }
    });
    
    // Add loading class removal after page load
    window.addEventListener('load', () => {
        document.body.classList.remove('loading');
    });
});

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Scroll to top functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add scroll to top button
function addScrollToTopButton() {
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollBtn.className = 'scroll-to-top';
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #007bff;
        color: white;
        border: none;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    `;
    
    scrollBtn.addEventListener('click', scrollToTop);
    document.body.appendChild(scrollBtn);
    
    // Show/hide scroll button based on scroll position
    window.addEventListener('scroll', debounce(() => {
        if (window.pageYOffset > 300) {
            scrollBtn.style.opacity = '1';
            scrollBtn.style.visibility = 'visible';
        } else {
            scrollBtn.style.opacity = '0';
            scrollBtn.style.visibility = 'hidden';
        }
    }, 100));
}

// Initialize scroll to top button
document.addEventListener('DOMContentLoaded', addScrollToTopButton);

// Export functions for potential external use
window.YTMSports = {
    switchLanguage,
    showSection,
    filterGallery,
    scrollToTop
}; 