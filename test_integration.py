#!/usr/bin/env python3
"""
Test script to verify the AI analysis integration.
This script tests the complete flow from route input to AI analysis.
"""

import requests
import json
import time

def test_api_health():
    """Test if the API server is running."""
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on port 5001.")
        return False
    except Exception as e:
        print(f"❌ Error testing API health: {e}")
        return False

def test_route_analysis():
    """Test the route analysis endpoint."""
    test_data = {
        "origin": "704 S Myrtle Ave, Tempe, AZ 85281",
        "destination": "Vista Del Sol B, 701 E Apache Blvd, Tempe, AZ 85281",
        "route_details": {
            "distance": "1.2 mi",
            "duration": "15 min",
            "summary": "Route via University Dr"
        }
    }
    
    try:
        print("🤖 Testing AI route analysis...")
        response = requests.post(
            'http://localhost:5001/analyze-route',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                analysis = result.get('analysis', {})
                print("✅ AI analysis completed successfully!")
                print(f"   Safety Score: {analysis.get('safety_score', 'N/A')}%")
                print(f"   Concerns: {len(analysis.get('concerns', []))} items")
                print(f"   Recommendations: {len(analysis.get('recommendations', []))} items")
                return True
            else:
                print(f"❌ AI analysis failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The AI analysis might be taking too long.")
        return False
    except Exception as e:
        print(f"❌ Error testing route analysis: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 SafeRoute AI Integration Test")
    print("=" * 40)
    
    # Test 1: API Health
    print("\n1. Testing API Health...")
    if not test_api_health():
        print("\n❌ Integration test failed: API server not available")
        print("Please start the API server first:")
        print("   cd agent-services")
        print("   python start_server.py")
        return False
    
    # Test 2: Route Analysis
    print("\n2. Testing Route Analysis...")
    if not test_route_analysis():
        print("\n❌ Integration test failed: Route analysis not working")
        return False
    
    print("\n✅ All tests passed! Integration is working correctly.")
    print("\n💡 You can now:")
    print("   1. Open main.html in your browser")
    print("   2. Enter start and end locations")
    print("   3. Click 'Get Directions'")
    print("   4. Select a route to see AI analysis")
    
    return True

if __name__ == "__main__":
    main()
