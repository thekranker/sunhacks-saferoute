class SafetyScoreService {
    constructor(edgeUrl = 'http://127.0.0.1:8081') {
        // For development, bypass the Cloudflare Worker and call backend directly
        // This avoids the 127.0.0.1 connectivity issue in the worker environment
        this.edgeUrl = edgeUrl;
    }

    async getSafetyScore(routePoints) {
        try {
            const response = await fetch(`${this.edgeUrl}/score-route`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    route_id: `route-${Date.now()}`, // Generate a unique route ID
                    points: routePoints
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching safety score:', error);
            throw error;
        }
    }

    extractRoutePointsFromDirections(directionsResult) {
        const route = directionsResult.routes[0];
        const points = [];
        
        // Extract points from the route overview path
        if (route.overview_path) {
            route.overview_path.forEach(point => {
                points.push({
                    lat: point.lat(),
                    lon: point.lng()
                });
            });
        }
        
        return points;
    }
}

export default SafetyScoreService;
