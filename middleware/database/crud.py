from .db_manager import MongoDBManager
from .models import get_collection
from bson import ObjectId

def save_metrics(db,service, project, commit, data, timestamp):
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

def get_metrics(project_name: str, selected_metric: str):
    db = MongoDBManager().get_db()
    all_data = {}

    coll = get_collection(db, selected_metric)
    docs = list(coll.find({"projectName": project_name}))
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])

    all_data[selected_metric] = docs  
    
    return all_data