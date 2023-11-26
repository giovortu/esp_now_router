import serial, os, json
import paho.mqtt.client as mqtt
from datetime import datetime
import requests
import time

# Get the current epoch time in seconds
current_epoch_time = int(time.time())

# Convert epoch time to a datetime object
datetime_object = datetime.utcfromtimestamp(current_epoch_time)

# Format the datetime object as a string in the desired format
formatted_time = datetime_object.strftime("%d/%m/%Y %H:%M:%S")

print("Started at: ", formatted_time)

url = "https://www.giovanniortu.it/tools/datalogger.php"
headers = {"Content-Type": "application/json"}


def is_jetson_nano():
    return True #os.path.isfile('/etc/nv_tegra_release')


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print(f"Connection to MQTT Broker failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} Published")

# MQTT configuration & serial port configuration 
mqtt_broker = "192.168.0.227"
serial_port="/dev/ttyUSB0"
SENSORS_TOPIC = "casaortu/sensors"

baud_rate = 115200

# Create MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
#mqtt_client.on_publish = on_publish
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
        type="NONE"
        if "type" in json_data:
           type = json_data["type"]
        if type == "agri":
              temp = json_data["temp"]
              soil = json_data["soil"]
              lum  = json_data["lum"]
              batt_volt = json_data["bv"]
              batt_lvl = json_data["bl"]
              charge = json_data["charge"]
              delta = json_data["delta"]
              usb = str( json_data["usb"] ).lower()

              if url != "":
                  response = requests.post(url, json=json_data, headers=headers )
                  print(response.text)

              USE_TOPIC = SENSORS_TOPIC + "/" + id

              topic =  USE_TOPIC + "/delta"
              command = f"{{\"value\":{delta},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )


              topic =  USE_TOPIC + "/is_battery_charging"
              command = f"{{\"value\":{usb},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/luminosity"
              command = f"{{\"value\":{lum},\"type\":\"luminosity\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/temperature"
              command = f"{{\"value\":{temp},\"type\":\"temperature\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/soil_moisture"
              command = f"{{\"value\":{soil},\"type\":\"soil\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/battery_level"
              command = f"{{\"value\":{batt_lvl},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/humidity"
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

