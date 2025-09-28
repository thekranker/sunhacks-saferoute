from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import signal
import sys
import os
import requests
from gemini_api import analyze_route_safety
from gemini_validation_agent import validate_route_safety_with_agent, GeminiValidationAgent
from gemini_streetview_agent import analyze_streetview_safety, GeminiStreetViewAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure timeout handling
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Request timed out")

# Set up timeout for long-running requests
signal.signal(signal.SIGALRM, timeout_handler)

def geocode_address(address):
    """
    Geocode an address to get coordinates using Google Geocoding API.
    
    Args:
        address (str): Address to geocode
        
    Returns:
        dict: Coordinates and formatted address, or None if failed
    """
    try:
        # Use Google Geocoding API
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("No Google API key found for geocoding")
            return None
            
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            return {
                'lat': location['lat'],
                'lng': location['lng'],
                'formatted_address': result['formatted_address']
            }
        else:
            logger.warning(f"Geocoding failed for {address}: {data.get('status', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"Geocoding error for {address}: {str(e)}")
        return None

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
        # Set a 90-second timeout for the entire analysis process
        signal.alarm(90)
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
        
        # Step 1: Get initial analysis from Gemini API
        logger.info("=" * 80)
        logger.info("SAFEROUTE AI WORKFLOW STARTING")
        logger.info("=" * 80)
        logger.info(f"Analyzing route: {origin} → {destination}")
        
        initial_result = analyze_route_safety(origin, destination, route_details)
        
        if not initial_result["success"]:
            logger.error(f"Initial analysis failed: {initial_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": f"Initial analysis failed: {initial_result.get('error', 'Unknown error')}",
                "workflow_stage": "initial_analysis"
            }), 500
        
        logger.info("INITIAL AI ANALYSIS COMPLETED:")
        logger.info(f"  Safety Score: {initial_result['analysis']['safety_score']}%")
        logger.info(f"  Main Concerns: {initial_result['analysis']['main_concerns']}")
        logger.info(f"  Quick Tips: {initial_result['analysis']['quick_tips']}")
        
        # Step 2: Validate the analysis using the validation agent
        logger.info("Starting validation agent...")
        route_context = {
            "origin": origin,
            "destination": destination
        }
        route_context.update(route_details)
        
        validation_result = validate_route_safety_with_agent(
            initial_result["analysis"], 
            route_context
        )
        
        if not validation_result["success"]:
            logger.error(f"Validation failed: {validation_result['error']}")
            # Return original analysis if validation fails
            return jsonify({
                "success": True,
                "analysis": initial_result["analysis"],
                "validation_applied": False,
                "validation_error": validation_result["error"],
                "workflow_metadata": {
                    "workflow_stage": "validation_failed",
                    "initial_analysis_success": True
                }
            })
        
        # Step 3: Analyze street view safety (text-based analysis)
        logger.info("Starting street view analysis (text-based)...")
        
        # Geocode the origin and destination for precise coordinates
        logger.info("Geocoding addresses for precise location analysis...")
        origin_coords = geocode_address(origin)
        dest_coords = geocode_address(destination)
        
        # Create location info for streetview analysis with real coordinates
        if origin_coords and dest_coords:
            # Use midpoint coordinates for route analysis
            mid_lat = (origin_coords['lat'] + dest_coords['lat']) / 2
            mid_lng = (origin_coords['lng'] + dest_coords['lng']) / 2
            coordinates = f"{mid_lat},{mid_lng}"
            logger.info(f"Using precise coordinates: {coordinates}")
        else:
            # Fallback to address-based analysis if geocoding fails
            coordinates = f"{origin} to {destination}"
            logger.warning("Using address-based analysis (geocoding failed)")
        
        streetview_location_info = {
            "address": f"{origin} to {destination}",
            "coordinates": coordinates,
            "time_context": "day"
        }
        
        streetview_result = analyze_streetview_safety(
            None,  # Will fetch real Street View image
            streetview_location_info
        )
        
        streetview_score = None
        if streetview_result["success"]:
            streetview_score = streetview_result['safety_score']
            logger.info(f"  Street view safety score: {streetview_result['safety_score']}%")
        else:
            logger.error(f"  Street view analysis failed: {streetview_result.get('error', 'Unknown error')}")
        
        # Step 4: Create enhanced analysis with validation results
        logger.info("Creating enhanced analysis with validation results...")
        
        # Get validation data
        validation_data = validation_result["validation_analysis"]
        final_score = validation_result["final_score"]
        adjustment = validation_result["adjustment"]
        
        enhanced_analysis = {
            "safety_score": final_score,
            "main_concerns": initial_result["analysis"]["main_concerns"],
            "quick_tips": initial_result["analysis"]["quick_tips"],
            "validation_metadata": {
                "original_score": initial_result["analysis"]["safety_score"],
                "score_adjustment": adjustment,
                "confidence_level": validation_data.get("confidence_level", "medium"),
                "validation_notes": validation_data.get("validation_notes", ""),
                "reasoning": validation_data.get("reasoning", "")
            },
            "streetview_analysis": {
                "available": streetview_result.get("success", False),
                "safety_score": streetview_score if streetview_score else "N/A",
                "images_analyzed": 1 if streetview_result.get("success", False) else 0,
                "total_images": 1,
                "status": f"Text-based analysis completed" if streetview_result.get("success", False) else "Text-based analysis failed",
                "detailed_results": [streetview_result] if streetview_result.get("success", False) else []
            }
        }
        
        # Add any additional concerns or tips from validation
        if validation_data.get("additional_concerns"):
            enhanced_analysis["main_concerns"].extend(validation_data["additional_concerns"])
        
        if validation_data.get("additional_tips"):
            enhanced_analysis["quick_tips"].extend(validation_data["additional_tips"])
        
        logger.info("=" * 80)
        logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Original Score: {initial_result['analysis']['safety_score']}%")
        logger.info(f"Validation Adjustment: {adjustment:+d} points")
        logger.info(f"Final Score: {final_score}%")
        logger.info("=" * 80)
        
        signal.alarm(0)  # Cancel timeout
        return jsonify({
            "success": True,
            "analysis": enhanced_analysis,
            "validation_applied": True,
            "workflow_metadata": {
                "workflow_stage": "completed",
                "initial_analysis_success": True,
                "validation_success": True,
                "score_adjustment": adjustment,
                "confidence_level": validation_data.get("confidence_level", "medium")
            },
            "raw_responses": {
                "initial_analysis": initial_result["raw_response"],
                "validation_response": validation_result.get("validation_response", "")
            }
        })
            
    except TimeoutException:
        signal.alarm(0)  # Cancel timeout
        return jsonify({
            "success": False,
            "error": "AI analysis timed out after 90 seconds. Please try again.",
            "workflow_stage": "timeout"
        }), 408
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
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
        "service": "SafeRoute Agentic AI Analysis API"
    })

