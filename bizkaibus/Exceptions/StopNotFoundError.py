class StopNotFoundError(Exception):
    def __init__(self, stop_id: str):
        super().__init__(f"The stop id '{stop_id}' does not exist")