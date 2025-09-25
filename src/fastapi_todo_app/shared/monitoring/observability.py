"""
Advanced Observability and Monitoring System
"""

import json
import time
import traceback
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import psutil
import logging

# Configure structured logging
class StructuredLogger:
    """Structured logging with JSON format"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create JSON formatter
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": "%(lineno)d"}'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        extra_data = json.dumps(kwargs) if kwargs else ""
        self.logger.info(f"{message} {extra_data}")
    
    def error(self, message: str, **kwargs):
        extra_data = json.dumps(kwargs) if kwargs else ""
        self.logger.error(f"{message} {extra_data}")
    
    def warning(self, message: str, **kwargs):
        extra_data = json.dumps(kwargs) if kwargs else ""
        self.logger.warning(f"{message} {extra_data}")


@dataclass
class RequestMetric:
    """Data class for request metrics"""
    timestamp: datetime
    method: str
    path: str
    status_code: int
    response_time: float
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class SystemMetric:
    """Data class for system metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    active_connections: int


class MetricsCollector:
    """Advanced metrics collection and analysis"""
    
    def __init__(self, max_metrics: int = 10000):
        self.request_metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=1000)
        self.error_metrics: deque = deque(maxlen=1000)
        self.endpoint_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'max_time': 0,
            'min_time': float('inf'),
            'error_count': 0,
            'last_accessed': None
        })
        
        # Start system metrics collection
        asyncio.create_task(self._collect_system_metrics())
    
    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # Get system information
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get active connections (approximation)
                connections = len(psutil.net_connections())
                
                metric = SystemMetric(
                    timestamp=datetime.now(timezone.utc),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    disk_percent=disk.percent,
                    active_connections=connections
                )
                
                self.system_metrics.append(metric)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logging.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)
    
    def record_request(self, metric: RequestMetric):
        """Record request metric"""
        self.request_metrics.append(metric)
        
        # Update endpoint statistics
        endpoint_key = f"{metric.method}:{metric.path}"
        stats = self.endpoint_stats[endpoint_key]
        
        stats['count'] += 1
        stats['total_time'] += metric.response_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], metric.response_time)
        stats['min_time'] = min(stats['min_time'], metric.response_time)
        stats['last_accessed'] = metric.timestamp
        
        if metric.status_code >= 400:
            stats['error_count'] += 1
    
    def record_error(self, error_info: Dict[str, Any]):
        """Record error information"""
        error_info['timestamp'] = datetime.now(timezone.utc)
        self.error_metrics.append(error_info)
    
    def get_request_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """Get request statistics for the last N minutes"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.request_metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'requests_per_minute': 0
            }
        
        total_requests = len(recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / total_requests
        error_count = sum(1 for m in recent_metrics if m.status_code >= 400)
        error_rate = (error_count / total_requests) * 100
        requests_per_minute = total_requests / minutes
        
        return {
            'total_requests': total_requests,
            'avg_response_time': round(avg_response_time, 4),
            'error_rate': round(error_rate, 2),
            'requests_per_minute': round(requests_per_minute, 2),
            'status_codes': self._get_status_code_distribution(recent_metrics)
        }
    
    def _get_status_code_distribution(self, metrics: List[RequestMetric]) -> Dict[int, int]:
        """Get distribution of status codes"""
        distribution = defaultdict(int)
        for metric in metrics:
            distribution[metric.status_code] += 1
        return dict(distribution)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health"""
        if not self.system_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        latest = self.system_metrics[-1]
        
        # Determine health status
        status = 'healthy'
        alerts = []
        
        if latest.cpu_percent > 80:
            status = 'warning'
            alerts.append(f'High CPU usage: {latest.cpu_percent}%')
        
        if latest.memory_percent > 85:
            status = 'critical' if status != 'critical' else status
            alerts.append(f'High memory usage: {latest.memory_percent}%')
        
        if latest.disk_percent > 90:
            status = 'critical'
            alerts.append(f'High disk usage: {latest.disk_percent}%')
        
        return {
            'status': status,
            'alerts': alerts,
            'metrics': asdict(latest),
            'uptime_seconds': time.time() - psutil.boot_time()
        }
    
    def get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top endpoints by various metrics"""
        endpoints = []
        
        for endpoint, stats in self.endpoint_stats.items():
            endpoints.append({
                'endpoint': endpoint,
                **stats
            })
        
        # Sort by request count
        endpoints.sort(key=lambda x: x['count'], reverse=True)
        
        return endpoints[:limit]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [e for e in self.error_metrics if e['timestamp'] > cutoff_time]
        
        error_types = defaultdict(int)
        for error in recent_errors:
            error_types[error.get('type', 'Unknown')] += 1
        
        return {
            'total_errors': len(recent_errors),
            'error_types': dict(error_types),
            'error_rate_per_hour': len(recent_errors) / hours
        }


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Comprehensive observability middleware"""
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        self.logger = StructuredLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        user_agent = request.headers.get('user-agent')
        ip_address = request.client.host if request.client else None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            # Record error
            self.metrics_collector.record_error({
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc(),
                'method': method,
                'path': path,
                'ip_address': ip_address
            })
            
            self.logger.error(
                "Request failed",
                method=method,
                path=path,
                error=str(e),
                ip_address=ip_address
            )
            
            raise
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Record request metric
        metric = RequestMetric(
            timestamp=datetime.now(timezone.utc),
            method=method,
            path=path,
            status_code=status_code,
            response_time=response_time,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.metrics_collector.record_request(metric)
        
        # Log request
        log_data = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time': round(response_time, 4),
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        if status_code >= 400:
            self.logger.error("Request error", **log_data)
        elif response_time > 1.0:  # Slow request threshold
            self.logger.warning("Slow request", **log_data)
        else:
            self.logger.info("Request processed", **log_data)
        
        # Add performance headers
        response.headers["X-Response-Time"] = str(response_time)
        response.headers["X-Request-ID"] = f"{int(time.time())}-{hash(request.url.path)}"
        
        return response


class AlertManager:
    """Alert management system"""
    
    def __init__(self):
        self.alert_rules = {
            'high_error_rate': {'threshold': 5.0, 'window_minutes': 5},
            'slow_response_time': {'threshold': 2.0, 'window_minutes': 5},
            'high_cpu_usage': {'threshold': 85.0, 'window_minutes': 2},
            'high_memory_usage': {'threshold': 90.0, 'window_minutes': 2}
        }
        self.active_alerts = set()
    
    async def check_alerts(self, metrics_collector: MetricsCollector):
        """Check all alert conditions"""
        alerts_triggered = []
        
        # Check error rate
        stats = metrics_collector.get_request_stats(minutes=5)
        if stats['error_rate'] > self.alert_rules['high_error_rate']['threshold']:
            alert = f"High error rate: {stats['error_rate']}%"
            if alert not in self.active_alerts:
                alerts_triggered.append(alert)
                self.active_alerts.add(alert)
        
        # Check response time
        if stats['avg_response_time'] > self.alert_rules['slow_response_time']['threshold']:
            alert = f"Slow response time: {stats['avg_response_time']}s"
            if alert not in self.active_alerts:
                alerts_triggered.append(alert)
                self.active_alerts.add(alert)
        
        # Check system health
        health = metrics_collector.get_system_health()
        for alert_msg in health.get('alerts', []):
            if alert_msg not in self.active_alerts:
                alerts_triggered.append(alert_msg)
                self.active_alerts.add(alert_msg)
        
        return alerts_triggered


# Global instances
metrics_collector = MetricsCollector()
alert_manager = AlertManager()

# Export main components
__all__ = [
    'MetricsCollector',
    'ObservabilityMiddleware',
    'AlertManager',
    'StructuredLogger',
    'RequestMetric',
    'SystemMetric',
    'metrics_collector',
    'alert_manager'
]