from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from pymongo import MongoClient
import os

client = MongoClient('mongodb://mongodb:27017/')
db = client['image_metadata']
collection = db['metadata']

app = Flask(__name__)

# Configure image directory path (replace with your actual path)
DOWNLOADS_DIR = '/app/downloads'

@app.route('/')
def index():
    # Get a list of image filenames from the directory (ensure valid images)
    images = [f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    # Create image data with URLs and empty tags (replace with your tag logic if needed)
    images_data = []
    for image_name in images:
        image_metadata = collection.find_one({'filename': image_name})
        if image_metadata:
            if 'tags' not in image_metadata:
                collection.update_one({'_id': image_metadata['_id']}, {'$set': {'tags': []}}, upsert=True)
            images_data.append({'image_url': f'/images/{image_name}', 'image_name': image_name, 'tags': image_metadata.get('tags', [])})
    return render_template('index.html', images_data=images_data)

@app.route('/add_tags', methods=['POST'])
def add_tags():
    print("Adding tags...")
    images_data = []
    for image_name in request.form:
        print(f"Processing image: {image_name}")
        image_metadata = collection.find_one({'filename': image_name})
        if image_metadata:
            print(f"Found metadata for image: {image_name}")
            tags = request.form.getlist(image_name)
            print(f"Tags for image {image_name}: {tags}")
            collection.update_one({'_id': image_metadata['_id']}, {'$set': {'tags': tags}}, upsert=True)
            images_data.append({'image_url': f'/images/{image_name}', 'image_name': image_name, 'tags': tags})
        else:
            print(f"No metadata found for image: {image_name}")
    print("Tags added.")
    return redirect(url_for('index'))

@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
    # Get a list of image filenames from the directory (ensure valid images)
    images = [f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    if request.method == 'POST':
        # Get the user's name and favorite images from the form submission
        name = request.form['name']
        favorite_images = [image_name for image_name, is_favorite in zip(images, request.form.getlist('favorites'))]

        # Insert the user's name and favorite images into the MongoDB collection
        print(f"Inserting document with name={name} and favorite_images={favorite_images}")
        result = collection.update_one(
            {'name': name},
            {'$set': {'favorites': favorite_images}},
            upsert=True
        )
        print(f"Matched {result.matched_count} documents and modified {result.modified_count} documents")

        # Redirect the user back to the favorites page
        return redirect(url_for('favorites'))

    # Create a list of checkboxes for each image
    checkboxes = []
    for image_name in images:
        image_metadata = collection.find_one({'filename': image_name})
        if image_metadata:
            if 'favorites' in image_metadata:
                is_favorite = image_name in image_metadata['favorites']
            else:
                is_favorite = False
        else:
            is_favorite = False
        checkboxes.append({'image_url': f'/images/{image_name}', 'image_name': image_name, 'is_favorite': is_favorite})

    # Render the favorites page template with the list of checkboxes
    return render_template('favorites.html', checkboxes=checkboxes)

@app.route('/images/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)