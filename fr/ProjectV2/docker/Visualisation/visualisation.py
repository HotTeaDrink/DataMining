import json
import matplotlib.pyplot as plt
import numpy as np

def colorVisual():

    # Open the JSON file
    with open('output/directory_metadata.json', 'r') as file:
        # Load the JSON data
        json_data = json.load(file)

        # Iterate through each object in the list
        for obj in json_data:
            # Create a list to store all the closest colors for this image
            all_main_colors = []

            # Get the dictionary within each object
            for _, details in obj.items():
                # Access the "closest_colors" key within each dictionary
                main_colors = details.get("main_colors")
                if main_colors:
                    # Extend the list of all closest colors with the closest colors of the current image
                    all_main_colors.extend(main_colors)

            # Count the occurrences of each closest color for this image
            unique_main_colors, counts = np.unique(all_main_colors, axis=0, return_counts=True)

            # Calculate percentages
            total_count = sum(counts)
            percentages = [(count / total_count) * 100 for count in counts]

            # Create labels with RGB values and percentages
            labels = [f"RGB: {color}, {percentage:.2f}%" for color, percentage in zip(unique_main_colors, percentages)]
            sizes = counts
            colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in unique_main_colors]

            # Plot the pie chart for this image
            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, colors=colors, startangle=90)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Pie Chart of Main Colors for Image')
            plt.show()
        
        

def yearVisual():
    # Open the JSON file
    with open('output/directory_metadata.json', 'r') as file:
        # Load the JSON data
        json_data = json.load(file)

        # Create a list to store all the dates
        all_dates = []
    
        # Create a dictionary to store the counts of each size_class
        all_size_class = []
    
        all_make = []
        all_model = []

        # Iterate through each object in the list
        for obj in json_data:
            # Get the dictionary within each object
            for filename, details in obj.items():
                # Access the "DateTimeOriginal" key within each dictionary
                datetime_str = details.get("DateTimeOriginal")
                if datetime_str:
                    # Split the datetime string and keep only the date part
                    year = datetime_str.split(':')[0]
                    # Append the date to the list of all dates
                    all_dates.append(year)
                size_class = details.get("size_class")
                if size_class:
                    all_size_class.append(size_class)
                make = details.get("Make")
                if make:
                    all_make.append(make)
                model = details.get("Model")
                if model:
                    all_model.append(model)

    # Count the occurrences of each date
    unique_dates, counts = np.unique(all_dates, return_counts=True)

    # Extracting unique size classes and their counts
    unique_size_classes, counts_size_classes = np.unique(all_size_class, return_counts=True)

    unique_make, counts_make = np.unique(all_make, return_counts=True)
    unique_model, counts_model = np.unique(all_model, return_counts=True)


    # Creating a subplot grid with 2 rows and 2 columns
    fig, axs = plt.subplots(2, 2, figsize=(15, 12))

    # Plotting the first diagram
    axs[0, 0].bar(unique_dates, counts, color='skyblue')
    axs[0, 0].set_xlabel('Date')
    axs[0, 0].set_ylabel('Frequency')
    axs[0, 0].set_title('Bar Diagram of Dates (DateTimeOriginal)')
    axs[0, 0].tick_params(axis='x', rotation=45)

    # Plotting the second diagram
    axs[0, 1].bar(unique_size_classes, counts_size_classes, color='skyblue')
    axs[0, 1].set_xlabel('Size Class')
    axs[0, 1].set_ylabel('Frequency')
    axs[0, 1].set_title('Bar Diagram of Size Classes')
    axs[0, 1].tick_params(axis='x', rotation=45)

    # Plotting the third diagram
    axs[1, 0].bar(unique_make, counts_make, color='skyblue')
    axs[1, 0].set_xlabel('Make')
    axs[1, 0].set_ylabel('Frequency')
    axs[1, 0].set_title('Bar Diagram of Make')
    axs[1, 0].tick_params(axis='x', rotation=45)

    # Plotting the fourth diagram
    axs[1, 1].bar(unique_model, counts_model, color='skyblue')
    axs[1, 1].set_xlabel('Model')
    axs[1, 1].set_ylabel('Frequency')
    axs[1, 1].set_title('Bar Diagram of Model')
    axs[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.show()

colorVisual()
yearVisual()