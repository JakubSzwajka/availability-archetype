from enum import StrEnum
from datetime import date as date_type, time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    DateTime,
    Integer,
    ForeignKey,
    Date,
    Time as SQLTime,
    Index,
    text,
)
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy_utils import DateTimeRangeType
from sqlalchemy import Integer, ARRAY
from sqlalchemy.dialects.postgresql import INT8RANGE


class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class ResourceModel(Base):
    __tablename__ = "resources"

    name: Mapped[str] = mapped_column(String, nullable=False)
    buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_upfront_days: Mapped[int] = mapped_column(Integer, nullable=False)

    availability_slots: Mapped[list["AvailabilitySlotModel"]] = relationship(
        back_populates="resource"
    )


class AvailabilitySlotModel(Base):
    __tablename__ = "resource_availability_slots"
    __table_args__ = (
        Index("ix_slot_resource", "resource_id"),
        # Default availability: equality on week_day, range on times; partial to only 'default' rows
        Index(
            "ix_slot_default",
            "week_day",
            "start_time",
            "end_time",
            "resource_id",
            postgresql_where=text("slot_type = 'default'"),
        ),
        # Overwrite + lock availability by exact date; partial to only those slot types
        Index(
            "ix_slot_dated",
            "date",
            "start_time",
            "end_time",
            "resource_id",
            postgresql_where=text("slot_type in ('overwrite','lock')"),
        ),
    )

    class SlotType(StrEnum):
        DEFAULT = "default"
        OVERWRITE = "overwrite"
        LOCK = "lock"

    class LockType(StrEnum):
        DAY_OFF = "day_off"
        BOOKING = "booking"
        GOOGLE_CALENDAR = "google_calendar"

    resource_id: Mapped[str] = mapped_column(
        String, ForeignKey("resources.id"), nullable=False
    )
    resource: Mapped[ResourceModel] = relationship(back_populates="availability_slots")

    # week_day: Mapped[int] = mapped_column(Integer, nullable=True)
    # date: Mapped[date_type] = mapped_column(Date, nullable=True)
    # start_time: Mapped[time] = mapped_column(SQLTime, nullable=False)
    # end_time: Mapped[time] = mapped_column(SQLTime, nullable=False)

    slot_type: Mapped[SlotType] = mapped_column(String, nullable=False)
    lock_type: Mapped[LockType] = mapped_column(String, nullable=True)
    lock_by_id: Mapped[str] = mapped_column(String, nullable=True)

    datetime_slot = mapped_column(DateTimeRangeType, nullable=False)
    week_day_slot = mapped_column(ARRAY(INT8RANGE), nullable=False)


# class AvailabilityDateTimeSlotModel(Base):
#     __tablename__ = "resource_availability_slots_2"

#     resource_id: Mapped[str] = mapped_column(
#         String, ForeignKey("resources.id"), nullable=False
#     )
#     resource: Mapped[ResourceModel] = relationship(back_populates="availability_slots")
#     datetime_slot = mapped_column(DateTimeRangeType, nullable=False)
#     week_day_slot = mapped_column(ARRAY(INT8RANGE), nullable=False)
