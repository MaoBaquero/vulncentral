"""Re-export — canónico en `vulncentral_db.auth`."""

from vulncentral_db.auth import hash_password, verify_password

__all__ = ["hash_password", "verify_password"]
