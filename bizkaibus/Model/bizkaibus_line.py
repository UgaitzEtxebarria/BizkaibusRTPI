class BizkaibusLine:
    id: str = ''
    route: str = ''
    incident: str | None = None

    def __init__(self, id, route, incident=None):
        """Initialize the data object."""
        self.id = id
        self.route = route
        self.incident = incident if incident != '' else None

    def __str__(self):
        """Return a string representation of the object."""
        prefix = '*' if self.incident is not None else ''
        return f"{prefix}({self.id}) {self.route}"
