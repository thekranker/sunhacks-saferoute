#!/usr/bin/env python3
"""
Startup script for the SafeRoute AI Analysis API server.
This script handles environment setup and starts the Flask server.
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set!")
        print("\nPlease set your Google API key:")
        print("1. Create a .env file in the agent-services directory")
        print("2. Add: GOOGLE_API_KEY=your-api-key-here")
        print("3. Or run: export GOOGLE_API_KEY='your-api-key-here'")
        return False
    
    print("✅ Environment variables configured")
    return True

def install_requirements():
    """Install required Python packages."""
    try:
        import subprocess
        requirements_file = Path(__file__).parent / 'requirements.txt'
        if requirements_file.exists():
            print("📦 Installing Python dependencies...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
            print("✅ Dependencies installed successfully")
        else:
            print("⚠️ requirements.txt not found, skipping dependency installation")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Could not install dependencies: {e}")
        print("Please install manually: pip install -r requirements.txt")
    
    return True

def start_server():
    """Start the Flask server."""
    try:
        from app import app
        print("\n🚀 Starting SafeRoute AI Analysis API...")
        print("📍 Server will be available at: http://localhost:5001")
        print("🔗 API endpoints:")
        print("   POST /analyze-route - Analyze route safety")
        print("   GET /health - Health check")
        print("   GET / - API information")
        print("\n💡 To stop the server, press Ctrl+C")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5001)
        
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        print("Make sure you're in the agent-services directory and all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def main():
    """Main startup function."""
    print("🤖 SafeRoute AI Analysis API Startup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("❌ Error: app.py not found!")
        print("Please run this script from the agent-services directory.")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("⚠️ Continuing without installing dependencies...")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
