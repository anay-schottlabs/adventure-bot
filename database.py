from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Get the database connection string
load_dotenv()
CONNECTION_STRING = os.getenv("DATABASE_CONNECTION_STRING")

# Connect to the database
cluster = MongoClient(CONNECTION_STRING)
collection = cluster["Campaigns"]["Campaigns"]

# Returns a list of all objects in the database
def get_all():
  return list(collection.find({}))

# Adds the provided object into the database
def add_item(item):
  collection.insert_one(item)

# Finds the object in the database by its id
# Replaces the found object's value with the object's current value
def update_item(item):
  id = item["_id"]
  collection.update_one({ "_id": id }, { "$set": item })

# Removes the provided object from the database
def remove_item(item):
  id = item["_id"]
  collection.delete_one({ "_id": id })
