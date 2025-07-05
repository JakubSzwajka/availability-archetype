import time
from sqlalchemy.orm import Session
from logging import getLogger
from models.date_time_slot import DateTimeSlot
from models.resource import Resource
from models.time_slot import TimeSlot
from resource_repo import ResourceRepo

logger = getLogger(__name__)


class ResourceFacade:
    def __init__(self, resource_repo: ResourceRepo):
        self.resource_repo = resource_repo

    def get_resource(self, resource_id: str, session: Session) -> Resource:
        return self.resource_repo.get(resource_id, session)

    def get_available_at(self, slot: DateTimeSlot, session: Session) -> list[Resource]:
        resources = self.resource_repo.get_all_for_slot(session, slot)
        # resources = self.resource_repo.get_all_naive(session)
        resources = [r for r in resources if r.is_available(slot)]
        return resources