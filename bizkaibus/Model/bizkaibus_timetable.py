from .bizkaibus_arrival import BizkaibusArrival


class BizkaibusTimetable:
    """The class for handling the data retrieval."""

    id: str = ""
    name: str | None = ""

    def __init__(self, id: str, name: str | None):
        """Initialize the data object."""
        self.id = id
        self.name = name
        self.arrivals: dict[str, BizkaibusArrival] = {}

    def __str__(self):
        """Return a string representation of the object."""
        arrivals_str = ", ".join(str(arrival) for arrival in self.arrivals.values())
        return f"Stop: ({self.id}) {self.name}, arrivals: {arrivals_str}"
