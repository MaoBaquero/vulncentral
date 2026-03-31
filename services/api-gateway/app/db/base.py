"""Base declarativa SQLAlchemy."""

from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase

# SQLite autoincrementa correctamente con INTEGER; en PostgreSQL sigue siendo BIGINT.
BigIntPk = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""