@app.route('/validate-analysis', methods=['POST'])
def validate_analysis():
    """
    Manually validate an existing safety analysis.
    
    Expected JSON payload:
    {
        "analysis": {
            "safety_score": 75,
            "main_concerns": ["Poor lighting"],
            "quick_tips": ["Stay alert"]
        },
        "route_context": {
            "origin": "starting address",
            "destination": "destination address",
            "distance": "route distance"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        analysis = data.get('analysis')
        route_context = data.get('route_context', {})
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis data is required"
            }), 400
        
        # Validate the analysis
        result = validate_route_safety_with_agent(analysis, route_context)
        
        if result["success"]:
            validation_data = result["validation_analysis"]
            return jsonify({
                "success": True,
                "validation_result": result,
                "updated_analysis": {
                    "safety_score": result["final_score"],
                    "main_concerns": analysis.get("main_concerns", []),
                    "quick_tips": analysis.get("quick_tips", []),
                    "validation_metadata": {
                        "original_score": analysis.get("safety_score", 0),
                        "score_adjustment": result["adjustment"],
                        "confidence_level": validation_data.get("confidence_level", "medium"),
                        "validation_notes": validation_data.get("validation_notes", ""),
                        "reasoning": validation_data.get("reasoning", "")
                    }
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Validation failed")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/analyze-route-with-streetview', methods=['POST'])
def analyze_route_with_streetview():
    """
    Analyze route safety with integrated street view analysis.
    
    Expected JSON payload:
    {
        "origin": "starting address",
        "destination": "destination address",
        "route_details": {
            "distance": "route distance",
            "duration": "route duration",
            "summary": "route summary"
        },
        "streetview_images": [
            {
                "image_data": "base64_encoded_image_data",
                "location_info": {
                    "address": "street address",
                    "coordinates": "lat,lng",
                    "time_context": "day/night/unknown"
                }
            }
        ]
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
        streetview_images = data.get('streetview_images', [])
        
        if not origin or not destination:
            return jsonify({
                "success": False,
                "error": "Both origin and destination are required"
            }), 400
        
        # Step 1: Get initial analysis from Gemini API
        logger.info("=" * 80)
        logger.info("SAFEROUTE AI WORKFLOW WITH STREET VIEW STARTING")
        logger.info("=" * 80)
        logger.info(f"Analyzing route: {origin} → {destination}")
        logger.info(f"Street view images provided: {len(streetview_images)}")
        
        initial_result = analyze_route_safety(origin, destination, route_details)
        
        if not initial_result["success"]:
            logger.error(f"Initial analysis failed: {initial_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": f"Initial analysis failed: {initial_result.get('error', 'Unknown error')}",
                "workflow_stage": "initial_analysis"
            }), 500
        
        logger.info("INITIAL AI ANALYSIS COMPLETED:")
        logger.info(f"  Safety Score: {initial_result['analysis']['safety_score']}%")
        logger.info(f"  Main Concerns: {initial_result['analysis']['main_concerns']}")
        logger.info(f"  Quick Tips: {initial_result['analysis']['quick_tips']}")
        
        # Step 2: Validate the analysis using the validation agent
        logger.info("Starting validation agent...")
        route_context = {
            "origin": origin,
            "destination": destination
        }
        route_context.update(route_details)
        
        validation_result = validate_route_safety_with_agent(
            initial_result["analysis"], 
            route_context
        )
        
        if not validation_result["success"]:
            logger.error(f"Validation failed: {validation_result['error']}")
            # Return original analysis if validation fails
            return jsonify({
                "success": True,
                "analysis": initial_result["analysis"],
                "validation_applied": False,
                "validation_error": validation_result["error"],
                "workflow_metadata": {
                    "workflow_stage": "validation_failed",
                    "initial_analysis_success": True
                }
            })
        
        # Step 3: Analyze street view safety (text-based analysis)
        streetview_results = []
        streetview_scores = []
        
        logger.info("Starting street view analysis (text-based)...")
        
        # Create location info for streetview analysis
        streetview_location_info = {
            "address": f"{origin} to {destination}",
            "coordinates": "route_coordinates",
            "time_context": "day"
        }
        
        streetview_result = analyze_streetview_safety(
            None,  # Will fetch real Street View image
            streetview_location_info
        )
        
        if streetview_result["success"]:
            streetview_results.append(streetview_result)
            streetview_scores.append(streetview_result['safety_score'])
            logger.info(f"  Street view safety score: {streetview_result['safety_score']}%")
        else:
            logger.error(f"  Street view analysis failed: {streetview_result.get('error', 'Unknown error')}")
        
        # Also analyze individual street view images if provided
        if streetview_images:
            logger.info(f"Analyzing {len(streetview_images)} additional street view images...")
            for i, streetview_data in enumerate(streetview_images):
                logger.info(f"Analyzing street view image {i+1}/{len(streetview_images)}")
                
                streetview_result = analyze_streetview_safety(
                    streetview_data.get('image_data'),
                    streetview_data.get('location_info', {})
                )
                
                if streetview_result["success"]:
                    streetview_results.append(streetview_result)
                    streetview_scores.append(streetview_result['safety_score'])
                    logger.info(f"  Street view {i+1} safety score: {streetview_result['safety_score']}%")
                else:
                    logger.error(f"  Street view {i+1} analysis failed: {streetview_result.get('error', 'Unknown error')}")
        
        # Step 4: Create enhanced analysis with all results
        logger.info("Creating enhanced analysis with all results...")
        
        # Get validation data
        validation_data = validation_result["validation_analysis"]
        final_score = validation_result["final_score"]
        adjustment = validation_result["adjustment"]
        
        # Calculate average street view score if available
        avg_streetview_score = None
        if streetview_scores:
            avg_streetview_score = round(sum(streetview_scores) / len(streetview_scores), 1)
        
        enhanced_analysis = {
            "safety_score": final_score,
            "main_concerns": initial_result["analysis"]["main_concerns"],
            "quick_tips": initial_result["analysis"]["quick_tips"],
            "validation_metadata": {
                "original_score": initial_result["analysis"]["safety_score"],
                "score_adjustment": adjustment,
                "confidence_level": validation_data.get("confidence_level", "medium"),
                "validation_notes": validation_data.get("validation_notes", ""),
                "reasoning": validation_data.get("reasoning", "")
            },
            "streetview_analysis": {
                "available": len(streetview_results) > 0,
                "safety_score": avg_streetview_score if avg_streetview_score else "N/A",
                "images_analyzed": len(streetview_results),
                "total_images": len(streetview_images),
                "detailed_results": streetview_results,
                "status": f"Analyzed {len(streetview_results)}/{len(streetview_images)} street view images" if streetview_images else "No street view images provided"
            }
        }
        
        # Add any additional concerns or tips from validation
        if validation_data.get("additional_concerns"):
            enhanced_analysis["main_concerns"].extend(validation_data["additional_concerns"])
        
        if validation_data.get("additional_tips"):
            enhanced_analysis["quick_tips"].extend(validation_data["additional_tips"])
        
        logger.info("=" * 80)
        logger.info("WORKFLOW WITH STREET VIEW COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Original Score: {initial_result['analysis']['safety_score']}%")
        logger.info(f"Validation Adjustment: {adjustment:+d} points")
        logger.info(f"Final Score: {final_score}%")
        if avg_streetview_score:
            logger.info(f"Average Street View Score: {avg_streetview_score}%")
        logger.info("=" * 80)
        
        return jsonify({
            "success": True,
            "analysis": enhanced_analysis,
            "validation_applied": True,
            "streetview_applied": len(streetview_results) > 0,
            "workflow_metadata": {
                "workflow_stage": "completed",
                "initial_analysis_success": True,
                "validation_success": True,
                "streetview_success": len(streetview_results) > 0,
                "score_adjustment": adjustment,
                "confidence_level": validation_data.get("confidence_level", "medium"),
                "streetview_images_processed": len(streetview_results)
            },
            "raw_responses": {
                "initial_analysis": initial_result["raw_response"],
                "validation_response": validation_result.get("validation_response", ""),
                "streetview_responses": [r.get("raw_analysis", {}) for r in streetview_results]
            }
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/analyze-streetview', methods=['POST'])
def analyze_streetview():
    """
    Analyze street view images for safety indicators.
    
    Expected JSON payload:
    {
        "image_data": "base64_encoded_image_data",
        "location_info": {
            "address": "street address",
            "coordinates": "lat,lng",
            "time_context": "day/night/unknown"
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
        image_data = data.get('image_data')
        location_info = data.get('location_info', {})
        
        if not image_data:
            return jsonify({
                "success": False,
                "error": "Image data is required"
            }), 400
        
        # Analyze street view image
        logger.info("=" * 80)
        logger.info("STREET VIEW ANALYSIS STARTING")
        logger.info("=" * 80)
        logger.info(f"Location: {location_info.get('address', 'Unknown')}")
        
        result = analyze_streetview_safety(image_data, location_info)
        
        if not result["success"]:
            logger.error(f"Street view analysis failed: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": f"Street view analysis failed: {result.get('error', 'Unknown error')}"
            }), 500
        
        logger.info("STREET VIEW ANALYSIS COMPLETED:")
        logger.info(f"  Safety Score: {result['safety_score']}%")
        logger.info(f"  Confidence: {result['confidence_level']}")
        logger.info(f"  Key Concerns: {result['key_concerns']}")
        
        return jsonify({
            "success": True,
            "analysis": {
                "safety_score": result['safety_score'],
                "metric_breakdown": result['metric_breakdown'],
                "detailed_observations": result['detailed_observations'],
                "key_concerns": result['key_concerns'],
                "positive_factors": result['positive_factors'],
                "recommendations": result['recommendations'],
                "confidence_level": result['confidence_level'],
                "time_context": result['time_context'],
                "image_quality": result['image_quality']
            },
            "metadata": {
                "analysis_timestamp": result['analysis_timestamp'],
                "location_info": result['location_info']
            }
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/workflow-stats', methods=['GET'])
def get_workflow_stats():
    """
    Get validation agent statistics.
    """
    try:
        return jsonify({
            "success": True,
            "workflow_stats": {
                "description": "AI-powered route safety analysis with validation and street view analysis",
                "agents": ["Gemini Analysis Agent", "Gemini Validation Agent", "Gemini Street View Agent"],
                "features": [
                    "Initial AI safety analysis",
                    "AI-powered validation of results", 
                    "Automatic score adjustment based on validation",
                    "Street view image analysis for visual safety indicators",
                    "Comprehensive logging of all AI processes",
                    "Score adjustment range: ±15 points"
                ]
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get workflow stats: {str(e)}"
        }), 500

@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint with API information.
    """
    return jsonify({
        "message": "SafeRoute AI Analysis API with Validation and Street View Analysis",
        "endpoints": {
            "POST /analyze-route": "Analyze route safety with integrated validation",
            "POST /analyze-route-with-streetview": "Analyze route safety with integrated street view analysis",
            "POST /analyze-streetview": "Analyze street view images for safety indicators",
            "POST /validate-analysis": "Manually validate an existing safety analysis",
            "GET /health": "Health check",
            "GET /workflow-stats": "Get validation statistics",
            "GET /": "This information"
        },
        "workflow": {
            "description": "Enhanced AI Analysis with Validation and Street View: Initial Analysis → AI Validation → Score Adjustment → Street View Analysis",
            "agents": ["Gemini Analysis Agent", "Gemini Validation Agent", "Gemini Street View Agent"],
            "features": [
                "Initial AI safety analysis",
                "AI-powered validation of results", 
                "Automatic score adjustment based on validation",
                "Street view image analysis for visual safety indicators",
                "Confidence scoring and validation notes",
                "Historical tracking of validations",
                "Enhanced safety recommendations"
            ],
            "validation_features": [
                "Accuracy validation of AI-generated safety scores",
                "Confidence-based score adjustments (-20 to +20 range)",
                "Validation notes and feedback",
                "Additional safety concerns and tips from validation",
                "Historical validation tracking and statistics"
            ],
            "streetview_features": [
                "Visual analysis of street view images",
                "7 comprehensive safety metrics (exposure, infrastructure, crime markers, etc.)",
                "Weighted scoring system for accurate safety assessment",
                "Detailed observations and recommendations",
                "Time context and image quality assessment"
            ]
        }
    })

if __name__ == '__main__':
    print("Starting SafeRoute AI Analysis API with Validation and Street View Analysis...")
    print("Available endpoints:")
    print("  POST /analyze-route - Analyze route safety with integrated validation")
    print("  POST /analyze-route-with-streetview - Analyze route safety with integrated street view analysis")
    print("  POST /analyze-streetview - Analyze street view images for safety indicators")
    print("  POST /validate-analysis - Manually validate an existing analysis")
    print("  GET /health - Health check")
    print("  GET /workflow-stats - Get validation statistics")
    print("  GET / - API information")
    print("\nWorkflow: Initial Analysis → AI Validation → Score Adjustment → Street View Analysis")
    app.run(debug=True, host='0.0.0.0', port=5002)
