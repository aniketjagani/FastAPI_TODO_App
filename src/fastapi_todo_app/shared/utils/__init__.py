"""
Shared utility functions
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def safe_dict_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return data.get(key, default) if isinstance(data, dict) else default


def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string"""
    if dt is None:
        return None
    return dt.isoformat()


def parse_comma_separated(value: Optional[str]) -> list:
    """Parse comma-separated string into list"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def log_operation(operation: str, entity: str, entity_id: Optional[int] = None):
    """Log business operation"""
    if entity_id:
        logger.info(f"Operation: {operation} - {entity} ID: {entity_id}")
    else:
        logger.info(f"Operation: {operation} - {entity}")


class PaginationHelper:
    """Helper class for pagination calculations"""
    
    @staticmethod
    def calculate_total_pages(total_items: int, page_size: int) -> int:
        """Calculate total number of pages"""
        if total_items <= 0 or page_size <= 0:
            return 0
        return (total_items + page_size - 1) // page_size
    
    @staticmethod
    def validate_pagination(skip: int, limit: int) -> tuple[int, int]:
        """Validate and normalize pagination parameters"""
        skip = max(0, skip)
        limit = max(1, min(limit, 1000))  # Cap at 1000
        return skip, limit