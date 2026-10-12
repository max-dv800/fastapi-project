from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum, auto
import uuid

from sqlalchemy import (
    DECIMAL,
    UUID,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Status(StrEnum):
    DRAFT = auto()
    PUBLISHED = auto()
    CANCELLED = auto()
    FINISHED = auto()


class StatusBooking(StrEnum):
    PENDING = auto()
    CONFIRMED = auto()
    CANCELLED = auto()
    EXPIRED = auto()


class StatusPayment(StrEnum):
    PENDING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    REFUNDED = auto()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, index=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    events: Mapped[list[Event]] = relationship(
        back_populates="organizer", cascade="all, delete-orphan", lazy="selectin"
    )
    my_booking: Mapped[list[Booking]] = relationship(
        back_populates="user_booking", cascade="all, delete-orphan", lazy="selectin"
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, index=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, default=capacity)
    price: Mapped[Decimal] = mapped_column(DECIMAL)

    organizer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    organizer: Mapped[User] = relationship(back_populates="events", lazy="selectin")

    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    booking: Mapped[list[Booking]] = relationship(
        "Booking", back_populates="event", lazy="selectin"
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, index=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user_booking: Mapped[User] = relationship(back_populates="my_booking")

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE")
    )
    event: Mapped[Event] = relationship(back_populates="booking")

    seats: Mapped[int] = mapped_column(Integer)
    status: Mapped[StatusBooking] = mapped_column(
        Enum(StatusBooking), default=StatusBooking.PENDING
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now() + timedelta(minutes=30)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    payment: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="booking", lazy="selectin"
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, index=True, default=uuid.uuid4
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE")
    )
    booking: Mapped[list[Booking]] = relationship(
        "Booking", back_populates="payment", lazy="selectin"
    )

    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    status: Mapped[StatusPayment] = mapped_column(
        Enum(StatusPayment), default=StatusPayment.PENDING
    )
    external_id: Mapped[int] = mapped_column(Integer, default=1001)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
