#!/usr/bin/env python3
"""
Test script for the updated Street View agent with real image analysis.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_streetview_agent import GeminiStreetViewAgent

def test_streetview_analysis():
    """Test the Street View agent with real image analysis."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is available
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: Please set the GOOGLE_API_KEY in your .env file")
        return False
    
    print("Testing Street View Agent with Real Image Analysis")
    print("=" * 60)
    
    # Create agent
    agent = GeminiStreetViewAgent()
    
    # Test location (Tempe, AZ - ASU area)
    test_location = {
        "address": "123 E Apache Blvd, Tempe, AZ 85281",
        "coordinates": "33.4255,-111.9400",
        "time_context": "day"
    }
    
    print(f"Testing location: {test_location['address']}")
    print(f"Coordinates: {test_location['coordinates']}")
    print()
    
    try:
        # Test the analysis
        print("Starting Street View analysis...")
        result = agent.analyze_streetview_safety(None, test_location)
        
        if result.get("success", False):
            print("✅ Analysis completed successfully!")
            print(f"Safety Score: {result['safety_score']}%")
            print(f"Analysis Type: {result.get('analysis_type', 'unknown')}")
            print(f"Confidence Level: {result['confidence_level']}")
            print(f"Image Quality: {result['image_quality']}")
            print()
            
            if result.get('key_concerns'):
                print("Key Concerns:")
                for concern in result['key_concerns']:
                    print(f"  - {concern}")
                print()
            
            if result.get('positive_factors'):
                print("Positive Factors:")
                for factor in result['positive_factors']:
                    print(f"  - {factor}")
                print()
            
            if result.get('recommendations'):
                print("Recommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
                print()
            
            # Show metric breakdown
            metric_breakdown = result.get('metric_breakdown', {})
            if metric_breakdown:
                print("Metric Breakdown:")
                for metric_name, metric_data in metric_breakdown.items():
                    if isinstance(metric_data, dict):
                        score = metric_data.get('score', 0)
                        print(f"  {metric_name.replace('_', ' ').title()}: {score}%")
            
            return True
            
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_streetview_analysis()
    if success:
        print("\n🎉 Street View integration test completed successfully!")
    else:
        print("\n💥 Street View integration test failed!")
        sys.exit(1)
