Problem: locks and conflicts are described. What about base availability?   

requirements: 

- We need to represent some regular availability pattern on day week level. (”Default Availability”)
- We need to support multiple timezones
- We need to add some overwrite for Default Availability. I.e. next monday    (23.06.2025) I want to work in different hours then set in “Default Availability”
- We want to have custom buffer rules. I want to have x minutes between meetings.
- Allow to book X days upfront.
- We want to allow to put locks on availability from multiple reasons (other bookings, 3rd party calendars etc.)
- full day off! I’m going on holidays 🌴
- locks might be not confirmed and valid for 15min
- Default availability change often
- By design we focus on asking about future. So is available in future. Not in past.

so we see there are two relations: 

- specific date to time slot.
- week day to time slot

- default availability is the tricky part here. The problem is that it cannot be represented as a point in time. Monday at 10:00? But which Monday? Next? Previous? So we cannot use all the goodies that we have from datetime lib. Thats why to simplify the operations on time, to know that 2:00 - 3:00 is moving over midnight and we should actually have two timestamps like 23:00-23:59 and 00:00 - 2:00.

- biggest achivement? 64test cases in 0.09s ? Testing most of the time management logic? Lol. Take my money.

## Performance & Complexity

### Query Algorithm (`ResourceRepo.get_all_for_slot`)
**Time Complexity**: O(M + P·S_filtered)
- M = matching availability slots across all resources
- P = page_size (typically 50)
- S_filtered = average slots loaded per resource (filtered by date/weekday)

**Strategy**: Two-phase query
1. Subquery finds resource IDs with matching slots (filtered + paginated)
2. Main query loads resources with filtered slot relationships

**Benchmark**: ~0.3s per query with 1,000 resources × ~210 slots each (210K total slots)

### Save Algorithm (`ResourceRepo.save`)
**Time Complexity**: O(S)
- S = total slots per resource (~210 typical)

**Strategy**: Set-based reconciliation using composite keys
1. Build desired state from domain model: O(S)
2. Build current state from database: O(S)
3. Compute delta (set difference): O(S)
4. Apply changes (DELETE + INSERT): O(|changes|)

**Key Insight**: Uses `AvailabilitySlotKey` (business attribute tuple) instead of database IDs for efficient diff without maintaining ID mappings in memory.

### Scalability Notes
- Pagination performance remains stable across deep offsets (tested 0-2450)
- Requires composite indexes on `(slot_type, week_day, start_time, end_time)` and `(slot_type, date, start_time, end_time)`
- Selectinload prevents N+1 queries when fetching resource availability