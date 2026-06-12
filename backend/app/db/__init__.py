"""Database module for ArchAgent."""
from app.db.client import get_pool, close_pool

__all__ = ["get_pool", "close_pool"]
