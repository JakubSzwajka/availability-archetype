
from datetime import date
from models.resource import Resource
from models.time_slot import TimeSlotSet, TimeSlot
from models.date_time_slot import DateTimeSlot
from models.time import Time


class TestResourceMixedCases:
    def setup_method(self):
        self.resource = Resource('r5', 'MeetingRoom')

        # default Monday 9-17
        self.resource.set_default_availability({0: TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})})

    def test_overwrite_and_lock_combination(self):
        test_date = date(2025, 6, 23)  # Monday

        # overwrite still full day 9-17 but represents custom schedule
        self.resource.set_overwrite_availability(test_date, TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))}))

        # lock a chunk 11-13 via API
        self.resource.lock(DateTimeSlot(test_date, Time(11, 0), Time(13, 0)))

        assert self.resource.is_available(DateTimeSlot(test_date, Time(10, 0), Time(11, 0))) is True
        assert self.resource.is_available(DateTimeSlot(test_date, Time(11, 30), Time(12, 0))) is False
        assert self.resource.is_available(DateTimeSlot(test_date, Time(16, 0), Time(17, 0))) is True

    def test_overwrite_disables_default_completely(self):
        test_date = date(2025, 6, 24)  # Tuesday (no default defined, but we still test behaviour)

        # create overwrite with zero availability (empty SlotSet)
        self.resource.set_overwrite_availability(test_date, TimeSlotSet())

        assert self.resource.is_available(DateTimeSlot(test_date, Time(10, 0), Time(11, 0))) is False

    def test_lock_outside_overwrite_window(self):
        test_date = date(2025, 6, 25)  # Wednesday, no default

        # overwrite 9-12
        self.resource.set_overwrite_availability(test_date, TimeSlotSet({TimeSlot(Time(9, 0), Time(12, 0))}))

        # lock 14-15 (outside overwrite)
        self.resource.lock(DateTimeSlot(test_date, Time(14, 0), Time(15, 0)))

        assert self.resource.is_available(DateTimeSlot(test_date, Time(10, 0), Time(11, 0))) is True

    def test_lock_and_unlock(self):
        test_date = date(2025, 6, 30)  # Monday

        self.resource.set_default_availability({0: TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})})

        booking_slot = DateTimeSlot(test_date, Time(14, 0), Time(15, 0))
        # lock then check unavailable
        self.resource.lock(booking_slot)
        assert self.resource.is_available(booking_slot) is False

        # unlock and check available again
        self.resource.unlock(booking_slot)
        assert self.resource.is_available(booking_slot) is True

