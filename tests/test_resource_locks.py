import pytest

from datetime import date
from models.resource import Resource
from models.time_slot import SlotSet, TimeSlot
from models.date_slot import DateSlot
from models.time import Time

class TestResourceLockAvailability:
    def setup_method(self):
        self.resource = Resource('r4', 'Laptop')

        monday = SlotSet({TimeSlot(Time(9, 0), Time(17, 0))})
        self.resource.set_default_availability({0: monday})

    @pytest.mark.parametrize(
        'lock_slots, start, end, expected',
        [
            # lock in the middle of the day -> unavailable
            (SlotSet({TimeSlot(Time(13, 0), Time(14, 0))}), Time(13, 30), Time(13, 45), False),
            # slot adjacent to lock end -> available
            (SlotSet({TimeSlot(Time(13, 0), Time(14, 0))}), Time(14, 0), Time(15, 0), True),
            # lock whole day -> unavailable
            (SlotSet({TimeSlot(Time(9, 0), Time(17, 0))}), Time(10, 0), Time(11, 0), False),
            # lock outside availability window -> no effect
            (SlotSet({TimeSlot(Time(17, 0), Time(18, 0))}), Time(10, 0), Time(11, 0), True),
        ],
    )
    def test_is_available_with_locks(self, lock_slots, start, end, expected):
        test_date = date(2025, 6, 23)  # Monday

        for s in lock_slots.slots:
            self.resource.lock(DateSlot(test_date, s.start_time, s.end_time))

        slot = DateSlot(test_date, start, end)
        assert self.resource.is_available(slot) is expected

