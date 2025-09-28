class RouteSelector {
    constructor(containerId) {
        this.containerId = containerId;
        this.element = document.getElementById(containerId);
        this.routes = [];
        this.selectedRouteIndex = 0;
        this.onRouteSelect = null;
        this.sidebarContentElement = document.getElementById('saferouteRoutesContent');
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
        if (!this.sidebarContentElement || this.routes.length === 0) {
            return;
        }

        // Clear existing content
        this.sidebarContentElement.innerHTML = '';

        // Create header
        const header = document.createElement('h3');
        header.textContent = `Available Routes (${this.routes.length})`;
        header.className = 'route-selector-header';
        this.sidebarContentElement.appendChild(header);

        // Create route options
        this.routes.forEach((routeData, index) => {
            const routeOption = this.createRouteOption(routeData, index);
            this.sidebarContentElement.appendChild(routeOption);
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
        
        // Create weighted score display
        const weightedScoreDisplay = this.createWeightedScoreDisplay(routeData);
        
        details.innerHTML = `
            <div class="safety-score-section">
                <div class="overall-safety-score">Overall: ${(routeData.safetyScore * 100).toFixed(1)}%</div>
                ${weightedScoreDisplay}
            </div>
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
        const options = this.sidebarContentElement.querySelectorAll('.route-option');
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

    createWeightedScoreDisplay(routeData) {
        // Check if we have the new weighted score data
        if (routeData.crimeScore !== undefined && routeData.streetviewScore !== undefined && routeData.aiScore !== undefined) {
            return `
                <div class="weighted-scores">
                    <span class="score-item crime-score">Crime: ${(routeData.crimeScore * 100).toFixed(0)}%</span>
                    <span class="score-item streetview-score">Streetview: ${(routeData.streetviewScore * 100).toFixed(0)}%</span>
                    <span class="score-item ai-score">AI Search: ${(routeData.aiScore * 100).toFixed(0)}%</span>
                </div>
            `;
        } else {
            // Fallback to old format if weighted scores not available
            return `<div class="safety-score">Safety: ${(routeData.safetyScore * 100).toFixed(1)}%</div>`;
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
            const hasStreetview = streetviewAnalysis && streetviewAnalysis.available && streetviewAnalysis.safety_score !== "N/A" && streetviewAnalysis.safety_score !== null;
            
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

    createLogosFooter() {
        const logosFooter = document.createElement('div');
        logosFooter.className = 'saferoute-logos-footer';
        
        logosFooter.innerHTML = `
            <div class="logos-container">
                <a href="https://github.com/thekranker/sunhacks-saferoute" target="_blank" rel="noopener noreferrer" class="logo-link" title="GitHub Repository">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="https://ai.google.dev/gemini-api/docs" target="_blank" rel="noopener noreferrer" class="logo-link" title="Google Gemini AI">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                </a>
                <a href="https://developers.google.com/maps" target="_blank" rel="noopener noreferrer" class="logo-link" title="Google Maps API">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                    </svg>
                </a>
                <a href="https://cloud.google.com/vertex-ai" target="_blank" rel="noopener noreferrer" class="logo-link" title="Google Cloud AI">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                </a>
            </div>
        `;
        
        return logosFooter;
    }

    getSelectedRoute() {
        return this.routes[this.selectedRouteIndex] || null;
    }

    getSelectedRouteIndex() {
        return this.selectedRouteIndex;
    }

    show() {
        if (this.sidebarContentElement) {
            // Remove loading state
            this.sidebarContentElement.classList.remove('loading');
            this.sidebarContentElement.classList.add('show');
            
            // Add staggered animation to route options
            setTimeout(() => {
                const routeOptions = this.sidebarContentElement.querySelectorAll('.route-option');
                routeOptions.forEach((option, index) => {
                    setTimeout(() => {
                        option.classList.add('animate-in');
                    }, index * 100); // Stagger each option by 100ms
                });
            }, 200); // Wait for the main content to appear first
        }
    }

    hide() {
        if (this.sidebarContentElement) {
            // Remove animation classes first
            const routeOptions = this.sidebarContentElement.querySelectorAll('.route-option');
            routeOptions.forEach(option => {
                option.classList.remove('animate-in');
            });
            
            // Then hide the content
            this.sidebarContentElement.classList.remove('show');
        }
    }
}

export default RouteSelector;
