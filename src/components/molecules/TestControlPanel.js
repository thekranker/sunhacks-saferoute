import ActionButton from '../atoms/ActionButton.js';
import LocationInput from '../atoms/LocationInput.js';
import OutputDisplay from '../atoms/OutputDisplay.js';
import RouteSelector from '../atoms/RouteSelector.js';
import SafetyScoreService from '../../services/SafetyScoreService.js';
import AIAnalysisService from '../../services/AIAnalysisService.js';

class TestControlPanel {
    constructor() {
        this.startLocationInput = new LocationInput('startLocation');
        this.endLocationInput = new LocationInput('endLocation');
        this.outputDisplay = new OutputDisplay('output');
        this.routeSelector = new RouteSelector('routeSelector');
        this.safetyScoreService = new SafetyScoreService();
        this.aiAnalysisService = new AIAnalysisService();
        
        this.geocodeButton = new ActionButton('geocodeBtn', () => this.testGeocoding());
        this.directionsButton = new ActionButton('directionsBtn', () => this.testDirections());
        this.clearButton = new ActionButton('clearBtn', () => this.clearMap());
        
        // Set up route selection callback
        this.routeSelector.setOnRouteSelect((routeData, index) => {
            this.onRouteSelected(routeData, index);
        });
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
        
        this.outputDisplay.updateOutput("Finding routes with safety options...");
        this.routeSelector.hide(); // Hide route selector initially
        
        try {
            // Get both standard and ultra-safe route alternatives
            const routes = await this.getAlternativeRoutes(start, end);
            
            if (routes.length === 0) {
                this.outputDisplay.updateOutput("No routes found!");
                return;
            }
            
            this.outputDisplay.updateOutput(`Found ${routes.length} route(s). Calculating safety scores...`);
            
            // Calculate safety scores for all routes
            const routesWithSafety = await this.calculateSafetyScores(routes);
            
            // Sort routes by safety score (highest first)
            routesWithSafety.sort((a, b) => b.safetyScore - a.safetyScore);
            
            // Filter routes by length - remove routes more than 2.5x longer than shortest
            const filteredRoutes = this.filterRoutesByLength(routesWithSafety);
            
            // Mark the safest route as "Ultra Safe" if it's significantly safer
            if (filteredRoutes.length > 0) {
                const safestRoute = filteredRoutes[0];
                const secondSafest = filteredRoutes[1];
                
                // If the safest route is significantly safer than the second safest, mark it as ultra-safe
                if (secondSafest && (safestRoute.safetyScore - secondSafest.safetyScore) > 0.1) {
                    safestRoute.summary = `🛡️ Ultra Safe Route (${safestRoute.summary})`;
                    safestRoute.isSafestRoute = true;
                }
            }
            
            // Show route selector with filtered routes
            this.routeSelector.setRoutes(filteredRoutes);
            this.routeSelector.show();
            
            // Display all filtered routes on map with the safest one selected
            this.displayAllRoutes(filteredRoutes);
            
            this.outputDisplay.updateOutput(`Routes displayed. Safest route (${filteredRoutes[0].summary}) auto-selected.`);
            
        } catch (error) {
            this.outputDisplay.updateOutput(`Route calculation failed: ${error.message}`);
        }
    }

