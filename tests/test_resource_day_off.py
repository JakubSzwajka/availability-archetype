import pytest

from datetime import date
from models.resource import Resource
from models.time_slot import TimeSlotSet, TimeSlot
from models.date_time_slot import DateTimeSlot
from models.time import Time


class TestResourceDayOff:
    def setup_method(self):
        self.resource = Resource("rd", "Drill")
        # Monday 09-17 default
        self.resource.set_default_availability(
            {0: TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})}
        )

        # choose a Monday as day-off
        self.day_off = date(2025, 8, 4)  # Monday

        # lock whole day (00:00-23:59)
        self.resource.lock(DateTimeSlot(self.day_off, Time(0, 0), Time(23, 59)))

    @pytest.mark.parametrize(
        "start,end",
        [
            (Time(0, 0), Time(7, 0)),
            (Time(9, 0), Time(10, 0)),
            (Time(16, 0), Time(17, 0)),
            (Time(22, 30), Time(23, 59)),
        ],
    )
    def test_unavailable_whole_day(self, start: Time, end: Time):
        assert (
            self.resource.is_available(DateTimeSlot(self.day_off, start, end)) is False
        )

    def test_other_day_still_available(self):
        other_day = date(2025, 8, 5)  # Tuesday
        assert (
            self.resource.is_available(
                DateTimeSlot(other_day, Time(10, 0), Time(11, 0))
            )
            is False
        )  # no default Tuesday

        # add default Tuesday to verify positive
        self.resource.set_default_availability(
            {1: TimeSlotSet({TimeSlot(Time(9, 0), Time(17, 0))})}
        )
        assert (
            self.resource.is_available(
                DateTimeSlot(other_day, Time(10, 0), Time(11, 0))
            )
            is True
        )

    def test_day_off_unlock(self):
        # unlock whole day and ensure availability returns
        self.resource.unlock(DateTimeSlot(self.day_off, Time(0, 0), Time(23, 59)))
        assert (
            self.resource.is_available(
                DateTimeSlot(self.day_off, Time(10, 0), Time(11, 0))
            )
            is True
        )
