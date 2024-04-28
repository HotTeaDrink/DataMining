from flask import Flask, render_template, request, send_from_directory, redirect, url_for, send_file
from pymongo import MongoClient
import os
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

client = MongoClient('mongodb://mongodb:27017/')
db = client['image_metadata']
collection = db['metadata']

app = Flask(__name__)

# Configure image directory path (replace with your actual path)
DOWNLOADS_DIR = '/app/downloads'

@app.route('/')
def index():
    images = [f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
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
    images = [f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    if request.method == 'POST':
        user_id = request.form['user_id']
        favorite_images = [image_name for image_name, is_favorite in zip(images, request.form.getlist('favorites'))]

        print(f"Inserting document with user_id={user_id} and favorite_images={favorite_images}")
        result = collection.update_one(
            {'user_id': user_id},
            {'$set': {'favorites': favorite_images}},
            upsert=True
        )
        print(f"Matched {result.matched_count} documents and modified {result.modified_count} documents")

        return redirect(url_for('favorites'))

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

    return render_template('favorites.html', checkboxes=checkboxes)

@app.route('/closest_colors_pie_chart')
def closest_colors_pie_chart():
    metadata = list(collection.find())

    all_closest_colors = []

    for doc in metadata:
        closest_colors = doc.get("closest_colors")
        if closest_colors:
            all_closest_colors.extend(closest_colors)

    unique_closest_colors, counts = np.unique(all_closest_colors, axis=0, return_counts=True)

    total_count = sum(counts)
    percentages = [(count / total_count) * 100 for count in counts]

    labels = [f"RGB: {color}, {percentage:.2f}%" for color, percentage in zip(unique_closest_colors, percentages)]
    sizes = counts
    colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in unique_closest_colors]

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, startangle=90)
    ax.axis('equal')
    ax.set_title('Pie Chart of Closest Colors')

    buffer = BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png')

@app.route('/images/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
