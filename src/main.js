import MainMapInterface from "./components/organisms/MainMapInterface.js";

// Global variable to hold the main interface
let mainInterface;

// Initialize the application when the page loads
function initMap() {
    try {
        mainInterface = new MainMapInterface();
        console.log("Application initialized successfully!");
    } catch (error) {
        console.error("Failed to initialize application:", error);
    }
}

// Make initMap globally available for Google Maps callback
window.initMap = initMap;

// Export for potential module usage
export { initMap };
