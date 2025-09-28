import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the API key from environment variable or .env file
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("Error: Please set the GOOGLE_API_KEY in your .env file or as an environment variable")
    print("Create a .env file with: GOOGLE_API_KEY=your-api-key-here")
    print("Or run: export GOOGLE_API_KEY='your-api-key-here'")
    exit(1)

genai.configure(api_key=api_key)

# Create the model - using gemini-2.5-flash which is available
model = genai.GenerativeModel('gemini-2.5-flash')

def analyze_route_safety(origin, destination, route_details=None):
    """
    Analyze the safety of a walking route using Gemini AI.
    
    Args:
        origin (str): Starting address
        destination (str): Destination address
    
    Returns:
        safety score (int): Safety score as a percentage (0-100%)
        
    """
       #route_details (dict, optional): Additional route information like distance, duration
       #dict: Analysis results with safety score, breakdown, and recommendations 
    try:
        # Create a comprehensive prompt for route safety analysis
         # Analyze the safety of this walking route and provide a detailed assessment:

        prompt = f"""

        Route: {origin} to {destination}
        """
        
        # if route_details:
        #     prompt += f"""
        # Additional Details:
        # - Distance: {route_details.get('distance', 'Not specified')}
        # - Duration: {route_details.get('duration', 'Not specified')}
        # - Route Summary: {route_details.get('summary', 'Not specified')}
        # """
        
        prompt += """
        
        Give a REALISTIC safety assessment in this exact JSON format:
        {
            "safety_score": <number 0-100>,
            "main_concerns": [<2-3 key safety issues>],
            "quick_tips": [<2-3 brief safety recommendations>]
        }
        
        Be realistic and accurate. Consider the actual safety factors of this specific route.
        Focus on practical concerns and real risks. Don't be overly optimistic or pessimistic.
        Keep it brief - just essential safety info.
        """
        
        # Generate content using Gemini
        response = model.generate_content(prompt)
        
        # Try to parse the response as JSON
        try:
            # Extract JSON from the response text
            response_text = response.text.strip()
            
            # Find JSON object in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                # If no JSON found, create a simple response
                analysis = {
                    "safety_score": 75,  # Default score
                    "main_concerns": ["Unable to analyze route"],
                    "quick_tips": ["Use caution and stay aware of surroundings"],
                    "raw_response": response_text
                }
            
            return {
                "success": True,
                "analysis": analysis,
                "raw_response": response.text
            }
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return a simple response
            return {
                "success": True,
                "analysis": {
                    "safety_score": 75,
                    "main_concerns": ["Unable to parse analysis"],
                    "quick_tips": ["Use caution and stay aware of surroundings"],
                    "raw_response": response.text
                },
                "raw_response": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": {
                "safety_score": 50,  # Default low score for errors
                "main_concerns": ["Unable to analyze route safety"],
                "quick_tips": ["Use extreme caution"]
            }
        }

def main():
    """
    Main function for testing the route analysis.
    """
    # Test with the original route
    origin = "704 S Myrtle Ave, Tempe, AZ 85281"
    destination = "Vista Del Sol B, 701 E Apache Blvd, Tempe, AZ 85281"
    
    print("Analyzing route safety...")
    result = analyze_route_safety(origin, destination)
    
    if result["success"]:
        print("Analysis completed successfully!")
        print(f"Safety Score: {result['analysis']['safety_score']}%")
        print(f"Raw Response: {result['raw_response']}")
    else:
        print(f"Analysis failed: {result['error']}")

if __name__ == "__main__":
    main()
