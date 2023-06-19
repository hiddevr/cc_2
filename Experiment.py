import os
import time
from google.cloud import monitoring_v3
from google.protobuf.timestamp_pb2 import Timestamp
from google.auth import load_credentials_from_file

PROJECT_ID = 'cc-assigment2-388310'
service_name = 'watermark-worker'
metrics_to_monitor = ['cpu/utilization', 'memory/utilization', '/instance_count']
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\stane\\Downloads\\Master\\Cloud Computing\\Assignment 2\\cc_2\\keys\\cc-assigment2-388310-5ed5f427886b.json'


def get_metric(metric_type, worker_type):
    credentials, project_id = load_credentials_from_file(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    client = monitoring_v3.MetricServiceClient()

    # Define the project and instance_id
    project_name = f"projects/{PROJECT_ID}"
    instance_id = f"'run.googleapis.com/instance/{metric_type}'"

    # Define the interval for metrics
    interval = monitoring_v3.TimeInterval()
    now = time.time()
    end_time = Timestamp()
    end_time.FromJsonString(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)))
    start_time = Timestamp()
    start_time.FromJsonString(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now - 3600)))
    interval.end_time = end_time
    interval.start_time = start_time

    results = client.list_time_series(
        request={
            "name": project_name,
            'filter': f"metric.type = {instance_id} AND metric.labels.service_name = '{service_name}'",
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    for result in results:
        print(f"Retrieved metric {metric_type} for {worker_type}:")
        for point in result.points:
            print(f"\t{point.value.double_value}")


def run_experiment():
    worker_types = ['cloud_run', 'kub']
    for worker_type in worker_types:
        for metric in metrics_to_monitor:
            get_metric(metric, worker_type)


if __name__ == "__main__":
    run_experiment()


















# import request
# import time
# import os
# from google.cloud import monitoring_v3
# from google.auth import load_credentials_from_file
# import json
#
# # Your project variables
# PROJECT_ID = 'cc-assigment2-388310'
# base_url = 'https://serve-frontend-cz4emo5pia-ew.a.run.app/'
# video_url = 'https://storage.googleapis.com/cc-test-data/small.mp4'
# image_url = 'https://storage.googleapis.com/cc-test-data/watermark.png'
# worker_types = ['cloud_run', 'kub']
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\stane\\Downloads\\Master\\Cloud Computing\\Assignment 2\\cc_2\\keys\\cc-assigment2-388310-5ed5f427886b.json'
#
# # Google Cloud Monitoring Client
# credentials, project_id = load_credentials_from_file(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
# client = monitoring_v3.MetricServiceClient()
#
# def get_utilization(worker_type):
#     interval = monitoring_v3.TimeInterval(
#         {
#             "end_time": {"seconds": int(time.time())},
#             "start_time": {"seconds": int(time.time() - 600)},
#         }
#     )
#
#     metrics = []
#     for metric_type in ["compute.googleapis.com/instance/cpu/utilization", "compute.googleapis.com/instance/memory/utilization", "compute.googleapis.com/instance/container/count"]:
#         results = client.list_time_series(
#             name=f"projects/{PROJECT_ID}",
#             filter="""
#             metric.type = "run.googleapis.com/request_count" AND
#             resource.type = "cloud_run_revision" AND
#             resource.labels.service_name = "YOUR_SERVICE_NAME"
#             """,
#             interval=interval,
#             view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
#         )
#         metrics.append(results)
#
#     return metrics
#
# def start_experiment(worker_type):
#     data = {
#         'video_url': video_url,
#         'image_url': image_url,
#         'worker_type': worker_type,
#     }
#
#     res = requests.post(f"{base_url}/startJob", json=data)
#     if res.status_code == 200:
#         return res.json()['id']
#     else:
#         time.sleep(20)
#         return None
#
# def get_status(job_id):
#     res = requests.get(f"{base_url}/status/{job_id}")
#     if res.status_code == 200:
#         return res.json()['status']
#     else:
#         return None
#
# def run_experiment(worker_type):
#     print(f"Starting experiment for worker type: {worker_type}")
#     job_id = start_experiment(worker_type)
#     if job_id is not None:
#         print(f"Job {job_id} started")
#         while True:
#             status = get_status(job_id)
#             if status == 'completed':
#                 print(f"Job {job_id} completed")
#                 break
#             print(f"Job {job_id} status: {status}")
#             time.sleep(5)  # sleep for 5 seconds before checking again
#     else:
#         print(f"Could not start job for worker type: {worker_type}")
#
#     utilization = get_utilization(worker_type)
#     print(f"Resource utilization for worker type {worker_type}: {json.dumps(utilization, indent=2)}")
#
#
# def main():
#     for worker_type in worker_types:
#         run_experiment(worker_type)
#
#
# if __name__ == "__main__":
#     main()






























# import requests
# import time
# import re
# from google.cloud import monitoring_v3
# from google.auth import load_credentials_from_file
# from google.protobuf.timestamp_pb2 import Timestamp
# import json
# import os
#
#
# #Information
# base_url = 'https://serve-frontend-cz4emo5pia-ew.a.run.app/'
# project_id = "cc-assigment2-388310"
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\stane\\Downloads\\Master\\Cloud Computing\\Assignment 2\\cc_2\\keys\\cc-assigment2-388310-5ed5f427886b.json'
#
#
# #Fill in
# video_url = 'https://storage.googleapis.com/cc-test-data/small.mp4'
# image_url = 'https://storage.googleapis.com/cc-test-data/watermark.png'
# worker_type = 'cloud_run'
#
# ## Use web app
# response = requests.post(f'{base_url}', data={'video-url': video_url, 'image-url': image_url, 'worker-type': worker_type})
# response.raise_for_status()
#
# pattern = r":\s*([^:\s]+)"
# match = re.search(pattern, response.text)
# video_id = match.group(1)
#
# progress_url = f'{base_url}progress'
#
# #Metrics for cloud_run
# credentials, project_id = load_credentials_from_file(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
# client = monitoring_v3.MetricServiceClient()
# project_name = f"projects/{project_id}"
#
# # Filter for CPU Utilization, Memory Utilization and Container count metrics
# cpu_filter = 'metric.type="run.googleapis.com/container/cpu/utilizations"'
# memory_filter = 'metric.type="run.googleapis.com/container/memory/utilizations"'
# container_count_filter = 'metric.type="run.googleapis.com/container/instance_count"'
#
# time.sleep(20)
#
# while True:
#     # Send request to check progress
#     response = requests.post(
#         progress_url,
#         headers={'Content-Type': 'application/json'},
#         data=json.dumps({'video-id': video_id})  # sending the video id as json in body
#     )
#
#     pattern = r"(\d+\.\d+)%"
#     match = re.search(pattern, response.text)
#     percentage = float(match.group(1))
#     percentage = round(percentage, 2)  # Round to two decimal places
#     print(percentage,"%")
#
#     # Define the interval for metrics
#     interval = monitoring_v3.TimeInterval()
#     now = time.time()
#     end_time = Timestamp()
#     end_time.FromJsonString(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)))
#     start_time = Timestamp()
#     start_time.FromJsonString(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now - 3600)))
#     interval.end_time = end_time
#     interval.start_time = start_time
#
#     # Request the CPU metrics
#     cpu_results = client.list_time_series(
#         request={
#             "name": project_name,
#             "filter": cpu_filter,
#             "interval": interval,
#             "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
#         }
#     )
#
#     # Request the Memory metrics
#     memory_results = client.list_time_series(
#         request={
#             "name": project_name,
#             "filter": memory_filter,
#             "interval": interval,
#             "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
#         }
#     )
#
#     # Request the Container Count metrics
#     container_count_results = client.list_time_series(
#         request={
#             "name": project_name,
#             "filter": container_count_filter,
#             "interval": interval,
#             "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
#         }
#     )
#
#     # Print the metrics
#     for result in cpu_results:
#         print("CPU Utilization:", result.points[0].value.double_value)
#
#     for result in memory_results:
#         print("Memory Utilization:", result.points[0].value.double_value)
#
#     for result in container_count_results:
#         print("Instances Count:", result.points[0].value.double_value)
#
#     time.sleep(1)
#
#     if percentage == 100.0:
#         break
