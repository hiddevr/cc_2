import os
from flask import Flask, request
from google.cloud import storage, pubsub_v1, firestore
import cv2
import numpy as np
from PIL import Image

app = Flask(__name__)

PROJECT_ID = 'cc-assigment2-388310'

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()
db = firestore.Client()


def process_frame(data):
    video_id = data['video_id']
    frame_number = data['frame_number']

    # Fetch the watermark.png and specific frame
    watermark_bucket = storage_client.get_bucket('full-vid-storage')
    watermark_blob = watermark_bucket.blob(f'{video_id}/watermark.png')
    watermark = Image.open(watermark_blob.download_as_bytes())

    frame_bucket = storage_client.get_bucket('worker-data-storage')
    frame_blob = frame_bucket.blob(f'{video_id}/frame{frame_number}.png')
    frame = Image.open(frame_blob.download_as_bytes())

    # Check if the frame is already processed
    processed_frames_bucket = storage_client.get_bucket('processed-frames')
    if not processed_frames_bucket.blob(f'{video_id}/frame{frame_number}.png').exists():
        # Add the watermark to the video frame
        frame.paste(watermark, (0, 0), watermark)

        # Upload it to the processed-frames bucket
        output_blob = processed_frames_bucket.blob(f'{video_id}/frame{frame_number}.png')
        frame.save(output_blob, 'PNG')

        # Update the 'processed' value in Firestore jobs collection
        doc_ref = db.collection('jobs').document(video_id)
        job = doc_ref.get().to_dict()
        job['processed'] += 1
        doc_ref.set(job)

        # If all frames are processed, publish a message to the 'reduce-video' topic
        if job['processed'] == job['frames']:
            topic_path = publisher.topic_path(PROJECT_ID, 'reduce-video')
            publisher.publish(topic_path, video_id.encode('utf-8'))


@app.route('/', methods=['POST'])
def index():
    # Parse Pub/Sub message
    message = request.get_json(force=True)
    data = message['message']['attributes']

    process_frame(data)

    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
