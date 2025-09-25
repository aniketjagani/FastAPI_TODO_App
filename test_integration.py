"""
Simple integration test to verify enhanced features are working
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8006"

def test_health_endpoint():
    """Test basic health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"Health endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health data: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health endpoint: {e}")
        return False

def test_metrics_endpoint():
    """Test metrics endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/advanced/monitoring/metrics")
        print(f"Metrics endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Metrics keys: {list(response.json().keys())}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing metrics endpoint: {e}")
        return False

def test_todos_endpoint():
    """Test basic todos functionality"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/todos/")
        print(f"Todos endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Todos response: {len(response.json())} items")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing todos endpoint: {e}")
        return False

def main():
    print("🧪 Testing Enhanced FastAPI Application Integration")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Metrics Endpoint", test_metrics_endpoint), 
        ("Todos Endpoint", test_todos_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
        print(f"✅ Passed" if result else "❌ Failed")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integrations working correctly!")
    else:
        print("⚠️ Some integrations need attention")

if __name__ == "__main__":
    main()