from flask import Flask, request, render_template
from google.cloud import storage
import requests
import uuid
import os
import tempfile
from google.cloud import firestore
from google.cloud import pubsub_v1
import json


app = Flask(__name__)


def process_file_or_url(file_obj, url):
    if file_obj is not None:
        # Save the file to a temporary file
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(file_obj.read())
    elif url is not None:
        # Download the file from the URL to a temporary file
        response = requests.get(url, stream=True)
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
    else:
        filename = None
    return filename


@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'GET':
        return render_template('upload.html')
    elif request.method == 'POST':
        user_id = str(uuid.uuid4()) # convert UUID to string

        # Process the video file
        video_file = request.files.get('video-file')
        video_url = request.form.get('video-url')
        video_filename = process_file_or_url(video_file, video_url)

        # Process the image file
        image_file = request.files.get('image-file')
        image_url = request.form.get('image-url')
        image_filename = process_file_or_url(image_file, image_url)

        # Instantiate the storage client
        storage_client = storage.Client()

        # Upload video file to Google Cloud Storage
        bucket = storage_client.get_bucket('full-vid-storage')
        blob = bucket.blob(f'{user_id}/video.mp4')
        with open(video_filename, 'rb') as vid_file:
            blob.upload_from_file(vid_file)

        # Upload watermark image to Google Cloud Storage
        blob = bucket.blob(f'{user_id}/watermark.png')
        with open(image_filename, 'rb') as img_file:
            blob.upload_from_file(img_file)

        # Clean up temporary files
        os.remove(video_filename)
        os.remove(image_filename)

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path('cc-assigment2-388310', 'split-video')

        # Publish a message to the Pub/Sub topic
        message = {
            'video_id': user_id,
        }
        message_data = json.dumps(message).encode('utf-8')
        future = publisher.publish(topic_path, data=message_data)

        # Non-blocking. Allow the publish() method to complete in the background.
        future.result()

        return f'Video ID: {user_id}'  # Return the video_id to the user


@app.route('/progress', methods=['GET', 'POST'])
def check_progress():
    if request.method == 'GET':
        return render_template('progress.html')
    elif request.method == 'POST':
        video_id = request.form.get('video-id')

        db = firestore.Client()
        doc_ref = db.collection('jobs').document(video_id)

        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            frames = data.get('frames')
            processed = data.get('processed')

            # Calculate the percentage of processed frames
            processed_count = sum([1 for frame in processed.values() if frame])
            percent_processed = (processed_count / frames) * 100

            # If all frames are processed, provide a download link to the completed video
            if data.get('completed'):
                link = f'https://storage.googleapis.com/completed-videos/{video_id}.mp4'
                return f'{percent_processed}% processed. <a href="{link}">Download video</a>'
            else:
                return f'{percent_processed}% processed.'
        else:
            return 'Video ID not found.', 404



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))