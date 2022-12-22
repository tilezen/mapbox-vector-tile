class SimpleShape:
    """
    A simple geometry class that holds coordinates.
    Provides an alternative to using a shapely geometry when it is not needed.
    """

    def __init__(self, coords, geom_type):
        self.coords = coords
        self.geom_type = geom_type
        self.is_empty = len(coords) == 0

    @property
    def exterior(self):
        return SimpleShape(self.coords[0], geom_type="Polygon")

    @property
    def interiors(self):
        return [SimpleShape(c, geom_type="Polygon") for c in self.coords[1:]]

    @property
    def geoms(self):
        if self.geom_type == "MultiPolygon":
            return [SimpleShape(c, "Polygon") for c in self.coords]
        elif self.geom_type == "MultiLineString":
            return [SimpleShape(c, "Linestring") for c in self.coords]
        elif self.geom_type == "MultiPoint":
            return [SimpleShape(c, "Point") for c in self.coords]

    @property
    def x(self):
        return self.coords[0]

    @property
    def y(self):
        return self.coords[1]
