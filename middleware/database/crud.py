from pymongo.errors import PyMongoError
from database.db_manager import MongoDBManager
from database.models import get_collection
from bson import ObjectId


def save_metrics(service, project, commit, data, timestamp):
    try:
        db = MongoDBManager().get_db()
        coll = get_collection(db, service)
        coll.update_one(
            {"projectName": project, "commitHash": commit},
            {"$set": {
                "projectName": project,
                "commitHash": commit,
                "data": data,
                "timestamp": timestamp,
                "default_benchmark": '10',
            }},
            upsert=True
        )
    except PyMongoError as e:
        print(f"[MongoDB] Failed to save metrics: {e}")


def get_metrics(service, project, commit):
    try:
        db = MongoDBManager().get_db()
        coll = get_collection(db, service)
        result = coll.find_one({"projectName": project, "commitHash": commit})
        if result and "_id" in result:
            result["_id"] = str(result["_id"])
        return result
    except PyMongoError as e:
        print(f"[MongoDB] Failed to get metrics: {e}")
        return None
