/**
 * MuseQuill.ink - JavaScript Functionality
 * Interactive features and dynamic content management
 */

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});

function initializeApp() {
    setupSmoothScrolling();
    setupScrollAnimations();
    startCountdownTimer();
    setupNewsletterForm();
    setupInteractiveEffects();
    setupPerformanceMonitoring();
    setupErrorHandling();
    setupAccessibility();
    trackPageLoad();
}

// ===== SMOOTH SCROLLING =====
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Track navigation
                trackEvent('navigation', {
                    target: this.getAttribute('href'),
                    from: window.location.hash
                });
            }
        });
    });
}

// ===== SCROLL ANIMATIONS =====
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');

                // Track section visibility
                const sectionId = entry.target.id || entry.target.closest('section')?.id;
                if (sectionId) {
                    trackEvent('section_view', { section: sectionId });
                }
            }
        });
    }, observerOptions);

    // Observe all fade-in elements
    document.querySelectorAll('.fade-in-up').forEach(el => {
        observer.observe(el);
    });

    // Observe main sections
    document.querySelectorAll('section[id]').forEach(el => {
        observer.observe(el);
    });
}

// ===== COUNTDOWN TIMER =====
function startCountdownTimer() {
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

function updateCountdown() {
    // Set launch date to September 1, 2025 at midnight UTC
    const launchDate = new Date('2025-09-01T00:00:00Z');
    const now = new Date().getTime();
    const distance = launchDate.getTime() - now;

    if (distance > 0) {
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        updateCountdownDisplay('days', days);
        updateCountdownDisplay('hours', hours);
        updateCountdownDisplay('minutes', minutes);
        updateCountdownDisplay('seconds', seconds);
    } else {
        handleLaunchDay();
    }
}

function updateCountdownDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value.toString().padStart(2, '0');
    }
}

function handleLaunchDay() {
    // Launch day has arrived!
    ['days', 'hours', 'minutes', 'seconds'].forEach(id => {
        updateCountdownDisplay(id, 0);
    });

    const launchHeader = document.querySelector('.coming-soon h2');
    if (launchHeader) {
        launchHeader.textContent = '🎉 We\'re Live!';
    }

    // Track launch day event
    trackEvent('launch_day_reached');

    // Could redirect to the actual app or show a launch message
    // window.location.href = '/app';
}

// ===== NEWSLETTER FORM =====
function setupNewsletterForm() {
    const form = document.getElementById('newsletter-form');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        await handleNewsletterSubmission(this);
    });
}

async function handleNewsletterSubmission(form) {
    const email = form.querySelector('input[type="email"]').value;
    const button = form.querySelector('button');
    const originalText = button.textContent;

    // Validate email
    if (!isValidEmail(email)) {
        showButtonFeedback(button, '❌ Invalid email', 'error', originalText);
        return;
    }

    // Show loading state
    button.textContent = '⏳ Saving...';
    button.disabled = true;

    // Collect signup data
    const signupData = {
        email: email,
        source: 'landing_page',
        campaign: 'early_access_2025',
        referrer: document.referrer,
        user_agent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        utm_source: getUrlParameter('utm_source'),
        utm_medium: getUrlParameter('utm_medium'),
        utm_campaign: getUrlParameter('utm_campaign'),
        utm_content: getUrlParameter('utm_content')
    };

    try {
        const result = await submitToNewsletterService(signupData);

        if (result.success) {
            handleSuccessfulSignup(form, button, originalText, signupData);
        } else {
            throw new Error(result.error || 'Newsletter service unavailable');
        }

    } catch (error) {
        handleFailedSignup(form, button, originalText, signupData, error);
    }
}

async function submitToNewsletterService(signupData) {
    try {
        const response = await fetch('https://musequill.ink/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(signupData)
        });

        if (response.ok) {
            const result = await response.json();
            return {
                success: true,
                data: result
            };
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `Server error: ${response.status}`);
        }

    } catch (error) {
        console.error('Newsletter signup API error:', error);

        // Fallback: Save to localStorage for manual processing
        const savedEmails = JSON.parse(localStorage.getItem('musequill_emails') || '[]');
        const emailData = {
            ...signupData,
            error: error.message,
            saved_at: new Date().toISOString(),
            status: 'api_failed_fallback'
        };
        savedEmails.push(emailData);
        localStorage.setItem('musequill_emails', JSON.stringify(savedEmails));

        return {
            success: false,
            error: error.message,
            fallback_saved: true
        };
    }
}