    async getAlternativeRoutes(start, end) {
        const directionsService = new google.maps.DirectionsService();
        const routes = [];
        
        // Get intermediate waypoints for ultra-safe routes
        const safeWaypoints = await this.generateSafeWaypoints(start, end);
        
        // Request configurations for different route alternatives
        const requestConfigs = [
            // Standard alternatives
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
            },
            // Ultra-safe routes with waypoints (longer but potentially much safer)
            ...safeWaypoints.slice(0, 3).map(waypoint => ({
                origin: start,
                destination: end,
                waypoints: [{ location: waypoint, stopover: false }],
                travelMode: google.maps.TravelMode.WALKING,
                avoidHighways: true,
                avoidTolls: true
            }))
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
        
        // Remove duplicate routes
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

    filterRoutesByLength(routesWithSafety) {
        if (routesWithSafety.length <= 1) {
            return routesWithSafety; // If only one route or none, return as is
        }
        
        // Get distance values in meters for all routes
        const routesWithDistance = routesWithSafety.map(routeData => {
            const distanceValue = routeData.route.legs[0].distance.value; // Distance in meters
            return {
                ...routeData,
                distanceValue: distanceValue
            };
        });
        
        // Find the shortest route distance
        const shortestDistance = Math.min(...routesWithDistance.map(r => r.distanceValue));
        
        // Filter routes that are more than 2.5x longer than the shortest
        const filteredRoutes = routesWithDistance.filter(routeData => {
            return routeData.distanceValue <= shortestDistance * 2.5;
        });
        
        // Log filtering results
        const originalCount = routesWithSafety.length;
        const filteredCount = filteredRoutes.length;
        if (originalCount > filteredCount) {
            this.outputDisplay.updateOutput(`Filtered out ${originalCount - filteredCount} route(s) that were more than 2.5x longer than the shortest route.`);
        }
        
        return filteredRoutes;
    }

    async findSafestRoute() {
        const start = this.startLocationInput.getValue();
        const end = this.endLocationInput.getValue();
        
        this.outputDisplay.updateOutput("Finding the safest possible route (may be longer)...");
        this.routeSelector.hide();
        
        try {
            // Get extensive route alternatives with wider search parameters
            const routes = await this.getSafestRouteAlternatives(start, end);
            
            if (routes.length === 0) {
                this.outputDisplay.updateOutput("No safe routes found!");
                return;
            }
            
            this.outputDisplay.updateOutput(`Found ${routes.length} extended route(s). Calculating safety scores...`);
            
            // Calculate safety scores for all routes
            const routesWithSafety = await this.calculateSafetyScores(routes);
            
            // Sort routes by safety score (highest first)
            routesWithSafety.sort((a, b) => b.safetyScore - a.safetyScore);
            
            // Filter routes by length - remove routes more than 2.5x longer than shortest
            const filteredRoutes = this.filterRoutesByLength(routesWithSafety);
            
            // Mark the safest route as "Ultra Safe"
            if (filteredRoutes.length > 0) {
                filteredRoutes[0].summary = `🛡️ Ultra Safe Route (${filteredRoutes[0].summary})`;
                filteredRoutes[0].isSafestRoute = true;
            }
            
            // Show route selector with filtered routes
            this.routeSelector.setRoutes(filteredRoutes);
            this.routeSelector.show();
            
            // Display all filtered routes on map with the safest one selected
            this.displayAllRoutes(filteredRoutes);
            
            this.outputDisplay.updateOutput(`Ultra-safe routes displayed. Safest route auto-selected with ${(filteredRoutes[0].safetyScore * 100).toFixed(1)}% safety score.`);
            
        } catch (error) {
            this.outputDisplay.updateOutput(`Safest route calculation failed: ${error.message}`);
        }
    }

    async getSafestRouteAlternatives(start, end) {
        const directionsService = new google.maps.DirectionsService();
        const routes = [];
        
        // Get intermediate waypoints to create safer, longer routes
        const waypoints = await this.generateSafeWaypoints(start, end);
        
        // Request configurations for maximum safety (longer routes)
        const requestConfigs = [
            // Standard alternatives first
            {
                origin: start,
                destination: end,
                travelMode: google.maps.TravelMode.WALKING,
                provideRouteAlternatives: true
            },
            // Avoid highways and tolls for safer pedestrian routes
            {
                origin: start,
                destination: end,
                travelMode: google.maps.TravelMode.WALKING,
                avoidHighways: true,
                avoidTolls: true
            },
            // Routes with safe waypoints (longer but potentially much safer)
            ...waypoints.map(waypoint => ({
                origin: start,
                destination: end,
                waypoints: [{ location: waypoint, stopover: false }],
                travelMode: google.maps.TravelMode.WALKING,
                avoidHighways: true
            }))
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
                console.warn(`Failed to get safe route with config:`, request, error);
            }
        }
        
        // Remove duplicate routes
        const uniqueRoutes = this.removeDuplicateRoutes(routes);
        
        return uniqueRoutes;
    }

