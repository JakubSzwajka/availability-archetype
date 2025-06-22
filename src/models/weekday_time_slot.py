from models.time import Time
from models.time_slot import TimeSlotSet, TimeSlot

class WeekDayTimeSlot(TimeSlot):
    def __init__(self, week_day: int, start_time: Time, end_time: Time):
        self.week_day = week_day
        super().__init__(start_time, end_time)

    def extend(self, delta: Time) -> "TimeSlotSet":
        slots = TimeSlotSet()
        base_slot = WeekDayTimeSlot(
            week_day=self.week_day,
            start_time=self.start_time,
            end_time=self.end_time
        )

        # Extend beginning of the slot
        if self._extend_is_less_then_sod(delta):
            # Previous day
            base_slot = WeekDayTimeSlot(
                week_day=self.week_day,
                start_time=Time.sod(),
                end_time=base_slot.start_time
            )
            prefix_slot = WeekDayTimeSlot(
                week_day=(self.week_day + 6) % 7,
                start_time=Time(
                    abs(self.start_time.hour - delta.hour),
                    abs(self.start_time.minute - delta.minute)
                ),
                end_time=Time.eod()
            )
            slots.add(prefix_slot)
        else:
            base_slot = WeekDayTimeSlot(
                week_day=self.week_day,
                start_time=base_slot.start_time - delta,
                end_time=base_slot.end_time
            )

        # Extend end of the slot
        if self._extend_is_more_then_eod(delta):
            # Next day
            base_slot = WeekDayTimeSlot(
                week_day=self.week_day,
                start_time=base_slot.start_time,
                end_time=Time.eod()
            )
            suffix_slot = WeekDayTimeSlot(
                week_day=(self.week_day + 1) % 7,
                start_time=Time.sod(),
                end_time=base_slot.end_time
            )
            slots.add(suffix_slot)
        else:
            base_slot = WeekDayTimeSlot(
                week_day=self.week_day,
                start_time=base_slot.start_time,
                end_time=base_slot.end_time + delta
            )
        slots.add(base_slot)
        return slots

