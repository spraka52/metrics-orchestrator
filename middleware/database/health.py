from .db_manager import MongoDBManager

def check_mongo_health():
    try:
        client = MongoDBManager().client
        client.admin.command('ping')
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "details": str(e)}