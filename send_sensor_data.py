import sys
import subprocess
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Constants
GYRO_SENSOR = "bmi160 Gyroscope Non-wakeup"
ACCEL_SENSOR = "bmi160 Accelerometer Non-wakeup"
DATA_TYPE = input("Type 'train' or 'demo' to specify this data: ")
ENDPOINT = "<aws endpoint>"
TOPIC = "form_monitor/sensor_data/chestSensor"

# MQTT Setup
client = mqtt.Client()
client.tls_set(
        ca_certs="<cert files path>",
        certfile="<cert files path>", 
        keyfile="<cert files path>")

client.enable_logger()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
        client.subscribe(TOPIC)
    else:
        print(f"Connection failed with code {rc}")

client.on_connect = on_connect
client.connect(ENDPOINT, 8883)
client.loop_start()

def get_sensor_data(sensor_name):
    try:
        result = subprocess.run(['termux-sensor', '-s', sensor_name, '-n', '1'], stdout=subprocess.PIPE, check=True)
        sensor_output = json.loads(result.stdout.decode('utf-8'))
        values = sensor_output[sensor_name]['values']
        return {"x": values[0], "y": values[1], "z": values[2]}
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        print(f"Error reading {sensor_name}: {e}")
        return {"x": None, "y": None, "z": None}

print("Start collecting sensor data...")


while True:
    gyro_data = get_sensor_data(GYRO_SENSOR)
    accel_data = get_sensor_data(ACCEL_SENSOR)
    sensor_data = {
        "device_id": "chestSensor",
        "timestamp": datetime.now().isoformat(),
        "gyro_data": {"data_type": DATA_TYPE, **gyro_data},
        "accel_data": {"data_type": DATA_TYPE, **accel_data}
    }
    client.publish(TOPIC, json.dumps(sensor_data))
    
