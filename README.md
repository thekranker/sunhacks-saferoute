# SafeRoute - Component-Based Architecture

This project has been reorganized into a component-based architecture following atomic design principles.

## Project Structure

```
/
├── main.html (updated template)
├── src/
│   ├── main.js (entry point)
│   ├── styles/
│   │   └── main.css (updated styles)
│   ├── components/
│   │   ├── atoms/
│   │   │   ├── MapComponent.js
│   │   │   ├── LocationInput.js
│   │   │   ├── ActionButton.js
│   │   │   └── OutputDisplay.js
│   │   ├── molecules/
│   │   │   └── TestControlPanel.js
│   │   └── organisms/
│   │       └── MainMapInterface.js
│   └── utils/
│       └── legacy-script.js (original code for reference)
```

## Component Architecture

### Atoms (Basic Building Blocks)
- **MapComponent.js**: Handles Google Maps initialization and basic map operations
- **LocationInput.js**: Manages location input fields
- **ActionButton.js**: Handles button interactions and events
- **OutputDisplay.js**: Manages output logging and display

### Molecules (Component Combinations)
- **TestControlPanel.js**: Combines input fields and buttons to create a control panel for testing geocoding and directions

### Organisms (Complex Components)
- **MainMapInterface.js**: Orchestrates the entire map interface, handling events between components

## Key Features

1. **Modular Design**: Each component has a single responsibility
2. **Event-Driven**: Components communicate through custom events
3. **Reusable**: Atomic components can be reused in different contexts
4. **Maintainable**: Clear separation of concerns makes the code easier to maintain

## Usage

1. Replace `YOUR_API_KEY` in `main.html` with your Google Maps API key
2. Open `main.html` in a web browser
3. The application will initialize automatically when the Google Maps API loads

## Migration from Legacy Code

The original functionality from `legacy-script.js` has been preserved and reorganized:
- Map initialization
- Geocoding functionality
- Directions service
- Output logging
- Clear map functionality

All features work exactly the same as before, but with better organization and maintainability.
