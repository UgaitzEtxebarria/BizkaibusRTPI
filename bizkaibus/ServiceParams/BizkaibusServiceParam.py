from abc import ABC, abstractmethod

class BizkaibusServiceParam(ABC):
    """Interface for handling service parameters."""

    params = {"callback": ""}

    @abstractmethod
    def GetURL(self) -> str:
        """Retrieve the URL for the service."""
        pass
    
    def BuildParams(self) -> dict[str, str]:
        """Retrieve the parameters for the service."""
        return self.params