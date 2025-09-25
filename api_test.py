#!/usr/bin/env python3
"""
Simple API test script to verify the FastAPI application is working
"""

import requests
import json
import time

def test_api():
    base_url = "http://127.0.0.1:8002"
    
    try:
        # Test health endpoint
        print("🔍 Testing Health Endpoint...")
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Health Check: {response.status_code}")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'Unknown')}")
            print(f"   Timestamp: {health_data.get('timestamp', 'Unknown')}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            
        # Test detailed health endpoint
        print("\n🔍 Testing Detailed Health Endpoint...")
        response = requests.get(f"{base_url}/api/v1/health/detailed", timeout=5)
        if response.status_code == 200:
            print(f"✅ Detailed Health Check: {response.status_code}")
            detailed_data = response.json()
            print(f"   Database Status: {detailed_data.get('database', {}).get('status', 'Unknown')}")
            print(f"   Background Tasks: {detailed_data.get('background_tasks', {}).get('status', 'Unknown')}")
        else:
            print(f"❌ Detailed Health Check Failed: {response.status_code}")
            
        # Test performance metrics endpoint  
        print("\n🔍 Testing Performance Metrics Endpoint...")
        response = requests.get(f"{base_url}/api/v1/health/metrics", timeout=5)
        if response.status_code == 200:
            print(f"✅ Performance Metrics: {response.status_code}")
            metrics_data = response.json()
            print(f"   Active Workers: {metrics_data.get('background_tasks', {}).get('active_workers', 'Unknown')}")
        else:
            print(f"❌ Performance Metrics Failed: {response.status_code}")
            
        # Test TODO endpoints (basic functionality)
        print("\n🔍 Testing TODO Endpoints...")
        response = requests.get(f"{base_url}/api/v1/todos", timeout=5)
        print(f"📋 GET /todos: {response.status_code}")
        
        # Test Employee endpoints (basic functionality)
        print("\n🔍 Testing Employee Endpoints...")
        response = requests.get(f"{base_url}/api/v1/employees", timeout=5)
        print(f"👥 GET /employees: {response.status_code}")
        
        print("\n🎉 API Testing Complete!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the FastAPI server is running on http://127.0.0.1:8001")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_api()