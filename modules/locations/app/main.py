import logging
import time
from concurrent import futures

import grpc
import location_pb2
import location_pb2_grpc

import psycopg2
import psycopg2.extras


class LocationServicer(location_pb2_grpc.LocationServiceServicer):

    def __init__(self, db, ):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    def Create(self, request, context):
        return location_pb2.Empty()

    def Get(self, request, context):
        q = """
        SELECT
            id, person_id,
            CAST(ST_X(coordinate) AS TEXT) as longitude,
            CAST(ST_Y(coordinate) AS TEXT) as latitude,
            CAST(EXTRACT(epoch FROM creation_time) as integer) AS creation_time
        FROM location WHERE id = %s
        """
        cur = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(q, (request.id,))
            row = cur.fetchone()
        finally:
            cur.close()

        return location_pb2.LocationMessage(**row)

    def All(self, request, context):
        query = """
        SELECT
            id, person_id,
            CAST(ST_X(coordinate) AS TEXT) as latitude,
            CAST(ST_Y(coordinate) AS TEXT) as longitude,
            CAST(EXTRACT(epoch FROM creation_time) as integer) AS creation_time
        FROM
            location
        WHERE
            person_id = %s
        AND
            creation_time < TO_TIMESTAMP(%s)
        AND
            creation_time >= TO_TIMESTAMP(%s)
        """
        ans = []
        cur = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(query, (request.person_id, request.end_date, request.start_date))
            rows = cur.fetchall()
            for row in rows:
                ans.append(location_pb2.LocationMessage(**row))
        finally:
            cur.close()
        return location_pb2.LocationMessageList(locations=ans)

    def Connections(self, request, context):
        query = """
        SELECT
            id, person_id,
            CAST(ST_X(coordinate) AS TEXT) as latitude,
            CAST(ST_Y(coordinate) AS TEXT) as longitude,
            CAST(EXTRACT(epoch FROM creation_time) as integer) AS creation_time
        FROM
            location
        WHERE
            ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, %s)
        AND
            person_id != %s
        AND
            creation_time >= TO_TIMESTAMP(%s)
        AND
            creation_time < TO_TIMESTAMP(%s)
        """
        cur = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        ans = []
        try:
            cur.execute(query,
                    (request.latitude, request.longitude, request.meters,
                        request.person_id, request.start_date, request.end_date),
                    )
            rows = cur.fetchall()
            for row in rows:
                ans.append(location_pb2.LocationMessage(**row))
        finally:
            cur.close()
        return location_pb2.LocationMessageList(locations=ans)


def main():
    logging.basicConfig(level=logging.DEBUG)
    db = psycopg2.connect(
            host="db",
            database="udaconnect",
            user="udaconnect",
            password="secret",
            )


    location_service = LocationServicer(db)

    # Initialize gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))

    location_pb2_grpc.add_LocationServiceServicer_to_server(location_service, server)


    print("Server starting on port 5005...")
    server.add_insecure_port("[::]:5005")
    server.start()
    # Keep thread alive
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        pass

if __name__ == "__main__":
    main()




