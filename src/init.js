// Simple initialization script for Google Maps callback
// This runs in global scope, not as a module

let mainInterface;

// Theme management
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // Set initial theme
        this.setTheme(this.currentTheme);
        
        // Add event listener for theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle icon
        const themeIcon = document.querySelector('.theme-icon');
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// Initialize the application when Google Maps is ready
function initMap() {
    try {
        // Import the MainMapInterface dynamically
        import('./components/organisms/MainMapInterface.js').then(module => {
            const MainMapInterface = module.default;
            mainInterface = new MainMapInterface();
            console.log("Application initialized successfully!");
        }).catch(error => {
            console.error("Failed to load MainMapInterface:", error);
        });
    } catch (error) {
        console.error("Failed to initialize application:", error);
    }
}

// Make initMap globally available
window.initMap = initMap; 