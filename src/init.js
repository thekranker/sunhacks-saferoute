// Simple initialization script for Google Maps callback
// This runs in global scope, not as a module

let mainInterface;

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