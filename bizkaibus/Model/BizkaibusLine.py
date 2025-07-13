class BizkaibusLine:
    id: str = ''
    route: str = ''

    def __init__(self, id, route):
        """Initialize the data object."""
        self.id = id
        self.route = route

    def __str__(self):
        """Return a string representation of the object."""
        return f"({self.id}) {self.route}"
