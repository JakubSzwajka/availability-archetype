import pytest

from models.time_slot import TimeSlot, SlotSet
from models.time import Time



@pytest.mark.parametrize(
    "initial_slots,new_slot,expected",
    [
        # add into empty set
        ([], TimeSlot(Time(9, 0), Time(10, 0)), {TimeSlot(Time(9, 0), Time(10, 0))}),
        # add non-overlapping (adjacent)
        ([TimeSlot(Time(9, 0), Time(10, 0))], TimeSlot(Time(10, 0), Time(11, 0)), {
            TimeSlot(Time(9, 0), Time(11, 0)),
        }),
        # add overlapping – should merge
        ([TimeSlot(Time(9, 0), Time(10, 0))], TimeSlot(Time(9, 30), Time(11, 0)), {
            TimeSlot(Time(9, 0), Time(11, 0))
        }),
        # chain merge: existing 9-10, 11-12; adding 10-11 merges all into 9-12
        ([TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(11, 0), Time(12, 0))], TimeSlot(Time(10, 0), Time(11, 0)), {
            TimeSlot(Time(9, 0), Time(12, 0))
        }),
    ],
)
def test_slot_set_add(initial_slots, new_slot, expected):
    ss = SlotSet(set(initial_slots))
    ss.add(new_slot)
    assert ss.slots == expected


@pytest.mark.parametrize(
    "initial_slots,remove_slot,expected",
    [
        # remove middle part – expect split into two
        ([TimeSlot(Time(9, 0), Time(12, 0))], TimeSlot(Time(10, 0), Time(11, 0)), {
            TimeSlot(Time(9, 0), Time(10, 0)),
            TimeSlot(Time(11, 0), Time(12, 0)),
        }),
        # remove prefix
        ([TimeSlot(Time(9, 0), Time(12, 0))], TimeSlot(Time(9, 0), Time(10, 0)), {
            TimeSlot(Time(10, 0), Time(12, 0)),
        }),
        # remove suffix
        ([TimeSlot(Time(9, 0), Time(12, 0))], TimeSlot(Time(11, 0), Time(12, 0)), {
            TimeSlot(Time(9, 0), Time(11, 0)),
        }),
        # remove exact match
        ([TimeSlot(Time(9, 0), Time(10, 0))], TimeSlot(Time(9, 0), Time(10, 0)), set()),
        # remove across two slots
        ([TimeSlot(Time(9, 0), Time(10, 0)), TimeSlot(Time(11, 0), Time(12, 0))], TimeSlot(Time(9, 30), Time(11, 30)), {
            TimeSlot(Time(9, 0), Time(9, 30)),
            TimeSlot(Time(11, 30), Time(12, 0)),
        }),
    ],
)
def test_slot_set_remove_success(initial_slots, remove_slot, expected):
    ss = SlotSet(set(initial_slots))
    ss.remove(remove_slot)
    assert ss.slots == expected


@pytest.mark.parametrize(
    "initial_slots,remove_slot",
    [
        # no overlap – should raise KeyError
        ([TimeSlot(Time(9, 0), Time(10, 0))], TimeSlot(Time(10, 0), Time(11, 0))),
    ],
)
def test_slot_set_remove_failure(initial_slots, remove_slot):
    ss = SlotSet(set(initial_slots))
    with pytest.raises(KeyError):
        ss.remove(remove_slot)


@pytest.mark.parametrize(
    "set_a,set_b,expected",
    [
        # simple overlapping merge
        (
            {TimeSlot(Time(9, 0), Time(10, 0))},
            {TimeSlot(Time(9, 30), Time(11, 0))},
            {TimeSlot(Time(9, 0), Time(11, 0))},
        ),
        # non-overlapping merge keeps both
        (
            {TimeSlot(Time(9, 0), Time(10, 0))},
            {TimeSlot(Time(10, 0), Time(11, 0))},
            {TimeSlot(Time(9, 0), Time(11, 0))},
        ),
    ],
)
def test_slot_set_merge(set_a, set_b, expected):
    ss_a = SlotSet(set_a)
    ss_b = SlotSet(set_b)
    ss_a.merge(ss_b)
    assert ss_a.slots == expected


def test_slot_set_overlaps():
    ss = SlotSet({TimeSlot(Time(9, 0), Time(10, 0))})
    assert ss.overlaps(TimeSlot(Time(9, 30), Time(9, 45))) is True
    assert ss.overlaps(TimeSlot(Time(10, 0), Time(11, 0))) is False


def test_slot_set_includes():
    ss = SlotSet({TimeSlot(Time(9, 0), Time(11, 0))})
    assert ss.includes(TimeSlot(Time(9, 30), Time(10, 0))) is True
    assert ss.includes(TimeSlot(Time(8, 0), Time(9, 0))) is False
