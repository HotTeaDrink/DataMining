import json
import matplotlib.pyplot as plt
import numpy as np
from pymongo import MongoClient

def generate_closest_colors_pie_chart():
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://mongodb:27017/')
        db = client['image_metadata']
        collection = db['metadata']

        # Get all documents from the collection
        metadata = list(collection.find())

        # Create a list to store all the closest colors
        all_closest_colors = []

        # Iterate through each document in the list
        for doc in metadata:
            # Get the closest colors for each image
            closest_colors = doc.get("closest_colors")
            if closest_colors:
                # Extend the list of all closest colors with the closest colors of the current image
                all_closest_colors.extend(closest_colors)

        if not all_closest_colors:
            raise ValueError("No closest colors found in MongoDB documents.")

        # Count the occurrences of each closest color
        unique_closest_colors, counts = np.unique(all_closest_colors, axis=0, return_counts=True)

        # Calculate percentages
        total_count = sum(counts)
        percentages = [(count / total_count) * 100 for count in counts]

        # Create labels with RGB values and percentages
        labels = [f"RGB: {color}, {percentage:.2f}%" for color, percentage in zip(unique_closest_colors, percentages)]
        sizes = counts
        colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in unique_closest_colors]

        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Pie Chart of Closest Colors')
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_closest_colors_pie_chart()
