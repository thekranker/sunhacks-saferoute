# SafeRoute AI Analysis Service

This service provides AI-powered route safety analysis using Google's Gemini API.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in this directory:

```bash
GOOGLE_API_KEY=your-google-api-key-here
```

Or set the environment variable directly:

```bash
export GOOGLE_API_KEY='your-google-api-key-here'
```

### 3. Start the Server

```bash
python start_server.py
```

Or run directly:

```bash
python app.py
```

The server will start on `http://localhost:5002`

## API Endpoints

### POST /analyze-route

Analyze the safety of a walking route.

**Request Body:**
```json
{
    "origin": "704 S Myrtle Ave, Tempe, AZ 85281",
    "destination": "Vista Del Sol B, 701 E Apache Blvd, Tempe, AZ 85281",
    "route_details": {
        "distance": "1.2 mi",
        "duration": "15 min",
        "summary": "Route via University Dr"
    }
}
```

**Response:**
```json
{
    "success": true,
    "analysis": {
        "safety_score": 85,
        "safety_breakdown": {
            "lighting": "Good street lighting along main roads",
            "crime_rate": "Low crime area with regular patrols",
            "pedestrian_infrastructure": "Well-maintained sidewalks",
            "traffic_safety": "Moderate traffic, crosswalks available"
        },
        "concerns": ["Some areas with limited lighting"],
        "recommendations": ["Walk during daylight hours", "Stay on main roads"],
        "time_considerations": "Avoid walking after 10 PM",
        "alternative_suggestions": ["Consider University Dr route"],
        "sources": ["Local crime statistics", "Street lighting data"]
    }
}
```

### GET /health

Check if the service is running.

**Response:**
```json
{
    "status": "healthy",
    "service": "SafeRoute AI Analysis API"
}
```

## Usage with Frontend

The frontend will automatically connect to this service when a route is selected. The AI analysis will be displayed in the output panel with detailed safety information.

## Troubleshooting

1. **API Key Issues**: Make sure your Google API key is valid and has access to the Gemini API
2. **Connection Issues**: Ensure the server is running on port 5002
3. **CORS Issues**: The server includes CORS headers to allow frontend connections

## Development

To run in development mode:

```bash
python app.py
```

The server will run with debug mode enabled and auto-reload on changes.
