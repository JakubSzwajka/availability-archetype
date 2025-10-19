"""Benchmark script for mass-seeding resources and querying availability."""

import sys
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db import Base
from faker import Faker

from models.date_time_slot import DateTimeSlot
from models.resource import Resource
from models.time import Time
from models.time_slot import TimeSlotSet
from models.weekday_time_slot import WeekDayTimeSlot
from resource_facade import ResourceFacade
from resource_repo import ResourceRepo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

faker = Faker()
repo = ResourceRepo()

url = "postgresql://postgres:@localhost/archetype-availability"
engine = create_engine(url)

RESOURCE_COUNT = 1_000
QUERY_RUNS = 50

# @event.listens_for(engine, "before_cursor_execute")
# def _before(conn, cursor, statement, params, context, executemany):
#     context._query_start = time.perf_counter()

# @event.listens_for(engine, "after_cursor_execute")
# def _after(conn, cursor, statement, params, context, executemany):
#     dur = time.perf_counter() - context._query_start
#     logger.info("SQL %.3f ms  %s", dur * 1_000, statement.split()[0])


def create_resource() -> Resource:
    resource = Resource(
        id=str(uuid.uuid4()),
        name=faker.name(),
        buffer_minutes=faker.random_int(min=0, max=30, step=15),
        booking_upfront_days=faker.random_int(min=0, max=180),
    )

    # Add 7 days of default availability
    default_availability: dict[int, TimeSlotSet] = {}
    for weekday in range(7):
        default_availability[weekday] = TimeSlotSet(
            {
                WeekDayTimeSlot(
                    week_day=weekday,
                    start_time=Time(8, 0),
                    end_time=Time(17, 0),
                )
            }
        )
    resource.set_default_availability(default_availability)

    # Add 100 days of overwrite availability randomly spread out
    for day in range(100):
        date = datetime.now(UTC).date() + timedelta(days=day)
        slots = TimeSlotSet(
            {
                DateTimeSlot(
                    date=date,
                    start_time=Time(12, 0),
                    end_time=Time(17, 0),
                )
            }
        )
        resource.set_overwrite_availability(date, slots)

    # Add 100 days of lock availability randomly spread out
    for day in range(100):
        date = datetime.now(UTC).date() + timedelta(days=day)
        resource.lock(
            DateTimeSlot(
                date=date,
                start_time=Time(12, 0),
                end_time=Time(17, 0),
            )
        )

    return resource


def drop_and_create_schema() -> None:
    logger.info("Recreating database schema …")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def seed_resources(resource_count: int) -> None:
    logger.info("Seeding %s resources …", resource_count)
    seed_start = time.perf_counter()
    with Session(engine) as session:
        for _ in range(resource_count):
            resource = create_resource()
            repo.save(resource, session)
    seed_elapsed = time.perf_counter() - seed_start
    logger.info("Seeded %s resources in %.2f s", resource_count, seed_elapsed)


def main(resource_count: int = RESOURCE_COUNT) -> None:
    # drop_and_create_schema()
    # seed_resources(resource_count)

    search_slot = DateTimeSlot(
        date=datetime.now(UTC).date() + timedelta(days=7),
        start_time=Time(10, 0),
        end_time=Time(11, 0),
    )

    facade = ResourceFacade(repo)
    # with Session(engine) as session:
    #     facade.get_available_at(search_slot, session)

    logger.info("Executing availability query %s times …", QUERY_RUNS)
    timings: list[float] = []
    page_size = 50
    for i in range(QUERY_RUNS):
        with Session(engine) as session:
            t0 = time.perf_counter()
            facade.get_available_at(search_slot, session, page_size, i * page_size)
            timings.append(time.perf_counter() - t0)

    avg_time = sum(timings) / QUERY_RUNS
    logger.info(
        "Average query time over %s runs: %.4f s (min %.4f, max %.4f)",
        QUERY_RUNS,
        avg_time,
        min(timings),
        max(timings),
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    resource_count = int(args[0])
    main(resource_count)
    print("-----" * 10)
