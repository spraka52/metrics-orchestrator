from flask import Flask, request, jsonify
from database.crud import save_metrics
from database.db_manager import MongoDBManager
from datetime import datetime, timezone

app = Flask(__name__)

@app.route("/store_metrics", methods=["POST"])
def store_metrics():
    try:
        response_json = request.get_json()
        print("Received data:", response_json)

        results = response_json.get("results", {})
        commit = response_json.get("commit_hash", "dummy_commit")
        project = response_json.get("project_name", "dummy_project")
        timestamp = datetime.now(timezone.utc).isoformat()

        db = MongoDBManager().get_db()

        for metric, content in results.items():
            print(f"Saving metric: {metric}, content: {content}")
            if "data" in content:
                data = content["data"]
            else:
                data = {
                    "error": content.get("error"),
                    "message": content.get("message")
                }
            save_metrics(db, metric, project, commit, data, timestamp)

        print("Metrics stored successfully.")
        return jsonify({"message": "Data Stored Successfully."}), 200
    except Exception as e:
        import traceback
        print("Exception occurred:")
        traceback.print_exc()   
        return jsonify({"error": f"Failed to store data: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007)
