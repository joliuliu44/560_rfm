import json
import boto3
import os
import urllib.parse
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
sns = boto3.client('sns')

def lambda_handler(event, context):
    input_bucket_name = os.environ['INPUT_BUCKET_NAME']
    stats_file_path = os.environ['STATS_FILE_PATH']
    anomaly_counts_path = os.environ['ANOMALY_COUNTS_PATH']
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    try:
        # Load pre-calculated stats from S3
        anomaly_object = s3.get_object(Bucket=input_bucket_name, Key=anomaly_counts_path)
        stats_object = s3.get_object(Bucket=input_bucket_name, Key=stats_file_path)

        stats_data = json.loads(stats_object['Body'].read())
        anomaly_counts = json.loads(anomaly_object['Body'].read())

        # Extract bounds and create variables
        variables = {}
        
        for sensor, types in stats_data.items():
            for data_type, axes in types.items():
                for axis, stats in axes.items():
                    lower_var_name = f"{sensor}_{data_type}_{axis}_lower"
                    upper_var_name = f"{sensor}_{data_type}_{axis}_upper"
                    variables[lower_var_name] = stats["lower_bound"]
                    variables[upper_var_name] = stats["upper_bound"]
        

    except ClientError as e:
        print(f"Error loading stats file: {e}") 
        return {
            'statusCode': 500,
            'body': json.dumps('Error loading stats file.')
        }


    for record in event['Records']:
        try:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']

            object_key = urllib.parse.unquote(object_key)

            # Get the new data file from S3
            response = s3.get_object(Bucket=bucket_name, Key=object_key)
            sensor_data = json.loads(response['Body'].read())
            
            device_id = sensor_data['device_id']
            gyro_data = sensor_data['gyro_data']
            accel_data = sensor_data['accel_data']

            
            for axis in ["x", "y", "z"]:
                if gyro_data[axis] > variables[f"{device_id}_gyro_{axis}_upper"] or gyro_data[axis] < variables[f"{device_id}_gyro_{axis}_lower"]:
                    anomaly_counts[device_id]["gyro_count"] += 1
                    anomaly_counts[device_id]["clean_streak"] = 0
                else:
                    anomaly_counts[device_id]["clean_streak"] += 1

            for axis in ["x", "y", "z"]:
                if accel_data[axis] > variables[f"{device_id}_accel_{axis}_upper"] or accel_data[axis] < variables[f"{device_id}_accel_{axis}_lower"]:
                    anomaly_counts[device_id]["accel_count"] += 1
                    anomaly_counts[device_id]["clean_streak"] = 0
                else:
                    anomaly_counts[device_id]["clean_streak"] += 1

           
            sns_response = None
            for sensor, counts in anomaly_counts.items():
                if counts["clean_streak"] > 36 and (counts["gyro_count"] > 5 or counts["accel_count"] > 5):
                    counts["gyro_count"] = 0
                    counts["accel_count"] = 0

                if (counts["gyro_count"] > 5 or counts["accel_count"] > 5) and (counts["clean_streak"] <= 36):
                    anomalous_sensor = ["gyro" if counts["gyro_count"] > 5 else "accel"]

                    if sensor == "chestSensor":
                        if anomalous_sensor[0] == "gyro":
                            message = "You are bouncing too much. Try reducing your impact to the ground."   
                        elif anomalous_sensor[0] == "accel":
                            message = "You are leaning forward too much. We recommend you straighten your torso."
                        print(message)
                    elif sensor == "ankleLeftSensor":
                        message = "Your left leg stride is not optimal. Keep your left stride on the same plane throughout its motion."
                        print(message)
                    elif sensor == "ankleRightSensor":
                        message = "Your right leg stride is not optimal. Keep your right stride on the same plane throughout its motion."
                        print(message)

                    try:    
                        sns_response = sns.publish(
                                TopicArn=sns_topic_arn,
                                Message=message,
                                Subject="Lambda Notification"
                                )
                        print(f"Text message sent successfully")
                    
                    except ClientError as e:
                        print(f"Failed to send text message: {e}")

                    counts["clean_streak"] = 0
                    counts["gyro_count"] = 0
                    counts["accel_count"] = 0

            # update the json file in the s3 bucket
            s3.put_object(Bucket=bucket_name, Key=anomaly_counts_path, Body=json.dumps(anomaly_counts))


        except Exception as e:
            print(f"Error processing file {record['s3']['object']['key']}: {e}")


    if sns_response:
        return {
            "statusCode": 200,
            "body": f"Message sent! Response: {sns_response}"
            }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Batch processed successfully.')
            }



