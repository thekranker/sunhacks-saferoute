class AIAnalysisService {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5001';
    }

    /**
     * Analyze route safety using AI
     * @param {string} origin - Starting address
     * @param {string} destination - Destination address
     * @param {Object} routeDetails - Additional route information
     * @returns {Promise<Object>} AI analysis results
     */
    async analyzeRouteSafety(origin, destination, routeDetails = {}) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/analyze-route`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    origin: origin,
                    destination: destination,
                    route_details: routeDetails
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('AI Analysis Service Error:', error);
            return {
                success: false,
                error: `Failed to analyze route: ${error.message}`,
                analysis: {
                    safety_score: 50,
                    safety_breakdown: {
                        lighting: "Analysis failed",
                        crime_rate: "Analysis failed",
                        pedestrian_infrastructure: "Analysis failed",
                        traffic_safety: "Analysis failed"
                    },
                    concerns: ["Unable to connect to AI analysis service"],
                    recommendations: ["Use caution and stay aware of surroundings"],
                    time_considerations: "Avoid walking alone at night",
                    alternative_suggestions: [],
                    sources: []
                }
            };
        }
    }

    /**
     * Check if the AI analysis service is available
     * @returns {Promise<boolean>} Service availability
     */
    async checkServiceHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            return response.ok;
        } catch (error) {
            console.warn('AI Analysis Service not available:', error);
            return false;
        }
    }

    /**
     * Format AI analysis for display
     * @param {Object} analysis - AI analysis results
     * @returns {string} Formatted HTML for display
     */
    formatAnalysisForDisplay(analysis) {
        if (!analysis || !analysis.success) {
            return `
                <div class="ai-analysis-error">
                    <h4>⚠️ AI Analysis Unavailable</h4>
                    <p>Unable to get AI safety analysis. Using standard safety scoring.</p>
                </div>
            `;
        }

        const data = analysis.analysis;
        const safetyScore = data.safety_score || 0;
        const safetyColor = this.getSafetyColor(safetyScore);

        return `
            <div class="ai-analysis-results">
                <div class="ai-analysis-header">
                    <h4>🤖 AI Safety Analysis</h4>
                    <div class="safety-score-display" style="background-color: ${safetyColor}">
                        ${safetyScore}% Safety Score
                    </div>
                </div>
                
                <div class="safety-breakdown">
                    <h5>Safety Breakdown:</h5>
                    <ul>
                        <li><strong>Lighting:</strong> ${data.safety_breakdown?.lighting || 'Not analyzed'}</li>
                        <li><strong>Crime Rate:</strong> ${data.safety_breakdown?.crime_rate || 'Not analyzed'}</li>
                        <li><strong>Pedestrian Infrastructure:</strong> ${data.safety_breakdown?.pedestrian_infrastructure || 'Not analyzed'}</li>
                        <li><strong>Traffic Safety:</strong> ${data.safety_breakdown?.traffic_safety || 'Not analyzed'}</li>
                    </ul>
                </div>

                ${data.concerns && data.concerns.length > 0 ? `
                    <div class="safety-concerns">
                        <h5>⚠️ Safety Concerns:</h5>
                        <ul>
                            ${data.concerns.map(concern => `<li>${concern}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${data.recommendations && data.recommendations.length > 0 ? `
                    <div class="safety-recommendations">
                        <h5>💡 Recommendations:</h5>
                        <ul>
                            ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${data.time_considerations ? `
                    <div class="time-considerations">
                        <h5>🕐 Time Considerations:</h5>
                        <p>${data.time_considerations}</p>
                    </div>
                ` : ''}

                ${data.alternative_suggestions && data.alternative_suggestions.length > 0 ? `
                    <div class="alternative-suggestions">
                        <h5>🛣️ Alternative Suggestions:</h5>
                        <ul>
                            ${data.alternative_suggestions.map(alt => `<li>${alt}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${data.sources && data.sources.length > 0 ? `
                    <div class="analysis-sources">
                        <h5>📚 Sources:</h5>
                        <ul>
                            ${data.sources.map(source => `<li>${source}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Get safety color based on score
     * @param {number} score - Safety score (0-100)
     * @returns {string} Color hex code
     */
    getSafetyColor(score) {
        if (score >= 90) return '#4CAF50'; // Green
        if (score >= 75) return '#FFC107'; // Yellow/Amber
        if (score >= 50) return '#FF9800'; // Orange
        return '#F44336'; // Red
    }
}

export default AIAnalysisService;
