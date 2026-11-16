from pymongo import MongoClient

DB_PASSWORD = "test_password"  # Pamiętaj o podmienieniu hasła

client = MongoClient(f"mongodb+srv://test_user:{DB_PASSWORD}@cluster0.lybvqum.mongodb.net/")
db = client["calendar_db"]
events_collection = db["events"]
users_collection = db["users"]