import pytest

from datetime import date
from models.resource import Resource
from models.time_slot import TimeSlotSet, TimeSlot
from models.date_time_slot import DateTimeSlot
from models.time import Time

class TestResourceBufferMinutes:
    def setup_method(self):
        # buffer 15 minutes
        self.resource = Resource('rb', 'Bike', buffer_minutes=15)

        # Monday 09-17 availability
        self.resource.set_default_availability({0: TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})})

        # Add a lock 13:00-14:00 on Monday
        self.lock_date = date(2025, 7, 7)  # Monday
        self.resource.lock(DateTimeSlot(self.lock_date, Time(13, 0), Time(14, 0)))

    @pytest.mark.parametrize(
        'start,end,expected',
        [
            # fully outside buffer on left side
            (Time(12, 30), Time(12, 44), True),
            # overlaps left buffer edge (12:45)
            (Time(12, 45), Time(12, 59), False),
            # inside actual lock
            (Time(13, 15), Time(13, 45), False),
            # overlaps right buffer edge (14:00-14:14)
            (Time(14, 0), Time(14, 14), False),
            # outside buffer on right
            (Time(14, 15), Time(14, 30), True),
        ],
    )
    def test_buffer_effect(self, start, end, expected):
        slot = DateTimeSlot(self.lock_date, start, end)
        assert self.resource.is_available(slot) is expected

    def test_back_to_back_locks_with_buffer(self):
        # existing lock 13-14 with buffer 15
        # add another lock 14:05-15:00 which overlaps buffer (should merge effectively)
        self.resource.lock(DateTimeSlot(self.lock_date, Time(14, 5), Time(15, 0)))

        # query 14:20-14:30 should be unavailable due to second lock
        assert self.resource.is_available(DateTimeSlot(self.lock_date, Time(14, 20), Time(14, 30))) is False

        # query 15:15-15:30 should be available (buffer ends 15:15)
        assert self.resource.is_available(DateTimeSlot(self.lock_date, Time(15, 15), Time(15, 30))) is True

