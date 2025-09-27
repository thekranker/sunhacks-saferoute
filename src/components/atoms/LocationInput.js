class LocationInput {
    constructor(inputId) {
        this.inputId = inputId;
        this.element = document.getElementById(inputId);
    }

    getValue() {
        return this.element ? this.element.value : '';
    }

    setValue(value) {
        if (this.element) {
            this.element.value = value;
        }
    }

    clear() {
        if (this.element) {
            this.element.value = '';
        }
    }

    getElement() {
        return this.element;
    }
}

export default LocationInput;
