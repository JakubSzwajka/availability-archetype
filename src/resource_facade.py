import time
from sqlalchemy.orm import Session
from logging import getLogger
from models.date_time_slot import DateTimeSlot
from models.resource import Resource
from resource_repo import ResourceRepo

logger = getLogger(__name__)


class ResourceFacade:
    def __init__(self, resource_repo: ResourceRepo):
        self.resource_repo = resource_repo

    def get_resource(self, resource_id: str, session: Session) -> Resource:
        return self.resource_repo.get(resource_id, session)

    def get_available_at(
        self, slot: DateTimeSlot, session: Session, limit: int, offset: int
    ) -> list[Resource]:
        # --- SQL phase ---
        t0_sql = time.perf_counter()
        resources = self.resource_repo.get_all_for_slot(session, slot, limit, offset)
        sql_dur = time.perf_counter() - t0_sql

        # --- Python phase ---
        t0_py = time.perf_counter()
        available = [r for r in resources if r.is_available(slot)]
        py_dur = time.perf_counter() - t0_py

        logger.info(
            "Availability lookup (limit=%d, offset=%d) – SQL: %.3f ms | Python: %.3f ms | candidates=%d | result=%d",
            limit,
            offset,
            sql_dur * 1_000,
            py_dur * 1_000,
            len(resources),
            len(available),
        )

        return available
