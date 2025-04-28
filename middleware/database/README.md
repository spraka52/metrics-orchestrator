# Database Setup Guide

Step-by-step instructions for setting up the database environment using Docker.

### Step 1: Start MongoDB in Docker

Start a MongoDB container that runs in the background with port 27017 exposed:

```bash
docker run -d --name test-mongo -p 27017:27017 mongo
```

### Step 2: Create a Docker Network

Create a dedicated network for containers to communicate:

```bash
docker network create test-net
```

### Step 3: Connect MongoDB to the Network

Add the MongoDB container to the network just created:

```bash
docker network connect test-net test-mongo
```

### Step 4: Build the Database Container

Navigate to the database directory and build the container:

```bash
cd middleware/database
docker build -t test-db .
```

### Step 5: Run the Database Container

Run your database container on the same network to test:

```bash
docker run --network test-net test-db
```

### Step 6: Test the health check 

Open your browser and go to: 
http://localhost:5007/health 

Using curl, run this commsnd:
curl http://localhost:5007/health 