function handleSuccessfulSignup(form, button, originalText, signupData) {
    showButtonFeedback(button, '✅ Welcome aboard!', 'success', originalText);
    form.reset();

    showNotification('🎉 You\'re on the list! Check your email for exclusive updates.', 'success');

    trackEvent('newsletter_signup', {
        email: signupData.email,
        source: signupData.source,
        campaign: signupData.campaign
    });
}

function handleFailedSignup(form, button, originalText, signupData, error) {
    console.error('Newsletter signup error:', error);

    // Fallback: Save to localStorage for manual processing
    saveToLocalStorage(signupData, error);

    showButtonFeedback(button, '📧 Saved locally!', 'warning', originalText);
    form.reset();

    showNotification('📧 Email saved! We\'ll contact you when we launch.', 'warning');

    trackEvent('newsletter_signup_error', {
        email: signupData.email,
        error: error.message,
        fallback: 'localStorage'
    });
}

function saveToLocalStorage(signupData, error) {
    try {
        const savedEmails = JSON.parse(localStorage.getItem('musequill_emails') || '[]');
        const emailData = {
            ...signupData,
            error: error.message,
            saved_at: new Date().toISOString()
        };
        savedEmails.push(emailData);
        localStorage.setItem('musequill_emails', JSON.stringify(savedEmails));
    } catch (storageError) {
        console.error('Failed to save to localStorage:', storageError);
    }
}

function showButtonFeedback(button, text, type, originalText) {
    button.textContent = text;

    const colors = {
        success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        error: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%)',
        warning: 'linear-gradient(135deg, #ffa726 0%, #ff9800 100%)'
    };

    button.style.background = colors[type] || colors.success;

    setTimeout(() => {
        button.textContent = originalText;
        button.style.background = 'var(--secondary-gradient)';
        button.disabled = false;
    }, 3000);
}

// ===== INTERACTIVE EFFECTS =====
function setupInteractiveEffects() {
    setupClickParticles();
    setupDynamicParticles();
}

function setupClickParticles() {
    document.addEventListener('click', function (e) {
        createClickExplosion(e.clientX, e.clientY);
    });
}

function createClickExplosion(x, y) {
    for (let i = 0; i < 5; i++) {
        const particle = document.createElement('div');
        const randomX = (Math.random() - 0.5) * 200;
        const randomY = (Math.random() - 0.5) * 200;

        particle.style.cssText = `
            position: fixed;
            width: 6px;
            height: 6px;
            background: var(--gold);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            left: ${x}px;
            top: ${y}px;
            animation: explode 1s ease-out forwards;
            --random-x: ${randomX}px;
            --random-y: ${randomY}px;
        `;

        document.body.appendChild(particle);

        setTimeout(() => {
            particle.remove();
        }, 1000);
    }
}

function setupDynamicParticles() {
    // Create additional floating particles periodically
    setInterval(() => {
        if (Math.random() < 0.3) { // 30% chance every interval
            createFloatingParticle();
        }
    }, 2000);
}

function createFloatingParticle() {
    const particle = document.createElement('div');
    const leftPosition = Math.random() * 100;
    const animationDelay = Math.random() * 8;

    particle.className = 'particle';
    particle.style.left = `${leftPosition}%`;
    particle.style.animationDelay = `${animationDelay}s`;

    document.body.appendChild(particle);

    // Remove after animation completes
    setTimeout(() => {
        particle.remove();
    }, 8000 + (animationDelay * 1000));
}

// ===== NOTIFICATION SYSTEM =====
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');

    const colors = {
        success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        warning: 'linear-gradient(135deg, #ffa726 0%, #ff9800 100%)',
        error: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%)',
        info: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    };

    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 300px;
        font-weight: 500;
        animation: slideInRight 0.5s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.5s ease forwards';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);

    // Track notification
    trackEvent('notification_shown', { message, type });
}

// ===== UTILITY FUNCTIONS =====
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

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

// ===== GEOLOCATION TRACKING =====
let geoLocationData = null;

