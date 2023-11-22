import serial, os, json
import paho.mqtt.client as mqtt
from datetime import datetime

import time

# Get the current epoch time in seconds
current_epoch_time = int(time.time())

# Convert epoch time to a datetime object
datetime_object = datetime.utcfromtimestamp(current_epoch_time)

# Format the datetime object as a string in the desired format
formatted_time = datetime_object.strftime("%d/%m/%Y %H:%M:%S")

print("Started at: ", formatted_time)

def is_jetson_nano():
    return os.path.isfile('/etc/nv_tegra_release')


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print(f"Connection to MQTT Broker failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} Published")

# MQTT configuration & serial port configuration 
if is_jetson_nano():
    mqtt_broker = "10.0.128.128"
    serial_port = "/dev/ttyTHS1" # JETSON NANO 
    SENSORS_TOPIC = "/ufficio28/acquario/sensors/"
else:
    mqtt_broker = "127.0.0.1"
    serial_port = "/dev/ttyS0" # RASPBERRY
    SENSORS_TOPIC = "homeassistant/sensors"

baud_rate = 115200

# Create MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish
# Connect to MQTT Broker
mqtt_client.connect(mqtt_broker, 1883, 60)
mqtt_client.loop_start()

mqtt_client.publish("LOG", "Connected" )
# Open serial port
ser = serial.Serial(serial_port, baud_rate)


while True:
    try:
        # Read JSON data from serial port
        serial_data = ser.readline().decode('utf-8').strip()
        clean_data = serial_data.replace('\r', '').replace('\n', '').replace("Received ","")
        print( "Clean data" , clean_data )

        # Parse JSON data
        json_data = json.loads( clean_data )
        command = ""

        current_epoch_time = int(time.time())
        print("Current Epoch Time (in seconds):", current_epoch_time)

        id = json_data["id"];
        if "type" in json_data:
           type = json_data["type"]
           if type == "agri":
              temp = json_data["temp"]
              soil = json_data["soil"]
              lum  = json_data["lum"]
              batt_volt = json_data["bv"]
              batt_lvl = json_data["bl"]
              charge = json_data["charge"]
              hum = json_data["hum"]
              usb = str( json_data["usb"] ).lower()

              if is_jetson_nano():
                  USE_TOPIC = SENSORS_TOPIC
              else:
                  USE_TOPIC = SENSORS_TOPIC + "/" + id

              topic =  USE_TOPIC + "/is_battery_charging"
              command = f"{{\"value\":{usb},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/luminosity"
              command = f"{{\"value\":{lum},\"type\":\"luminosity\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + id + "/temperature"
              command = f"{{\"value\":{temp},\"type\":\"temperature\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + id + "/soil_moisture"
              command = f"{{\"value\":{soil},\"type\":\"soil\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + id + "/battery_level"
              command = f"{{\"value\":{batt_lvl},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + id + "/humidity"
              command = f"{{\"value\":{hum},\"type\":\"humidity\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

           else: #HOME ASSISTANT ONLY
              command =  json_data["command"]

              #"{\"id\":\"bagno\",\"command\":\"toggle\"}"
              topic =  "homeassistant/light/" + id + "/set"
              mqtt_client.publish(topic, command )
              print("Data published to MQTT:", json_data)


    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            print(f"Error : {e}")
        else:
            break


print("Exiting program.")
ser.close()
mqtt_client.disconnect()
mqtt_client.loop_stop()

