import logging
import time
from datetime import datetime, timedelta
import json

from app.udaconnect.models import Connection, Location
from app.udaconnect.schemas import ConnectionSchema, LocationSchema, PersonSchema

import location_pb2
import location_pb2_grpc

from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
import grpc


from flask import current_app
import requests


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("udaconnect-api")

class ConnectionService:
    stub = None

    @classmethod
    def init(cls):
        if not cls.stub:
            grpc_addr = current_app.config["LOCATION_SERVICE_ADDR"]
            channel = grpc.insecure_channel(grpc_addr)
            cls.stub = location_pb2_grpc.LocationServiceStub(channel)

    @classmethod
    def find_contacts(cls, person_id: int, start_date: datetime, end_date: datetime, meters=5):
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?
        """
        cls.init()
        # Cache all users in memory for quick lookup
        person_map = {person["id"]: person for person in PersonService.retrieve_all()}

        req = location_pb2.SearchRequest(
                person_id=int(person_id),
                start_date=int(start_date.timestamp()),
                end_date=int(end_date.timestamp()),
        )

        locations = [Location(e.id, e.person_id, e.longitude, e.latitude, e.creation_time)
                for e in cls.stub.All(req).locations]
        logger.info(locations)

        # Prepare arguments for queries
        data = []
        for location in locations:
            data.append(
                location_pb2.ConnectionQuery(
                    person_id=int(person_id),
                    start_date=int(start_date.timestamp()),
                    end_date=int((end_date + timedelta(days=1)).timestamp()),
                    meters=int(meters),
                    longitude=location.longitude,
                    latitude=location.latitude)
            )

        result: List[Connection] = []
        for q in data:
            other = cls.stub.Connections(q).locations
            for l in other:
                con = Connection(person=person_map[l.person_id],
                        location=Location(l.id, l.person_id, l.longitude, l.latitude, l.creation_time),
                        )

                result.append(con)
        return result

class LocationService:
    stub = None

    @classmethod
    def init(cls):
        if not cls.stub:
            grpc_addr = current_app.config["LOCATION_SERVICE_ADDR"]
            channel = grpc.insecure_channel(grpc_addr)
            cls.stub = location_pb2_grpc.LocationServiceStub(channel)

    @classmethod
    def retrieve(cls, location_id):
        cls.init()
        req = location_pb2.LocationRequest(
                id=int(location_id),
        )
        ans = cls.stub.Get(req)
        location = Location(ans.id, ans.person_id, ans.longitude, ans.latitude, ans.creation_time)
        return location

    @classmethod
    def create(cls, location):
        cls.init()
        validation_results = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        req = location_pb2.LocationMessage(
                person_id=int(location["person_id"]),
                longitude=location["longitude"],
                latitude=location["latitude"],
                creation_time=int(time.time()),
        )
        ans = cls.stub.Create(req)
        return ans

class PersonService:
    session = None
    base_url = None

    @classmethod
    def init(cls):
        if not cls.base_url:
            cls.base_url = current_app.config["PERSON_SERVICE_URL"]
            cls.session = requests.Session()

    @classmethod
    def create(cls, person):
        cls.init()
        u = cls.base_url + "/api/"
        resp = cls.session.post(u, json=person, headers={"Content-Type": "application/json"})
        try:
            resp.raise_for_status()
        except Exception as e:
            logger.debug(resp.text)
            raise
        return resp.json()

    @classmethod
    def retrieve(cls, person_id: int):
        cls.init()
        u = cls.base_url + f"/api/{person_id}"
        resp = cls.session.get(u, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp.json()

    @classmethod
    def retrieve_all(cls):
        cls.init()
        u = cls.base_url + "/api"
        resp = cls.session.get(u, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp.json()
