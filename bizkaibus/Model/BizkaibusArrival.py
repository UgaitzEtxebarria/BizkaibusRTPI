
from typing import Optional

from .BizkaibusArrivalTime import BizkaibusArrivalTime
from .BizkaibusLine import BizkaibusLine


class BizkaibusArrival:
    line: BizkaibusLine
    nearest_arrival: BizkaibusArrivalTime
    next_arrival: Optional[BizkaibusArrivalTime] = None

    def __init__(
            self, 
            line: BizkaibusLine, 
            nearest_arrival: BizkaibusArrivalTime, 
            next_arrival: Optional[BizkaibusArrivalTime] = None
            ):
        """Initialize the data object."""
        self.line = line
        self.nearest_arrival = nearest_arrival
        self.next_arrival = next_arrival

    def __str__(self):
        """Return a string representation of the object."""
        return (
            f"Line: {self.line}, nearest: {self.nearest_arrival}, "
            f"next: {self.next_arrival}"
        )