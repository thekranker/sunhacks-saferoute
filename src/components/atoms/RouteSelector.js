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

        // Add special styling for safest route
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
            ${routeData.isSafestRoute ? '<span class="safest-badge">🛡️ SAFEST</span>' : ''}
        `;

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
