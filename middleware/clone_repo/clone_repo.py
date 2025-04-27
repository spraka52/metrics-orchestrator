import subprocess
from urllib.parse import urlparse
import re
from pathlib import Path
import fcntl
import git
from datetime import timezone
SHARED_BASE_DIR = "/shared/repos"

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
    with open(lockfile, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            if repo_dir.exists():
                git_dir = repo_dir / ".git"
                if git_dir.exists():
                    subprocess.run(
                        ["git", "-C", str(repo_dir), "pull"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                else:
                    subprocess.run(["rm", "-rf", str(repo_dir)], check=True)
                    subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True)
            else:
                subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True)

            repo        = git.Repo(str(repo_dir))
            head_commit = repo.head.commit
            head_sha    = head_commit.hexsha
            head_ts_iso = head_commit.committed_datetime.astimezone(
                timezone.utc
            ).isoformat()

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

    return head_sha, head_ts_iso, str(repo_dir)


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
        f"git -C {repo_dir} log --pretty=format:'%cI|%H' --reverse {head_sha} "
        "| awk -F'|' '{date = substr($1, 1, 10); commit[date] = $0} "
        "END {for (d in commit) print commit[d]}' "
        f"| sort | tail -n {days_back}"
    )

    commit_lines = subprocess.check_output(
        ["bash", "-c", cmd],
        text=True
    ).strip().splitlines()
    commits: list[tuple[str, str]] = [
        tuple(line.split("|", 1)) for line in commit_lines
    ]
    try:
        for ts, sha  in commits:
            subprocess.check_call(["git", "-C", repo_dir, "checkout", "-f", sha])
            await run_metrics_async(repo_url, sha, ts)
    finally:
        # always restore HEAD
        subprocess.check_call(["git", "-C", repo_dir, "checkout", "-f", default_branch])