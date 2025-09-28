#!/usr/bin/env python3
"""
Test script to verify the new user-friendly UI with automatic AI analysis.
"""

import requests
import json
import time

def test_multiple_routes_analysis():
    """Test AI analysis for multiple routes to simulate the new UI behavior."""
    test_routes = [
        {
            "origin": "ASU Tempe Campus, Tempe, AZ",
            "destination": "Mill Avenue, Tempe, AZ",
            "route_details": {
                "distance": "0.8 mi",
                "duration": "12 min",
                "summary": "Route via University Dr"
            }
        },
        {
            "origin": "Downtown Phoenix, AZ",
            "destination": "Phoenix Convention Center, Phoenix, AZ",
            "route_details": {
                "distance": "1.2 mi",
                "duration": "18 min",
                "summary": "Route via Washington St"
            }
        }
    ]
    
    print("🚀 Testing new UI with multiple route analysis...")
    start_time = time.time()
    
    # Test all routes in parallel (like the new UI does)
    ai_promises = []
    for i, route_data in enumerate(test_routes):
        print(f"   📍 Starting AI analysis for route {i+1}...")
        ai_promises.append(analyze_single_route(route_data, i+1))
    
    # Wait for all analyses to complete
    results = []
    for promise in ai_promises:
        try:
            result = promise
            results.append(result)
        except Exception as e:
            print(f"   ❌ Route analysis failed: {e}")
            results.append({
                "success": False,
                "error": str(e),
                "analysis": {
                    "safety_score": 50,
                    "main_concerns": ["Analysis failed"],
                    "quick_tips": ["Use caution"]
                }
            })
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ All analyses completed in {duration:.2f} seconds!")
    
    # Display results in the new UI format
    for i, result in enumerate(results):
        print(f"\n📍 Route {i+1} Analysis:")
        if result.get('success'):
            analysis = result.get('analysis', {})
            score = analysis.get('safety_score', 0)
            concerns = analysis.get('main_concerns', [])
            tips = analysis.get('quick_tips', [])
            
            print(f"   AI Score: {score}%")
            if concerns:
                print(f"   Concerns: {', '.join(concerns[:2])}")
            if tips:
                print(f"   Tips: {', '.join(tips[:2])}")
        else:
            print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
    
    return len([r for r in results if r.get('success')]) == len(test_routes)

def analyze_single_route(route_data, route_num):
    """Analyze a single route (simulating the parallel processing)."""
    try:
        response = requests.post(
            'http://localhost:5002/analyze-route',
            json=route_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ Route {route_num} analysis completed")
                return result
            else:
                print(f"   ⚠️ Route {route_num} analysis failed: {result.get('error')}")
                return result
        else:
            print(f"   ❌ Route {route_num} API error: {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "analysis": {
                    "safety_score": 50,
                    "main_concerns": ["API error"],
                    "quick_tips": ["Use caution"]
                }
            }
    except Exception as e:
        print(f"   ❌ Route {route_num} request failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "analysis": {
                "safety_score": 50,
                "main_concerns": ["Request failed"],
                "quick_tips": ["Use caution"]
            }
        }

def main():
    """Test the new UI functionality."""
    print("🎨 Testing New User-Friendly UI")
    print("=" * 40)
    
    # Test API health first
    try:
        response = requests.get('http://localhost:5002/health', timeout=5)
        if response.status_code != 200:
            print("❌ API server not running. Please start it first:")
            print("   cd agent-services && python start_server.py")
            return False
    except:
        print("❌ Cannot connect to API server. Please start it first:")
        print("   cd agent-services && python start_server.py")
        return False
    
    print("✅ API server is running")
    
    # Test multiple routes analysis
    if test_multiple_routes_analysis():
        print("\n🎉 New UI test successful!")
        print("\n💡 What you'll see in the browser:")
        print("   1. Routes appear immediately with 'AI: Loading...' indicators")
        print("   2. AI analysis loads automatically in background")
        print("   3. Each route shows AI score, concerns, and tips")
        print("   4. No need to click individual routes for analysis")
        return True
    else:
        print("\n❌ New UI test failed")
        return False

if __name__ == "__main__":
    main()
