FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install pymongo

ENV MONGO_URI=mongodb://test-mongo:27017

CMD ["python", "test_db.py"]
