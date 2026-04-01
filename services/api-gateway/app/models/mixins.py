"""Re-export — mixins canónicos en `vulncentral_db`."""

from vulncentral_db.mixins import SoftDeleteMixin, TimestampMixin

__all__ = ["SoftDeleteMixin", "TimestampMixin"]
