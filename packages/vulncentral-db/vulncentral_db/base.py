"""Base declarativa SQLAlchemy."""

from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase

BigIntPk = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""
