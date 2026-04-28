# config.py
# Central configuration for the Disease Outbreak Hotspot Predictor
# Replace the MONGO_URI below with your actual MongoDB connection string

import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGO_URI = "mongodb://localhost:27017"

DATABASE_NAME = "dengue"
COLLECTION_NAME = "dengue_data"

# Path to the dataset relative to the project root
DATASET_PATH = "data/dengue.csv"

# Path to the saved model
MODEL_PATH = "model/model.pkl"

# SMS alert settings (Twilio)
# Set SMS_ENABLED=true to send SMS for Medium/High risk.
SMS_ENABLED = os.getenv("SMS_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
SMS_ACCOUNT_SID = os.getenv("SMS_ACCOUNT_SID", "")
SMS_AUTH_TOKEN = os.getenv("SMS_AUTH_TOKEN", "")
SMS_FROM_NUMBER = os.getenv("SMS_FROM_NUMBER", "")
SMS_TO_NUMBER = os.getenv("SMS_TO_NUMBER", "")

# Risk thresholds (percentile-based, set during training)
# These are overridden at runtime by train_model.py
RISK_LOW_THRESHOLD = 33
RISK_HIGH_THRESHOLD = 66
