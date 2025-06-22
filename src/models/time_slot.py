from abc import abstractmethod
from dataclasses import dataclass, field
from models.time import Time

class TimeSlot:
    start_time: Time
    end_time: Time

    def __init__(self, start_time: Time, end_time: Time):
        if start_time >= end_time:
            raise ValueError(f"Invalid time slot: {start_time} - {end_time}")
        self.start_time = start_time
        self.end_time = end_time

    def __eq__(self, other: "TimeSlot") -> bool:
        return self.start_time == other.start_time and self.end_time == other.end_time

    def __hash__(self) -> int:
        return hash((self.start_time, self.end_time))

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_time < other.end_time and self.end_time > other.start_time

    def includes(self, other: "TimeSlot") -> bool:
        return self.start_time <= other.start_time and self.end_time >= other.end_time

    def merge(self, other: "TimeSlot") -> "TimeSlot":
        # allow merging when slots overlap or are directly adjacent (touching endpoints)
        if not (self.overlaps(other) or self.end_time == other.start_time or self.start_time == other.end_time):
            raise ValueError(f"Slots {self} and {other} cannot be merged")

        return TimeSlot(min(self.start_time, other.start_time), max(self.end_time, other.end_time))

    def subtract(self, other: "TimeSlot") -> "SlotSet":
        if not self.overlaps(other):
            raise ValueError(f"Slots {self} and {other} do not overlap")

        slots = set()
        if self.start_time < other.start_time:
            slots.add(TimeSlot(self.start_time, other.start_time))
        if self.end_time > other.end_time:
            slots.add(TimeSlot(other.end_time, self.end_time))
        return SlotSet(slots)

    @abstractmethod
    def extend(self, delta: Time) -> "SlotSet": ...

    def _extend_is_less_then_sod(self, delta: Time) -> bool:
        diff_hour = self.start_time.hour - delta.hour
        diff_minute = self.start_time.minute - delta.minute
        if diff_hour < 0:
            return True
        elif diff_hour == 0 and diff_minute < 0:
            return True
        else:
            return False

    def _extend_is_more_then_eod(self, delta: Time) -> bool:
        diff_hour = self.end_time.hour + delta.hour
        diff_minute = self.end_time.minute + delta.minute
        if diff_hour > 23:
            return True
        elif diff_hour == 23 and diff_minute > 59:
            return True
        else:
            return False



@dataclass(frozen=True, slots=True)
class SlotSet():
    slots: set[TimeSlot] = field(default_factory=set)

    def add(self, slot: TimeSlot):
        # merge with any slots that overlap OR are directly adjacent
        merged = slot
        # iterate over snapshot since we may modify the set
        for current_slot in list(self.slots):
            if (
                merged.overlaps(current_slot)
                or merged.end_time == current_slot.start_time
                or merged.start_time == current_slot.end_time
            ):
                self.slots.remove(current_slot)
                merged = current_slot.merge(merged)
        self.slots.add(merged)

    def remove(self, slot: TimeSlot):
        # iterate over snapshot to allow modification during loop
        processed_any = False
        for current_slot in list(self.slots):
            if slot.overlaps(current_slot):
                self.slots.remove(current_slot)
                # subtract may yield zero, one, or two slots; merge them back
                self.merge(current_slot.subtract(slot))
                processed_any = True
        if not processed_any:
            # no overlapping slot found -> KeyError to mirror set.remove behaviour
            raise KeyError(slot)

    def merge(self, other: "SlotSet") -> "SlotSet":
        for slot in other.slots:
            self.add(slot)
        return self

    def overlaps(self, slot: TimeSlot) -> bool:
        return any(slot.overlaps(s) for s in self.slots)

    def includes(self, slot: TimeSlot) -> bool:
        return any(s.includes(slot) for s in self.slots)

