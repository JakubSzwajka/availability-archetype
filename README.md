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