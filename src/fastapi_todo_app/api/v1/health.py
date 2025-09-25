"""
Health check endpoints for monitoring application status
"""

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time
import psutil
import os
from datetime import datetime, timezone

from ...shared.database.async_db import todos_db, employees_db
from ...shared.utils.caching import cache_service, cache_stats

router = APIRouter()


@router.get("/health", tags=["Health Check"])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/detailed", tags=["Health Check"])
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with database and cache status
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {},
        "system": {}
    }
    
    # Check database connectivity
    try:
        if todos_db:
            todos_healthy = await todos_db.health_check()
            todos_pool = todos_db.get_pool_status()
            health_data["services"]["todos_database"] = {
                "status": "healthy" if todos_healthy else "unhealthy",
                "pool_info": todos_pool
            }
        else:
            health_data["services"]["todos_database"] = {
                "status": "not_configured",
                "message": "Async database not initialized"
            }
            
        if employees_db:
            employees_healthy = await employees_db.health_check()
            employees_pool = employees_db.get_pool_status()
            health_data["services"]["employees_database"] = {
                "status": "healthy" if employees_healthy else "unhealthy", 
                "pool_info": employees_pool
            }
        else:
            health_data["services"]["employees_database"] = {
                "status": "not_configured",
                "message": "Async database not initialized"
            }
            
    except Exception as e:
        health_data["services"]["databases"] = {
            "status": "error",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Check cache service
    try:
        test_key = "health_check_test"
        await cache_service.set(test_key, "test_value", ttl=30)
        cached_value = await cache_service.get(test_key)
        
        health_data["services"]["cache"] = {
            "status": "healthy" if cached_value == "test_value" else "unhealthy",
            "stats": cache_stats.to_dict()
        }
        
        # Cleanup test key
        await cache_service.delete(test_key)
        
    except Exception as e:
        health_data["services"]["cache"] = {
            "status": "error",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # System metrics
    try:
        process = psutil.Process(os.getpid())
        health_data["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "process_memory_mb": process.memory_info().rss / 1024 / 1024,
            "process_cpu_percent": process.cpu_percent(),
            "uptime_seconds": time.time() - process.create_time()
        }
    except Exception as e:
        health_data["system"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Determine overall status
    service_statuses = [service.get("status") for service in health_data["services"].values()]
    if "error" in service_statuses or "unhealthy" in service_statuses:
        health_data["status"] = "degraded"
    
    return health_data


@router.get("/health/readiness", tags=["Health Check"])
async def readiness_check() -> JSONResponse:
    """
    Kubernetes readiness probe endpoint
    """
    try:
        # Check critical services
        ready = True
        
        # Check databases if configured
        if todos_db:
            todos_ready = await todos_db.health_check()
            ready = ready and todos_ready
            
        if employees_db:
            employees_ready = await employees_db.health_check()
            ready = ready and employees_ready
        
        if ready:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ready"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "error": str(e)}
        )


@router.get("/health/liveness", tags=["Health Check"])
async def liveness_check() -> JSONResponse:
    """
    Kubernetes liveness probe endpoint
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
    )