from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

class Location():

    def __init__(self, id, person_id, longitude, latitude, creation_time):
        self.id = id
        self.person_id = person_id
        self.longitude = longitude
        self.latitude = latitude
        self.creation_time = datetime.utcfromtimestamp(creation_time)

@dataclass
class Connection:
    location: Location
    person: Person