async function getGeolocationData() {
    if (geoLocationData) {
        return geoLocationData;
    }

    try {
        // Try multiple IP geolocation services
        const services = [
            'https://ipapi.co/json/',
            'https://ip-api.com/json/',
            'https://ipinfo.io/json',
            'https://api.ipify.org/?format=json' // Fallback for IP only
        ];

        for (const service of services) {
            try {
                const response = await fetch(service);
                if (response.ok) {
                    const data = await response.json();

                    // Normalize the response format
                    geoLocationData = {
                        ip: data.ip || data.query || 'unknown',
                        country: data.country || data.country_name || data.countryCode || 'unknown',
                        country_code: data.country_code || data.countryCode || data.country || 'unknown',
                        region: data.region || data.regionName || data.region_name || 'unknown',
                        city: data.city || 'unknown',
                        latitude: data.latitude || data.lat || null,
                        longitude: data.longitude || data.lon || null,
                        timezone: data.timezone || data.time_zone || 'unknown',
                        isp: data.isp || data.org || 'unknown',
                        service_used: service
                    };

                    return geoLocationData;
                }
            } catch (error) {
                console.log(`Geolocation service ${service} failed:`, error.message);
                continue;
            }
        }

        // If all services fail, return basic data
        geoLocationData = {
            ip: 'unknown',
            country: 'unknown',
            country_code: 'unknown',
            region: 'unknown',
            city: 'unknown',
            latitude: null,
            longitude: null,
            timezone: 'unknown',
            isp: 'unknown',
            service_used: 'none'
        };

    } catch (error) {
        console.log('Geolocation detection failed:', error);
        geoLocationData = {
            country: 'unknown',
            error: error.message
        };
    }

    return geoLocationData;
}

// ===== ANALYTICS & TRACKING =====
async function trackEventWithGeo(event, data = {}) {
    try {
        // Get geolocation data
        const geoData = await getGeolocationData();

        // Comprehensive event data collection
        const eventData = {
            // Core event data
            event: event,
            data: data,
            timestamp: new Date().toISOString(),

            // Geolocation data
            geo: geoData,

            // Page and navigation data
            page: window.location.href,
            page_title: document.title,
            page_path: window.location.pathname,
            page_search: window.location.search,
            page_hash: window.location.hash,
            referrer: document.referrer,

            // User session data
            session_id: getOrCreateSessionId(),
            user_agent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages,
            platform: navigator.platform,
            cookie_enabled: navigator.cookieEnabled,
            do_not_track: navigator.doNotTrack,

            // Device and display data
            screen_resolution: `${screen.width}x${screen.height}`,
            screen_color_depth: screen.colorDepth,
            screen_pixel_depth: screen.pixelDepth,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            device_pixel_ratio: window.devicePixelRatio,

            // Browser capabilities
            online: navigator.onLine,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezone_offset: new Date().getTimezoneOffset(),

            // Performance data
            page_load_time: performance.now(),
            connection_type: getConnectionInfo(),

            // Scroll and engagement data
            scroll_depth: getCurrentScrollDepth(),
            time_on_page: getTimeOnPage(),

            // UTM and campaign data
            utm_source: getUrlParameter('utm_source'),
            utm_medium: getUrlParameter('utm_medium'),
            utm_campaign: getUrlParameter('utm_campaign'),
            utm_term: getUrlParameter('utm_term'),
            utm_content: getUrlParameter('utm_content'),

            // Additional tracking parameters
            gclid: getUrlParameter('gclid'), // Google Ads
            fbclid: getUrlParameter('fbclid'), // Facebook
            msclkid: getUrlParameter('msclkid'), // Microsoft Ads

            // Page visibility and focus
            page_visible: !document.hidden,
            page_visibility_state: document.visibilityState,
            window_focused: document.hasFocus(),

            // Local storage availability
            local_storage_available: isLocalStorageAvailable(),
            session_storage_available: isSessionStorageAvailable(),

            // Previous page tracking
            previous_page: getPreviousPage(),
            pages_viewed: getPagesViewedInSession(),

            // Feature detection
            touch_support: isTouchDevice(),
            webgl_support: hasWebGLSupport(),
            service_worker_support: 'serviceWorker' in navigator,

            // Custom business metrics
            newsletter_emails_saved: getLocalNewsletterCount(),
            return_visitor: isReturnVisitor(),
            first_visit_timestamp: getFirstVisitTimestamp()
        };

        // Send to analytics service
        fetch('https://musequill.ink/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        }).catch(error => {
            console.log('Analytics service unavailable:', error.message);

            // Fallback: Save to localStorage
            const analytics = JSON.parse(localStorage.getItem('musequill_analytics') || '[]');
            analytics.push(eventData);
            localStorage.setItem('musequill_analytics', JSON.stringify(analytics.slice(-100)));
        });

        // Google Analytics (if available)
        if (typeof gtag !== 'undefined') {
            gtag('event', event, data);
        }

        // Console logging for development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('📊 Event tracked:', event, data);
        }

    } catch (error) {
        console.error('Analytics tracking failed:', error);
    }
}

