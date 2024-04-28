import os
import random
import string
import json
import logging
from pymongo import MongoClient
from bson import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Load image metadata from MongoDB
client = MongoClient('mongodb://mongodb:27017/')
db = client['image_metadata']
collection = db['metadata']
image_data = {}
for doc in collection.find({'metadata': {'$exists': True}}).limit(1000):
    image_data[str(doc['_id'])] = doc['metadata']

# Function to extract properties from selected images
def extract_properties(selected_image_names, json_data):
    extracted_properties = {}
    for image_name in selected_image_names:
        image_metadata = json_data[image_name]
        extracted_properties[image_name] = {
            'format': image_metadata['format'],
            'size': image_metadata['size'],
            'size_class': image_metadata['size_class'],
            'main_colors': image_metadata['main_colors'],
            'orientation': image_metadata['orientation'],
            'tags': image_metadata.get('tags', [])
        }
    return extracted_properties

# Function to save user properties to MongoDB
def save_user_properties(username, selected_image_names, json_data, mongo_uri, db_name, collection_name):
    # Extract properties
    extracted_properties = extract_properties(selected_image_names, json_data)

    # Connect to the MongoDB database
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # Create a new user document or update an existing one
    user_doc = {
        'username': username,
        'properties': extracted_properties
    }
    result = collection.update_one(
        {'username': username},
        {'$set': user_doc},
        upsert=True
    )

    logging.info(f"User properties for {username} have been saved to MongoDB ({result.matched_count} documents matched, {result.modified_count} documents modified)")

# Generate 100 fake users with favorite images
import os
import random
import string

def generate_fake_users(num_users, mongo_uri, db_name, collection_name):
    # Connect to the MongoDB database
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # Retrieve the image filenames and metadata from MongoDB
    image_data = {}
    image_files = []
    for doc in collection.find({'metadata': {'$exists': True}}).limit(1000):
        image_data[str(doc['_id'])] = doc['metadata']
        image_files.append(str(doc['_id']))

    # Generate a random number of images for each user
    max_images_per_user = 100
    num_images = random.randint(1, max_images_per_user)
    selected_images = random.sample(image_files, num_images)

    # Call save_user_properties function
    username = 'fake_user'
    save_user_properties(username, selected_images, image_data, mongo_uri, db_name, collection_name)

generate_fake_users(100, 'mongodb://mongodb:27017/', 'image_metadata', 'metadata')

generate_fake_users(100, 'images', 100, 'mongodb://mongodb:27017/', 'user_properties', 'user_properties')