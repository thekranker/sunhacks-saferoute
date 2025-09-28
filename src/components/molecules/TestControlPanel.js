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
            
            // Get AI analysis for all routes automatically
            this.outputDisplay.updateOutput("🤖 Getting AI analysis for all routes...");
            
            // Show routes first with loading indicators
            this.routeSelector.setRoutes(filteredRoutes.map(route => ({
                ...route,
                aiAnalysis: { loading: true }
            })));
            this.routeSelector.show();
            
            // Get AI analysis in background
            const routesWithAI = await this.getAIAnalysisForAllRoutes(filteredRoutes);
            
            // Mark the safest route as "Ultra Safe" if it's significantly safer
            if (routesWithAI.length > 0) {
                const safestRoute = routesWithAI[0];
                const secondSafest = routesWithAI[1];
                
                // If the safest route is significantly safer than the second safest, mark it as ultra-safe
                if (secondSafest && (safestRoute.safetyScore - secondSafest.safetyScore) > 0.1) {
                    safestRoute.summary = `🛡️ Ultra Safe Route (${safestRoute.summary})`;
                    safestRoute.isSafestRoute = true;
                }
            }
            
            // Update route selector with AI analysis
            this.routeSelector.setRoutes(routesWithAI);
            
            // Display all filtered routes on map with the safest one selected
            this.displayAllRoutes(routesWithAI);
            
            this.outputDisplay.updateOutput(`Routes displayed with AI analysis. Safest route (${routesWithAI[0].summary}) auto-selected.`);
            
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
                
                // Calculate weighted safety score with loading states
                const weightedScore = await this.calculateWeightedSafetyScore(routePoints, i + 1);
                
                routesWithSafety.push({
                    route: route,
                    safetyScore: weightedScore.overallScore,
                    crimeScore: weightedScore.crimeScore,
                    streetviewScore: weightedScore.streetviewScore,
                    aiScore: weightedScore.aiScore,
                    safetyBreakdown: weightedScore.breakdown,
                    distance: route.legs[0].distance.text,
                    duration: route.legs[0].duration.text,
                    summary: route.summary || `Route ${i + 1}`
                });
                
                this.outputDisplay.updateOutput(`Route ${i + 1}: Overall Safety Score ${(weightedScore.overallScore * 100).toFixed(1)}%`);
                
            } catch (error) {
                console.warn(`Failed to calculate safety score for route ${i + 1}:`, error);
                // Include route with default low safety score if calculation fails
                routesWithSafety.push({
                    route: route,
                    safetyScore: 0.1, // Low default score
                    crimeScore: 0.1,
                    streetviewScore: 0.1,
                    aiScore: 0.1,
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

    async calculateWeightedSafetyScore(routePoints, routeNumber) {
        // Show loading screen with cycling messages
        const loadingMessages = [
            "Studying crime statistics",
            "Analyzing streetview data", 
            "Picking optimal routes"
        ];
        
        let messageIndex = 0;
        const loadingInterval = setInterval(() => {
            this.outputDisplay.updateOutput(`Route ${routeNumber}: ${loadingMessages[messageIndex]}...`);
            messageIndex = (messageIndex + 1) % loadingMessages.length;
        }, 1500);

        try {
            // Step 1: Get crime data (65% weight)
            this.outputDisplay.updateOutput(`Route ${routeNumber}: Studying crime statistics...`);
            const crimeData = await this.safetyScoreService.getSafetyScore(routePoints);
            const crimeScore = crimeData.safety_score;

            // Step 2: Get streetview analysis (25% weight)
            this.outputDisplay.updateOutput(`Route ${routeNumber}: Analyzing streetview data...`);
            const streetviewScore = await this.getStreetviewScore(routePoints);

            // Step 3: Get AI analysis (15% weight)
            this.outputDisplay.updateOutput(`Route ${routeNumber}: Picking optimal routes...`);
            const aiScore = await this.getAIScore(routePoints);

            // Calculate weighted overall score
            const overallScore = (crimeScore * 0.65) + (streetviewScore * 0.25) + (aiScore * 0.15);

            // Clear loading interval
            clearInterval(loadingInterval);

            return {
                overallScore: overallScore,
                crimeScore: crimeScore,
                streetviewScore: streetviewScore,
                aiScore: aiScore,
                breakdown: crimeData.breakdown
            };

        } catch (error) {
            clearInterval(loadingInterval);
            throw error;
        }
    }

    async getStreetviewScore(routePoints) {
        try {
            // Use the streetview analysis endpoint
            const response = await fetch('http://localhost:5002/analyze-streetview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    location_info: {
                        address: "Route Analysis",
                        coordinates: `${routePoints[0].lat},${routePoints[0].lon}`,
                        time_context: "day"
                    }
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.safety_score !== undefined) {
                    return data.safety_score / 100; // Convert percentage to decimal
                } else {
                    console.warn('Streetview analysis returned unsuccessful result:', data);
                    return 0.7; // 70% default
                }
            } else {
                console.warn('Streetview analysis HTTP error:', response.status);
                return 0.7; // 70% default
            }
        } catch (error) {
            console.warn('Streetview analysis failed:', error);
            return 0.7; // 70% default
        }
    }

    async getAIScore(routePoints) {
        try {
            // Use the AI analysis service
            const origin = this.startLocationInput.getValue();
            const destination = this.endLocationInput.getValue();
            
            const routeDetails = {
                distance: "Route Analysis",
                duration: "Route Analysis", 
                summary: "Route Analysis"
            };

            const aiAnalysis = await this.aiAnalysisService.analyzeRouteSafety(origin, destination, routeDetails);
            
            if (aiAnalysis.success && aiAnalysis.analysis) {
                return aiAnalysis.analysis.safety_score / 100; // Convert percentage to decimal
            } else {
                return 0.6; // 60% default
            }
        } catch (error) {
            console.warn('AI analysis failed:', error);
            return 0.6; // 60% default
        }
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

        // AI analysis is already loaded and displayed in the route selector
        if (routeData.aiAnalysis && routeData.aiAnalysis.success) {
            const analysis = routeData.aiAnalysis.analysis;
            this.outputDisplay.updateOutput(`AI Analysis: ${analysis.safety_score}% safety score`);
        }
    }

    async getAIAnalysisForAllRoutes(routes) {
        const origin = this.startLocationInput.getValue();
        const destination = this.endLocationInput.getValue();
        
        // Process all routes in parallel for faster loading
        const aiPromises = routes.map(async (routeData, index) => {
            try {
                const routeDetails = {
                    distance: routeData.distance,
                    duration: routeData.duration,
                    summary: routeData.summary
                };

                const aiAnalysis = await this.aiAnalysisService.analyzeRouteSafety(origin, destination, routeDetails);
                
                // Add AI analysis to route data
                return {
                    ...routeData,
                    aiAnalysis: aiAnalysis
                };
            } catch (error) {
                console.error(`AI Analysis Error for route ${index + 1}:`, error);
                // Return route with failed analysis
                return {
                    ...routeData,
                    aiAnalysis: {
                        success: false,
                        error: error.message,
                        analysis: {
                            safety_score: 50,
                            main_concerns: ["Analysis failed"],
                            quick_tips: ["Use caution"]
                        }
                    }
                };
            }
        });

        // Wait for all AI analyses to complete
        const routesWithAI = await Promise.all(aiPromises);
        
        this.outputDisplay.updateOutput(`✅ AI analysis completed for ${routesWithAI.length} routes!`);
        return routesWithAI;
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