// Keep the original trackEvent function for backward compatibility
function trackEvent(event, data = {}) {
    // Use the geo-enhanced version
    trackEventWithGeo(event, data);
}

// ===== HELPER FUNCTIONS FOR ENHANCED TRACKING =====
function getConnectionInfo() {
    if ('connection' in navigator) {
        const conn = navigator.connection;
        return {
            effective_type: conn.effectiveType,
            downlink: conn.downlink,
            rtt: conn.rtt,
            save_data: conn.saveData
        };
    }
    return null;
}

function getCurrentScrollDepth() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    return docHeight > 0 ? Math.round((scrollTop / docHeight) * 100) : 0;
}

function getTimeOnPage() {
    const startTime = sessionStorage.getItem('page_start_time');
    if (startTime) {
        return Date.now() - parseInt(startTime);
    }
    return 0;
}

function isLocalStorageAvailable() {
    try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return true;
    } catch (e) {
        return false;
    }
}

function isSessionStorageAvailable() {
    try {
        sessionStorage.setItem('test', 'test');
        sessionStorage.removeItem('test');
        return true;
    } catch (e) {
        return false;
    }
}

function getPreviousPage() {
    return sessionStorage.getItem('previous_page') || null;
}

function setPreviousPage() {
    sessionStorage.setItem('previous_page', window.location.href);
}

function getPagesViewedInSession() {
    const pages = JSON.parse(sessionStorage.getItem('pages_viewed') || '[]');
    return pages.length;
}

function addPageToSession() {
    const pages = JSON.parse(sessionStorage.getItem('pages_viewed') || '[]');
    const currentPage = {
        url: window.location.href,
        timestamp: new Date().toISOString(),
        title: document.title
    };
    pages.push(currentPage);
    sessionStorage.setItem('pages_viewed', JSON.stringify(pages));
}

function isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

function hasWebGLSupport() {
    try {
        const canvas = document.createElement('canvas');
        return !!(window.WebGLRenderingContext && canvas.getContext('webgl'));
    } catch (e) {
        return false;
    }
}

function getLocalNewsletterCount() {
    try {
        const emails = JSON.parse(localStorage.getItem('musequill_emails') || '[]');
        return emails.length;
    } catch (e) {
        return 0;
    }
}

function isReturnVisitor() {
    const firstVisit = localStorage.getItem('musequill_first_visit');
    return !!firstVisit;
}

function getFirstVisitTimestamp() {
    let firstVisit = localStorage.getItem('musequill_first_visit');
    if (!firstVisit) {
        firstVisit = new Date().toISOString();
        localStorage.setItem('musequill_first_visit', firstVisit);
    }
    return firstVisit;
}

function getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('musequill_session_id');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('musequill_session_id', sessionId);
    }
    return sessionId;
}

function initializePageTracking() {
    // Set page start time
    sessionStorage.setItem('page_start_time', Date.now().toString());

    // Add current page to session
    addPageToSession();

    // Track page view
    trackEvent('page_view', {
        is_return_visitor: isReturnVisitor(),
        pages_in_session: getPagesViewedInSession(),
        previous_page: getPreviousPage()
    });
}

function trackPageLoad() {
    const loadTime = performance.now();

    trackEvent('page_load', {
        load_time_ms: Math.round(loadTime),
        page_title: document.title,
        utm_source: getUrlParameter('utm_source'),
        utm_medium: getUrlParameter('utm_medium'),
        utm_campaign: getUrlParameter('utm_campaign')
    });
}

