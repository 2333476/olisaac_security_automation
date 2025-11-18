import psycopg2
import logging

log = logging.getLogger("neon")

class NeonClient:
    def init(self, db_url: str):
        self.db_url = db_url
        self.conn = psycopg2.connect(db_url)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        log.info("Connected to Neon PostgreSQL")

    def insert_environmental(self, data: dict):
        try:
            self.cur.execute(
                """
                INSERT INTO environmental_readings
                (temperature, humidity, raw_timestamp)
                VALUES (%s, %s, %s)
                """,
                (
                    data.get("temperature"),
                    data.get("humidity"),
                    data.get("timestamp"),
                )
            )
        except Exception as e:
            log.error("Failed to insert environmental:", e)

    def close(self):
        try:
            self.cur.close()
            self.conn.close()
        except:
            pass
