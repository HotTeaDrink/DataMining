import os
import random
import string
import json
import logging
from pymongo import MongoClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Function to retrieve filenames from MongoDB
def get_image_filenames_from_mongodb():
    client = MongoClient('mongodb://mongodb:27017/')
    db = client['image_metadata']
    collection = db['metadata']
    filenames = []
    for doc in collection.find({}, {'filename': 1}):
        filenames.append(doc['filename'])
        print(doc)
    return filenames

# Function to save user properties (favorite filenames) to MongoDB
def save_user_properties(username, favorite_filenames, mongo_uri, db_name, collection_name):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    user_doc = {
        'username': username,
        'favorite_filenames': favorite_filenames
    }
    result = collection.update_one(
        {'username': username},
        {'$set': user_doc},
        upsert=True
    )

    # logging.info(f"User properties for {username} have been saved to MongoDB ({result.matched_count} documents matched, {result.modified_count} documents modified)")

# Generate 100 fake users with favorite images
def generate_fake_users(num_users):
    image_filenames = get_image_filenames_from_mongodb()

    if not image_filenames:
        logging.warning("No image filenames found in MongoDB")
        return

    # max_images_per_user = min(num_users, len(image_filenames))
    # for i in range(num_users):
    #     username = 'fake_user_' + str(i)
    #     num_images = random.randint(1, max_images_per_user)
    #     favorite_filenames = random.sample(image_filenames, num_images)
    #     save_user_properties(username, favorite_filenames, mongo_uri='mongodb://mongodb:27017/', db_name='image_metadata', collection_name='users')

generate_fake_users(1)
