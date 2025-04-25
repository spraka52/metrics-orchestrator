def get_collection(db, service_name):
    collection = db[f"metrics_{service_name}"]
    collection.create_index([("projectName", 1), ("commitHash", 1), ("timestamp", -1)])
    return collection
