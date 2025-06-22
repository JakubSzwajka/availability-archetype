from dataclasses import dataclass
from enum import StrEnum
from datetime import time, date

@dataclass
class CalendarEvent:
    id: str

@dataclass
class Booking:
    id: str


@dataclass
class AvailabilitySlot:
    class SlotType(StrEnum):
        DEFAULT = "default"
        OVERWRITE = "overwrite"
        LOCK = "lock"

    class LockType(StrEnum):
        DAY_OFF = "day_off"
        BOOKING = "booking"
        GOOGLE_CALENDAR = "google_calendar"

    resource_id: str

    week_day: int | None # for default slots and locks for day off.
    date: date | None # for overwrite slots and locks

    start_time: time
    end_time: time

    slot_type: SlotType
    lock_type: LockType | None
    lock_by_id: str # id of the booking or calendar event that locked the slot.



@dataclass
class Resource:
    id: str
    name: str
    availability_slots: list[AvailabilitySlot] = []
