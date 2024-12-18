import os
import json
import boto3
from datetime import datetime



s3 = boto3.client('s3')
bucket_name = os.environ['INPUT_BUCKET_NAME'] 

def lambda_handler(event, context):
    device = event['device_id']

    if device == 'chestSensor':
        device_id = "chestSensor"
    elif device == 'ankleLeftSensor':
        device_id = "ankleLeftSensor"
    elif device == 'ankleRightSensor':
        device_id = "ankleRightSensor"
    else:
        device_id = "unknown"

    data_type = event['gyro_data']['data_type']
    gyro_data = event['gyro_data']
    accel_data = event['accel_data']
    timestamp = event['timestamp']


    s3_key = f"{data_type}/{device_id}/{timestamp}.json"
    
    data = {
        'device_id': device_id,
        'timestamp': timestamp,
        'gyro_data': gyro_data,
        'accel_data': accel_data
        }
    
    print(data)
    s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType='application/json'
            )

    return {'statusCode': 200, 'body': json.dumps('Data processed and stored in S3')}