function setupAdvancedTracking() {
    // Track page visibility changes
    document.addEventListener('visibilitychange', function () {
        trackEvent('page_visibility_change', {
            visibility_state: document.visibilityState,
            hidden: document.hidden,
            time_on_page: getTimeOnPage()
        });
    });

    // Track window focus/blur
    window.addEventListener('focus', function () {
        trackEvent('window_focus', { time_on_page: getTimeOnPage() });
    });

    window.addEventListener('blur', function () {
        trackEvent('window_blur', { time_on_page: getTimeOnPage() });
    });

    // Track scroll milestones
    let scrollMilestones = [25, 50, 75, 90, 100];
    let trackedMilestones = new Set();

    const trackScrollMilestones = debounce(() => {
        const scrollDepth = getCurrentScrollDepth();
        scrollMilestones.forEach(milestone => {
            if (scrollDepth >= milestone && !trackedMilestones.has(milestone)) {
                trackedMilestones.add(milestone);
                trackEvent('scroll_milestone', {
                    milestone: milestone,
                    scroll_depth: scrollDepth,
                    time_on_page: getTimeOnPage()
                });
            }
        });
    }, 1000);

    window.addEventListener('scroll', trackScrollMilestones);

    // Track clicks on important elements
    document.addEventListener('click', function (e) {
        const target = e.target;

        // Track CTA clicks
        if (target.classList.contains('cta-button')) {
            trackEvent('cta_click', {
                button_text: target.textContent,
                button_location: target.closest('section')?.id || 'unknown',
                time_on_page: getTimeOnPage()
            });
        }

        // Track navigation clicks
        if (target.closest('.nav-links a')) {
            trackEvent('navigation_click', {
                link_text: target.textContent,
                link_href: target.href,
                time_on_page: getTimeOnPage()
            });
        }

        // Track social link clicks
        if (target.closest('.social-links a')) {
            trackEvent('social_click', {
                platform: target.title || target.textContent,
                time_on_page: getTimeOnPage()
            });
        }
    });

    // Track form interactions
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        const emailInput = newsletterForm.querySelector('input[type="email"]');

        if (emailInput) {
            emailInput.addEventListener('focus', function () {
                trackEvent('newsletter_input_focus', { time_on_page: getTimeOnPage() });
            });

            emailInput.addEventListener('blur', function () {
                trackEvent('newsletter_input_blur', {
                    has_value: !!this.value,
                    time_on_page: getTimeOnPage()
                });
            });
        }
    }

    // Track time spent on page
    setInterval(() => {
        if (!document.hidden) {
            trackEvent('time_on_page_ping', {
                time_on_page: getTimeOnPage(),
                scroll_depth: getCurrentScrollDepth()
            });
        }
    }, 30000); // Every 30 seconds
}

// ===== PERFORMANCE MONITORING =====
function setupPerformanceMonitoring() {
    setupAdvancedTracking();
    initializePageTracking();

    // Track scroll depth
    let maxScrollDepth = 0;
    const trackScrollDepth = debounce(() => {
        const scrollDepth = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
        if (scrollDepth > maxScrollDepth) {
            maxScrollDepth = scrollDepth;
            trackEvent('scroll_depth', { depth: scrollDepth });
        }
    }, 1000);

    window.addEventListener('scroll', trackScrollDepth);
}

// ===== ERROR HANDLING =====
function setupErrorHandling() {
    window.addEventListener('error', function (event) {
        trackEvent('javascript_error', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error?.stack
        });
    });

    window.addEventListener('unhandledrejection', function (event) {
        trackEvent('unhandled_promise_rejection', {
            reason: event.reason?.toString(),
            stack: event.reason?.stack
        });
    });
}

// ===== ACCESSIBILITY IMPROVEMENTS =====
function setupAccessibility() {
    // Add skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main';
    skipLink.textContent = 'Skip to main content';
    skipLink.style.cssText = `
        position: absolute;
        left: -9999px;
        z-index: 999;
        padding: 1em;
        background-color: #000;
        color: #fff;
        text-decoration: none;
    `;
    skipLink.addEventListener('focus', function () {
        this.style.left = '6px';
        this.style.top = '7px';
    });
    skipLink.addEventListener('blur', function () {
        this.style.left = '-9999px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);

    // Add main landmark if not present
    const main = document.querySelector('main');
    if (main && !main.id) {
        main.id = 'main';
    }
}

// Export functions for testing (if in a module environment)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        updateCountdown,
        isValidEmail,
        getUrlParameter,
        trackEvent,
        showNotification,
        getGeolocationData,
        getCurrentScrollDepth,
        getTimeOnPage,
        isReturnVisitor,
        getOrCreateSessionId
    };
}