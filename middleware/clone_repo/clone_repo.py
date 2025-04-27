import subprocess
from urllib.parse import urlparse
import re
from pathlib import Path
import fcntl
import git
from datetime import timezone, datetime, timedelta
import logging

SHARED_BASE_DIR = "/shared/repos"

# Set up logging
logging.basicConfig(level=logging.INFO)

def clone_repo(repo_url):
    if not repo_url:
        raise ValueError("No repository URL provided. Please enter a valid GitHub repository URL.")

    parsed = urlparse(repo_url)
    if parsed.netloc.lower() != "github.com" or parsed.path.count("/") < 2:
        raise ValueError("Invalid GitHub repository URL. Ensure it follows the format 'https://github.com/owner/repo'.")

    repo_path = parsed.path.strip("/")
    if repo_path.endswith(".git"):
        repo_path = repo_path[:-4]
    if not re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", repo_path):
        raise ValueError("Malformed repository URL. Ensure the URL points to a valid GitHub repository.")

    owner, repo = repo_path.split("/")
    repo_dir = Path(SHARED_BASE_DIR) / owner / repo
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    lockfile = repo_dir.with_suffix(".lock")

    was_cloned = False 

    with open(lockfile, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            if repo_dir.exists():
                was_cloned = False   
                subprocess.run(["rm", "-rf", str(repo_dir)], check=True)
                subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True)
            else:
                subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True)
                was_cloned = True    # cloned

            repo        = git.Repo(str(repo_dir))
            head_commit = repo.head.commit
            head_sha    = head_commit.hexsha
            head_ts_iso = head_commit.committed_datetime.astimezone(timezone.utc).date().isoformat()


        except subprocess.CalledProcessError as e:
            error_output = e.stderr.lower() if e.stderr else ""
            if "not found" in error_output:
                raise RuntimeError("Repository not found. Please check the URL.")
            elif "authentication" in error_output or "permission denied" in error_output:
                raise PermissionError("Private repository or insufficient permissions. Please check your access.")
            else:
                raise RuntimeError(f"Git error: {e.stderr or e.stdout}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")

    return head_sha, head_ts_iso, str(repo_dir), was_cloned


async def replay_history_and_store(repo_dir: str,
                                   repo_url: str,
                                   head_sha: str,
                                   days_back: int,
                                   run_metrics_async):         # callback from gateway
    """
    Walk back ≤ days_back commits (one per day) and re-run metrics.
    `run_metrics_async(repo_url, sha, ts)` must be an *awaitable* supplied by the caller.
    """
    default_branch = subprocess.check_output(
        ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
        text=True
    ).strip()
    
    # get list of commits (oldest→newest)
    cmd = (
        f"git -C {repo_dir} log --pretty=format:'%cI|%H' --reverse {head_sha}"
    )

    commit_lines = subprocess.check_output(
        ["bash", "-c", cmd],
        text=True
    ).strip().splitlines()

    commits: list[tuple[str, str]] = [
        tuple(line.split("|", 1)) for line in commit_lines if "|" in line
    ]

    # Build a mapping: date (YYYY-MM-DD) -> latest commit_sha
    commit_map = {}
    for ts, sha in commits:
        date_str = ts.split("T")[0]
        commit_map[date_str] = sha

    # Build final list for past `days_back` days, filling gaps
    today = datetime.utcnow().date()
    final_commits = []

    latest_sha = None
    for i in range(days_back):
        day = today - timedelta(days=(days_back - 1 - i))
        day_str = day.isoformat()

        if day_str in commit_map:
            latest_sha = commit_map[day_str]

        if latest_sha:
            final_commits.append((day_str, latest_sha))


    final_commits.reverse()


    # logging.info(f"Commits to replay: {final_commits}")

    try:
        for ts, sha in final_commits:
            subprocess.check_call(["git", "-C", repo_dir, "checkout", "-f", sha])
            await run_metrics_async(repo_url, sha, ts)
    finally:
        # always restore HEAD
        subprocess.check_call(["git", "-C", repo_dir, "checkout", "-f", default_branch])
