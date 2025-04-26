import os
from clone_repo import clone_repo
import config
from flask import Flask, request, jsonify, make_response
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

def load_service_config():
    services = config.services_list
    service_mapping = {}
    for service in services:
        service_mapping[os.getenv(f"{service}_PORT")] = os.getenv(f"{service}_NAME")
    return service_mapping

def fetch_metrics(name, port, payload):
    try:
        url = f"{config.endpoint_prefix}{name}_api:{port}/{name}"
        response = requests.post(url, json=payload)
        return name, response.json()
    except Exception as e:
        return name, {"error": str(e)}
    
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/metrics", methods=["OPTIONS", "POST"])
def get_metrics():
    try:
        if request.method == "OPTIONS":
            return _build_cors_preflight_response()
        elif request.method == "POST":
            data = request.get_json()
            repo_url = data["repo_url"]
            head_sha, repo_dir = clone_repo(repo_url)

            services = load_service_config()
            payload = {config.payload_key: repo_url}
            
            

            results = {}
            with ThreadPoolExecutor(max_workers=len(services)) as executor:
                futures = [executor.submit(fetch_metrics, name, port, payload) for port, name in services.items()]
                for future in as_completed(futures):
                    name, result = future.result()
                    results[name] = result

            return _corsify_actual_response(jsonify({"results": results})), 200
    except Exception as e:
        return _corsify_actual_response(jsonify({"message": f"Error occurred while cloning repository or fetching metrics: {e}"})), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)