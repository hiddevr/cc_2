from flask import Flask, request, render_template
from google.cloud import storage
import cv2
import requests
import numpy as np
import uuid
import os
import tempfile
from google.cloud import firestore

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


@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'GET':
        # Serve the HTML frontend
        return render_template('upload.html')
    elif request.method == 'POST':
        user_id = uuid.uuid4()

        # Process the video file
        video_file = request.files.get('video-file')
        video_url = request.form.get('video-url')
        video_filename = process_file_or_url(video_file, video_url)

        # Process the image file
        image_file = request.files.get('image-file')
        image_url = request.form.get('image-url')
        image_filename = process_file_or_url(image_file, image_url)

        # Open video file with OpenCV
        vidcap = cv2.VideoCapture(video_filename)
        success, image_frame = vidcap.read()
        frames = []
        while success:
            frames.append(image_frame)
            success, image_frame = vidcap.read()
        vidcap.release()

        # Instantiate the storage client
        storage_client = storage.Client()
        db = firestore.Client()

        # Upload watermark image to Google Cloud Storage
        bucket = storage_client.get_bucket('worker-data-store')
        blob = bucket.blob(f'{user_id}/watermark.png')
        with open(image_filename, 'rb') as img_file:
            blob.upload_from_file(img_file)

        # Then upload each frame to Google Cloud Storage
        for i, frame in enumerate(frames):
            _, encoded_image = cv2.imencode('.png', frame)
            blob = bucket.blob(f'{user_id}/frame{i}.png')
            blob.upload_from_string(encoded_image.tostring(), content_type='image/png')

        os.remove(video_filename)
        os.remove(image_filename)

        doc_ref = db.collection(u'jobs').document(user_id)
        doc_ref.set({
            'frames': len(frames),
            'processed': 0,
            'completed': False
        })

        return 'Done'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))