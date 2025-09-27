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
            const { result } = event.detail;
            this.directionsRenderer.setDirections(result);
        });

        // Listen for clear map
        document.addEventListener('clearMap', () => {
            if (this.directionsRenderer) {
                this.directionsRenderer.setDirections({ routes: [] });
            }
        });
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
