from datetime import date as _date
from datetime import date
from datetime import time as _time

from sqlalchemy.orm import Session, selectinload, with_loader_criteria
from sqlalchemy import delete, or_, and_, select

from db import AvailabilitySlotModel, ResourceModel
from models.date_time_slot import DateTimeSlot
from models.resource import Resource
from models.time import Time
from models.time_slot import TimeSlotSet
from models.weekday_time_slot import WeekDayTimeSlot


# helper
def _time_from(t: Time) -> _time:
    return _time(hour=t.hour, minute=t.minute)


class ResourceRepo:
    def _make_key(
        self,
        slot_type: AvailabilitySlotModel.SlotType,
        week_day: int | None,
        d: date | None,
        start: Time,
        end: Time,
    ) -> tuple:
        return (
            slot_type.value,
            week_day if week_day is not None else -1,
            d.isoformat() if d else "",
            start.hour,
            start.minute,
            end.hour,
            end.minute,
        )

    def _to_domain(self, resource_row: ResourceModel) -> Resource:
            resource = Resource(
                id=resource_row.id,
                name=resource_row.name,
                buffer_minutes=resource_row.buffer_minutes,
                booking_upfront_days=resource_row.booking_upfront_days,
            )

            default_map: dict[int, TimeSlotSet] = {}
            overwrite_map: dict[_date, TimeSlotSet] = {}

            for slot_row in resource_row.availability_slots:
                start_time = Time(slot_row.start_time.hour, slot_row.start_time.minute)
                end_time = Time(slot_row.end_time.hour, slot_row.end_time.minute)
                if slot_row.slot_type == AvailabilitySlotModel.SlotType.DEFAULT:
                    default_map.setdefault(slot_row.week_day, TimeSlotSet()).add(WeekDayTimeSlot(
                        week_day=slot_row.week_day,
                        start_time=start_time,
                        end_time=end_time,
                    ))
                elif slot_row.slot_type == AvailabilitySlotModel.SlotType.OVERWRITE:
                    overwrite_map.setdefault(slot_row.date, TimeSlotSet()).add(DateTimeSlot(
                        date=slot_row.date,
                        start_time=start_time,
                        end_time=end_time,
                    ))
                elif slot_row.slot_type == AvailabilitySlotModel.SlotType.LOCK:
                    resource.lock(DateTimeSlot(
                        date=slot_row.date,
                        start_time=start_time,
                        end_time=end_time,
                    ))

            if default_map:
                resource.set_default_availability(default_map)
            for d, set_ in overwrite_map.items():
                resource.set_overwrite_availability(d, set_)
            return resource

    def get(self, resource_id: str, session: Session) -> Resource:
        with session.begin():
            resource_row = (
                session.query(ResourceModel)
                .options(selectinload(ResourceModel.availability_slots))
                .filter(ResourceModel.id == resource_id)
                .one()
            )

            return self._to_domain(resource_row)

    def get_all_naive(self, session: Session) -> list[Resource]:
        with session.begin():
            query = (
                session.query(ResourceModel)
                # .options(selectinload(ResourceModel.availability_slots))
            )
            resource_rows = query.all()
            return [self._to_domain(row) for row in resource_rows]

    def get_all(self, session: Session, available_at: date) -> list[Resource]:
        week_day = available_at.weekday()
        slot_alias = AvailabilitySlotModel

        id_subq = (
            select(ResourceModel.id)
            .join(slot_alias, slot_alias.resource_id == ResourceModel.id)
            .filter(
                or_(
                    and_(
                        slot_alias.slot_type == AvailabilitySlotModel.SlotType.DEFAULT,
                        slot_alias.week_day == week_day,
                    ),
                    and_(
                        slot_alias.slot_type.in_(
                            [
                                AvailabilitySlotModel.SlotType.OVERWRITE,
                                AvailabilitySlotModel.SlotType.LOCK,
                            ]
                        ),
                        slot_alias.date == available_at,
                    ),
                )
            )
            .distinct()
        ).subquery()

        slot_filter = or_(
            and_(
                AvailabilitySlotModel.slot_type == AvailabilitySlotModel.SlotType.DEFAULT,
                AvailabilitySlotModel.week_day == week_day,
            ),
            and_(
                AvailabilitySlotModel.slot_type.in_(
                    [
                        AvailabilitySlotModel.SlotType.OVERWRITE,
                        AvailabilitySlotModel.SlotType.LOCK,
                    ]
                ),
                AvailabilitySlotModel.date == available_at,
            ),
        )

        resource_rows = (
            session.query(ResourceModel)
            .filter(ResourceModel.id.in_(select(id_subq.c.id)))
            .options(
                selectinload(ResourceModel.availability_slots),
                with_loader_criteria(AvailabilitySlotModel, slot_filter, include_aliases=True),
            )
            .all()
        )

        return [self._to_domain(row) for row in resource_rows]

    def get_all_for_slot(self, session: Session, slot: DateTimeSlot, limit: int, offset: int) -> list[Resource]:
        week_day = slot.date.weekday()
        slot_alias = AvailabilitySlotModel

        filter = or_(
                    and_(
                        slot_alias.slot_type == AvailabilitySlotModel.SlotType.DEFAULT,
                        slot_alias.week_day == week_day,
                        slot_alias.start_time <= slot.start_time.time(),
                        slot_alias.end_time >= slot.end_time.time(),
                    ),
                    and_(
                        slot_alias.slot_type.in_(
                            [
                                AvailabilitySlotModel.SlotType.OVERWRITE,
                                AvailabilitySlotModel.SlotType.LOCK,
                            ]
                        ),
                        slot_alias.date == slot.date,
                        slot_alias.start_time <= slot.start_time.time(),
                        slot_alias.end_time >= slot.end_time.time(),
                    ),
                )

        id_subq = (
            select(ResourceModel.id)
            .join(slot_alias, slot_alias.resource_id == ResourceModel.id)
            .filter(filter)
            .distinct()
            .limit(limit)
            .offset(offset)
        ).subquery()


        resource_rows = (
            session.query(ResourceModel)
            .filter(ResourceModel.id.in_(select(id_subq.c.id)))
            .options(
                selectinload(ResourceModel.availability_slots),
                with_loader_criteria(AvailabilitySlotModel, filter, include_aliases=True),
            )
            .all()
        )

        return [self._to_domain(row) for row in resource_rows]

    def save(self, resource: Resource, session: Session) -> None:
        with session.begin():
            db_resource = session.get(ResourceModel, resource.id)
            if db_resource is None:
                db_resource = ResourceModel(id=resource.id)
                session.add(db_resource)

            db_resource.name = resource.name
            db_resource.buffer_minutes = getattr(resource, "_Resource__buffer_minutes")
            db_resource.booking_upfront_days = getattr(resource, "_Resource__booking_upfront_days")

            desired_keys: set[tuple] = set()
            desired_rows: list[AvailabilitySlotModel] = []

            # default availability
            for week_day, slot_set in getattr(resource, "_Resource__default_availability").items():
                for slot in slot_set.slots:
                    key = self._make_key(
                        AvailabilitySlotModel.SlotType.DEFAULT,
                        week_day,
                        None,
                        slot.start_time,
                        slot.end_time,
                    )
                    desired_keys.add(key)
                    desired_rows.append(
                        AvailabilitySlotModel(
                            resource_id=db_resource.id,
                            week_day=week_day,
                            date=None,
                            start_time=_time_from(slot.start_time),
                            end_time=_time_from(slot.end_time),
                            slot_type=AvailabilitySlotModel.SlotType.DEFAULT,
                        )
                    )

            # overwrites
            for d, slot_set in getattr(resource, "_Resource__overwrites").items():
                for slot in slot_set.slots:
                    key = self._make_key(
                        AvailabilitySlotModel.SlotType.OVERWRITE,
                        None,
                        d,
                        slot.start_time,
                        slot.end_time,
                    )
                    desired_keys.add(key)
                    desired_rows.append(
                        AvailabilitySlotModel(
                            resource_id=db_resource.id,
                            week_day=None,
                            date=d,
                            start_time=_time_from(slot.start_time),
                            end_time=_time_from(slot.end_time),
                            slot_type=AvailabilitySlotModel.SlotType.OVERWRITE,
                        )
                    )

            # locks
            for d, slot_set in getattr(resource, "_Resource__locks").items():
                for slot in slot_set.slots:
                    key = self._make_key(
                        AvailabilitySlotModel.SlotType.LOCK,
                        None,
                        d,
                        slot.start_time,
                        slot.end_time,
                    )
                    desired_keys.add(key)
                    desired_rows.append(
                        AvailabilitySlotModel(
                            resource_id=db_resource.id,
                            week_day=None,
                            date=d,
                            start_time=_time_from(slot.start_time),
                            end_time=_time_from(slot.end_time),
                            slot_type=AvailabilitySlotModel.SlotType.LOCK,
                            lock_type=AvailabilitySlotModel.LockType.BOOKING,
                        )
                    )

            # compute existing keys
            existing_keys_to_id: dict[tuple, str] = {
                self._make_key(
                    r.slot_type,
                    r.week_day,
                    r.date,
                    Time(r.start_time.hour, r.start_time.minute),
                    Time(r.end_time.hour, r.end_time.minute),
                ): r.id  # type: ignore[attr-defined]
                for r in db_resource.availability_slots
            }

            keys_to_delete = set(existing_keys_to_id.keys()) - desired_keys
            keys_to_insert = desired_keys - set(existing_keys_to_id.keys())

            # ensure parent resource row is persisted before manipulating child rows
            session.flush()

            # delete rows not desired
            if keys_to_delete:
                ids = [existing_keys_to_id[k] for k in keys_to_delete]
                session.execute(
                    delete(AvailabilitySlotModel).where(AvailabilitySlotModel.id.in_(ids))
                )

            # insert new rows
            if keys_to_insert:
                rows_to_add = [row for row in desired_rows if self._make_key(
                    row.slot_type,
                    row.week_day,
                    row.date,
                    Time(row.start_time.hour, row.start_time.minute),
                    Time(row.end_time.hour, row.end_time.minute),
                ) in keys_to_insert]
                session.bulk_save_objects(rows_to_add)

            # nothing to do for unchanged rows – left intact


