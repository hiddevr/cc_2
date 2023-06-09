import base64
import json
import os
from flask import Flask, request
from google.cloud import storage, pubsub_v1, firestore
import cv2
import numpy as np
from PIL import Image
import io


app = Flask(__name__)

PROJECT_ID = 'cc-assigment2-388310'

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()
db = firestore.Client()


@firestore.transactional
def process_frame(transaction, doc_ref, frame_number):
    transaction.update(doc_ref, {
        f'processed.{frame_number}': True
    })

    return


@app.route('/', methods=['GET'])
def health_check():
    return 'OK', 200


@app.route('/', methods=['POST'])
def index():
    # Parse Pub/Sub message
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

    video_id = data['video_id']
    frame_number = data['frame_number']

    # Fetch the watermark.png and specific frame
    watermark_bucket = storage_client.get_bucket('full-vid-storage')
    watermark_blob = watermark_bucket.blob(f'{video_id}/watermark.png')
    watermark = Image.open(io.BytesIO(watermark_blob.download_as_bytes()))

    frame_bucket = storage_client.get_bucket('worker-data-storage')
    frame_blob = frame_bucket.blob(f'{video_id}/frame{frame_number}.png')
    frame = Image.open(io.BytesIO(frame_blob.download_as_bytes()))

    # Check if the frame is already processed
    output_bucket = storage_client.get_bucket('processed-frames')
    output_blob = output_bucket.blob(f'{video_id}/frame{frame_number}.png')

    frame.paste(watermark, (0, 0), watermark)

    # Save image to BytesIO object
    byte_arr = io.BytesIO()
    frame.save(byte_arr, format='PNG')
    byte_arr.seek(0) # reset the pointer to the start of BytesIO object

    # Upload BytesIO object to GCS
    output_blob.upload_from_file(byte_arr, content_type='image/png')

    # Update Firestore
    doc_ref = db.collection('jobs').document(video_id)
    transaction = db.transaction()
    process_frame(transaction, doc_ref, frame_number)

    doc_ref = db.collection('jobs').document(video_id)
    processed_dict = doc_ref.get().to_dict().get('processed')
    completed = doc_ref.get().to_dict().get('completed')
    if all(processed_dict.values()) and not completed:
        finished = True
        doc_ref.update({'completed': True})
    else:
        finished = False

    # If all frames are processed, publish a message to the 'reduce-video' topic
    if finished:
        topic_path = publisher.topic_path(PROJECT_ID, 'reduce-video')
        message = json.dumps({'video_id': video_id}).encode('utf-8')
        publisher.publish(topic_path, data=message)

    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
