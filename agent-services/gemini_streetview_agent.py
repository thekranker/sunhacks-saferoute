import google.generativeai as genai
import os
import json
import logging
import base64
import requests
import io
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streetview_agent.log'),
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

class GeminiStreetViewAgent:
    """
    Street view analysis agent that analyzes street view images for safety indicators.
    """
    
    def __init__(self):
        self.logger = logger
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        if not self.google_api_key:
            self.logger.error("Error: Please set the GOOGLE_API_KEY in your .env file")
            exit(1)
        self.safety_metrics = {
            "exposure_visibility": {
                "weight": 0.20,
                "description": "Lighting conditions, visibility, hidden areas"
            },
            "infrastructure_condition": {
                "weight": 0.15,
                "description": "Sidewalk condition, streetlights, crosswalks, building maintenance"
            },
            "crime_markers": {
                "weight": 0.20,
                "description": "Graffiti, boarded windows, security features, surveillance"
            },
            "pedestrian_infrastructure": {
                "weight": 0.15,
                "description": "Crosswalks, sidewalks, pedestrian signals, accessibility"
            },
            "traffic_danger": {
                "weight": 0.15,
                "description": "Road proximity, barriers, traffic separation"
            },
            "vegetation_obstructions": {
                "weight": 0.10,
                "description": "Overgrown foliage, visibility obstructions"
            },
            "human_activity": {
                "weight": 0.05,
                "description": "Presence of people, activity level (privacy-conscious)"
            }
        }
    
    def fetch_streetview_image(self, location_info):
        """
        Fetch a real Google Street View image for the given location.
        
        Args:
            location_info (dict): Location information with coordinates or address
            
        Returns:
            str: Base64 encoded image data, or None if failed
        """
        try:
            # Extract coordinates or geocode address
            if 'coordinates' in location_info:
                lat, lng = location_info['coordinates'].split(',')
                lat, lng = float(lat.strip()), float(lng.strip())
            else:
                # Geocode the address to get coordinates
                geocoded = self._geocode_address(location_info.get('address', ''))
                if not geocoded:
                    self.logger.error("Failed to geocode address for Street View")
                    return None
                lat, lng = geocoded['lat'], geocoded['lng']
            
            # Fetch Street View image
            url = "https://maps.googleapis.com/maps/api/streetview"
            params = {
                'location': f"{lat},{lng}",
                'size': '640x640',  # Good resolution for analysis
                'fov': '90',  # Wide field of view
                'heading': '0',  # North-facing
                'pitch': '0',  # Level view
                'key': self.google_api_key
            }
            
            self.logger.info(f"Fetching Street View image for {lat},{lng}")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # Convert to base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            self.logger.info(f"Successfully fetched Street View image ({len(image_data)} chars)")
            return image_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Street View image: {str(e)}")
            return None
    
    def _geocode_address(self, address):
        """
        Geocode an address to get coordinates.
        
        Args:
            address (str): Address to geocode
            
        Returns:
            dict: Coordinates and formatted address, or None if failed
        """
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': self.google_api_key
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
                self.logger.warning(f"Geocoding failed for {address}: {data.get('status', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Geocoding error for {address}: {str(e)}")
            return None
    
    def _fallback_text_analysis(self, location_info):
        """
        Fallback to text-based analysis when Street View image cannot be fetched.
        
        Args:
            location_info (dict): Location information
            
        Returns:
            dict: Analysis results with safety score and detailed breakdown
        """
        try:
            self.logger.info("FALLING BACK TO TEXT-BASED ANALYSIS")
            self.logger.info("  - Analyzing location safety based on area knowledge")
            self.logger.info("  - Evaluating 7 safety metrics with weighted scoring")
            self.logger.info("  - Considering typical infrastructure and crime patterns")
            
            # Create comprehensive text-based analysis prompt
            analysis_prompt = self._create_text_based_analysis_prompt(location_info)
            
            # Generate content without image
            response = model.generate_content(analysis_prompt)
            
            # Parse analysis response
            analysis_result = self._parse_streetview_response(response.text, location_info)
            
            # Mark as fallback analysis
            analysis_result["analysis_type"] = "text_based_fallback"
            analysis_result["image_quality"] = "unavailable"
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Fallback text analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "safety_score": 0,
                "confidence_level": "low",
                "analysis_type": "failed"
            }
    
    def analyze_streetview_safety(self, image_data=None, location_info=None):
        """
        Analyze street view safety indicators using real Google Street View images.
        
        Args:
            image_data (str, optional): Base64 encoded image data (if provided, will be used)
            location_info (dict): Location information (address, coordinates, time_context)
            
        Returns:
            dict: Analysis results with safety score and detailed breakdown
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("STREET VIEW AGENT STARTING REAL IMAGE ANALYSIS")
            self.logger.info("=" * 80)
            self.logger.info(f"Location: {location_info.get('address', 'Unknown')}")
            self.logger.info(f"Coordinates: {location_info.get('coordinates', 'Unknown')}")
            self.logger.info(f"Time Context: {location_info.get('time_context', 'Unknown')}")
            
            # Fetch real Street View image if not provided
            if not image_data:
                self.logger.info("No image data provided, fetching real Street View image...")
                image_data = self.fetch_streetview_image(location_info)
                if not image_data:
                    self.logger.warning("Failed to fetch Street View image, falling back to text-based analysis")
                    return self._fallback_text_analysis(location_info)
            else:
                self.logger.info("Using provided image data for analysis")
            
            self.logger.info("STREET VIEW AGENT THINKING PROCESS:")
            self.logger.info("  - Analyzing actual Street View image for visual safety indicators")
            self.logger.info("  - Evaluating 7 safety metrics with weighted scoring")
            self.logger.info("  - Looking for lighting, infrastructure, crime markers, etc.")
            self.logger.info("  - Assessing pedestrian safety factors from visual evidence")
            self.logger.info("")
            
            # Create comprehensive image-based analysis prompt
            analysis_prompt = self._create_streetview_analysis_prompt(location_info)
            
            self.logger.info("Sending image analysis request to Gemini...")
            self.logger.info("  - Prompt includes 7 weighted safety metrics")
            self.logger.info("  - Requesting detailed visual observations and recommendations")
            self.logger.info("  - Expecting JSON response with metric breakdown")
            
            # Generate content with image
            response = model.generate_content([analysis_prompt, {"mime_type": "image/jpeg", "data": image_data}])
            
            self.logger.info("Received response from Gemini, parsing analysis...")
            self.logger.info(f"  - Response length: {len(response.text)} characters")
            
            # Parse analysis response
            analysis_result = self._parse_streetview_response(response.text, location_info)
            
            # Log detailed analysis process
            self._log_streetview_analysis(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Street view analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "safety_score": 0,
                "confidence_level": "low"
            }
    
    def _create_streetview_analysis_prompt(self, location_info):
        """Create comprehensive prompt for real street view image safety analysis."""
        
        prompt = f"""
        You are a safety analysis expert specializing in visual assessment of street environments. Analyze this Google Street View image for pedestrian safety indicators.

        LOCATION CONTEXT:
        - Address: {location_info.get('address', 'Unknown')}
        - Coordinates: {location_info.get('coordinates', 'Unknown')}
        - Time Context: {location_info.get('time_context', 'Unknown')}

        YOUR TASK:
        Carefully examine this Street View image and analyze it for the following safety metrics. Look at what you can actually see in the image:

        1. EXPOSURE/VISIBILITY (Weight: 20%):
           - Lighting conditions (day/night, streetlights, building lights)
           - Visibility of the area (clear sightlines, hidden corners)
           - Dark alleys or poorly lit areas
           - Overall visibility for pedestrians

        2. INFRASTRUCTURE CONDITION (Weight: 15%):
           - Sidewalk condition (cracked, broken, missing)
           - Streetlight functionality and placement
           - Crosswalk availability and condition
           - Building maintenance and upkeep
           - Fence and barrier condition

        3. CRIME-RELATED MARKERS (Weight: 20%):
           - Graffiti presence and extent
           - Boarded-up windows or buildings
           - Security bars on windows
           - Surveillance cameras
           - "No loitering" or security signs
           - High fences or barriers
           - Police presence indicators

        4. PEDESTRIAN INFRASTRUCTURE (Weight: 15%):
           - Crosswalk availability and visibility
           - Sidewalk width and accessibility
           - Pedestrian signals
           - Curb cuts for accessibility
           - Street-level access

        5. TRAFFIC DANGER (Weight: 15%):
           - Proximity to busy roads
           - Separation between sidewalk and road
           - Protective barriers
           - Traffic flow and speed indicators

        6. VEGETATION/OBSTRUCTIONS (Weight: 10%):
           - Overgrown foliage blocking visibility
           - Tree branches obstructing paths
           - Other visibility obstructions

        7. HUMAN ACTIVITY (Weight: 5%):
           - Presence of people (be privacy-conscious)
           - Activity level and type
           - Social environment indicators

        ADDITIONAL CONSIDERATIONS:
        - Time context: Consider if this appears to be day/night based on lighting
        - Weather conditions visible in the image
        - Overall cleanliness and maintenance
        - Accessibility features

        RESPOND IN THIS EXACT JSON FORMAT:
        {{
            "safety_score": <overall score 0-100>,
            "metric_breakdown": {{
                "exposure_visibility": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "infrastructure_condition": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "crime_markers": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "pedestrian_infrastructure": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "traffic_danger": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "vegetation_obstructions": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "human_activity": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }}
            }},
            "detailed_observations": "<comprehensive analysis of what you see in the image>",
            "key_concerns": ["<top 3-5 safety concerns>"],
            "positive_factors": ["<top 3-5 positive safety factors>"],
            "recommendations": ["<specific safety recommendations>"],
            "confidence_level": "<high/medium/low>",
            "time_context": "<day/night/unknown based on image analysis>",
            "image_quality": "<excellent/good/fair/poor>",
            "analysis_notes": "<any additional observations or limitations>"
        }}

        IMPORTANT: Base your analysis ONLY on what you can actually see in this Street View image. 
        Be thorough, accurate, and realistic in your assessment. Focus on actual safety factors visible in the image.
        Consider both risks and positive safety indicators. Be specific about what you observe in the image.
        If certain elements are not visible in the image, note that in your observations.
        """
        
        return prompt
    
    def _create_text_based_analysis_prompt(self, location_info):
        """Create comprehensive prompt for text-based street safety analysis."""
        
        prompt = f"""
        You are a safety analysis expert specializing in street environment assessment. Analyze the safety of this location based on available information and general knowledge.

        LOCATION CONTEXT:
        - Address: {location_info.get('address', 'Unknown')}
        - Coordinates: {location_info.get('coordinates', 'Unknown')}
        - Time Context: {location_info.get('time_context', 'Unknown')}

        YOUR TASK:
        Analyze this location for the following safety metrics and provide a comprehensive safety assessment:

        1. EXPOSURE/VISIBILITY (Weight: 20%):
           - Typical lighting conditions for this area
           - Visibility of the area (clear sightlines, hidden corners)
           - Dark alleys or poorly lit areas
           - Overall visibility for pedestrians

        2. INFRASTRUCTURE CONDITION (Weight: 15%):
           - Typical sidewalk condition in this area
           - Streetlight functionality and placement
           - Crosswalk availability and condition
           - Building maintenance and upkeep
           - Fence and barrier condition

        3. CRIME-RELATED MARKERS (Weight: 20%):
           - Typical graffiti presence in this area
           - Boarded-up windows or buildings
           - Security bars on windows
           - Surveillance cameras
           - "No loitering" or security signs
           - High fences or barriers
           - Police presence indicators

        4. PEDESTRIAN INFRASTRUCTURE (Weight: 15%):
           - Crosswalk availability and visibility
           - Sidewalk width and accessibility
           - Pedestrian signals
           - Curb cuts for accessibility
           - Street-level access

        5. TRAFFIC DANGER (Weight: 15%):
           - Proximity to busy roads
           - Separation between sidewalk and road
           - Protective barriers
           - Traffic flow and speed indicators

        6. VEGETATION/OBSTRUCTIONS (Weight: 10%):
           - Overgrown foliage blocking visibility
           - Tree branches obstructing paths
           - Other visibility obstructions

        7. HUMAN ACTIVITY (Weight: 5%):
           - Typical activity level in this area
           - Social environment indicators

        ADDITIONAL CONSIDERATIONS:
        - Time context: Consider day/night safety differences
        - Weather conditions typical for this area
        - Overall cleanliness and maintenance
        - Accessibility features
        - Area reputation and crime statistics

        RESPOND IN THIS EXACT JSON FORMAT:
        {{
            "safety_score": <overall score 0-100>,
            "metric_breakdown": {{
                "exposure_visibility": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "infrastructure_condition": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "crime_markers": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "pedestrian_infrastructure": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "traffic_danger": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "vegetation_obstructions": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }},
                "human_activity": {{
                    "score": <0-100>,
                    "observations": "<detailed observations>",
                    "concerns": ["<specific concerns>"],
                    "positive_factors": ["<positive factors>"]
                }}
            }},
            "detailed_observations": "<comprehensive analysis of what you know about this location>",
            "key_concerns": ["<top 3-5 safety concerns>"],
            "positive_factors": ["<top 3-5 positive safety factors>"],
            "recommendations": ["<specific safety recommendations>"],
            "confidence_level": "<high/medium/low>",
            "time_context": "<day/night/unknown based on analysis>",
            "image_quality": "text-based",
            "analysis_notes": "<any additional observations or limitations>"
        }}

        Be thorough, accurate, and realistic in your assessment. Focus on actual safety factors for this location.
        Consider both risks and positive safety indicators. Be specific about what you know about this area.
        """
        
        return prompt
    
    def _parse_streetview_response(self, response_text, location_info):
        """Parse the street view analysis response and calculate weighted score."""
        
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                analysis_data = json.loads(json_str)
            else:
                # Fallback if no JSON found
                analysis_data = {
                    "safety_score": 50,
                    "metric_breakdown": {},
                    "detailed_observations": "Unable to parse analysis response",
                    "key_concerns": ["Analysis parsing failed"],
                    "positive_factors": [],
                    "recommendations": ["Use caution"],
                    "confidence_level": "low",
                    "time_context": "unknown",
                    "image_quality": "unknown",
                    "analysis_notes": "JSON parsing failed"
                }
            
            # Calculate weighted safety score
            weighted_score = self._calculate_weighted_score(analysis_data.get('metric_breakdown', {}))
            
            # Use calculated score if available, otherwise use provided score
            final_score = weighted_score if weighted_score > 0 else analysis_data.get('safety_score', 50)
            
            return {
                "success": True,
                "safety_score": final_score,
                "metric_breakdown": analysis_data.get('metric_breakdown', {}),
                "detailed_observations": analysis_data.get('detailed_observations', ''),
                "key_concerns": analysis_data.get('key_concerns', []),
                "positive_factors": analysis_data.get('positive_factors', []),
                "recommendations": analysis_data.get('recommendations', []),
                "confidence_level": analysis_data.get('confidence_level', 'medium'),
                "time_context": analysis_data.get('time_context', 'unknown'),
                "image_quality": analysis_data.get('image_quality', 'unknown'),
                "analysis_notes": analysis_data.get('analysis_notes', ''),
                "analysis_type": "real_streetview_image",
                "location_info": location_info,
                "analysis_timestamp": datetime.now().isoformat(),
                "raw_analysis": response_text
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {str(e)}")
            return {
                "success": False,
                "error": f"JSON parsing failed: {str(e)}",
                "safety_score": 0,
                "confidence_level": "low"
            }
    
    def _calculate_weighted_score(self, metric_breakdown):
        """Calculate weighted safety score based on metric breakdown."""
        
        if not metric_breakdown:
            return 0
        
        total_weighted_score = 0
        total_weight = 0
        
        for metric_name, metric_data in metric_breakdown.items():
            if isinstance(metric_data, dict) and 'score' in metric_data:
                score = metric_data['score']
                weight = self.safety_metrics.get(metric_name, {}).get('weight', 0.1)
                
                total_weighted_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return round(total_weighted_score / total_weight, 1)
        
        return 0
    
    def _log_streetview_analysis(self, analysis_result):
        """Log the complete street view analysis process."""
        
        self.logger.info("=" * 80)
        self.logger.info("STREET VIEW AGENT ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        
        if analysis_result.get("success", False):
            self.logger.info("STREET VIEW AGENT OBSERVATIONS:")
            self.logger.info(f"  Overall Safety Score: {analysis_result['safety_score']}%")
            self.logger.info(f"  Confidence Level: {analysis_result['confidence_level']}")
            self.logger.info(f"  Time Context: {analysis_result['time_context']}")
            self.logger.info(f"  Image Quality: {analysis_result['image_quality']}")
            
            self.logger.info("DETAILED OBSERVATIONS:")
            self.logger.info(f"  {analysis_result['detailed_observations']}")
            
            if analysis_result.get('key_concerns'):
                self.logger.info("KEY SAFETY CONCERNS:")
                for concern in analysis_result['key_concerns']:
                    self.logger.info(f"  - {concern}")
            
            if analysis_result.get('positive_factors'):
                self.logger.info("POSITIVE SAFETY FACTORS:")
                for factor in analysis_result['positive_factors']:
                    self.logger.info(f"  - {factor}")
            
            if analysis_result.get('recommendations'):
                self.logger.info("SAFETY RECOMMENDATIONS:")
                for rec in analysis_result['recommendations']:
                    self.logger.info(f"  - {rec}")
            
            # Log metric breakdown
            metric_breakdown = analysis_result.get('metric_breakdown', {})
            if metric_breakdown:
                self.logger.info("METRIC BREAKDOWN:")
                for metric_name, metric_data in metric_breakdown.items():
                    if isinstance(metric_data, dict):
                        score = metric_data.get('score', 0)
                        weight = self.safety_metrics.get(metric_name, {}).get('weight', 0) * 100
                        self.logger.info(f"  {metric_name.replace('_', ' ').title()}: {score}% (Weight: {weight:.0f}%)")
            
            if analysis_result.get('analysis_notes'):
                self.logger.info(f"ANALYSIS NOTES: {analysis_result['analysis_notes']}")
            
            self.logger.info("=" * 80)
            self.logger.info("FINAL STREET VIEW SAFETY SCORE")
            self.logger.info("=" * 80)
            self.logger.info(f"Street View Safety Score: {analysis_result['safety_score']}%")
            self.logger.info("=" * 80)
            
        else:
            self.logger.error("STREET VIEW ANALYSIS FAILED:")
            self.logger.error(f"  Error: {analysis_result.get('error', 'Unknown error')}")
            self.logger.error(f"  Safety Score: {analysis_result.get('safety_score', 0)}%")

def analyze_streetview_safety(image_data=None, location_info=None):
    """
    Convenience function to analyze street view safety.
    No longer requires actual street view images.
    
    Args:
        image_data (str, optional): Base64 encoded image data (ignored)
        location_info (dict): Location information
        
    Returns:
        dict: Analysis results with safety score and detailed breakdown
    """
    agent = GeminiStreetViewAgent()
    return agent.analyze_streetview_safety(image_data, location_info)

def main():
    """
    Test function for the street view agent.
    """
    # Sample test data (would normally come from actual street view images)
    sample_location = {
        "address": "123 Main St, Tempe, AZ",
        "coordinates": "33.4255,-111.9400",
        "time_context": "day"
    }
    
    # Note: In real usage, this would be actual base64 image data
    sample_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    print("Testing street view agent...")
    result = analyze_streetview_safety(sample_image_data, sample_location)
    
    if result["success"]:
        print(f"\nStreet View Safety Score: {result['safety_score']}%")
        print(f"Confidence: {result['confidence_level']}")
        print(f"Key Concerns: {result['key_concerns']}")
    else:
        print(f"Analysis failed: {result['error']}")

if __name__ == "__main__":
    main()
