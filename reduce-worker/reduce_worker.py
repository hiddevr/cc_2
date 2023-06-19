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

storage_client = storage.Client()


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

    bucket = storage_client.get_bucket('processed-frames')

    # Create a temporary list to hold the image data
    images = []

    # Get the FPS from Firestore
    db = firestore.Client()
    doc_ref = db.collection('jobs').document(video_id)
    fps = doc_ref.get().to_dict().get('fps')

    # Retrieve the frames from storage
    blobs = list(bucket.list_blobs(prefix=f'{video_id}/'))
    blobs.sort(
        key=lambda blob: int(blob.name.split('frame')[-1].split('.png')[0]))  # Sort the blobs based on the frame number

    for blob in blobs:
        frame = Image.open(io.BytesIO(blob.download_as_bytes()))
        images.append(np.array(frame))

    # Convert the frames back into a video
    height, width, layers = images[0].shape
    size = (width, height)

    video_name = f'{video_id}.mp4'
    video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

    for i in range(len(images)):
        video.write(cv2.cvtColor(images[i], cv2.COLOR_RGB2BGR))  # OpenCV uses BGR

    video.release()

    # Upload the video to the completed-videos bucket
    output_bucket = storage_client.get_bucket('completed-videos')
    output_blob = output_bucket.blob(video_name)

    with open(video_name, 'rb') as video_file:
        output_blob.upload_from_file(video_file)

    # Remove the local video file
    os.remove(video_name)

    doc_ref = db.collection('jobs').document(video_id)
    doc_ref.update({'watermarked': True})

    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
