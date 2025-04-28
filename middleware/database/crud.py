from pymongo.errors import PyMongoError
from database.db_manager import MongoDBManager
from database.models import get_collection
from bson import ObjectId

def save_metrics(service, project, commit, data, timestamp):
    try:
        db = MongoDBManager().get_db()
        coll = get_collection(db, service)
        coll.update_one(
            {"projectName": project, "commitHash": commit, "timestamp": timestamp},
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

def get_metrics(project_name: str, selected_metrics: list[str]):
    try:

        db = MongoDBManager().get_db()
        all_data = {}
        for metric in selected_metrics:
            coll = get_collection(db, metric)
            docs = list(coll.find({"projectName": project_name}))
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
        for metric in selected_metrics:
            coll = get_collection(db, metric)
            docs = list(coll.find({"projectName": project_name}))
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            all_data[metric] = docs  
        
        return all_data
    
    except PyMongoError as e:
        print(f"[MongoDB] Failed to get metrics: {e}")
        return None