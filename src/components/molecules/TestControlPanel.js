import ActionButton from '../atoms/ActionButton.js';
import LocationInput from '../atoms/LocationInput.js';
import RouteSelector from '../atoms/RouteSelector.js';
import SafetyScoreService from '../../services/SafetyScoreService.js';
import AIAnalysisService from '../../services/AIAnalysisService.js';

class TestControlPanel {
    constructor() {
        this.endLocationInput = new LocationInput('endLocation');
        this.routeSelector = new RouteSelector('routeSelector');
        this.safetyScoreService = new SafetyScoreService();
        this.aiAnalysisService = new AIAnalysisService();
        
        // User's current location
        this.userLocation = null;
        this.userLocationAddress = '';
        this.locationWatchId = null;
        
        // Smart caching system for performance optimization
        this.cache = {
            safetyScores: new Map(), // Cache safety scores by route fingerprint
            geocoding: new Map(),    // Cache geocoding results
            aiAnalysis: new Map(),   // Cache AI analysis results
            streetview: new Map()    // Cache streetview analysis
        };
        
        // No buttons needed - just Enter key support
        
        // Add Enter key support for the destination input
        this.setupEnterKeySupport();
        
        // Add autocomplete functionality
        this.setupAutocomplete();
        
        // Automatically get user location on initialization
        this.autoDetectLocation();
        
        // Set up route selection callback
        this.routeSelector.setOnRouteSelect((routeData, index) => {
            this.onRouteSelected(routeData, index);
        });
    }

