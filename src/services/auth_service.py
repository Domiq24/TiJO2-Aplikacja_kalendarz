from services.db import users_collection
from werkzeug.security import check_password_hash, generate_password_hash


def register_user(username, password, confirm_password):
  # Sprawdzenie czy hasła się zgadzają
  if password != confirm_password:
    raise ValueError("Podane hasła nie są identyczne.")

  if users_collection.find_one({"username": username}):
    raise ValueError("Użytkownik o tej nazwie już istnieje.")

  hashed_password = generate_password_hash(password)
  users_collection.insert_one({"username": username, "password": hashed_password})


def authenticate_user(username, password):
  user = users_collection.find_one({"username": username})
  if user and check_password_hash(user["password"], password):
    return str(user["_id"])
  return None