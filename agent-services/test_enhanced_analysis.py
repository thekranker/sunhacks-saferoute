#!/usr/bin/env python3
"""
Test script for the enhanced route analysis system.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_route_analysis():
    """Test the enhanced route analysis system."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is available
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: Please set the GOOGLE_API_KEY in your .env file")
        return False
    
    print("Testing Enhanced Route Analysis System")
    print("=" * 60)
    
    # Test route (Tempe, AZ area)
    test_data = {
        "origin": "123 E Apache Blvd, Tempe, AZ 85281",
        "destination": "Mill Ave & University Dr, Tempe, AZ 85281",
        "route_details": {
            "distance": "1.2 miles",
            "duration": "15 minutes",
            "summary": "Walking route through ASU campus"
        },
        "max_samples": 5
    }
    
    print(f"Testing route: {test_data['origin']} → {test_data['destination']}")
    print(f"Max samples: {test_data['max_samples']}")
    print()
    
    try:
        # Test the enhanced analysis endpoint
        print("Calling enhanced analysis endpoint...")
        response = requests.post(
            'http://localhost:5002/analyze-route-enhanced',
            json=test_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success", False):
                print("✅ Enhanced analysis completed successfully!")
                
                analysis = result.get("analysis", {})
                comprehensive = analysis.get("comprehensive_streetview_analysis", {})
                
                print(f"Final Safety Score: {analysis.get('safety_score', 'N/A')}%")
                print(f"Comprehensive Street View Score: {comprehensive.get('safety_score', 'N/A')}%")
                print(f"Points Analyzed: {comprehensive.get('points_analyzed', 0)}/{comprehensive.get('total_points_sampled', 0)}")
                print(f"Coverage: {comprehensive.get('coverage_percentage', 0)}%")
                print(f"Confidence Level: {comprehensive.get('confidence_level', 'unknown')}")
                print(f"Analysis Type: {comprehensive.get('analysis_type', 'unknown')}")
                print()
                
                # Show main concerns
                main_concerns = analysis.get("main_concerns", [])
                if main_concerns:
                    print("Main Safety Concerns:")
                    for concern in main_concerns[:5]:  # Top 5 concerns
                        print(f"  - {concern}")
                    print()
                
                # Show quick tips
                quick_tips = analysis.get("quick_tips", [])
                if quick_tips:
                    print("Safety Recommendations:")
                    for tip in quick_tips[:5]:  # Top 5 tips
                        print(f"  - {tip}")
                    print()
                
                # Show comprehensive concerns
                aggregated_concerns = comprehensive.get("aggregated_concerns", [])
                if aggregated_concerns:
                    print("Route-Specific Concerns:")
                    for concern in aggregated_concerns[:3]:  # Top 3 route concerns
                        print(f"  - {concern}")
                    print()
                
                # Show enhancement notes
                enhancement_notes = comprehensive.get("enhancement_notes", "")
                if enhancement_notes:
                    print(f"Enhancement Notes: {enhancement_notes}")
                    print()
                
                # Show workflow metadata
                workflow_metadata = result.get("workflow_metadata", {})
                print("Workflow Summary:")
                print(f"  - Initial Analysis: {'✅' if workflow_metadata.get('initial_analysis_success') else '❌'}")
                print(f"  - Validation: {'✅' if workflow_metadata.get('validation_success') else '❌'}")
                print(f"  - Comprehensive Analysis: {'✅' if workflow_metadata.get('comprehensive_analysis_success') else '❌'}")
                print(f"  - Score Adjustment: {workflow_metadata.get('score_adjustment', 0):+d} points")
                print(f"  - Points Analyzed: {workflow_metadata.get('points_analyzed', 0)}")
                print(f"  - Coverage: {workflow_metadata.get('coverage_percentage', 0)}%")
                
                return True
                
            else:
                print("❌ Enhanced analysis failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
                return False
                
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120 seconds)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running on localhost:5002")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False

def test_route_sampler():
    """Test the route sampler module directly."""
    
    print("\nTesting Route Sampler Module")
    print("=" * 40)
    
    try:
        from route_sampler import sample_route_for_analysis
        
        # Test with sample coordinates
        origin = (33.4255, -111.9400)  # ASU Tempe
        destination = (33.4484, -111.9250)  # Downtown Tempe
        
        print(f"Sampling route from {origin} to {destination}")
        
        sampling_points = sample_route_for_analysis(origin, destination, max_samples=5)
        
        print(f"Generated {len(sampling_points)} sampling points:")
        for i, point in enumerate(sampling_points):
            print(f"  {i+1}. {point['segment_type']} at {point['coordinates']} (weight: {point.get('weight', 1.0)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Route sampler test failed: {str(e)}")
        return False

def test_enhanced_agent():
    """Test the enhanced street view agent directly."""
    
    print("\nTesting Enhanced Street View Agent")
    print("=" * 40)
    
    try:
        from enhanced_streetview_agent import analyze_route_comprehensive
        
        # Test with sample coordinates
        origin = (33.4255, -111.9400)  # ASU Tempe
        destination = (33.4484, -111.9250)  # Downtown Tempe
        
        print(f"Testing comprehensive analysis from {origin} to {destination}")
        
        result = analyze_route_comprehensive(origin, destination, max_samples=3)
        
        if result.get("success", False):
            print("✅ Comprehensive analysis successful!")
            print(f"Safety Score: {result.get('comprehensive_safety_score', 'N/A')}%")
            print(f"Points Analyzed: {result.get('points_analyzed', 0)}/{result.get('total_points_sampled', 0)}")
            print(f"Coverage: {result.get('coverage_percentage', 0)}%")
            return True
        else:
            print(f"❌ Comprehensive analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced agent test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Enhanced Route Analysis System Test Suite")
    print("=" * 60)
    
    # Test individual components
    sampler_success = test_route_sampler()
    agent_success = test_enhanced_agent()
    
    # Test the full API endpoint
    api_success = test_enhanced_route_analysis()
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print(f"  Route Sampler: {'✅ PASS' if sampler_success else '❌ FAIL'}")
    print(f"  Enhanced Agent: {'✅ PASS' if agent_success else '❌ FAIL'}")
    print(f"  API Endpoint: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if all([sampler_success, agent_success, api_success]):
        print("\n🎉 All tests passed! Enhanced route analysis system is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the error messages above.")
        sys.exit(1)
