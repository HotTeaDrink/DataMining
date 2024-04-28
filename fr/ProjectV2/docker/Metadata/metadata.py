import os
import json
import pika
from PIL import Image, TiffImagePlugin
import PIL.ExifTags
import numpy as np
from sklearn.cluster import KMeans
from pymongo import MongoClient
import base64

# Function to cast values to appropriate types
def cast(v):
    if isinstance(v, TiffImagePlugin.IFDRational):
        if v.denominator == 0:
            return None
        return float(v.numerator) / float(v.denominator)
    elif isinstance(v, tuple):
        return tuple(cast(t) for t in v)
    elif isinstance(v, bytes):
        return v.decode(errors="replace")
    elif isinstance(v, dict):
        for kk, vv in v.items():
            v[kk] = cast(vv)
        return v
    else:
        return v
    
import numpy as np

# Function to find the closest main color for a given RGB value
def find_closest_color(rgb):
    main_colors = [
        [0, 0, 0],      # Black
        [128, 128, 128],  # White
        [139, 69, 19],    # Red
        [139, 69, 19],    # Green
        [139, 69, 19],    # Blue
        [255, 255, 0],  # Yellow
        [255, 0, 255],  # Magenta
        [0, 255, 255],  # Cyan
        [128, 128, 128], # Grey
        [255, 165, 0],   # Orange
        [139, 69, 19],     # Dark Green
        [128, 0, 128],   # Purple
        [128, 0, 0],     # Maroon
        [0, 128, 128],   # Teal
        [128, 128, 0],   # Olive
        [0, 255, 255],   # Light Blue
        [210, 105, 30],  # Chocolate
        [139, 69, 19],   # Saddle Brown
        [255, 192, 203], # Pink
        [139, 69, 19],     # Navy
        [220, 20, 60]    # Crimson
        # Add more main colors as needed
    ]

    # Convert list of main colors to numpy array for vectorized calculations
    main_colors = np.array(main_colors)

    # Convert input RGB list to numpy array
    rgb = np.array(rgb)

    # Calculate Euclidean distances between input RGB and all main colors
    distances = np.linalg.norm(main_colors - rgb, axis=1)

    # Find index of the closest main color
    closest_index = np.argmin(distances)

    return main_colors[closest_index].tolist()  # Convert NumPy array to list

# Function to get main colors using KMeans clustering
def get_main_colors(image_path, num_clusters):
    print(f"[DEBUG] Getting main colors for image: {image_path}")
    imgfile = Image.open(image_path)
    imgfile.thumbnail((100, 100))
    numarray = np.array(imgfile)
    
    # Ensure that the number of elements in numarray is divisible by 3
    num_elements = numarray.shape[0] * numarray.shape[1]
    if num_elements % 3 != 0:
        numarray = np.resize(numarray, (num_elements // 3, 3))
    
    np.random.shuffle(numarray)
    num_samples = min(10000, len(numarray))
    numarray = numarray[:num_samples]
    
    # Reshape numarray into a 2D array
    numarray_flat = numarray.reshape(-1, 3)
    
    clusters = KMeans(n_clusters=num_clusters, n_init=2)
    clusters.fit(numarray_flat)
    main_colors = clusters.cluster_centers_.astype(int)
    return main_colors.tolist()


# Function to classify image size
def classify_image_size(image_size):
    width, height = image_size
    small_threshold = 500
    medium_threshold = 1000
    if width <= small_threshold or height <= small_threshold:
        return "Small"
    elif width <= medium_threshold or height <= medium_threshold:
        return "Medium"
    else:
        return "Large"

# Function to extract image metadata
def get_image_metadata(image_path):
    print(f"[DEBUG] Extracting metadata for image: {image_path}")
    metadata = {}
    imgfile = Image.open(image_path)
    metadata['format'] = imgfile.format
    metadata['size'] = imgfile.size
    image_size = imgfile.size
    metadata['size_class'] = classify_image_size(image_size)
    metadata["main_colors"] = get_main_colors(image_path, 3)
    metadata["closest_colors"] = [find_closest_color(color) for color in metadata["main_colors"]]
    metadata['orientation'] = 'Unknown'
    exif_data = imgfile._getexif()
    if exif_data:
        hasExif = True
        for k, v in imgfile._getexif().items():
            if k in PIL.ExifTags.TAGS:
                v = cast(v)
                if PIL.ExifTags.TAGS[k] == 'Orientation':
                    if v == 1:
                        metadata['orientation'] = 'Landscape'
                    elif v == 3:
                        metadata['orientation'] = 'Portrait'
                metadata[PIL.ExifTags.TAGS[k]] = v
    
    return metadata

# Function to consume image paths from RabbitMQ
def consume_image_paths():
    # MongoDB setup
    client = MongoClient('mongodb://mongodb:27017/')
    db = client['image_metadata']
    collection = db['metadata']

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='image_paths')

    def callback(ch, method, properties, body):
        image_path = body.decode('utf-8')
        print(f"Received image path: {image_path}")
        metadata = get_image_metadata(image_path)
        print("Extracted metadata:", metadata)
        
        # Convert integer keys of GPSInfo dictionary to strings
        gps_info_str_keys = {str(k): v for k, v in metadata.get('GPSInfo', {}).items()}
        # Update the metadata with the modified GPSInfo dictionary
        metadata['GPSInfo'] = gps_info_str_keys
        
        # Create a new document with the filename as a separate field
        document = {
            'filename': os.path.basename(image_path),
            **metadata
        }
        
        # Check if the image already exists in the database
        existing_entry = collection.find_one({'filename': document['filename']})
        
        if existing_entry:
            # Update the existing entry with new metadata
            collection.update_one(
                {'filename': document['filename']},
                {"$set": document}
            )
            print("Updated existing entry in the database.")
        else:
            # Insert metadata into MongoDB collection
            collection.insert_one(document)
            print("Inserted new entry into the database.")

    channel.basic_consume(queue='image_paths', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    consume_image_paths()