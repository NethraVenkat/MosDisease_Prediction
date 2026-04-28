# db.py
# MongoDB connection and CRUD operations using PyMongo

from pymongo import MongoClient, errors
from MosDisease_Prediction.backend.config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from datetime import datetime


def get_collection():
    """Return the MongoDB predictions collection."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Force connection check
        db = client[DATABASE_NAME]
        return db[COLLECTION_NAME]
    except errors.ServerSelectionTimeoutError as e:
        raise ConnectionError(f"MongoDB connection failed: {e}")


def insert_prediction(record: dict) -> str:
    """Insert a prediction record into MongoDB. Returns the inserted document ID."""
    collection = get_collection()
    record["timestamp"] = datetime.utcnow()
    result = collection.insert_one(record)
    return str(result.inserted_id)


def fetch_all_predictions() -> list:
    """Return all stored prediction documents."""
    collection = get_collection()
    records = list(collection.find({}, {"_id": 0}))
    return records


def fetch_high_risk_predictions() -> list:
    """Return only High-risk prediction records."""
    collection = get_collection()
    records = list(collection.find({"predicted_risk": "High"}, {"_id": 0}))
    return records
