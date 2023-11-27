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
#mqtt_broker = "192.168.0.227"
#serial_port="/dev/ttyUSB0"
#SENSORS_TOPIC = "casaortu/sensors"
#url = "https://www.giovanniortu.it/tools/datalogger.php"
mqtt_broker = "10.0.128.128"
serial_port="/dev/ttyS0"
SENSORS_TOPIC = "/ufficio28/acquario/sensors"
url = ""


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

              USE_TOPIC = SENSORS_TOPIC + "/" + id

              if  "delta" in json_data:
                 delta = json_data["delta"]
                 topic =  USE_TOPIC + "/delta"
                 command = f"{{\"value\":{delta},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "hum" in json_data:
                 hum = json_data["hum"]
                 topic =  USE_TOPIC + "/humidity"
                 command = f"{{\"value\":{hum},\"type\":\"humidity\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "usb" in json_data:
                 usb = str( json_data["usb"] ).lower()
                 topic =  USE_TOPIC + "/is_battery_charging"
                 command = f"{{\"value\":{usb},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "lum" in json_data:
                 lum  = json_data["lum"]
                 topic =  USE_TOPIC + "/luminosity"
                 command = f"{{\"value\":{lum},\"type\":\"luminosity\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "temp" in json_data:
                 temp  = json_data["temp"]
                 topic =  USE_TOPIC + "/temperature"
                 command = f"{{\"value\":{temp},\"type\":\"temperature\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "soil" in json_data:
                 soil  = json_data["soil"]
                 topic =  USE_TOPIC + "/soil_moisture"
                 command = f"{{\"value\":{soil},\"type\":\"soil\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "bl" in json_data:
                 batt_lvl  = json_data["bl"]
                 topic =  USE_TOPIC + "/battery_level"
                 command = f"{{\"value\":{batt_lvl},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "bv" in json_data:
                 batt_volt = json_data["bv"]
                 topic =  USE_TOPIC + "/battery_voltage"
                 command = f"{{\"value\":{batt_volt},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "charge" in json_data:
                 charge = str( json_data["charge"] ).lower()
                 topic =  USE_TOPIC + "/is_charging"
                 command = f"{{\"value\":{charge},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )


              if url != "":
                  response = requests.post(url, json=json_data, headers=headers )
                  print(response.text)


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

