from abc import ABC, abstractmethod

class BizkaibusServiceParam(ABC):
    """Interface for handling service parameters."""

    @abstractmethod
    def GetParams(self) -> dict:
        """Retrieve the parameters for the service."""
        pass