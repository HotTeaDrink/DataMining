import requests
import shutil
import os
import pika
import time
from pyspark import SparkContext
from urllib3.exceptions import IncompleteRead

def download_image(url):
    # Decode bytes to string
    url = url.decode('utf-8')  
    print(f"[DEBUG] Downloading image from URL: {url}")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        request = requests.get(url, allow_redirects=True, headers=headers, stream=True)
        request.raise_for_status()  # Raise HTTPError for bad status codes
        if request.status_code == 200:
            print("[DEBUG] Image download successful.")
            
            # Create 'downloads' directory if it doesn't exist
            if not os.path.exists("./downloads"):
                try:
                    os.makedirs("./downloads")
                except OSError as e:
                    print(f" [!] Error: Failed to create the directory: {e}")

            # Extract the filename from the URL and save the image in 'downloads' directory
            filename = os.path.join("./downloads", os.path.basename(url))
            print(f"[DEBUG] Saving image to file: {filename}")
            
            with open(filename, "wb") as image:
                request.raw.decode_content = True
                shutil.copyfileobj(request.raw, image)
            
            print("[DEBUG] Image saved successfully.")

            # Send the path of the downloaded image to RabbitMQ for analysis
            send_image_path_to_queue(filename)  # New function call
    except IncompleteRead as e:
        print(f" [!] Error: Incomplete read occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f" [!] Error: Request failed: {e}")

    return request.status_code if 'request' in locals() else None

def send_image_path_to_queue(path):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='image_paths')

    channel.basic_publish(exchange='',
                          routing_key='image_paths',
                          body=path)
    print(f"[DEBUG] Image path sent to RabbitMQ: {path}")

    connection.close()

def clear_downloads_directory():
    # Clear 'downloads' directory if it exists
    if os.path.exists("./downloads"):
        try:
            shutil.rmtree("./downloads")
        except OSError as e:
            print(f" [!] Error: Failed to clear downloads directory: {e}")

# Clear 'downloads' directory before every execution
clear_downloads_directory()

def callback(ch, method, properties, body):
    download_image(body)
    print(" [x] Downloaded %r" % body)

def consume_image_links():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='image_links')

    # Loop indefinitely
    while True:
        # Wait until a message is available in the queue
        print(' [*] Waiting for messages. To exit press CTRL+C')
        method_frame, header_frame, body = channel.basic_get(queue='image_links', auto_ack=True)

        if method_frame:
            # If a message is available, process it
            callback(None, method_frame, None, body)
        else:
            # If no message is available, print a message and wait before checking again
            print(' [!] No messages in the queue. Waiting for 5 seconds...')
            time.sleep(5)

if __name__ == "__main__":
    consume_image_links()
