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
                }),
                signal: AbortSignal.timeout(10000) // 10 second timeout
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
                    main_concerns: ["Unable to connect to AI analysis service"],
                    quick_tips: ["Use caution and stay aware of surroundings"]
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
                
                ${data.main_concerns && data.main_concerns.length > 0 ? `
                    <div class="safety-concerns">
                        <h5>⚠️ Main Concerns:</h5>
                        <ul>
                            ${data.main_concerns.map(concern => `<li>${concern}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${data.quick_tips && data.quick_tips.length > 0 ? `
                    <div class="safety-recommendations">
                        <h5>💡 Quick Tips:</h5>
                        <ul>
                            ${data.quick_tips.map(tip => `<li>${tip}</li>`).join('')}
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
