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

    updateOutputWithHTML(htmlContent) {
        if (this.element) {
            this.element.innerHTML += htmlContent;
            this.element.scrollTop = this.element.scrollHeight;
        }
    }

    displayAIAnalysis(analysis) {
        if (this.element) {
            // Add a separator and AI analysis section
            this.element.innerHTML += `
                <div class="ai-analysis-section">
                    <hr style="margin: 20px 0; border: 1px solid #ddd;">
                    ${analysis}
                </div>
            `;
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
