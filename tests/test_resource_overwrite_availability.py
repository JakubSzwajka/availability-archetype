import pytest

from datetime import date
from models.resource import Resource
from models.time_slot import TimeSlotSet, TimeSlot
from models.date_time_slot import DateTimeSlot
from models.time import Time

class TestResourceOverwriteAvailability:
    def setup_method(self):
        self.resource = Resource('r3', 'Camera')

        # default availability same as previous suite
        monday = TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})
        tuesday = TimeSlotSet({
            TimeSlot(Time(8, 0), Time(12, 0)),
            TimeSlot(Time(13, 0), Time(17, 0)),
        })
        self.resource.set_default_availability({0: monday, 1: tuesday})

    @pytest.mark.parametrize(
        'overwrite_slots, test_date, start, end, expected',
        [
            # overwrite narrows monday window to 10-12
            (
                TimeSlotSet({TimeSlot(Time(10, 0), Time(12, 0))}),
                date(2025, 6, 23),
                Time(10, 30),
                Time(11, 0),
                True,
            ),
            # inside default but outside overwrite -> unavailable
            (
                TimeSlotSet({TimeSlot(Time(10, 0), Time(12, 0))}),
                date(2025, 6, 23),
                Time(14, 0),
                Time(15, 0),
                False,
            ),
            # overwrite removes all availability (empty set)
            (
                TimeSlotSet(),
                date(2025, 6, 24),
                Time(10, 0),
                Time(11, 0),
                False,
            ),
            # default still applies on date without overwrite
            (
                TimeSlotSet({TimeSlot(Time(10, 0), Time(12, 0))}),
                date(2025, 6, 24),  # Tuesday, but overwrite is for Monday
                Time(10, 0),
                Time(11, 0),
                True,
            ),
        ],
    )
    def test_is_available_overwrite(self, overwrite_slots, test_date, start, end, expected):
        # apply overwrite regardless (may be empty)
        self.resource.set_overwrite_availability(test_date, overwrite_slots)

        slot = DateTimeSlot(test_date, start, end)
        assert self.resource.is_available(slot) is expected
