// Global variables
let map;
let directionsService;
let directionsRenderer;

// Initialize the map when the page loads
function initMap() {
    // Create a new map centered on New York City
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 13,
        center: { lat: 40.7589, lng: -73.9851 }, // Times Square coordinates
        mapTypeId: 'roadmap'
    });

    // Initialize directions service and renderer
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(map);

    console.log("Map initialized successfully!");
    updateOutput("Map initialized successfully!");
}

// Test geocoding functionality
function testGeocoding() {
    const geocoder = new google.maps.Geocoder();
    const address = document.getElementById("startLocation").value;
    
    geocoder.geocode({ address: address }, (results, status) => {
        if (status === "OK") {
            const location = results[0].geometry.location;
            map.setCenter(location);
            map.setZoom(15);
            
            // Add a marker
            new google.maps.Marker({
                position: location,
                map: map,
                title: address
            });
            
            updateOutput(`Geocoding successful! Found: ${results[0].formatted_address}`);
        } else {
            updateOutput(`Geocoding failed: ${status}`);
        }
    });
}

// Test directions functionality
function testDirections() {
    const start = document.getElementById("startLocation").value;
    const end = document.getElementById("endLocation").value;
    
    const request = {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING
    };
    
    directionsService.route(request, (result, status) => {
        if (status === "OK") {
            directionsRenderer.setDirections(result);
            updateOutput(`Directions found! Distance: ${result.routes[0].legs[0].distance.text}, Duration: ${result.routes[0].legs[0].duration.text}`);
        } else {
            updateOutput(`Directions failed: ${status}`);
        }
    });
}

// Clear the map
function clearMap() {
    if (directionsRenderer) {
        directionsRenderer.setDirections({ routes: [] });
    }
    updateOutput("Map cleared!");
}

// Update the output display
function updateOutput(message) {
    const output = document.getElementById("output");
    const timestamp = new Date().toLocaleTimeString();
    output.innerHTML += `<p>[${timestamp}] ${message}</p>`;
    output.scrollTop = output.scrollHeight;
}
