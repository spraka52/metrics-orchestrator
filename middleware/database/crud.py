from .db_manager import MongoDBManager
from .models import get_collection


def save_metrics(db, service, project, commit, data, timestamp):
    coll = get_collection(db, service)
    coll.update_one(
        {"projectName": project, "commitHash": commit, "timestamp": timestamp},
        {"$set": {
            "projectName": project,
            "commitHash": commit,
            "data": data,
            "timestamp": timestamp
        }},
        upsert=True
    )


def get_metrics(service, project, commit):
    db = MongoDBManager().get_db()
    coll = get_collection(db, service)
    return coll.find_one({"projectName": project, "commitHash": commit})