    async generateSafeWaypoints(start, end) {
        // Generate waypoints that route through potentially safer areas
        // This creates longer routes that avoid high-crime areas
        const waypoints = [];
        
        try {
            const geocoder = new google.maps.Geocoder();
            
            // Get coordinates for start and end
            const startResult = await new Promise((resolve, reject) => {
                geocoder.geocode({ address: start }, (results, status) => {
                    if (status === "OK") resolve(results[0]);
                    else reject(new Error(`Geocoding failed for start: ${status}`));
                });
            });
            
            const endResult = await new Promise((resolve, reject) => {
                geocoder.geocode({ address: end }, (results, status) => {
                    if (status === "OK") resolve(results[0]);
                    else reject(new Error(`Geocoding failed for end: ${status}`));
                });
            });
            
            const startLat = startResult.geometry.location.lat();
            const startLng = startResult.geometry.location.lng();
            const endLat = endResult.geometry.location.lat();
            const endLng = endResult.geometry.location.lng();
            
            // Generate waypoints that create detours through potentially safer areas
            // These create longer routes that might avoid high-crime corridors
            
            // Waypoint 1: Route through commercial/business areas (usually safer)
            const midLat = (startLat + endLat) / 2;
            const midLng = (startLng + endLng) / 2;
            
            // Create waypoints that deviate from direct path
            const deviations = [
                { lat: midLat + 0.01, lng: midLng + 0.01 }, // Northeast deviation
                { lat: midLat - 0.01, lng: midLng - 0.01 }, // Southwest deviation
                { lat: midLat + 0.01, lng: midLng - 0.01 }, // Northwest deviation
                { lat: midLat - 0.01, lng: midLng + 0.01 }  // Southeast deviation
            ];
            
            // Add these as potential waypoints
            waypoints.push(...deviations.map(point => `${point.lat},${point.lng}`));
            
        } catch (error) {
            console.warn("Failed to generate safe waypoints:", error);
        }
        
        return waypoints;
    }

    displayAllRoutes(routesWithSafety) {
        // Emit event for displaying all routes with the safest one selected
        this.dispatchEvent('displayMultipleRoutes', {
            routes: routesWithSafety,
            selectedIndex: 0, // Auto-select the safest route (first in sorted array)
            origin: this.startLocationInput.getValue(),
            destination: this.endLocationInput.getValue()
        });
    }

    async onRouteSelected(routeData, index) {
        this.outputDisplay.updateOutput(`Selected route: ${routeData.summary} (Safety: ${(routeData.safetyScore * 100).toFixed(1)}%)`);
        
        // Emit event for route selection change
        this.dispatchEvent('routeSelectionChanged', {
            routeData: routeData,
            selectedIndex: index
        });

        // Get AI analysis for the selected route
        await this.getAIAnalysisForRoute(routeData);
    }

    async getAIAnalysisForRoute(routeData) {
        try {
            this.outputDisplay.updateOutput("🤖 Getting quick AI safety analysis...");
            
            const origin = this.startLocationInput.getValue();
            const destination = this.endLocationInput.getValue();
            
            const routeDetails = {
                distance: routeData.distance,
                duration: routeData.duration,
                summary: routeData.summary
            };

            const aiAnalysis = await this.aiAnalysisService.analyzeRouteSafety(origin, destination, routeDetails);
            
            if (aiAnalysis.success) {
                this.outputDisplay.updateOutput("✅ AI analysis completed!");
                const formattedAnalysis = this.aiAnalysisService.formatAnalysisForDisplay(aiAnalysis);
                this.outputDisplay.displayAIAnalysis(formattedAnalysis);
            } else {
                this.outputDisplay.updateOutput(`⚠️ AI analysis failed: ${aiAnalysis.error}`);
                // Still show the formatted analysis even if it failed
                const formattedAnalysis = this.aiAnalysisService.formatAnalysisForDisplay(aiAnalysis);
                this.outputDisplay.displayAIAnalysis(formattedAnalysis);
            }
            
        } catch (error) {
            this.outputDisplay.updateOutput(`❌ Error getting AI analysis: ${error.message}`);
            console.error('AI Analysis Error:', error);
        }
    }

    clearMap() {
        this.routeSelector.hide();
        this.dispatchEvent('clearMap');
        this.outputDisplay.updateOutput("Map cleared!");
    }

    dispatchEvent(eventName, data = {}) {
        const event = new CustomEvent(eventName, { detail: data });
        document.dispatchEvent(event);
    }
}

export default TestControlPanel;
