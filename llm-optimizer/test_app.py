#!/usr/bin/env python3
import requests
import time
import sys

def test_app():
    """Test if the Flask app is running and accessible."""
    base_url = "http://localhost:5011"
    
    print("Testing LLM Training Optimizer App...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
        # Test main page
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Main page accessible!")
            print(f"Page title found: {'LLM Training Optimizer' in response.text}")
        else:
            print(f"❌ Main page failed with status {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the app. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        return False

if __name__ == "__main__":
    # Wait a moment for the app to start
    time.sleep(2)
    
    if test_app():
        print("\n🎉 App is running successfully!")
        print("You can access it at: http://localhost:5011")
    else:
        print("\n💥 App test failed. Check the Flask app output for errors.")
        sys.exit(1)