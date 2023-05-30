from flask import Flask, request
from google.cloud import storage
from google.cloud import firestore
from google.cloud import pubsub_v1
import cv2
import numpy as np
import os
import tempfile
import json
import base64

frame_splitter = Flask(__name__)


@frame_splitter.route('/', methods=['POST'])
def index():
    # Extract the Pub/Sub message from the request body
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'Error: {msg}')
        return f'Error: {msg}', 400

    if 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'Error: {msg}')
        return f'Error: {msg}', 400

    pubsub_message = envelope['message']

    # Decode the Pub/Sub message
    data = base64.b64decode(pubsub_message.get('data')).decode('utf-8')
    data = json.loads(data)

    # Get video ID
    video_id = data.get('video_id')
    if not video_id:
        msg = 'video_id not provided in the message'
        print(f'Error: {msg}')
        return f'Error: {msg}', 400

    # Instantiate the storage client
    storage_client = storage.Client()

    # Download the video from the bucket
    bucket = storage_client.get_bucket('full-vid-storage')
    blob = bucket.blob(f'{video_id}/video.mp4')
    _, video_path = tempfile.mkstemp()
    blob.download_to_filename(video_path)

    # Open video file with OpenCV
    vidcap = cv2.VideoCapture(video_path)
    success, image_frame = vidcap.read()
    frames = []
    while success:
        frames.append(image_frame)
        success, image_frame = vidcap.read()
    vidcap.release()

    # Create another bucket for storing frames
    bucket = storage_client.get_bucket('worker-data-storage')

    # Then upload each frame to Google Cloud Storage
    for i, frame in enumerate(frames):
        _, encoded_image = cv2.imencode('.png', frame)
        blob = bucket.blob(f'{video_id}/frame{i}.png')
        blob.upload_from_string(encoded_image.tostring(), content_type='image/png')

    # Add a document to Firestore
    db = firestore.Client()
    doc_ref = db.collection(u'jobs').document(video_id)
    doc_ref.set({
        'frames': len(frames),
        'processed': 0,
        'completed': False
    })

    # Publish a message to a topic for each frame
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.getenv('GOOGLE_CLOUD_PROJECT'), 'frame-processing')
    for i in range(len(frames)):
        message = json.dumps({'video_id': video_id, 'frame_number': i}).encode('utf-8')
        publisher.publish(topic_path, data=message)

    # Clean up temporary files
    os.remove(video_path)

    return 'Message processed', 200


if __name__ == "__main__":
    frame_splitter.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
