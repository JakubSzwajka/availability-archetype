import pytest
from models.time_slot import TimeSlot
from models.time import Time


class TestTimeSlot:
    @pytest.mark.parametrize("slot1, slot2, expected", [
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(10, 0), Time(11, 0)), False),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(11, 0), Time(12, 0)), False),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(10, 0)), True),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(11, 0)), True),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(8, 0), Time(9, 30)), True),
    ])
    def test_Time_slot_overlaps(self, slot1, slot2, expected):
        assert slot1.overlaps(slot2) == expected

    @pytest.mark.parametrize("slot1, slot2, expected", [
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(10, 0), Time(11, 0)), False),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(11, 0), Time(12, 0)), False),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(10, 0)), True),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(11, 0)), False),
        (TimeSlot(Time(9, 0), Time(11, 0)), TimeSlot(Time(9, 0), Time(10, 0)), True),
    ])
    def test_Time_slot_includes(self, slot1, slot2, expected):
        assert slot1.includes(slot2) == expected

    @pytest.mark.parametrize("slot1, slot2, expected", [
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(10, 0), Time(11, 0)), TimeSlot(Time(9, 0), Time(11, 0))),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(10, 0))),
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(11, 0)), TimeSlot(Time(9, 0), Time(11, 0))),
        (TimeSlot(Time(9, 0), Time(11, 0)), TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(11, 0))),
        (TimeSlot(Time(10, 0), Time(11, 0)), TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(9, 0), Time(11, 0))),
    ])
    def test_Time_slot_merge_success(self, slot1, slot2, expected):
        assert slot1.merge(slot2) == expected

    @pytest.mark.parametrize("slot1, slot2", [
        (TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(11, 0), Time(12, 0))),
    ])
    def test_Time_slot_merge_failure(self, slot1, slot2):
        with pytest.raises(ValueError):
            slot1.merge(slot2)

    # -------------------- SUBTRACT --------------------

    @pytest.mark.parametrize("slot1, slot2, expected", [
        # other fully inside -> two pieces
        (
            TimeSlot(Time(9, 0), Time(12, 0)),
            TimeSlot(Time(10, 0), Time(11, 0)),
            {TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(11, 0), Time(12, 0))},
        ),
        # other covers beginning
        (
            TimeSlot(Time(9, 0), Time(12, 0)),
            TimeSlot(Time(9, 0), Time(10, 0)),
            {TimeSlot(Time(10, 0), Time(12, 0))},
        ),
        # other covers end
        (
            TimeSlot(Time(9, 0), Time(12, 0)),
            TimeSlot(Time(11, 0), Time(12, 0)),
            {TimeSlot(Time(9, 0), Time(11, 0))},
        ),
        # other equals self -> empty set
        (
            TimeSlot(Time(9, 0), Time(10, 0)),
            TimeSlot(Time(9, 0), Time(10, 0)),
            set(),
        ),
        # other extends past start
        (
            TimeSlot(Time(9, 0), Time(10, 0)),
            TimeSlot(Time(8, 0), Time(9, 30)),
            {TimeSlot(Time(9, 30), Time(10, 0))},
        ),
        # other extends past end
        (
            TimeSlot(Time(9, 0), Time(10, 0)),
            TimeSlot(Time(9, 30), Time(11, 0)),
            {TimeSlot(Time(9, 0), Time(9, 30))},
        ),
    ])
    def test_Time_slot_subtract_success(self, slot1, slot2, expected):
        result_set = slot1.subtract(slot2).slots
        assert result_set == expected

    @pytest.mark.parametrize("slot1, slot2", [
        # no overlap -> error
        (
            TimeSlot(Time(9, 0), Time(10, 0)),
            TimeSlot(Time(10, 0), Time(11, 0)),
        ),
    ])
    def test_Time_slot_subtract_failure(self, slot1, slot2):
        with pytest.raises(ValueError):
            slot1.subtract(slot2)