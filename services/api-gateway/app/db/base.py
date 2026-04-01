"""Re-export — canónico en paquete `vulncentral_db` (BD compartida API/worker)."""

from vulncentral_db.base import Base, BigIntPk

__all__ = ["Base", "BigIntPk"]
