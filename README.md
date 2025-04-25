# Metrics Orchestrator
This tool works as an api gateway that the frontend will call. This will inturn handle interactions with the metrics micoroservices, as well as handling historical data and caching.

## Running
To run the application, you need to have Docker installed. You can run the application using the following command:

```bash
docker-compose up --build
```

This will build the application and start the server. The server will be available at `http://localhost` on the port you specified in the `.env` file.

This uses the latest published versions of the microservices, and the local code for the api gateway.