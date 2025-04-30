import os
import asyncio
import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from middleware.database.crud import get_metrics
from middleware.clone_repo.clone_repo import clone_repo, replay_history_and_store

GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8080))
STORE_METRICS_URL = os.getenv("STORE_METRICS_URL", "http://store_metrics:5000/store_metrics")

class AddRepoReq(BaseModel):
    repo_url: str

app = FastAPI(title="metrics-orchestrator-gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_service_config() -> dict[str, str]:
    services_raw = os.getenv("SERVICES")
    if not services_raw:
        raise Exception("SERVICES environment variable not set")
    
    service_mapping = {}
    services = services_raw.split(",")
    for service in services:
        service_mapping[service] = service.replace("/", "-")
    return service_mapping

async def call_metric(service_name: str, payload: dict, client: httpx.AsyncClient):
    try:
        url = f"http://{service_name}:5000/{service_name}"
        resp = await client.post(url, json=payload, timeout=120)
        return service_name, resp.json()
    except Exception as e:
        return service_name, {"error": str(e)}

async def run_all_metrics(repo_url: str, head_sha: str, time_stamp: str, is_history_mode: bool = False):
    payload = {"repo_url": repo_url}
    services = load_service_config()

    if is_history_mode:
        # Skip defects-stats in history mode
        services = {k: v for k, v in services.items() if v != "defects-stats"}

    async with httpx.AsyncClient() as client:
        tasks = [call_metric(service_name, payload, client) for service_name in services.values()]
        results_list = await asyncio.gather(*tasks)
        results = dict(results_list)

    project_name = repo_url.split("/")[-1].removesuffix(".git")
    store_payload = {
        "results": results,
        "repo_url": repo_url,
        "commit_hash": head_sha,
        "timestamp": time_stamp,
        "project_name": project_name
    }
    async with httpx.AsyncClient() as client:
        await client.post(STORE_METRICS_URL, json=store_payload, timeout=120)
    return results


@app.post("/add_repo", response_model=dict)
async def add_repo(req: AddRepoReq, bg: BackgroundTasks):
    try:
        head_sha, time_stamp, repo_dir, was_cloned = clone_repo(req.repo_url)
        current_results = await run_all_metrics(req.repo_url, head_sha, time_stamp, is_history_mode=False)

        if was_cloned:
            bg.add_task(
                replay_history_and_store,
                repo_dir,
                req.repo_url,
                head_sha,
                90,
                lambda url, sha, ts: run_all_metrics(url, sha, ts, is_history_mode=True)
            )

        return {"results": current_results}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/get_metrics", response_model=dict)
async def get_metrics_api(repo_url: str, metrics: str = Query(...)):
    try:
        selected_metrics = metrics.split(",")
        project_name = repo_url.split("/")[-1].removesuffix(".git")
        data = [get_metrics(project_name, metric) for metric in selected_metrics]
        return {"metrics_data": data}
    except Exception as e:
        raise HTTPException(500, str(e))