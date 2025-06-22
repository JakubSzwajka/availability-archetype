from datetime import date, timedelta
from models.time import Time
from models.date_slot import DateSlot
from models.time_slot import SlotSet


class Resource:
    def __init__(self, id: str, name: str, buffer_minutes: int = 0, booking_upfront_days: int = 90):
        self.id = id
        self.name = name

        self.__buffer_minutes = buffer_minutes
        self.__booking_upfront_days = booking_upfront_days

        self.__default_availability: dict[int, SlotSet] = {}
        self.__overwrites: dict[date, SlotSet] = {}
        self.__locks: dict[date, SlotSet] = {}

    def is_available(self, slot: DateSlot) -> bool:
        if slot.date < date.today() + timedelta(days=1) or slot.date > date.today() + timedelta(days=self.__booking_upfront_days):
            return False

        week_day = slot.date.weekday()

        available_by_default = self.__default_availability.get(week_day, SlotSet()).includes(slot)
        has_overwrite_for_that_date = slot.date in self.__overwrites
        available_by_overwrite = self.__overwrites.get(slot.date, SlotSet()).includes(slot)

        locked = False
        if self.__buffer_minutes == 0:
            locked = self.__locks.get(slot.date, SlotSet()).overlaps(slot)
        else:
            locks = self.__locks.get(slot.date, SlotSet())
            for l in locks.slots:
                extended = l.extend(Time(0, self.__buffer_minutes))
                if extended.overlaps(slot):
                    locked = True
                    break

        return (available_by_default if not has_overwrite_for_that_date else available_by_overwrite) and not locked

    def lock(self, slot: DateSlot) -> None:
        if slot.date not in self.__locks:
            self.__locks[slot.date] = SlotSet()
        self.__locks[slot.date].add(slot)

    def unlock(self, slot: DateSlot) -> None:
        if slot.date in self.__locks:
            self.__locks[slot.date].remove(slot)
            if not self.__locks[slot.date].slots:
                # clean up empty lock set
                del self.__locks[slot.date]

    def set_default_availability(self, week_availability: dict[int, SlotSet]) -> None:
        self.__default_availability = week_availability

    def set_overwrite_availability(self, date: date, slots: SlotSet) -> None:
        self.__overwrites[date] = slots

