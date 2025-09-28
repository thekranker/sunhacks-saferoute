from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from gemini_api import analyze_route_safety

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/analyze-route', methods=['POST'])
def analyze_route():
    """
    Analyze the safety of a walking route using Gemini AI.
    
    Expected JSON payload:
    {
        "origin": "starting address",
        "destination": "destination address", 
        "route_details": {
            "distance": "route distance",
            "duration": "route duration",
            "summary": "route summary"
        }
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Extract required fields
        origin = data.get('origin')
        destination = data.get('destination')
        route_details = data.get('route_details', {})
        
        if not origin or not destination:
            return jsonify({
                "success": False,
                "error": "Both origin and destination are required"
            }), 400
        
        # Analyze the route using Gemini
        result = analyze_route_safety(origin, destination, route_details)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "analysis": result["analysis"],
                "raw_response": result.get("raw_response", "")
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Analysis failed"),
                "analysis": result.get("analysis", {})
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return jsonify({
        "status": "healthy",
        "service": "SafeRoute AI Analysis API"
    })

@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint with API information.
    """
    return jsonify({
        "message": "SafeRoute AI Analysis API",
        "endpoints": {
            "POST /analyze-route": "Analyze route safety",
            "GET /health": "Health check",
            "GET /": "This information"
        }
    })

if __name__ == '__main__':
    print("Starting SafeRoute AI Analysis API...")
    print("Available endpoints:")
    print("  POST /analyze-route - Analyze route safety")
    print("  GET /health - Health check")
    print("  GET / - API information")
    app.run(debug=True, host='0.0.0.0', port=5001)
