class MapComponent {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
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

    getMap() {
        return this.map;
    }
}

export default MapComponent;
