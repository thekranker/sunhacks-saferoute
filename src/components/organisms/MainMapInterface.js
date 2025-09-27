import MapComponent from '../atoms/MapComponent.js';
import TestControlPanel from '../molecules/TestControlPanel.js';

class MainMapInterface {
    constructor() {
        this.mapComponent = new MapComponent('map');
        this.controlPanel = new TestControlPanel();
        this.directionsService = null;
        this.directionsRenderer = null;
        this.init();
    }

    init() {
        // Initialize the map
        this.mapComponent.init();
        
        // Initialize directions service and renderer
        this.directionsService = new google.maps.DirectionsService();
        this.directionsRenderer = new google.maps.DirectionsRenderer();
        this.directionsRenderer.setMap(this.mapComponent.getMap());

        // Bind event listeners
        this.bindEvents();
        
        console.log("MainMapInterface initialized successfully!");
    }

    bindEvents() {
        // Listen for geocoding success
        document.addEventListener('geocodeSuccess', (event) => {
            const { location, address } = event.detail;
            this.mapComponent.setCenter(location);
            this.mapComponent.setZoom(15);
            this.mapComponent.addMarker(location, address);
        });

        // Listen for directions success
        document.addEventListener('directionsSuccess', (event) => {
            const { result, safetyScore, isSafetyOptimized } = event.detail;
            
            // Set route color based on safety score
            if (safetyScore !== undefined && isSafetyOptimized) {
                this.setRouteColor(safetyScore);
            }
            
            this.directionsRenderer.setDirections(result);
        });

        // Listen for clear map
        document.addEventListener('clearMap', () => {
            if (this.directionsRenderer) {
                this.directionsRenderer.setDirections({ routes: [] });
            }
        });
    }

    setRouteColor(safetyScore) {
        // Convert safety score to percentage (assuming it's between 0-1)
        const safetyPercentage = safetyScore * 100;
        
        let routeColor;
        let routeWeight = 6; // Default weight
        
        if (safetyPercentage >= 90) {
            // Green for high safety (90%+)
            routeColor = '#4CAF50'; // Green
            routeWeight = 8; // Thicker line for high safety
        } else if (safetyPercentage >= 75) {
            // Yellow for medium safety (75-89%)
            routeColor = '#FFC107'; // Yellow/Amber
            routeWeight = 6; // Medium thickness
        } else {
            // Red for low safety (<75%)
            routeColor = '#F44336'; // Red
            routeWeight = 4; // Thinner line for low safety
        }
        
        // Configure the directions renderer with custom styling
        this.directionsRenderer.setOptions({
            polylineOptions: {
                strokeColor: routeColor,
                strokeWeight: routeWeight,
                strokeOpacity: 0.8
            },
            suppressMarkers: false, // Keep start/end markers
            suppressInfoWindows: false // Keep info windows
        });
        
        console.log(`Route color set to ${routeColor} for safety score: ${safetyPercentage.toFixed(1)}%`);
    }

    getMap() {
        return this.mapComponent.getMap();
    }

    getDirectionsService() {
        return this.directionsService;
    }

    getDirectionsRenderer() {
        return this.directionsRenderer;
    }
}

export default MainMapInterface;
