class MapComponent {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.userLocationMarker = null;
        this.options = {
            zoom: 15,
            center: { lat: 40.7589, lng: -73.9851 }, // Default to Times Square, will be updated with user location
            mapTypeId: 'roadmap',
            ...options
        };
    }

    init() {
        this.map = new google.maps.Map(document.getElementById(this.containerId), this.options);
        console.log("Map initialized successfully!");
        return this.map;
    }

    setCenter(location) {
        if (this.map) {
            this.map.setCenter(location);
        }
    }

    setZoom(zoom) {
        if (this.map) {
            this.map.setZoom(zoom);
        }
    }

    addMarker(position, title = '') {
        if (this.map) {
            return new google.maps.Marker({
                position: position,
                map: this.map,
                title: title
            });
        }
        return null;
    }

    // Set user location with blue dot (like Google Maps)
    setUserLocation(location, address = '') {
        if (this.map) {
            // Center map on user location
            this.map.setCenter(location);
            this.map.setZoom(15);
            
            // Remove existing user location marker if it exists
            if (this.userLocationMarker) {
                this.userLocationMarker.setMap(null);
            }
            
            // Create a blue dot marker for user location (similar to Google Maps)
            this.userLocationMarker = new google.maps.Marker({
                position: location,
                map: this.map,
                title: address || 'Your location',
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 8,
                    fillColor: '#4285F4', // Google blue
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2
                },
                zIndex: 1000 // Ensure it's on top
            });
            
            // No animation needed - keep it simple like Google Maps
        }
    }

    // Update user location (for when user moves)
    updateUserLocation(location) {
        if (this.userLocationMarker) {
            this.userLocationMarker.setPosition(location);
            this.map.setCenter(location);
        }
    }

    // Remove user location marker
    clearUserLocation() {
        if (this.userLocationMarker) {
            this.userLocationMarker.setMap(null);
            this.userLocationMarker = null;
        }
    }

    getMap() {
        return this.map;
    }
}

export default MapComponent;
