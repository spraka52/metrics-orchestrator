import os, asyncio, httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from middleware.database.crud import get_metrics
from middleware.clone_repo.clone_repo import clone_repo, replay_history_and_store
import middleware.clone_repo.config as config

GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8080))
STORE_METRICS_URL = os.getenv(
    "STORE_METRICS_URL",            # read from env
    "http://store_metrics:5007/store_metrics",   # fallback
)

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

def build_service_map() -> dict[str, str]:
    return {os.getenv(f"{svc}_PORT"): os.getenv(f"{svc}_NAME")
            for svc in config.services_list}

async def call_metric(name: str, port: str, payload: dict, client: httpx.AsyncClient):
    try:
        url = f"{config.endpoint_prefix}{name}_api:{port}/{name}"
        resp = await client.post(url, json=payload, timeout=120)
        return name, resp.json()
    except Exception as e:
        return name, {"error": str(e)}

async def run_all_metrics(repo_url: str, head_sha: str, time_stamp: str):
    payload = {config.payload_key: repo_url}
    services = build_service_map()
    async with httpx.AsyncClient() as client:
        tasks = [call_metric(n, p, payload, client) for p, n in services.items()]
        results = dict(await asyncio.gather(*tasks))
    store_payload = {
        "results": results,
        "repo_url": repo_url,
        "commit_hash": head_sha,
        "timestamp": time_stamp,
        "project_name": repo_url.split("/")[-1].removesuffix(".git")
    }
    async with httpx.AsyncClient() as client:
        await client.post(STORE_METRICS_URL, json=store_payload, timeout=120)
    return results

@app.post("/add_repo/", response_model=dict)
async def add_repo(req: AddRepoReq, bg: BackgroundTasks):
    try:
        head_sha, time_stamp, repo_dir, was_cloned = clone_repo(req.repo_url)
        current_results = await run_all_metrics(req.repo_url, head_sha, time_stamp)

        if was_cloned:
            bg.add_task(
                replay_history_and_store,
                repo_dir,
                req.repo_url,
                head_sha,
                90,
                run_all_metrics
            )

        return {"results": current_results}
    except Exception as e:
        raise HTTPException(500, str(e))
    

@app.get("/get_metrics/", response_model=dict)
async def get_metrics_api(repo_url: str, metrics: str = Query(...)):
    try:
        selected_metrics = metrics.split(",")
        project_name = repo_url.split("/")[-1].removesuffix(".git")
        data = []
        for i in range(len(selected_metrics)):
            metric = selected_metrics[i]
            data.append(get_metrics(project_name, metric))
        # data = get_metrics(project_name, metrics)
        return {"metrics_data": data}
    except Exception as e:
        raise HTTPException(500, str(e))

