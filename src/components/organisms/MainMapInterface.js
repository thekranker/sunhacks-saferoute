import MapComponent from '../atoms/MapComponent.js';
import TestControlPanel from '../molecules/TestControlPanel.js';

class MainMapInterface {
    constructor() {
        this.mapComponent = new MapComponent('map');
        this.controlPanel = new TestControlPanel();
        this.directionsService = null;
        this.directionsRenderers = []; // Array to hold multiple renderers
        this.currentRoutes = [];
        this.selectedRouteIndex = 0;
        this.init();
    }

    init() {
        // Initialize the map
        this.mapComponent.init();
        
        // Initialize directions service
        this.directionsService = new google.maps.DirectionsService();

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

        // Listen for displaying multiple routes
        document.addEventListener('displayMultipleRoutes', (event) => {
            const { routes, selectedIndex, origin, destination } = event.detail;
            this.displayMultipleRoutes(routes, selectedIndex, origin, destination);
        });

        // Listen for route selection changes
        document.addEventListener('routeSelectionChanged', (event) => {
            const { selectedIndex } = event.detail;
            this.updateRouteSelection(selectedIndex);
        });

        // Listen for clear map
        document.addEventListener('clearMap', () => {
            this.clearAllRoutes();
        });
    }

    displayMultipleRoutes(routes, selectedIndex, origin, destination) {
        // Clear existing routes
        this.clearAllRoutes();
        
        this.currentRoutes = routes;
        this.selectedRouteIndex = selectedIndex;
        
        // Create a renderer for each route
        routes.forEach((routeData, index) => {
            const renderer = new google.maps.DirectionsRenderer();
            renderer.setMap(this.mapComponent.getMap());
            
            // Create directions result for this route
            const result = {
                routes: [routeData.route],
                request: {
                    origin: origin,
                    destination: destination,
                    travelMode: google.maps.TravelMode.WALKING
                },
                geocoded_waypoints: [],
                status: "OK"
            };
            
            // Set route styling based on whether it's selected or not
            this.setRouteStyle(renderer, routeData.safetyScore, index === selectedIndex);
            
            renderer.setDirections(result);
            this.directionsRenderers.push(renderer);
        });
    }

    updateRouteSelection(newSelectedIndex) {
        if (newSelectedIndex < 0 || newSelectedIndex >= this.currentRoutes.length) {
            return;
        }
        
        this.selectedRouteIndex = newSelectedIndex;
        
        // Update styling for all routes
        this.directionsRenderers.forEach((renderer, index) => {
            const routeData = this.currentRoutes[index];
            this.setRouteStyle(renderer, routeData.safetyScore, index === newSelectedIndex);
        });
    }

    setRouteStyle(renderer, safetyScore, isSelected) {
        const safetyPercentage = safetyScore * 100;
        
        let routeColor;
        let routeWeight;
        let routeOpacity;
        
        // Determine base color based on safety score
        if (safetyPercentage >= 90) {
            routeColor = '#4CAF50'; // Green
        } else if (safetyPercentage >= 75) {
            routeColor = '#FFC107'; // Yellow/Amber
        } else {
            routeColor = '#F44336'; // Red
        }
        
        // Adjust styling based on selection status
        if (isSelected) {
            routeWeight = 8; // Thicker for selected route
            routeOpacity = 0.9; // More opaque
        } else {
            routeWeight = 5; // Thinner for alternative routes
            routeOpacity = 0.5; // More transparent (like Google Maps alternatives)
        }
        
        renderer.setOptions({
            polylineOptions: {
                strokeColor: routeColor,
                strokeWeight: routeWeight,
                strokeOpacity: routeOpacity
            },
            suppressMarkers: !isSelected, // Only show markers for selected route
            suppressInfoWindows: !isSelected // Only show info windows for selected route
        });
    }

    clearAllRoutes() {
        // Clear all existing renderers
        this.directionsRenderers.forEach(renderer => {
            renderer.setDirections({ routes: [] });
            renderer.setMap(null);
        });
        this.directionsRenderers = [];
        this.currentRoutes = [];
        this.selectedRouteIndex = 0;
    }

    getMap() {
        return this.mapComponent.getMap();
    }

    getDirectionsService() {
        return this.directionsService;
    }

    getDirectionsRenderers() {
        return this.directionsRenderers;
    }
}

export default MainMapInterface;
