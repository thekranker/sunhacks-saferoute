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
