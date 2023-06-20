import google.cloud.monitoring_v3.query
import requests
import time
import datetime
import re
from google.cloud import monitoring_v3
from google.auth import load_credentials_from_file
import json
import os


#Information
base_url = 'https://serve-frontend-cz4emo5pia-ew.a.run.app/'
project_id = "cc-assigment2-388310"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\stane\\Downloads\\Master\\Cloud Computing\\Assignment 2\\cc_2\\keys\\cc-assigment2-388310-222a6c410a30.json'


#Fill in
video_url = 'https://storage.googleapis.com/cc-test-data/small.mp4'
image_url = 'https://storage.googleapis.com/cc-test-data/watermark.png'
worker_type = 'cloud_run'

for i in range(2):
    start_time = datetime.datetime.now()

    # Use web app
    response = requests.post(f'{base_url}',
                             data={'video-url': video_url, 'image-url': image_url, 'worker-type': worker_type})
    response.raise_for_status()

    pattern = r":\s*([^:\s]+)"
    match = re.search(pattern, response.text)
    video_id = match.group(1)

    progress_url = f'{base_url}progress'

    # Metrics for cloud_run
    credentials, project_id = load_credentials_from_file(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    # Wait for video to get rendered
    time.sleep(20)

    while True:
        # Send request to check progress
        response = requests.post(
            progress_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'video-id': video_id})  # sending the video id as json in body
        )

        pattern = r"(\d+\.\d+)%"
        match = re.search(pattern, response.text)
        percentage = float(match.group(1))
        percentage = round(percentage, 2)  # Round to two decimal places
        print(percentage,"%")

        time.sleep(1)

        if percentage == 100.0:
            print("Video number:", i+1)
            interval = monitoring_v3.TimeInterval()

            end_time = datetime.datetime.now()
            duration = end_time - start_time
            minutes = duration.total_seconds() / 60

            cpu_results = google.cloud.monitoring_v3.query.Query(
                client=client,
                project=project_id,
                metric_type='run.googleapis.com/container/cpu/utilizations',
                end_time=end_time,
                minutes=minutes
            )

            # cpu_results = cpu_results.select_metrics(revision_name="watermarker-worker-00057-bes")

            # Print the metrics
            print(cpu_results)

            break


