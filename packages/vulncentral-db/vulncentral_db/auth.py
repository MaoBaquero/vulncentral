"""Hash y verificación de contraseñas (bcrypt) — compartido API/worker."""

import bcrypt

_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    """Devuelve hash bcrypt para almacenar en la columna `password`."""
    raw = plain.encode("utf-8")
    if len(raw) > _BCRYPT_MAX_BYTES:
        raise ValueError(f"contraseña demasiado larga (máx. {_BCRYPT_MAX_BYTES} bytes en bcrypt)")
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12))
    return hashed.decode("ascii")


def verify_password(plain: str, password_hash: str) -> bool:
    """Comprueba texto plano contra el hash almacenado."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False
