# Tutorial: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal
# Upload logs code: https://learn.microsoft.com/en-us/python/api/overview/azure/monitor-ingestion-readme?view=azure-python
# GitHub: https://github.com/Azure/azure-sdk-for-python/tree/azure-monitor-ingestion_1.0.3/sdk/monitor/azure-monitor-ingestion

import logging
import os
import sys
from datetime import datetime, timezone
import json

import pandas as pd
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus

# Define constants for environment variables
LOGS_WORKSPACE_ID = "7fab0529-6c13-452c-8ec7-5bd11f1e8c15"
DATA_COLLECTION_ENDPOINT = "https://eurofins-poc-luy3.francecentral-1.ingest.monitor.azure.com"
LOGS_DCR_RULE_ID = "dcr-64f6b80f117447aaa1b49dd525c8ac9b"
LOGS_DCR_STREAM_NAME = "Custom-centralizedlogstorage_CL"

# Configure logging
logger = logging.getLogger('azure.monitor.ingestion')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

# Create clients
credential = DefaultAzureCredential()
logs_client = LogsQueryClient(credential)
ingestion_client = LogsIngestionClient(endpoint=DATA_COLLECTION_ENDPOINT, credential=credential, logging_enable=True)

# Define query and time span
query = """AADNonInteractiveUserSignInLogs | take 100 | project Category, AppDisplayName """
start_time = datetime(2024, 1, 11, tzinfo=timezone.utc)
end_time = datetime(2024, 1, 15, tzinfo=timezone.utc)

try:
    # Query Log Analytics Workspace
    response = logs_client.query_workspace(
        LOGS_WORKSPACE_ID,
        query=query,
        timespan=(start_time, end_time)
    )
    if response.status == LogsQueryStatus.PARTIAL:
        error = response.partial_error
        data = response.partial_data
        print(error)
    elif response.status == LogsQueryStatus.SUCCESS:
        data = response.tables

    # Convert data to JSON list
    json_list = []
    for table in data:
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        # Use f-string for string formatting
        print(f"Dataframe:\n{df}\n")
        # Use list comprehension for creating list
        json_list.extend([json.loads(row) for row in df.to_json(orient="records", lines=True).splitlines()])
        # Use f-string for string formatting
        print(f"JSON list:\n{json_list}\n")

    # Upload logs
    ingestion_client.upload(rule_id=LOGS_DCR_RULE_ID, stream_name=LOGS_DCR_STREAM_NAME, logs=json_list)
    print("Upload done")
except HttpResponseError as e:
    # Use f-string for string formatting
    print(f"Upload failed: {e}")
