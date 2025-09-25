"""
Database query optimization utilities
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Type, Tuple
from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from sqlalchemy.sql import Select
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Query performance tracking"""
    query: str
    execution_time: float
    rows_returned: int
    rows_examined: Optional[int] = None
    cache_hit: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class QueryOptimizer:
    """Database query optimization and monitoring"""
    
    def __init__(self):
        self.query_metrics: List[QueryPerformanceMetrics] = []
        self.slow_query_threshold = 1.0  # seconds
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl = 300  # 5 minutes
    
    @asynccontextmanager
    async def track_query(self, session: AsyncSession, query_name: str = ""):
        """Context manager for tracking query performance"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            yield session
        finally:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {query_name} took {execution_time:.3f}s"
                )
            
            # Store metrics
            metrics = QueryPerformanceMetrics(
                query=query_name,
                execution_time=execution_time,
                rows_returned=0,  # Would need to be set by caller
                timestamp=datetime.now(timezone.utc)
            )
            
            self.query_metrics.append(metrics)
            
            # Keep only recent metrics (last 1000)
            if len(self.query_metrics) > 1000:
                self.query_metrics = self.query_metrics[-1000:]
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryPerformanceMetrics]:
        """Get queries that exceeded the slow query threshold"""
        threshold = threshold or self.slow_query_threshold
        return [m for m in self.query_metrics if m.execution_time > threshold]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get comprehensive query statistics"""
        if not self.query_metrics:
            return {"message": "No query metrics available"}
        
        execution_times = [m.execution_time for m in self.query_metrics]
        
        return {
            "total_queries": len(self.query_metrics),
            "average_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "slow_queries_count": len(self.get_slow_queries()),
            "cache_hits": sum(1 for m in self.query_metrics if m.cache_hit),
            "cache_hit_ratio": sum(1 for m in self.query_metrics if m.cache_hit) / len(self.query_metrics),
        }


