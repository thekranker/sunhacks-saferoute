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
        
        this.outputDisplay.updateOutput("Finding safest route...");
        
        try {
            // Get multiple alternative routes
            const routes = await this.getAlternativeRoutes(start, end);
            
            if (routes.length === 0) {
                this.outputDisplay.updateOutput("No routes found!");
                return;
            }
            
            this.outputDisplay.updateOutput(`Found ${routes.length} route(s). Calculating safety scores...`);
            
            // Calculate safety scores for all routes
            const routesWithSafety = await this.calculateSafetyScores(routes);
            
            // Select the safest route
            const safestRoute = this.selectSafestRoute(routesWithSafety);
            
            // Display the safest route
            this.displayRoute(safestRoute);
            
        } catch (error) {
            this.outputDisplay.updateOutput(`Route calculation failed: ${error.message}`);
        }
    }

    async getAlternativeRoutes(start, end) {
        const directionsService = new google.maps.DirectionsService();
        const routes = [];
        
        // Request configurations for different route alternatives
        const requestConfigs = [
            {
                origin: start,
                destination: end,
                travelMode: google.maps.TravelMode.WALKING,
                provideRouteAlternatives: true
            },
            {
                origin: start,
                destination: end,
                travelMode: google.maps.TravelMode.WALKING,
                avoidHighways: true
            },
            {
                origin: start,
                destination: end,
                travelMode: google.maps.TravelMode.WALKING,
                avoidTolls: true
            }
        ];
        
        // Get routes from each configuration
        for (const request of requestConfigs) {
            try {
                const result = await new Promise((resolve, reject) => {
                    directionsService.route(request, (result, status) => {
                        if (status === "OK") {
                            resolve(result);
                        } else {
                            reject(new Error(`Directions failed: ${status}`));
                        }
                    });
                });
                
                // Add all routes from this result
                if (result.routes && result.routes.length > 0) {
                    routes.push(...result.routes);
                }
            } catch (error) {
                console.warn(`Failed to get route with config:`, request, error);
            }
        }
        
        // Remove duplicate routes (simple deduplication by comparing route summaries)
        const uniqueRoutes = this.removeDuplicateRoutes(routes);
        
        return uniqueRoutes;
    }

    removeDuplicateRoutes(routes) {
        const seen = new Set();
        return routes.filter(route => {
            const summary = route.summary || '';
            const distance = route.legs[0]?.distance?.value || 0;
            const key = `${summary}-${distance}`;
            
            if (seen.has(key)) {
                return false;
            }
            seen.add(key);
            return true;
        });
    }

    async calculateSafetyScores(routes) {
        const routesWithSafety = [];
        
        for (let i = 0; i < routes.length; i++) {
            const route = routes[i];
            
            try {
                // Create a directions result object for this route
                const routeResult = {
                    routes: [route]
                };
                
                const routePoints = this.safetyScoreService.extractRoutePointsFromDirections(routeResult);
                const safetyData = await this.safetyScoreService.getSafetyScore(routePoints);
                
                routesWithSafety.push({
                    route: route,
                    safetyScore: safetyData.safety_score,
                    safetyBreakdown: safetyData.breakdown,
                    distance: route.legs[0].distance.text,
                    duration: route.legs[0].duration.text,
                    summary: route.summary || `Route ${i + 1}`
                });
                
                this.outputDisplay.updateOutput(`Route ${i + 1}: Safety Score ${safetyData.safety_score}/1.0`);
                
            } catch (error) {
                console.warn(`Failed to calculate safety score for route ${i + 1}:`, error);
                // Include route with default low safety score if calculation fails
                routesWithSafety.push({
                    route: route,
                    safetyScore: 0.1, // Low default score
                    safetyBreakdown: {},
                    distance: route.legs[0].distance.text,
                    duration: route.legs[0].duration.text,
                    summary: route.summary || `Route ${i + 1}`,
                    error: error.message
                });
            }
        }
        
        return routesWithSafety;
    }

    selectSafestRoute(routesWithSafety) {
        if (routesWithSafety.length === 0) {
            throw new Error("No routes available for selection");
        }
        
        // Sort by safety score (highest first)
        routesWithSafety.sort((a, b) => b.safetyScore - a.safetyScore);
        
        const safestRoute = routesWithSafety[0];
        
        this.outputDisplay.updateOutput(`Selected safest route: ${safestRoute.summary}`);
        this.outputDisplay.updateOutput(`Safety Score: ${safestRoute.safetyScore}/1.0`);
        this.outputDisplay.updateOutput(`Distance: ${safestRoute.distance}, Duration: ${safestRoute.duration}`);
        
        // Show comparison with other routes
        if (routesWithSafety.length > 1) {
            this.outputDisplay.updateOutput("--- Route Comparison ---");
            routesWithSafety.forEach((routeData, index) => {
                const status = index === 0 ? " (SELECTED)" : "";
                this.outputDisplay.updateOutput(`${routeData.summary}: Safety ${routeData.safetyScore}/1.0, ${routeData.distance}${status}`);
            });
        }
        
        if (safestRoute.safetyBreakdown && Object.keys(safestRoute.safetyBreakdown).length > 0) {
            this.outputDisplay.updateOutput(`Safety breakdown: ${JSON.stringify(safestRoute.safetyBreakdown)}`);
        }
        
        return safestRoute;
    }

    displayRoute(safestRoute) {
        // Create a proper directions result object for the safest route
        const result = {
            routes: [safestRoute.route],
            request: {
                origin: this.startLocationInput.getValue(),
                destination: this.endLocationInput.getValue(),
                travelMode: google.maps.TravelMode.WALKING
            },
            geocoded_waypoints: [],
            status: "OK"
        };
        
        // Emit event for directions update with safety score
        this.dispatchEvent('directionsSuccess', {
            result: result,
            distance: safestRoute.distance,
            duration: safestRoute.duration,
            safetyScore: safestRoute.safetyScore,
            isSafetyOptimized: true
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
