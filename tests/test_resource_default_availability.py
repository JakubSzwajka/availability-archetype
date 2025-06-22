import pytest

from datetime import date
from models.resource import Resource
from models.time_slot import SlotSet, TimeSlot
from models.date_slot import DateSlot
from models.time import Time

class TestResourceDefaultAvailability:
    def setup_method(self):
        self.resource = Resource('r1', 'Printer')

        # Monday 09:00-17:00
        monday = SlotSet({TimeSlot(Time(9, 0), Time(17, 0))})

        # Tuesday split availability 08-12 and 13-17
        tuesday = SlotSet({
            TimeSlot(Time(8, 0), Time(12, 0)),
            TimeSlot(Time(13, 0), Time(17, 0)),
        })
        self.resource.set_default_availability({0: monday, 1: tuesday})

    @pytest.mark.parametrize(
        'test_date,start,end,expected',
        [
            # Monday inside window
            (date(2025, 6, 23), Time(9, 30), Time(10, 30), True),
            # Monday outside window
            (date(2025, 6, 23), Time(17, 0), Time(18, 0), False),
            # Tuesday inside morning slot
            (date(2025, 6, 24), Time(10, 0), Time(11, 0), True),
            # Tuesday gap between slots
            (date(2025, 6, 24), Time(12, 0), Time(13, 0), False),
            # Tuesday slot spanning across the gap 11:30-13:30 -> unavailable
            (date(2025, 6, 24), Time(11, 30), Time(13, 30), False),
            # Thursday no availability defined
            (date(2025, 6, 26), Time(9, 0), Time(10, 0), False),
        ],
    )
    def test_is_available_from_default(self, test_date, start, end, expected):
        slot = DateSlot(test_date, start, end)
        assert self.resource.is_available(slot) is expected


    def test_is_available_without_default(self):
        resource = Resource('r2', 'Projector')
        slot = DateSlot(date(2025, 6, 23), Time(9, 0), Time(10, 0))
        assert resource.is_available(slot) is False

    def test_explicit_empty_default(self):
        resource = Resource('r6', 'Scanner')
        resource.set_default_availability({0: SlotSet()})
        slot = DateSlot(date(2025, 6, 23), Time(9, 0), Time(10, 0))
        assert resource.is_available(slot) is False
