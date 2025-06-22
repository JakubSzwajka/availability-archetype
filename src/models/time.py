
class Time:
    def __init__(self, hour: int, minute: int):
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError(f"Invalid time: {hour}:{minute}")
        self.hour = hour
        self.minute = minute

    def __lt__(self, other: "Time") -> bool:
        return (self.hour, self.minute) < (other.hour, other.minute)

    def __eq__(self, other: "Time") -> bool:
        return (self.hour, self.minute) == (other.hour, other.minute)

    def __le__(self, other: "Time") -> bool:
        return self < other or self == other

    def __add__(self, other: "Time") -> "Time":
        hour = self.hour + other.hour
        minute = self.minute + other.minute
        if minute > 59:
            hour += 1
            minute -= 60
        return Time(hour, minute)

    def __sub__(self, other: "Time") -> "Time":
        hour = self.hour - other.hour
        minute = self.minute - other.minute
        if minute < 0:
            hour -= 1
            minute += 60
        return Time(hour, minute)

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    @classmethod
    def eod(cls) -> "Time":
        return Time(23, 59)

    @classmethod
    def sod(cls) -> "Time":
        return Time(0, 0)

    def __hash__(self) -> int:
        return hash((self.hour, self.minute))
