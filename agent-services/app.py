from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from gemini_api import analyze_route_safety
from gemini_validation_agent import validate_route_safety_with_agent, GeminiValidationAgent

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
        
        # Step 3: Create enhanced analysis with validation results
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

@app.route('/workflow-stats', methods=['GET'])
def get_workflow_stats():
    """
    Get validation agent statistics.
    """
    try:
        return jsonify({
            "success": True,
            "workflow_stats": {
                "description": "AI-powered route safety analysis with validation",
                "agents": ["Gemini Analysis Agent", "Gemini Validation Agent"],
                "features": [
                    "Initial AI safety analysis",
                    "AI-powered validation of results", 
                    "Automatic score adjustment based on validation",
                    "Comprehensive logging of both AI processes",
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
        "message": "SafeRoute AI Analysis API with Validation",
        "endpoints": {
            "POST /analyze-route": "Analyze route safety with integrated validation",
            "POST /validate-analysis": "Manually validate an existing safety analysis",
            "GET /health": "Health check",
            "GET /workflow-stats": "Get validation statistics",
            "GET /": "This information"
        },
        "workflow": {
            "description": "Enhanced AI Analysis with Validation: Initial Analysis → AI Validation → Score Adjustment",
            "agents": ["Gemini Analysis Agent", "Gemini Validation Agent"],
            "features": [
                "Initial AI safety analysis",
                "AI-powered validation of results", 
                "Automatic score adjustment based on validation",
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
            ]
        }
    })

if __name__ == '__main__':
    print("Starting SafeRoute AI Analysis API with Validation...")
    print("Available endpoints:")
    print("  POST /analyze-route - Analyze route safety with integrated validation")
    print("  POST /validate-analysis - Manually validate an existing analysis")
    print("  GET /health - Health check")
    print("  GET /workflow-stats - Get validation statistics")
    print("  GET / - API information")
    print("\nWorkflow: Initial Analysis → AI Validation → Score Adjustment")
    app.run(debug=True, host='0.0.0.0', port=5002)
