from abc import ABC, abstractmethod
from .ResponseType import ResponseType

class BizkaibusServiceParam(ABC):
    """Interface for handling service parameters."""

    response_type: ResponseType = ResponseType.JSON

    def __init__(self):
        self.params: dict[str, str] = {"callback": ""}

    @abstractmethod
    def get_url(self) -> str:
        """Retrieve the URL for the service."""

    def build_params(self) -> dict[str, str]:
        """Return the parameters for the request."""
        return dict(self.params)