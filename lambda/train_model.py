import os
import json
import boto3
from collections import defaultdict
from math import sqrt

s3 = boto3.client('s3')

def calculate_stats(values):
    if not values:
        return {"mean": 0, "lower_bound": 0, "upper_bound": 0}

    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    stddev = sqrt(variance)
    lower_bound = mean - 3 * stddev
    upper_bound = mean + 3 * stddev

    return {"mean": mean, "lower_bound": lower_bound, "upper_bound": upper_bound}

def train_handler(event, context):
    print("pre-try\n\n\n\n\n")
    try:
        print("*****Beginning*****\n\n\n")
        prefix = "train/"
        bucket_name = os.environ['INPUT_BUCKET_NAME']
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' not in response:
            print("No files found in the specified prefix.")
            return

        print("***** response variable successful *****\n\n\n\n")
        
        # Data storage for each directory
        directories = ["chestSensor", "ankleLeftSensor", "ankleRightSensor"]
        stats = {directory: {"gyro": {"x": [], "y": [], "z": []}, 
                             "accel": {"x": [], "y": [], "z": []}} for directory in directories}

        #print(response)
        
        # Process each file in the subdirectories
        for obj in response['Contents']:
            key = obj['Key']

            print(f"KEY: {key}")
            
            # Skip files not in subdirectories or not JSON
            if not any(f"{prefix}{dir_name}/" in key for dir_name in directories) or not key.endswith(".json"):
                print("had to skip a file") 
                continue
            
            # Determine directory
            directory = next((dir_name for dir_name in directories if f"{prefix}{dir_name}/" in key), None)
            if not directory:
                continue

            print(directory)
            
            # Get file content
            file_obj = s3.get_object(Bucket=bucket_name, Key=key)
            file_content = file_obj['Body'].read().decode('utf-8')
            data = json.loads(file_content)
            
            # Process gyro and accel data
            gyro_data = data.get("gyro_data", {})
            accel_data = data.get("accel_data", {})
            
            if gyro_data:
                stats[directory]["gyro"]["x"].append(gyro_data.get("x", 0))
                stats[directory]["gyro"]["y"].append(gyro_data.get("y", 0))
                stats[directory]["gyro"]["z"].append(gyro_data.get("z", 0))
            
            if accel_data:
                stats[directory]["accel"]["x"].append(accel_data.get("x", 0))
                stats[directory]["accel"]["y"].append(accel_data.get("y", 0))
                stats[directory]["accel"]["z"].append(accel_data.get("z", 0))
        
        # Calculate statistics
        results = {}
        for directory, sensors in stats.items():
            results[directory] = {
                "gyro": {
                    axis: calculate_stats(values) for axis, values in sensors["gyro"].items()
                },
                "accel": {
                    axis: calculate_stats(values) for axis, values in sensors["accel"].items()
                }
            }
        
        # Write results to a JSON file in S3
        output_key = f"{prefix}summary.json"
        output_body = json.dumps(results, indent=2)
        s3.put_object(Bucket=bucket_name, Key=output_key, Body=output_body)
        
        print(f"Statistics written to {output_key}")
        return results

    except Exception as e:
        print(f"Error processing files: {e}")
        raise
