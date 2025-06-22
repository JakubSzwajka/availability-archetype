"""Quick playground demonstrating Resource availability features for a single user."""

from datetime import date


# NOTE: If you reorganised code into packages (models.time_slot, models.resource, etc.)
# adjust the imports below accordingly.
from models.resource import Resource
from models.time_slot import TimeSlotSet, TimeSlot
from models.date_time_slot import DateTimeSlot
from models.time import Time


def banner(title: str):
    print("\n" + "=" * 10, title, "=" * 10)


def main() -> None:
    # 1. Create resource with a 15-minute buffer before/after every lock
    resource = Resource("printer-1", "Office Printer", buffer_minutes=15)

    # 2. Default weekly availability (09:00-17:00 Monday-Friday)
    weekday_slot = TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})
    resource.set_default_availability({i: weekday_slot for i in range(0, 5)})

    banner("Default availability (Mon-Fri 9-17)")
    monday = date(2025, 6, 23)  # Monday
    print("10-11:", resource.is_available(DateTimeSlot(monday, Time(10, 0), Time(11, 0))))
    print("17-18:", resource.is_available(DateTimeSlot(monday, Time(17, 0), Time(18, 0))))

    # 3. Overwrite availability for a specific date (make Tuesday morning only)
    tuesday = date(2025, 6, 24)
    resource.set_overwrite_availability(
        tuesday,
        TimeSlotSet({TimeSlot(Time(9, 0), Time(12, 0))}),
    )

    banner("Tuesday overwrite (9-12 only)")
    print("10-11:", resource.is_available(DateTimeSlot(tuesday, Time(10, 0), Time(11, 0))))
    print("14-15:", resource.is_available(DateTimeSlot(tuesday, Time(14, 0), Time(15, 0))))

    # 4. Add a booking lock on Monday 13-14 (buffer makes it 12:45-14:15)
    resource.lock(DateTimeSlot(monday, Time(13, 0), Time(14, 0)))

    banner("Lock Monday 13-14 with 15-min buffer")
    print("12:30-12:44:", resource.is_available(DateTimeSlot(monday, Time(12, 30), Time(12, 44))))
    print("12:45-13:00:", resource.is_available(DateTimeSlot(monday, Time(12, 45), Time(13, 0))))
    print("14:00-14:14:", resource.is_available(DateTimeSlot(monday, Time(14, 0), Time(14, 14))))
    print("14:15-14:30:", resource.is_available(DateTimeSlot(monday, Time(14, 15), Time(14, 30))))

    # 5. Mark a full day off by locking 00:00-23:59
    day_off = date(2025, 7, 3)
    resource.lock(DateTimeSlot(day_off, Time(0, 0), Time(23, 59)))

    banner(f"Whole day off {day_off}")
    print("09-10:", resource.is_available(DateTimeSlot(day_off, Time(9, 0), Time(10, 0))))


if __name__ == "__main__":
    main()
