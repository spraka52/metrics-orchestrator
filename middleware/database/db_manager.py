from pymongo import MongoClient
import os

class MongoDBManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance.client = MongoClient(os.getenv("MONGO_URI"))
        return cls._instance

    def get_db(self):
        return self.client["metrics_db"]

    def close(self):
        self.client.close()
