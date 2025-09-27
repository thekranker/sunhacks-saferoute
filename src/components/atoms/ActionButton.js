class ActionButton {
    constructor(buttonId, onClickHandler) {
        this.buttonId = buttonId;
        this.element = document.getElementById(buttonId);
        this.onClickHandler = onClickHandler;
        this.bindEvents();
    }

    bindEvents() {
        if (this.element && this.onClickHandler) {
            this.element.addEventListener('click', this.onClickHandler);
        }
    }

    setEnabled(enabled) {
        if (this.element) {
            this.element.disabled = !enabled;
        }
    }

    setText(text) {
        if (this.element) {
            this.element.textContent = text;
        }
    }

    getElement() {
        return this.element;
    }
}

export default ActionButton;
