#!/usr/bin/env python3
"""
Quick test script to verify the application can start up correctly.
Run this to test your installation before starting the server.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from app.main import app
        print("✅ FastAPI app imports successfully")
    except Exception as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        return False
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Debug mode: {settings.DEBUG}")
        print(f"   - Host: {settings.HOST}")
        print(f"   - Port: {settings.PORT}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    try:
        from app.api.v1.learning.basic_agents import router as basic_router
        from app.api.v1.learning.agent_tools import router as tools_router
        from app.api.v1.learning.multi_agent import router as multi_router
        print("✅ All learning API modules import successfully")
    except Exception as e:
        print(f"❌ Failed to import learning modules: {e}")
        return False
    
    return True

def test_app_creation():
    """Test that the FastAPI app can be created."""
    print("\nTesting app creation...")
    
    try:
        from app.main import create_app
        app = create_app()
        print("✅ FastAPI app created successfully")
        print(f"   - Title: {app.title}")
        print(f"   - Version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ Failed to create FastAPI app: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Microsoft Agent Framework Reference API - Startup Test ===\n")
    
    # Test Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    else:
        print("✅ Python version compatible")
    
    # Test imports
    if not test_imports():
        return False
    
    # Test app creation
    if not test_app_creation():
        return False
    
    print("\n=== All Tests Passed! ===")
    print("\nYou can now start the server with:")
    print("  python3 -m app.main")
    print("  or")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nOnce running, visit:")
    print("  http://localhost:8000/docs - Interactive API documentation")
    print("  http://localhost:8000/ - API overview")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)