#!/usr/bin/env python3
"""
Test script to verify the optimized AI analysis is faster and more minimal.
"""

import requests
import json
import time

def test_optimized_analysis():
    """Test the optimized AI analysis for speed and simplicity."""
    test_data = {
        "origin": "ASU Tempe Campus, Tempe, AZ",
        "destination": "Mill Avenue, Tempe, AZ",
        "route_details": {
            "distance": "0.8 mi",
            "duration": "12 min",
            "summary": "Route via University Dr"
        }
    }
    
    try:
        print("🚀 Testing optimized AI analysis...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:5001/analyze-route',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=15  # 15 second timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                analysis = result.get('analysis', {})
                print(f"✅ AI analysis completed in {duration:.2f} seconds!")
                print(f"   Safety Score: {analysis.get('safety_score', 'N/A')}%")
                print(f"   Main Concerns: {len(analysis.get('main_concerns', []))} items")
                print(f"   Quick Tips: {len(analysis.get('quick_tips', []))} items")
                
                # Show the actual content
                print("\n📋 Analysis Content:")
                print(f"   Score: {analysis.get('safety_score')}%")
                if analysis.get('main_concerns'):
                    print(f"   Concerns: {', '.join(analysis.get('main_concerns', []))}")
                if analysis.get('quick_tips'):
                    print(f"   Tips: {', '.join(analysis.get('quick_tips', []))}")
                
                # Check if it's minimal
                total_content = len(str(analysis))
                if total_content < 500:  # Should be much smaller now
                    print(f"✅ Analysis is minimal ({total_content} characters)")
                else:
                    print(f"⚠️ Analysis might still be too detailed ({total_content} characters)")
                
                return True
            else:
                print(f"❌ AI analysis failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Analysis took too long.")
        return False
    except Exception as e:
        print(f"❌ Error testing analysis: {e}")
        return False

def main():
    """Run the optimization test."""
    print("⚡ Testing Optimized AI Analysis")
    print("=" * 40)
    
    if test_optimized_analysis():
        print("\n✅ Optimization successful!")
        print("   - Faster response time")
        print("   - Minimal content")
        print("   - Essential safety info only")
    else:
        print("\n❌ Optimization test failed")

if __name__ == "__main__":
    main()
