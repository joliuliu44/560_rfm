# Running Form Monitor Project

This project implements an IoT-based system to monitor running form using AWS services. The system utilizes sensor data collected from three Android phones acting as IoT devices. The phones run Termux, use the `termux-sensor` command to gather accelerometer, gyroscope, and vibration data, and send the data to AWS IoT Core via Python scripts. The collected data undergoes preprocessing, anomaly detection, and alert generation using AWS resources.

## Features

- **IoT Integration**: Collects sensor data from multiple devices via AWS IoT Core.  
- **Data Preprocessing**: Formats and stores sensor data in S3 buckets.  
- **Anomaly Detection**: Uses SageMaker's Random Cut Forest (RCF) algorithm.  
- **Notification System**: Sends email alerts to users via Amazon SNS when bad running form is detected.  

## Directory Structure

- final_proj/
- ├── app.py                 # Entry point for AWS CDK application.
- ├── cdk.json               # AWS CDK configuration file.
- ├── final_proj/
- │   ├── final_proj_stack.py  # CDK stack script that spins up AWS resources.
- │
- ├── lambda/
- │   ├── preprocess.py       # Formats IoT sensor data and stores it in S3.
- │   ├── train_model.py      # Configures and trains the SageMaker model.
- │   ├── sagemaker_lambda.py # Creates a SageMaker endpoint.
- │   ├── batch_processor.py  # Processes data through the endpoint and sends alerts.
- |
- ├── send_sensor_data.py   # Python script located on each iot device and should be running when user is engaged in running activity
- │
- └── README.md              # This file.



## AWS Resources

The following AWS resources are deployed via the CDK stack:  
1. **Amazon S3**: Stores formatted sensor data and SageMaker model artifacts.  
2. **AWS IoT Core**: Ingests sensor data from Termux-based devices.  
3. **AWS Lambda**: Processes data, trains models, and triggers notifications.  
4. **Amazon SageMaker**: Hosts an anomaly detection model using the Random Cut Forest (RCF) algorithm.  
5. **Amazon SNS**: Sends email alerts for anomalies in running form.  

## Important Files 
- **final_proj_stack.py**: This is the file that spins up all of the aws resources which involve sns, s3, lambda, iot hub, and sagemaker. 
- **preprocess.py**: The lambda function code  that takes sensor data from the iot hub and formats the sensor data correctly and then sends it to the s3 bucket for data storage.
- **batch_processor.py**: lambda function that will take the sagemaker endpoint and will ingest data and process it through the sagemaker endpoint. Then, this lambda function will send an email notification to the user using aws sns.
- **train_model.py and sagemaker_lambda.py**: The lambda function that will set the parameters for the anomaly detection model and will work in tandem with the sagemaker_lambda.py file to create a sagemaker endpoint which is stored in the s3 bucket.
- **send_sensor_data.py**: This script is the script that is found on each android iot device. This script will run and will send gyroscope and accelerometer sensor data to aws iot core.

## Setup Instructions

### Prerequisites  
1. **AWS Account**: Ensure you have an active AWS account.  
2. **AWS CLI**: Install and configure the [AWS CLI](https://aws.amazon.com/cli/).  
3. **AWS CDK**: Install the AWS Cloud Development Kit using:  
   ```bash
   npm install -g aws-cdk
	 ```
4. **Python Environment**: Set up Python 3.8+ and install dependencies.
5. **Android Devices**: Install Termux and python on the three android devices.

## Termux Setup (On Android Phones)
1. Install required packages:
	```bash
	pkg install python termux-api
	pip install awscli
	```
2. Run the python scripts to collect sensor data which will be sent to aws iot core

## AWS CDK Setup
1. Clone this repository:
	```bash
	git clone <copy and paste this repos url>
	cd final_proj
	```
2. Create a virtual python environment:
	```bash
	python3 -m venv .env
	source .env/bin/activate
	```
3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
4. Bootstrap your aws environment:
	```bash
	cdk bootstrap
	```
5. Deploy the stack:
	```bash
	cdk deploy
	```

## Next Steps:
1. Strap the phones to you chest and legs. (I unfortunately had to use duct tape)
2. Run the python scripts on the termux command line.
3. Monitor your phone for email notifications on your phone
4. Stay healthy, friends!











