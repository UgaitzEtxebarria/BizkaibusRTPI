import datetime

class BizkaibusArrivalTime:
    time: int = 0

    def __init__(self, time: int):
        """Initialize the data object."""
        self.time = time

    def GetUTC(self):
        """Get the time in UTC format."""
        now = datetime.datetime.now(datetime.timezone.utc)
        time = (now + datetime.timedelta(minutes=int(self.time))).isoformat()
        return time

    def GetAbsolute(self):
        """Get the time in absolute format."""
        now = datetime.datetime.now()
        time = (now + datetime.timedelta(minutes=int(self.time))).isoformat()
        return time

    def __str__(self):
        """Return a string representation of the object."""
        return f"{self.time} min"