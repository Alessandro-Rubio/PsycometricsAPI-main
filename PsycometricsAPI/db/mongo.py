from pymongo import MongoClient
from decouple import config

client = MongoClient(config("MONGO_URI"))
db = client[config("MONGO_DB")]

hr_collection = db["hr"]
candidate_collection = db["candidate"]
test_collection = db["test"]
result_collection = db["result"]
report_collection = db["report"]