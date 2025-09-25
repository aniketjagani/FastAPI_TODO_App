#!/usr/bin/env python3
"""
Docker health check script for FastAPI TODO application
"""

import urllib.request
import urllib.error
import json
import sys
import os

def health_check():
    """Perform health check on the FastAPI application"""
    
    # Get health check URL
    host = os.environ.get('HEALTH_CHECK_HOST', 'localhost')
    port = os.environ.get('PORT', '8000')
    health_url = f"http://{host}:{port}/api/v1/health"
    
    try:
        # Make health check request
        with urllib.request.urlopen(health_url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check if status is healthy
                if data.get('status') == 'healthy':
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Health check failed: status = {data.get('status')}")
                    return False
            else:
                print(f"❌ Health check failed: HTTP {response.status}")
                return False
                
    except urllib.error.URLError as e:
        print(f"❌ Health check failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure