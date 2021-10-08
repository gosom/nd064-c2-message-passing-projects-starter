import os
import logging
import json
from datetime import datetime

import psycopg2
from kafka import KafkaConsumer


class LocationWriter():
    insq = '''INSERT INTO location(person_id, coordinate, creation_time)
        VALUES(%s, ST_POINT(%s, %s), %s)'''

    def __init__(self, db, broker):
        self.db = db
        self.broker = broker
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        for message in self.broker:
            data = json.loads(message.value)
            self.save_location(data)

    def save_location(self, data):
        with self.db.cursor() as cur:
            try:
                cur.execute(self.insq,
                        (
                            data["person_id"],
                            data["latitude"],
                            data["longitude"],
                            datetime.utcfromtimestamp(data["creation_time"],),
                        ))
                self.db.commit()
            except Exception as e:
                self.logger.exception(e)
                self.db.rollback()
            else:
                self.logger.info("wrote location for person %d", data["person_id"])


def main():
    logging.basicConfig(level=logging.INFO)
    db = psycopg2.connect(
            host=os.environ["DB_HOST"],
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USERNAME"],
            password=os.environ["DB_PASSWORD"],
            )

    consumer = KafkaConsumer(
            os.environ["KAFKA_TOPIC"],
            bootstrap_servers=[os.environ["KAFKA_ADDR"],],
        )

    writer = LocationWriter(db, consumer)

    writer.run()


if __name__ == '__main__':
    main()
