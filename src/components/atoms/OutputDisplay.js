class OutputDisplay {
    constructor(containerId) {
        this.containerId = containerId;
        this.element = document.getElementById(containerId);
    }

    updateOutput(message) {
        if (this.element) {
            const timestamp = new Date().toLocaleTimeString();
            this.element.innerHTML += `<p>[${timestamp}] ${message}</p>`;
            this.element.scrollTop = this.element.scrollHeight;
        }
    }

    updateOutputFormatted(message, isBreakdown = false) {
        if (this.element) {
            const timestamp = new Date().toLocaleTimeString();
            if (isBreakdown) {
                // Format breakdown data as a more readable list
                const breakdownData = JSON.parse(message);
                let formattedBreakdown = '<div style="margin-left: 20px; background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 5px;">';
                formattedBreakdown += '<strong>Safety Breakdown:</strong><br>';
                for (const [incident, count] of Object.entries(breakdownData)) {
                    formattedBreakdown += `• ${incident}: ${count} incident(s)<br>`;
                }
                formattedBreakdown += '</div>';
                this.element.innerHTML += `<p>[${timestamp}] ${formattedBreakdown}</p>`;
            } else {
                this.element.innerHTML += `<p>[${timestamp}] ${message}</p>`;
            }
            this.element.scrollTop = this.element.scrollHeight;
        }
    }

    clear() {
        if (this.element) {
            this.element.innerHTML = '';
        }
    }

    getElement() {
        return this.element;
    }
}

export default OutputDisplay;
