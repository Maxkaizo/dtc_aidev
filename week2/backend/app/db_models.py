"""Portable SQLAlchemy tables; API/Pydantic schemas remain in models.py."""

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventRow(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(3))
    revision: Mapped[int] = mapped_column(BigInteger, default=0)


class GroupRow(Base):
    __tablename__ = "groups"
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), primary_key=True)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    representative: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("event_id", "position"),)


class AttendeeRow(Base):
    __tablename__ = "attendees"
    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(80))
    categories: Mapped[list[str]] = mapped_column(JSON)
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        ForeignKeyConstraint(["event_id", "group_id"], ["groups.event_id", "groups.id"]),
        UniqueConstraint("event_id", "group_id", "position"),
    )


class ExpenseRow(Base):
    __tablename__ = "expenses"
    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(120))
    amount: Mapped[int] = mapped_column(BigInteger)
    category: Mapped[str] = mapped_column(String(10))
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        ForeignKeyConstraint(["event_id", "group_id"], ["groups.event_id", "groups.id"]),
        UniqueConstraint("event_id", "position"),
        CheckConstraint("amount > 0 AND amount <= 10000000000", name="expense_amount_range"),
    )


class AccountRow(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class TokenRow(Base):
    __tablename__ = "tokens"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    expires_at: Mapped[float] = mapped_column(Float, index=True)
