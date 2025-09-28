import google.generativeai as genai
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure the API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    logger.error("Error: Please set the GOOGLE_API_KEY in your .env file")
    exit(1)

genai.configure(api_key=api_key)

# Create the model
model = genai.GenerativeModel('gemini-2.5-flash')

class GeminiValidationAgent:
    """
    Validation agent that reviews Gemini API safety analysis and adjusts scores.
    """
    
    def __init__(self):
        self.logger = logger
        self.max_adjustment = 12  # Balanced maximum score adjustment (+/-12)
        self.bias_toward_positive = False  # No bias - be accurate
    
    def validate_safety_analysis(self, original_analysis, route_info):
        """
        Validate and potentially adjust the safety analysis from the primary Gemini agent.
        
        Args:
            original_analysis (dict): The original analysis from gemini_api.py
            route_info (dict): Route information (origin, destination, etc.)
            
        Returns:
            dict: Updated analysis with validation results and adjusted score
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("VALIDATION AGENT STARTING ANALYSIS")
            self.logger.info("=" * 60)
            
            # Log original analysis
            self.logger.info(f"ORIGINAL ANALYSIS RECEIVED:")
            self.logger.info(f"  Safety Score: {original_analysis.get('safety_score', 'N/A')}%")
            self.logger.info(f"  Main Concerns: {original_analysis.get('main_concerns', [])}")
            self.logger.info(f"  Quick Tips: {original_analysis.get('quick_tips', [])}")
            self.logger.info(f"  Raw Response: {original_analysis.get('raw_response', 'N/A')[:200]}...")
            
            # Create validation prompt
            validation_prompt = self._create_validation_prompt(original_analysis, route_info)
            
            # Get validation response from Gemini
            self.logger.info("Sending validation request to Gemini...")
            response = model.generate_content(validation_prompt)
            
            # Parse validation response
            validation_result = self._parse_validation_response(response.text, original_analysis)
            
            # Log validation process
            self._log_validation_process(original_analysis, validation_result)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_analysis": original_analysis,
                "validation_analysis": None,
                "final_score": original_analysis.get('safety_score', 50),
                "adjustment": 0
            }
    
    def _create_validation_prompt(self, original_analysis, route_info):
        """Create a comprehensive validation prompt for the Gemini model."""
        
        prompt = f"""
        You are a safety validation expert with a realistic, accurate perspective. Your job is to review another AI's safety analysis and determine if the score needs adjustment.

        ROUTE INFORMATION:
        - Origin: {route_info.get('origin', 'Unknown')}
        - Destination: {route_info.get('destination', 'Unknown')}
        
        ORIGINAL AI ANALYSIS:
        - Safety Score: {original_analysis.get('safety_score', 'N/A')}%
        - Main Concerns: {original_analysis.get('main_concerns', [])}
        - Quick Tips: {original_analysis.get('quick_tips', [])}
        - Raw Analysis: {original_analysis.get('raw_response', 'N/A')}
        
        YOUR TASK:
        1. Review the original analysis for accuracy and completeness
        2. Consider both safety concerns AND positive safety factors (good lighting, safe infrastructure, low crime areas, etc.)
        3. Be accurate and realistic - adjust the score based on actual safety factors (up to ±12 points)
        4. Focus on practical, real-world safety rather than worst-case scenarios
        5. Be harsh when there are genuine high-risk factors, but not overly harsh for normal urban routes
        6. Consider the specific context of the route (university area, downtown, residential, etc.)
        
        IMPORTANT: Be accurate and realistic. Make adjustments based on actual safety factors, not just positive thinking.
        Consider both risks and safety factors, but don't artificially inflate scores.
        
        Respond in this EXACT JSON format:
        {{
            "validation_score": <your assessment 0-100>,
            "original_score": {original_analysis.get('safety_score', 50)},
            "adjustment_needed": <±12 to ±12>,
            "reasoning": "<realistic explanation focusing on actual safety factors and context>",
            "additional_concerns": [<any significant new safety concerns you identified>],
            "additional_tips": [<any new safety recommendations>],
            "confidence_level": "<high/medium/low>",
            "validation_notes": "<realistic observations about the route's actual safety context>"
        }}
        
        Be thorough and accurate. Consider both risks and safety factors realistically.
        """
        
        return prompt
    
    def _parse_validation_response(self, response_text, original_analysis):
        """Parse the validation response and calculate final score."""
        
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                validation_data = json.loads(json_str)
            else:
                # Fallback if no JSON found
                validation_data = {
                    "validation_score": original_analysis.get('safety_score', 50),
                    "original_score": original_analysis.get('safety_score', 50),
                    "adjustment_needed": 0,
                    "reasoning": "Unable to parse validation response",
                    "additional_concerns": [],
                    "additional_tips": [],
                    "confidence_level": "low",
                    "validation_notes": "JSON parsing failed"
                }
            
            # Calculate final score with adjustment
            original_score = original_analysis.get('safety_score', 50)
            adjustment = validation_data.get('adjustment_needed', 0)
            
            # No bias - be accurate and realistic
            # Ensure adjustment is within bounds (±12)
            adjustment = max(-12, min(12, adjustment))
            final_score = max(0, min(100, original_score + adjustment))
            
            return {
                "success": True,
                "original_analysis": original_analysis,
                "validation_analysis": validation_data,
                "final_score": final_score,
                "adjustment": adjustment,
                "validation_response": response_text
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {str(e)}")
            return {
                "success": False,
                "error": f"JSON parsing failed: {str(e)}",
                "original_analysis": original_analysis,
                "validation_analysis": None,
                "final_score": original_analysis.get('safety_score', 50),
                "adjustment": 0
            }
    
    def _log_validation_process(self, original_analysis, validation_result):
        """Log the complete validation process for transparency."""
        
        self.logger.info("=" * 60)
        self.logger.info("VALIDATION AGENT ANALYSIS COMPLETE")
        self.logger.info("=" * 60)
        
        if validation_result["success"]:
            validation_data = validation_result["validation_analysis"]
            
            self.logger.info("VALIDATION AGENT THOUGHTS:")
            self.logger.info(f"  Original Score: {validation_data.get('original_score', 'N/A')}%")
            self.logger.info(f"  Validation Score: {validation_data.get('validation_score', 'N/A')}%")
            self.logger.info(f"  Adjustment Needed: {validation_data.get('adjustment_needed', 0)} points")
            self.logger.info(f"  Final Score: {validation_result['final_score']}%")
            self.logger.info(f"  Confidence: {validation_data.get('confidence_level', 'N/A')}")
            
            self.logger.info("VALIDATION REASONING:")
            self.logger.info(f"  {validation_data.get('reasoning', 'No reasoning provided')}")
            
            if validation_data.get('additional_concerns'):
                self.logger.info("ADDITIONAL CONCERNS IDENTIFIED:")
                for concern in validation_data['additional_concerns']:
                    self.logger.info(f"  - {concern}")
            
            if validation_data.get('additional_tips'):
                self.logger.info("ADDITIONAL SAFETY TIPS:")
                for tip in validation_data['additional_tips']:
                    self.logger.info(f"  - {tip}")
            
            if validation_data.get('validation_notes'):
                self.logger.info(f"VALIDATION NOTES: {validation_data['validation_notes']}")
            
            self.logger.info("=" * 60)
            self.logger.info("FINAL RESULT SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Original AI Score: {original_analysis.get('safety_score', 'N/A')}%")
            self.logger.info(f"Validation Adjustment: {validation_result['adjustment']:+d} points")
            self.logger.info(f"Final Safety Score: {validation_result['final_score']}%")
            self.logger.info("=" * 60)
            
        else:
            self.logger.error("VALIDATION FAILED:")
            self.logger.error(f"  Error: {validation_result.get('error', 'Unknown error')}")
            self.logger.error(f"  Using original score: {validation_result['final_score']}%")

def validate_route_safety_with_agent(original_analysis, route_info):
    """
    Convenience function to validate route safety analysis.
    
    Args:
        original_analysis (dict): Original analysis from gemini_api.py
        route_info (dict): Route information
        
    Returns:
        dict: Validation results with final score
    """
    agent = GeminiValidationAgent()
    return agent.validate_safety_analysis(original_analysis, route_info)

def main():
    """
    Test function for the validation agent.
    """
    # Sample original analysis (as would come from gemini_api.py)
    sample_original = {
        "safety_score": 75,
        "main_concerns": ["Poor lighting", "Heavy traffic"],
        "quick_tips": ["Walk with a friend", "Stay on main roads"],
        "raw_response": "This route has moderate safety concerns due to lighting and traffic."
    }
    
    # Sample route info
    sample_route = {
        "origin": "704 S Myrtle Ave, Tempe, AZ 85281",
        "destination": "Vista Del Sol B, 701 E Apache Blvd, Tempe, AZ 85281"
    }
    
    print("Testing validation agent...")
    result = validate_route_safety_with_agent(sample_original, sample_route)
    
    if result["success"]:
        print(f"\nFinal Safety Score: {result['final_score']}%")
        print(f"Adjustment: {result['adjustment']:+d} points")
    else:
        print(f"Validation failed: {result['error']}")

if __name__ == "__main__":
    main()
