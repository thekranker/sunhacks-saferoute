# SafeRoute 

SafeRoute is an AI-powered web app that helps users find the safest walking routes, not just the fastest ones. By combining real-world police data, AI agent analysis, and Google Street View inspection, SafeRoute empowers people to make safer choices every day.

## Functionality

SafeRoute calculates and compares safety across all possible walking routes so users can make informed decisions. 
For each route, our system generates three safety scores: 

1. One derived from the public Tempe government database of police reports
2. Another from a Gemini AI agent’s summarized safety analysis (validated through a second agent)
3. A third from a Gemini agent that inspects Google Maps Street View imagery
  
These scores are combined and displayed to the user, highlighting the safest route while still showing all available options.


## Frontend Project Structure

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

## Usage

1. Replace `YOUR_API_KEY` in `main.html` with your Google Maps API key
2. Open `main.html` in a web browser
3. The application will initialize automatically when the Google Maps API loads

# What’s next for SafeRoute 

Nationwide Expansion – Expand dataset beyond Tempe to cover the U.S.

Mobile Apps – iOS & Android versions for accessibility on the go

Emergency SOS – Quick help feature for unsafe situations

Secure Accounts – Validation with encryption & privacy safeguards

Live Safety Map – Real-time safety scores for nearby streets

