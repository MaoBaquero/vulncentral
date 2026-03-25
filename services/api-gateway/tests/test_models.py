"""Modelos, metadata y hashing de contraseñas (sin BD en vivo)."""

from sqlalchemy.schema import CheckConstraint

from app.db.base import Base
from app.models import User
from app.security.password import hash_password, verify_password


def test_metadata_contains_core_tables() -> None:
    names = {t.name for t in Base.metadata.sorted_tables}
    assert names >= {
        "users",
        "projects",
        "scans",
        "vulnerabilities",
        "audit_logs",
        "use_cases",
        "roles",
        "permissions",
    }


def test_permissions_columns_c_r_u_d() -> None:
    cols = {c.name for c in Base.metadata.tables["permissions"].columns}
    assert {"c", "r", "u", "d"}.issubset(cols)


def test_user_set_password_stores_bcrypt_hash() -> None:
    starter = hash_password("bootstrap")
    user = User(name="Test User", email="test@example.com", password=starter)
    user.set_password("my_secret_password")
    assert user.password != "my_secret_password"
    assert user.password.startswith("$2")
    assert verify_password("my_secret_password", user.password)


def test_user_password_column_rejects_plain_text() -> None:
    starter = hash_password("bootstrap")
    user = User(name="U", email="u@example.com", password=starter)
    try:
        user.password = "plain_text_not_allowed"
    except ValueError as e:
        assert "bcrypt" in str(e).lower() or "hash" in str(e).lower()
    else:
        raise AssertionError("se esperaba ValueError al asignar texto plano")


def test_vulnerabilities_line_number_check() -> None:
    t = Base.metadata.tables["vulnerabilities"]
    names = {c.name for c in t.constraints if isinstance(c, CheckConstraint)}
    assert "ck_vulnerabilities_line_number" in names
