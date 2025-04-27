from crud import save_metrics, get_metrics
from datetime import datetime

project = "https://github.com/test/repo.git"
commit = "abc123"
service = "loc"
data = {"lines": 500, "files": 3}
timestamp = datetime.utcnow().isoformat()

print("Saving to MongoDB:")
save_metrics(service, project, commit, data, timestamp=timestamp)

print("Fetching from MongoDB:")
result = get_metrics(service, project, commit)
print("Result from DB:", result)

project = "https://github.com/test/testingrepo.git"
commit = "abc1234"
service = "lcom4"
data = {"class.name": "calculate", "score": 3}
timestamp = datetime.utcnow().isoformat()

print("Saving to MongoDB:")
save_metrics(service, project, commit, data, timestamp=timestamp)

print("Fetching from MongoDB:")
result = get_metrics(service, project, commit)
print("Result from DB:", result)