    autoDetectLocation() {
        if (!navigator.geolocation) {
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;
                const userLocation = new google.maps.LatLng(userLat, userLng);
                
                this.userLocation = userLocation;
                
                // Reverse geocode to get address
                const geocoder = new google.maps.Geocoder();
                geocoder.geocode({ location: userLocation }, (results, status) => {
                    if (status === "OK" && results[0]) {
                        this.userLocationAddress = results[0].formatted_address;
                        
                        // Emit event for map update
                        this.dispatchEvent('geocodeSuccess', {
                            location: userLocation,
                            address: this.userLocationAddress,
                            formattedAddress: this.userLocationAddress
                        });
                        
                        
                        // Start continuous location tracking
                        this.startLocationTracking();
                    } else {
                        // Start tracking even without address
                        this.startLocationTracking();
                    }
                });
            },
            (error) => {
                // Location detection failed - user can still enter destination manually
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 300000 // 5 minutes
            }
        );
    }

    async testDirections() {
        if (!this.userLocation) {
            return;
        }
        
        const start = this.userLocationAddress;
        const end = this.endLocationInput.getValue();
        
        this.showLoadingIndicator();
        this.routeSelector.hide(); // Hide route selector initially
        
        try {
            // Get both standard and ultra-safe route alternatives
            const routes = await this.getAlternativeRoutes(start, end);
            
            if (routes.length === 0) {
                return;
            }
            
            // Pre-filter obviously unsafe routes before expensive analysis
            const preFilteredRoutes = this.preFilterUnsafeRoutes(routes);
            
            if (preFilteredRoutes.length === 0) {
                return;
            }
            
            // Calculate safety scores for filtered routes
            const routesWithSafety = await this.calculateSafetyScores(preFilteredRoutes);
            
            // Sort routes by safety score (highest first)
            routesWithSafety.sort((a, b) => b.safetyScore - a.safetyScore);
            
            // Filter routes by length - remove routes more than 2.5x longer than shortest
            const filteredRoutes = this.filterRoutesByLength(routesWithSafety);
            
            // Show routes immediately with basic safety scores (progressive loading)
            this.routeSelector.setRoutes(filteredRoutes.map(route => ({
                ...route,
                aiAnalysis: { loading: true }
            })));
            this.routeSelector.show();
            
            // Display routes on map immediately
            this.displayAllRoutes(filteredRoutes);
            
            // Get AI analysis in background and update progressively
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
            
            // Update route selector with final AI analysis
            this.routeSelector.setRoutes(routesWithAI);
            
            // Re-display routes with final scores
            this.displayAllRoutes(routesWithAI);
            
            this.hideLoadingIndicator();
            
        } catch (error) {
            this.hideLoadingIndicator();
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
        const origin = this.userLocationAddress;
        const destination = this.endLocationInput.getValue();
        
        // Pre-extract route points for all routes to avoid redundant processing
        const routesWithPoints = routes.map((route, i) => {
            const routeResult = { routes: [route] };
            const routePoints = this.safetyScoreService.extractRoutePointsFromDirections(routeResult);
            return { route, routePoints, index: i };
        });
        
        // Process all routes in parallel for maximum performance
        const safetyPromises = routesWithPoints.map(async ({ route, routePoints, index }) => {
            try {
                // Calculate weighted safety score with loading states
                const weightedScore = await this.calculateWeightedSafetyScore(routePoints, index + 1, origin, destination);
                
                
                return {
                    route: route,
                    safetyScore: weightedScore.overallScore,
                    crimeScore: weightedScore.crimeScore,
                    streetviewScore: weightedScore.streetviewScore,
                    aiScore: weightedScore.aiScore,
                    safetyBreakdown: weightedScore.breakdown,
                    distance: route.legs[0].distance.text,
                    duration: route.legs[0].duration.text,
                    summary: route.summary || `Route ${index + 1}`,
                    origin: origin,
                    destination: destination
                };
                
            } catch (error) {
                console.warn(`Failed to calculate safety score for route ${index + 1}:`, error);
                // Include route with default low safety score if calculation fails
                return {
                    route: route,
                    safetyScore: 0.1, // Low default score
                    crimeScore: 0.1,
                    streetviewScore: 0.1,
                    aiScore: 0.1,
                    safetyBreakdown: {},
                    distance: route.legs[0].distance.text,
                    duration: route.legs[0].duration.text,
                    summary: route.summary || `Route ${index + 1}`,
                    error: error.message,
                    origin: origin,
                    destination: destination
                };
            }
        });
        
        // Wait for all routes to complete in parallel
        const routesWithSafety = await Promise.all(safetyPromises);
        
        return routesWithSafety;
    }

    // Generate cache key for route segments
    generateRouteCacheKey(routePoints) {
        if (routePoints.length === 0) return null;
        const start = routePoints[0];
        const end = routePoints[routePoints.length - 1];
        return `${start.lat.toFixed(4)},${start.lon.toFixed(4)}-${end.lat.toFixed(4)},${end.lon.toFixed(4)}`;
    }

    // Get cached safety score or calculate new one
    async getCachedSafetyScore(routePoints, routeNumber) {
        const cacheKey = this.generateRouteCacheKey(routePoints);
        if (cacheKey && this.cache.safetyScores.has(cacheKey)) {
            return this.cache.safetyScores.get(cacheKey);
        }

        const result = await this.safetyScoreService.getSafetyScore(routePoints);
        
        if (cacheKey) {
            this.cache.safetyScores.set(cacheKey, result);
        }
        
        return result;
    }

    // Get cached streetview score or calculate new one
    async getCachedStreetviewScore(routePoints, routeNumber) {
        const cacheKey = this.generateRouteCacheKey(routePoints);
        if (cacheKey && this.cache.streetview.has(cacheKey)) {
            return this.cache.streetview.get(cacheKey);
        }

        const result = await this.getStreetviewScore(routePoints);
        
        if (cacheKey) {
            this.cache.streetview.set(cacheKey, result);
        }
        
        return result;
    }

    async calculateWeightedSafetyScore(routePoints, routeNumber, origin, destination) {
        // Show loading screen with cycling messages
        const loadingMessages = [
            "Studying crime statistics",
            "Analyzing streetview data", 
            "Getting AI analysis"
        ];
        
        let messageIndex = 0;
        const loadingInterval = setInterval(() => {
            messageIndex = (messageIndex + 1) % loadingMessages.length;
        }, 1500);

        try {
            // Run crime and streetview analysis in parallel with caching
            const [crimeData, streetviewScore] = await Promise.all([
                // Step 1: Get crime data (65% weight) with caching
                this.getCachedSafetyScore(routePoints, routeNumber),
                
                // Step 2: Get streetview analysis (25% weight) with caching
                this.getCachedStreetviewScore(routePoints, routeNumber)
            ]);

            const crimeScore = crimeData.safety_score;
            
            // Calculate weighted score without AI (AI will be added later in getAIAnalysisForAllRoutes)
            const overallScore = (crimeScore * 0.65) + (streetviewScore * 0.25) + (0.6 * 0.15); // Use default AI score temporarily

            // Clear loading interval
            clearInterval(loadingInterval);

            return {
                overallScore: overallScore,
                crimeScore: crimeScore,
                streetviewScore: streetviewScore,
                aiScore: 0.6, // Temporary default, will be updated later
                breakdown: crimeData.breakdown,
                origin: origin,
                destination: destination
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
            const origin = this.userLocationAddress;
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

    // Smart route filtering to skip obviously unsafe routes
    preFilterUnsafeRoutes(routes) {
        return routes.filter(route => {
            const distance = route.legs[0].distance.value; // Distance in meters
            const duration = route.legs[0].duration.value; // Duration in seconds
            
            // Skip routes that are extremely long (more than 5km for walking)
            if (distance > 5000) {
                return false;
            }
            
            // Skip routes that take more than 1 hour to walk
            if (duration > 3600) {
                return false;
            }
            
            // Skip routes with suspicious patterns (very short segments might indicate issues)
            if (route.overview_path && route.overview_path.length < 3) {
                return false;
            }
            
            return true;
        });
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
        
        return filteredRoutes;
    }

    async findSafestRoute() {
        if (!this.userLocation) {
            return;
        }
        
        const start = this.userLocationAddress;
        const end = this.endLocationInput.getValue();
        
        this.showLoadingIndicator();
        this.routeSelector.hide();
        
        try {
            // Get extensive route alternatives with wider search parameters
            const routes = await this.getSafestRouteAlternatives(start, end);
            
            if (routes.length === 0) {
                return;
            }
            
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
            
            this.hideLoadingIndicator();
            
        } catch (error) {
            this.hideLoadingIndicator();
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
            origin: this.userLocationAddress,
            destination: this.endLocationInput.getValue()
        });
    }

    async onRouteSelected(routeData, index) {
        // Emit event for route selection change
        this.dispatchEvent('routeSelectionChanged', {
            routeData: routeData,
            selectedIndex: index
        });
    }

    // Batch API calls for similar routes to reduce overhead
    async batchAIAnalysis(routes) {
        const batchSize = 3; // Process 3 routes at a time to avoid overwhelming the API
        const batches = [];
        
        for (let i = 0; i < routes.length; i += batchSize) {
            batches.push(routes.slice(i, i + batchSize));
        }
        
        const results = [];
        for (const batch of batches) {
            const batchPromises = batch.map(async (routeData, index) => {
                try {
                    const routeDetails = {
                        distance: routeData.distance,
                        duration: routeData.duration,
                        summary: routeData.summary
                    };

                    const aiAnalysis = await this.aiAnalysisService.analyzeRouteSafety(routeData.origin, routeData.destination, routeDetails);
                    
                    // Calculate final safety score with real AI score
                    const realAiScore = aiAnalysis.success ? (aiAnalysis.analysis.safety_score / 100) : 0.6;
                    const finalSafetyScore = (routeData.crimeScore * 0.65) + (routeData.streetviewScore * 0.25) + (realAiScore * 0.15);
                    
                    // Add AI analysis to route data and update safety score
                    return {
                        ...routeData,
                        safetyScore: finalSafetyScore,
                        aiScore: realAiScore,
                        aiAnalysis: aiAnalysis
                    };
                } catch (error) {
                    console.error(`AI Analysis Error for route:`, error);
                    // Return route with failed analysis but keep existing safety score
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
            
            const batchResults = await Promise.all(batchPromises);
            results.push(...batchResults);
            
            // Update UI progressively as each batch completes
        }
        
        return results;
    }

    async getAIAnalysisForAllRoutes(routes) {
        // Use batched processing for better API efficiency
        const routesWithAI = await this.batchAIAnalysis(routes);
        
        return routesWithAI;
    }

    async getAIAnalysisForRoute(routeData) {
        try {
            const origin = this.userLocationAddress;
            const destination = this.endLocationInput.getValue();
            
            const routeDetails = {
                distance: routeData.distance,
                duration: routeData.duration,
                summary: routeData.summary
            };

            const aiAnalysis = await this.aiAnalysisService.analyzeRouteSafety(origin, destination, routeDetails);
            
            if (aiAnalysis.success) {
                const formattedAnalysis = this.aiAnalysisService.formatAnalysisForDisplay(aiAnalysis);
            } else {
                const formattedAnalysis = this.aiAnalysisService.formatAnalysisForDisplay(aiAnalysis);
            }
            
        } catch (error) {
            console.error('AI Analysis Error:', error);
        }
    }

    clearMap() {
        this.routeSelector.hide();
        this.dispatchEvent('clearMap');
    }

    showLoadingIndicator() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'flex';
        }
    }

    hideLoadingIndicator() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    startLocationTracking() {
        if (!navigator.geolocation) {
            return;
        }

        // Stop any existing tracking
        if (this.locationWatchId) {
            navigator.geolocation.clearWatch(this.locationWatchId);
        }

        // Start continuous location tracking
        this.locationWatchId = navigator.geolocation.watchPosition(
            (position) => {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;
                const userLocation = new google.maps.LatLng(userLat, userLng);
                
                // Update user location
                this.userLocation = userLocation;
                
                // Emit event to update the blue dot on the map
                this.dispatchEvent('userLocationUpdate', {
                    location: userLocation,
                    address: this.userLocationAddress
                });
            },
            (error) => {
                console.warn('Location tracking error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 30000 // 30 seconds
            }
        );
    }

    stopLocationTracking() {
        if (this.locationWatchId) {
            navigator.geolocation.clearWatch(this.locationWatchId);
            this.locationWatchId = null;
        }
    }

    setupEnterKeySupport() {
        const destinationInput = document.getElementById('endLocation');
        if (destinationInput) {
            destinationInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.testDirections();
                }
            });
        }
    }

    setupAutocomplete() {
        const destinationInput = document.getElementById('endLocation');
        const suggestionsList = document.getElementById('locationSuggestions');
        const searchSuggestions = document.getElementById('searchSuggestions');
        const clearButton = document.getElementById('clearButton');
        const searchLoading = document.getElementById('searchLoading');
        
        if (destinationInput && suggestionsList && searchSuggestions && clearButton && searchLoading) {
            let autocompleteService = null;
            let placesService = null;
            let currentSuggestions = [];
            let selectedIndex = -1;
            let searchTimeout = null;
            
            // Initialize Google Places services when available
            const initializePlacesServices = () => {
                if (window.google && window.google.maps && window.google.maps.places) {
                    try {
                        autocompleteService = new google.maps.places.AutocompleteService();
                        placesService = new google.maps.places.PlacesService(document.createElement('div'));
                        console.log('Google Places services initialized successfully');
                    } catch (error) {
                        console.warn('Failed to initialize Google Places services:', error);
                    }
                }
            };
            
            // Try to initialize immediately
            initializePlacesServices();
            
            // Also try after a delay in case Google Maps is still loading
            setTimeout(initializePlacesServices, 1000);
            
            // Show/hide clear button based on input content
            const updateClearButton = () => {
                if (destinationInput.value.trim()) {
                    clearButton.style.display = 'flex';
                } else {
                    clearButton.style.display = 'none';
                }
            };
            
            // Clear input and hide suggestions
            const clearInput = () => {
                destinationInput.value = '';
                searchSuggestions.style.display = 'none';
                updateClearButton();
                destinationInput.focus();
            };
            
            // Show loading state
            const showLoading = () => {
                searchLoading.style.display = 'flex';
                clearButton.style.display = 'none';
            };
            
            // Hide loading state
            const hideLoading = () => {
                searchLoading.style.display = 'none';
                updateClearButton();
            };
            
            // Display suggestions in custom dropdown
            const displaySuggestions = (predictions) => {
                searchSuggestions.innerHTML = '';
                currentSuggestions = predictions || [];
                selectedIndex = -1;
                
                if (currentSuggestions.length === 0) {
                    searchSuggestions.style.display = 'none';
                    return;
                }
                
                currentSuggestions.forEach((prediction, index) => {
                    const suggestion = document.createElement('div');
                    suggestion.className = 'search-suggestion';
                    suggestion.setAttribute('data-index', index);
                    
                    const icon = document.createElement('span');
                    icon.className = 'search-suggestion-icon';
                    icon.textContent = '📍';
                    
                    const text = document.createElement('div');
                    text.className = 'search-suggestion-text';
                    text.textContent = prediction.description;
                    
                    suggestion.appendChild(icon);
                    suggestion.appendChild(text);
                    
                    // Add click handler
                    suggestion.addEventListener('click', () => {
                        this.selectSuggestion(prediction);
                    });
                    
                    // Add hover effects
                    suggestion.addEventListener('mouseenter', () => {
                        this.highlightSuggestion(index);
                    });
                    
                    searchSuggestions.appendChild(suggestion);
                });
                
                searchSuggestions.style.display = 'block';
            };
            
            // Highlight suggestion
            this.highlightSuggestion = (index) => {
                const suggestions = searchSuggestions.querySelectorAll('.search-suggestion');
                suggestions.forEach((suggestion, i) => {
                    suggestion.classList.toggle('selected', i === index);
                });
                selectedIndex = index;
            };
            
            // Select suggestion
            this.selectSuggestion = (prediction) => {
                destinationInput.value = prediction.description;
                searchSuggestions.style.display = 'none';
                updateClearButton();
                
                // Trigger search
                this.testDirections();
            };
            
            // Handle input with debouncing
            destinationInput.addEventListener('input', (event) => {
                const query = event.target.value.trim();
                updateClearButton();
                
                // Clear previous timeout
                if (searchTimeout) {
                    clearTimeout(searchTimeout);
                }
                
                if (query.length < 2) {
                    searchSuggestions.style.display = 'none';
                    return;
                }
                
                // Show loading state
                showLoading();
                
                // Debounce search
                searchTimeout = setTimeout(() => {
                    // Try to initialize services if not already done
                    if (!autocompleteService) {
                        initializePlacesServices();
                    }
                    
                    if (autocompleteService) {
                        autocompleteService.getPlacePredictions({
                            input: query,
                            types: ['geocode', 'establishment']
                        }, (predictions, status) => {
                            hideLoading();
                            if (status === google.maps.places.PlacesServiceStatus.OK && predictions) {
                                displaySuggestions(predictions.slice(0, 5));
                            } else {
                                searchSuggestions.style.display = 'none';
                            }
                        });
                    } else {
                        hideLoading();
                        // Fallback: show basic suggestions if Places API not available
                        this.showBasicSuggestions(query, searchSuggestions);
                    }
                }, 300); // 300ms debounce
            });
            
            // Handle keyboard navigation
            destinationInput.addEventListener('keydown', (event) => {
                if (searchSuggestions.style.display === 'none') return;
                
                switch (event.key) {
                    case 'ArrowDown':
                        event.preventDefault();
                        if (selectedIndex < currentSuggestions.length - 1) {
                            this.highlightSuggestion(selectedIndex + 1);
                        }
                        break;
                    case 'ArrowUp':
                        event.preventDefault();
                        if (selectedIndex > 0) {
                            this.highlightSuggestion(selectedIndex - 1);
                        }
                        break;
                    case 'Enter':
                        event.preventDefault();
                        if (selectedIndex >= 0 && currentSuggestions[selectedIndex]) {
                            this.selectSuggestion(currentSuggestions[selectedIndex]);
                        } else {
                            this.testDirections();
                        }
                        break;
                    case 'Escape':
                        searchSuggestions.style.display = 'none';
                        selectedIndex = -1;
                        break;
                }
            });
            
            // Clear button functionality
            clearButton.addEventListener('click', (event) => {
                event.preventDefault();
                clearInput();
            });
            
            // Hide suggestions when clicking outside
            document.addEventListener('click', (event) => {
                if (!event.target.closest('.search-overlay')) {
                    searchSuggestions.style.display = 'none';
                    selectedIndex = -1;
                }
            });
            
            // Handle selection from autocomplete (fallback)
            destinationInput.addEventListener('change', (event) => {
                const selectedValue = event.target.value;
                if (selectedValue) {
                    searchSuggestions.style.display = 'none';
                }
            });
        }
    }
    
    showBasicSuggestions(query, searchSuggestions) {
        // Basic fallback suggestions when Places API is not available
        const basicSuggestions = [
            `${query}, New York, NY`,
            `${query}, Los Angeles, CA`,
            `${query}, Chicago, IL`,
            `${query}, Houston, TX`,
            `${query}, Phoenix, AZ`
        ];
        
        searchSuggestions.innerHTML = '';
        
        basicSuggestions.forEach((suggestion, index) => {
            const suggestionElement = document.createElement('div');
            suggestionElement.className = 'search-suggestion';
            suggestionElement.setAttribute('data-index', index);
            
            const icon = document.createElement('span');
            icon.className = 'search-suggestion-icon';
            icon.textContent = '📍';
            
            const text = document.createElement('div');
            text.className = 'search-suggestion-text';
            text.textContent = suggestion;
            
            suggestionElement.appendChild(icon);
            suggestionElement.appendChild(text);
            
            // Add click handler
            suggestionElement.addEventListener('click', () => {
                const destinationInput = document.getElementById('endLocation');
                destinationInput.value = suggestion;
                searchSuggestions.style.display = 'none';
                this.testDirections();
            });
            
            // Add hover effects
            suggestionElement.addEventListener('mouseenter', () => {
                this.highlightSuggestion(index);
            });
            
            searchSuggestions.appendChild(suggestionElement);
        });
        
        searchSuggestions.style.display = 'block';
    }

    dispatchEvent(eventName, data = {}) {
        const event = new CustomEvent(eventName, { detail: data });
        document.dispatchEvent(event);
    }
}

export default TestControlPanel;
