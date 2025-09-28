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
        route_details (dict, optional): Additional route information like distance, duration
    
    Returns:
        dict: Analysis results with safety score, breakdown, and recommendations
    """
    try:
        # Create a comprehensive prompt for route safety analysis
        prompt = f"""
        Analyze the safety of this walking route and provide a detailed assessment:

        Route: {origin} to {destination}
        """
        
        if route_details:
            prompt += f"""
        Additional Details:
        - Distance: {route_details.get('distance', 'Not specified')}
        - Duration: {route_details.get('duration', 'Not specified')}
        - Route Summary: {route_details.get('summary', 'Not specified')}
        """
        
        prompt += """
        
        Please provide:
        1. A safety score as a percentage (0-100%)
        2. A detailed breakdown of safety factors (lighting, crime rates, pedestrian infrastructure, etc.)
        3. Specific safety concerns or risks along this route
        4. Recommendations for safer alternatives if applicable
        5. Time-of-day considerations for safety
        6. Any recent safety incidents or patterns in this area (if available)
        
        Format your response as a JSON object with the following structure:
        {
            "safety_score": <percentage>,
            "safety_breakdown": {
                "lighting": <assessment>,
                "crime_rate": <assessment>,
                "pedestrian_infrastructure": <assessment>,
                "traffic_safety": <assessment>
            },
            "concerns": [<list of specific concerns>],
            "recommendations": [<list of safety recommendations>],
            "time_considerations": <advice for different times of day>,
            "alternative_suggestions": [<safer route suggestions if applicable>],
            "sources": [<any sources used for the analysis>]
        }
        
        Be specific and cite any sources you use for crime data, safety statistics, or area information.
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
                # If no JSON found, create a structured response from the text
                analysis = {
                    "safety_score": 75,  # Default score
                    "safety_breakdown": {
                        "lighting": "Analysis not available",
                        "crime_rate": "Analysis not available", 
                        "pedestrian_infrastructure": "Analysis not available",
                        "traffic_safety": "Analysis not available"
                    },
                    "concerns": ["Unable to parse detailed analysis"],
                    "recommendations": ["Use caution and stay aware of surroundings"],
                    "time_considerations": "Avoid walking alone at night",
                    "alternative_suggestions": [],
                    "sources": [],
                    "raw_response": response_text
                }
            
            return {
                "success": True,
                "analysis": analysis,
                "raw_response": response.text
            }
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw response in a structured format
            return {
                "success": True,
                "analysis": {
                    "safety_score": 75,
                    "safety_breakdown": {
                        "lighting": "Analysis not available",
                        "crime_rate": "Analysis not available",
                        "pedestrian_infrastructure": "Analysis not available", 
                        "traffic_safety": "Analysis not available"
                    },
                    "concerns": ["Unable to parse detailed analysis"],
                    "recommendations": ["Use caution and stay aware of surroundings"],
                    "time_considerations": "Avoid walking alone at night",
                    "alternative_suggestions": [],
                    "sources": [],
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
                "safety_breakdown": {
                    "lighting": "Analysis failed",
                    "crime_rate": "Analysis failed",
                    "pedestrian_infrastructure": "Analysis failed",
                    "traffic_safety": "Analysis failed"
                },
                "concerns": ["Unable to analyze route safety"],
                "recommendations": ["Use extreme caution"],
                "time_considerations": "Avoid this route if possible",
                "alternative_suggestions": [],
                "sources": []
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
