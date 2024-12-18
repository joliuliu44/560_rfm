import boto3
import os

def lambda_handler(event, context):
    sagemaker_client = boto3.client('sagemaker')

    input_data_uri = f"s3://{os.environ['INPUT_BUCKET_NAME']}/input-data"
    output_data_uri = f"s3://{os.environ['OUTPUT_BUCKET_NAME']}/output-data"

    response = sagemaker_client.create_processing_job(
        ProcessingJobName="FormMonitorProcessingJob",
        ProcessingResources={
            "ClusterConfig": {
                "InstanceCount": 1,
                "InstanceType": "ml.t3.medium",  
                "VolumeSizeInGB": 10,           
            }
        },
        AppSpecification={
            "ImageUri": "156387875391.dkr.ecr.us-west-2.amazonaws.com/my-processing-image:latest"  
        },
        ProcessingInputs=[
            {
                "InputName": "input-data",
                "S3Input": {
                    "S3Uri": input_data_uri,
                    "LocalPath": "/opt/ml/processing/input",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File",
                },
            },
        ],
        ProcessingOutputConfig={
            "Outputs": [
                {
                    "OutputName": "output-data",
                    "S3Output": {
                        "S3Uri": output_data_uri,
                        "LocalPath": "/opt/ml/processing/output",
                        "S3UploadMode": "EndOfJob",
                    }
                },
            ]
        },
        RoleArn=os.environ["<sagemaker role arn>"]
    )

    return {
        "status": "Processing job started",
        "job_name": response["ProcessingJobName"]
    }
