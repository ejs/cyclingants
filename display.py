from datetime import datetime
from gpxpy import gpx


class GPXOutput:
    def __init__(self):
        self.store = gpx.GPX()
        self.now = datetime.now()

    def add_track(self, track):
        s = gpx.GPXTrackSegment()
        for point in track:
            s.points.append(gpx.GPXTrackPoint(*point, time=self.now))
        t = gpx.GPXTrack()
        t.segments.append(s)
        self.store.routes.append(t)

    def add_route(self, route):
        # [(lat, lon), ...]
        r = gpx.GPXRoute()
        for point in route:
            r.points.append(gpx.GPXRoutePoint(*point, time=self.now))
        self.store.routes.append(r)

    def add_points(self, *points):
        for point in points:
            self.store.waypoints.append(gpx.GPXWaypoint(*point))

    def save_to_file(self, filename):
        with open(filename, 'w') as sink:
            sink.write(self.store.to_xml())
