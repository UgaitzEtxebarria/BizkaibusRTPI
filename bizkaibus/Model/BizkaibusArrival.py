
from typing import Optional
from bizkaibus.Model.BizkaibusArrivalTime import BizkaibusArrivalTime
from bizkaibus.Model.BizkaibusLine import BizkaibusLine

class BizkaibusArrival:
    line: BizkaibusLine
    nearestArrival: BizkaibusArrivalTime
    nextArrival: Optional[BizkaibusArrivalTime] = None

    def __init__(self, line: BizkaibusLine, nearestArrival: BizkaibusArrivalTime, nextArrival: Optional[BizkaibusArrivalTime] = None):
        """Initialize the data object."""
        self.line = line
        self.nearestArrival = nearestArrival
        self.nextArrival = nextArrival
    
    def __str__(self):
        """Return a string representation of the object."""
        return f"Line: {self.line}, nearest: {self.nearestArrival}, next: {self.nextArrival}"