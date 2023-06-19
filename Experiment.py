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
    instance_id = f"'cloud_run_revision/{metric_type}'"

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
            'filter': f"metric.type = cloud_run_revision/cpu/utilization AND metric.labels.service_name = '{service_name}'", ##Stan: Hier zit het probleem
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