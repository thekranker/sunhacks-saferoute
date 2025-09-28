class RouteSelector {
    constructor(containerId) {
        this.containerId = containerId;
        this.element = document.getElementById(containerId);
        this.routes = [];
        this.selectedRouteIndex = 0;
        this.onRouteSelect = null;
    }

    setRoutes(routes) {
        this.routes = routes;
        this.selectedRouteIndex = 0; // Auto-select the first (safest) route
        this.render();
    }

    setOnRouteSelect(callback) {
        this.onRouteSelect = callback;
    }

    render() {
        if (!this.element || this.routes.length === 0) {
            return;
        }

        // Clear existing content
        this.element.innerHTML = '';

        // Create header
        const header = document.createElement('h3');
        header.textContent = `Available Routes (${this.routes.length})`;
        header.className = 'route-selector-header';
        this.element.appendChild(header);

        // Create route options
        this.routes.forEach((routeData, index) => {
            const routeOption = this.createRouteOption(routeData, index);
            this.element.appendChild(routeOption);
        });
    }

    createRouteOption(routeData, index) {
        const option = document.createElement('div');
        option.className = `route-option ${index === this.selectedRouteIndex ? 'selected' : ''}`;
        option.dataset.routeIndex = index;

        // Add special styling for ultra-safe route
        if (routeData.isSafestRoute) {
            option.classList.add('safest-route');
        }

        // Safety color indicator
        const safetyColor = this.getSafetyColor(routeData.safetyScore);
        const safetyIndicator = document.createElement('div');
        safetyIndicator.className = 'safety-indicator';
        safetyIndicator.style.backgroundColor = safetyColor;
        safetyIndicator.title = `Safety Score: ${(routeData.safetyScore * 100).toFixed(1)}%`;

        // Route info
        const routeInfo = document.createElement('div');
        routeInfo.className = 'route-info';

        const summary = document.createElement('div');
        summary.className = 'route-summary';
        summary.textContent = routeData.summary || `Route ${index + 1}`;

        const details = document.createElement('div');
        details.className = 'route-details';
        details.innerHTML = `
            <span class="safety-score">Safety: ${(routeData.safetyScore * 100).toFixed(1)}%</span>
            <span class="distance">${routeData.distance}</span>
            <span class="duration">${routeData.duration}</span>
            ${routeData.isSafestRoute ? '<span class="safest-badge">🛡️ ULTRA SAFE</span>' : ''}
        `;

        // Add AI analysis if available
        if (routeData.aiAnalysis) {
            const aiAnalysisDiv = this.createAIAnalysisDisplay(routeData.aiAnalysis);
            routeInfo.appendChild(aiAnalysisDiv);
        }

        routeInfo.appendChild(summary);
        routeInfo.appendChild(details);

        // Selection indicator
        const selectionIndicator = document.createElement('div');
        selectionIndicator.className = 'selection-indicator';
        if (index === this.selectedRouteIndex) {
            selectionIndicator.innerHTML = '✓';
        }

        option.appendChild(safetyIndicator);
        option.appendChild(routeInfo);
        option.appendChild(selectionIndicator);

        // Add click handler
        option.addEventListener('click', () => {
            this.selectRoute(index);
        });

        return option;
    }

    selectRoute(index) {
        if (index < 0 || index >= this.routes.length) {
            return;
        }

        // Update visual selection
        const options = this.element.querySelectorAll('.route-option');
        options.forEach((option, i) => {
            option.classList.toggle('selected', i === index);
            const indicator = option.querySelector('.selection-indicator');
            indicator.innerHTML = i === index ? '✓' : '';
        });

        this.selectedRouteIndex = index;

        // Trigger callback
        if (this.onRouteSelect) {
            this.onRouteSelect(this.routes[index], index);
        }
    }

    getSafetyColor(safetyScore) {
        const safetyPercentage = safetyScore * 100;
        
        if (safetyPercentage >= 90) {
            return '#4CAF50'; // Green
        } else if (safetyPercentage >= 75) {
            return '#FFC107'; // Yellow/Amber
        } else {
            return '#F44336'; // Red
        }
    }

    createAIAnalysisDisplay(aiAnalysis) {
        const aiDiv = document.createElement('div');
        aiDiv.className = 'route-ai-analysis';
        
        if (aiAnalysis.loading) {
            aiDiv.innerHTML = `
                <div class="ai-analysis-mini ai-analysis-loading">
                    <div class="ai-score" style="background-color: #6c757d">
                        AI: Loading...
                    </div>
                    <div class="ai-concerns">⏳ Getting AI analysis...</div>
                </div>
            `;
        } else if (aiAnalysis.success && aiAnalysis.analysis) {
            const analysis = aiAnalysis.analysis;
            const aiScore = analysis.safety_score || 0;
            const aiColor = this.getSafetyColor(aiScore / 100);
            
            // Check for streetview analysis
            const streetviewAnalysis = analysis.streetview_analysis;
            const hasStreetview = streetviewAnalysis && streetviewAnalysis.available && streetviewAnalysis.safety_score !== "N/A";
            
            let streetviewSection = '';
            if (hasStreetview) {
                const streetviewScore = streetviewAnalysis.safety_score;
                const streetviewColor = this.getSafetyColor(streetviewScore / 100);
                streetviewSection = `
                    <div class="streetview-analysis">
                        <div class="streetview-score" style="background-color: ${streetviewColor}">
                            Streetview: ${streetviewScore}%
                        </div>
                        <div class="streetview-status">
                            📸 ${streetviewAnalysis.images_analyzed}/${streetviewAnalysis.total_images} images analyzed
                        </div>
                    </div>
                `;
            } else {
                streetviewSection = `
                    <div class="streetview-analysis">
                        <div class="streetview-score" style="background-color: #6c757d">
                            Streetview: N/A
                        </div>
                        <div class="streetview-status">
                            📸 No street view images available
                        </div>
                    </div>
                `;
            }
            
            aiDiv.innerHTML = `
                <div class="ai-analysis-mini">
                    <div class="ai-score" style="background-color: ${aiColor}">
                        AI: ${aiScore}%
                    </div>
                    <div class="ai-concerns">
                        ${analysis.main_concerns && analysis.main_concerns.length > 0 ? 
                            `⚠️ ${analysis.main_concerns.slice(0, 2).join(', ')}` : ''}
                    </div>
                    <div class="ai-tips">
                        ${analysis.quick_tips && analysis.quick_tips.length > 0 ? 
                            `💡 ${analysis.quick_tips.slice(0, 2).join(', ')}` : ''}
                    </div>
                    ${streetviewSection}
                </div>
            `;
        } else {
            aiDiv.innerHTML = `
                <div class="ai-analysis-mini ai-analysis-error">
                    <div class="ai-score" style="background-color: #F44336">
                        AI: Failed
                    </div>
                    <div class="ai-concerns">⚠️ Analysis unavailable</div>
                </div>
            `;
        }
        
        return aiDiv;
    }

    getSelectedRoute() {
        return this.routes[this.selectedRouteIndex] || null;
    }

    getSelectedRouteIndex() {
        return this.selectedRouteIndex;
    }

    show() {
        if (this.element) {
            this.element.style.display = 'block';
        }
    }

    hide() {
        if (this.element) {
            this.element.style.display = 'none';
        }
    }
}

export default RouteSelector;