class EfficientQueryBuilder:
    """Build efficient database queries with optimizations"""
    
    @staticmethod
    def build_paginated_query(
        base_query: Select,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> Tuple[Select, Select]:
        """Build paginated query with count query"""
        # Validate parameters
        page = max(1, page)
        page_size = min(max(1, page_size), max_page_size)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build paginated query
        paginated_query = base_query.offset(offset).limit(page_size)
        
        # Build count query (remove ordering for efficiency)
        count_query = select(func.count()).select_from(base_query.alias())
        
        return paginated_query, count_query
    
    @staticmethod
    def add_eager_loading(query: Select, model_class: Type, relationships: List[str]) -> Select:
        """Add eager loading for relationships to avoid N+1 queries"""
        for relationship in relationships:
            if hasattr(model_class, relationship):
                # Use selectinload for collections, joinedload for single objects
                attr = getattr(model_class, relationship)
                if hasattr(attr.property, 'collection_class'):  # Collection relationship
                    query = query.options(selectinload(attr))
                else:  # Single object relationship
                    query = query.options(joinedload(attr))
        
        return query
    
    @staticmethod
    def build_filtered_query(
        base_query: Select,
        filters: Dict[str, Any],
        model_class: Type
    ) -> Select:
        """Build query with dynamic filters"""
        for field, value in filters.items():
            if value is None:
                continue
            
            if not hasattr(model_class, field):
                continue
            
            attr = getattr(model_class, field)
            
            # Handle different filter types
            if isinstance(value, list):
                # IN clause for lists
                base_query = base_query.where(attr.in_(value))
            elif isinstance(value, dict):
                # Handle range queries, etc.
                if 'gte' in value:
                    base_query = base_query.where(attr >= value['gte'])
                if 'lte' in value:
                    base_query = base_query.where(attr <= value['lte'])
                if 'gt' in value:
                    base_query = base_query.where(attr > value['gt'])
                if 'lt' in value:
                    base_query = base_query.where(attr < value['lt'])
                if 'contains' in value:
                    base_query = base_query.where(attr.contains(value['contains']))
                if 'startswith' in value:
                    base_query = base_query.where(attr.startswith(value['startswith']))
            else:
                # Exact match
                base_query = base_query.where(attr == value)
        
        return base_query


class BatchProcessor:
    """Efficient batch processing for database operations"""
    
    @staticmethod
    async def batch_insert(
        session: AsyncSession,
        model_class: Type,
        data_list: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[Any]:
        """Efficiently insert multiple records in batches"""
        inserted_objects = []
        
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            # Create model instances
            objects = [model_class(**data) for data in batch]
            
            # Add to session
            session.add_all(objects)
            
            # Flush to get IDs
            await session.flush()
            
            inserted_objects.extend(objects)
            
            # Log progress
            logger.debug(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
        
        return inserted_objects
    
    @staticmethod
    async def batch_update(
        session: AsyncSession,
        model_class: Type,
        updates: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """Efficiently update multiple records in batches"""
        total_updated = 0
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            for update_data in batch:
                # Extract ID and update data
                record_id = update_data.pop('id')
                
                # Build update query
                query = (
                    session.query(model_class)
                    .filter(model_class.id == record_id)
                )
                
                # Execute update
                result = await query.update(update_data)
                total_updated += result.rowcount if result else 0
            
            logger.debug(f"Updated batch {i//batch_size + 1}: {len(batch)} records")
        
        return total_updated
    
    @staticmethod
    async def batch_delete(
        session: AsyncSession,
        model_class: Type,
        ids: List[int],
        batch_size: int = 100
    ) -> int:
        """Efficiently delete multiple records in batches"""
        total_deleted = 0
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            # Build delete query
            result = await session.execute(
                text(f"DELETE FROM {model_class.__tablename__} WHERE id = ANY(:ids)"),
                {"ids": batch_ids}
            )
            
            total_deleted += result.rowcount
            
            logger.debug(f"Deleted batch {i//batch_size + 1}: {len(batch_ids)} records")
        
        return total_deleted


class ConnectionPoolMonitor:
    """Monitor database connection pool health"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get detailed connection pool status"""
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in_connections": pool.checkedin(),
            "checked_out_connections": pool.checkedout(),
            "overflow_connections": pool.overflow(),
            "invalid_connections": pool.invalid(),
            "total_connections": pool.size() + pool.overflow(),
            "utilization_percentage": (pool.checkedout() / pool.size()) * 100,
        }
    
    def is_healthy(self) -> bool:
        """Check if connection pool is healthy"""
        status = self.get_pool_status()
        
        # Pool is unhealthy if utilization is too high or there are many invalid connections
        return (
            status["utilization_percentage"] < 90 and
            status["invalid_connections"] < status["pool_size"] * 0.1
        )


# Global instances
query_optimizer = QueryOptimizer()


# Utility functions
async def execute_with_retry(
    session: AsyncSession,
    query,
    max_retries: int = 3,
    delay: float = 1.0
) -> Any:
    """Execute query with retry logic for transient failures"""
    for attempt in range(max_retries):
        try:
            return await session.execute(query)
        except Exception as e:
            logger.warning(f"Query attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                raise
            
            await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff


async def bulk_fetch_with_cursor(
    session: AsyncSession,
    query: Select,
    chunk_size: int = 1000
) -> List[Any]:
    """Fetch large result sets efficiently using cursor"""
    results = []
    offset = 0
    
    while True:
        chunk_query = query.offset(offset).limit(chunk_size)
        chunk_result = await session.execute(chunk_query)
        chunk_data = chunk_result.scalars().all()
        
        if not chunk_data:
            break
        
        results.extend(chunk_data)
        offset += chunk_size
        
        # Log progress for very large datasets
        if offset % 10000 == 0:
            logger.info(f"Fetched {offset} records...")
    
    return results