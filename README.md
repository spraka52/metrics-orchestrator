# Metrics Orchestrator
This tool works as an api gateway that the frontend will call. This will inturn handle interactions with the metrics micoroservices, as well as handling historical data and caching.

## Running
To run the application, you need to have Docker installed. You can run the application using the following command:

```bash
docker-compose up --build
```

This will build the application and start the server. The server will be available at `http://localhost` on the port you specified in the `.env` file.

This uses the latest published versions of the microservices, and the local code for the api gateway.

This will spin up:

- All metric microservices (Java & Python based)
- MongoDB
- Shared volume for cloned repos
- The orchestrator (`clone_repo`)
- The `store_metrics` service

---

## How to View MongoDB Data from Docker

Follow these steps to inspect the metrics stored in MongoDB:

---

### List Running Docker Containers

```bash
docker ps
```

Look for the container named `mongo`.

---

###  Connect to MongoDB Container

```bash
docker exec -it mongo mongosh
```

> For older MongoDB versions, use `mongo` instead of `mongosh`.

---

### Show All Databases

```javascript
show dbs
```

You should see databases like `admin`, `local`, and your custom metrics database (e.g., `metrics`, `projects`, etc.).

---

###  Switch to the Metrics Database

```javascript
use metrics
```

> Replace `metrics` with the actual name of your database if different.

---

### Show All Collections

```javascript
show collections
```

Each metric service should have its own collection.

---

### Query a Collection

```javascript
db.metrics_defects.find().pretty()
```

Replace `metrics_defects` with the name of any metric service collection (e.g., `loc`, `mttr`, `hal`, etc.).

---

### Exit the Mongo Shell

```bash
exit
```

---

## API Endpoints

### POST `/metrics`

Clone repo and calculate metrics for the latest commit.

### POST `/store_metrics`

Internal call from orchestrator to store metric data.

---


