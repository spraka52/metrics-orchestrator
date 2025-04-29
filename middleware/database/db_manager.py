from pymongo import MongoClient, errors
import os
from time import sleep


class MongoDBManager:
    _instance = None
    MAX_RETRIES = 5
    RETRY_DELAY = 2  # seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            retries = 0
            while retries < cls.MAX_RETRIES:
                try:
                    cls._instance.client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
                    cls._instance.client.admin.command('ping')  # trigger actual connection attempt
                    break
                except errors.ServerSelectionTimeoutError as e:
                    print(f"[MongoDB] Connection failed. Retrying in {cls.RETRY_DELAY} seconds... ({retries + 1}/{cls.MAX_RETRIES})")
                    sleep(cls.RETRY_DELAY)
                    retries += 1
            else:
                raise ConnectionError("Could not connect to MongoDB after multiple retries.")
        return cls._instance

    def get_db(self):
        return self.client["metrics_db"]

    def close(self):
        self.client.close()
