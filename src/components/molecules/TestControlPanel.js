import ActionButton from '../atoms/ActionButton.js';
import LocationInput from '../atoms/LocationInput.js';
import OutputDisplay from '../atoms/OutputDisplay.js';
import SafetyScoreService from '../../services/SafetyScoreService.js';

class TestControlPanel {
    constructor() {
        this.startLocationInput = new LocationInput('startLocation');
        this.endLocationInput = new LocationInput('endLocation');
        this.outputDisplay = new OutputDisplay('output');
        this.safetyScoreService = new SafetyScoreService();
        
        this.geocodeButton = new ActionButton('geocodeBtn', () => this.testGeocoding());
        this.directionsButton = new ActionButton('directionsBtn', () => this.testDirections());
        this.clearButton = new ActionButton('clearBtn', () => this.clearMap());
    }

    testGeocoding() {
        const geocoder = new google.maps.Geocoder();
        const address = this.startLocationInput.getValue();
        
        geocoder.geocode({ address: address }, (results, status) => {
            if (status === "OK") {
                const location = results[0].geometry.location;
                
                // Emit event for map update
                this.dispatchEvent('geocodeSuccess', {
                    location: location,
                    address: address,
                    formattedAddress: results[0].formatted_address
                });
                
                this.outputDisplay.updateOutput(`Geocoding successful! Found: ${results[0].formatted_address}`);
            } else {
                this.outputDisplay.updateOutput(`Geocoding failed: ${status}`);
            }
        });
    }

    async testDirections() {
        const start = this.startLocationInput.getValue();
        const end = this.endLocationInput.getValue();
        
        const request = {
            origin: start,
            destination: end,
            travelMode: google.maps.TravelMode.WALKING
        };
        
        const directionsService = new google.maps.DirectionsService();
        directionsService.route(request, async (result, status) => {
            if (status === "OK") {
                // Emit event for directions update
                this.dispatchEvent('directionsSuccess', {
                    result: result,
                    distance: result.routes[0].legs[0].distance.text,
                    duration: result.routes[0].legs[0].duration.text
                });
                
                this.outputDisplay.updateOutput(`Directions found! Distance: ${result.routes[0].legs[0].distance.text}, Duration: ${result.routes[0].legs[0].duration.text}`);
                
                // Get safety score for the route
                try {
                    this.outputDisplay.updateOutput("Calculating safety score...");
                    const routePoints = this.safetyScoreService.extractRoutePointsFromDirections(result);
                    const safetyData = await this.safetyScoreService.getSafetyScore(routePoints);
                    
                    this.outputDisplay.updateOutput(`Safety Score: ${safetyData.safety_score}/100`);
                    if (safetyData.breakdown) {
                        this.outputDisplay.updateOutput(`Safety breakdown: ${JSON.stringify(safetyData.breakdown)}`);
                    }
                } catch (error) {
                    this.outputDisplay.updateOutput(`Safety score calculation failed: ${error.message}`);
                }
            } else {
                this.outputDisplay.updateOutput(`Directions failed: ${status}`);
            }
        });
    }

    clearMap() {
        this.dispatchEvent('clearMap');
        this.outputDisplay.updateOutput("Map cleared!");
    }

    dispatchEvent(eventName, data = {}) {
        const event = new CustomEvent(eventName, { detail: data });
        document.dispatchEvent(event);
    }
}

export default TestControlPanel;
