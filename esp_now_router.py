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

def find_object_by_id(json_array, target_id):
    for obj in json_array:
        if obj.get("id") == target_id:
            return obj
    return None    

# MQTT configuration & serial port configuration from settings

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the settings file
settings_file_path = os.path.join(script_directory, 'settings.json')
devices_file_path = os.path.join(script_directory, 'devices.json')

print("Reading settings from ", settings_file_path )

with open(settings_file_path, 'r') as file:
    settings = json.load(file)


mqtt_broker = settings["mqtt_broker"]
serial_port= settings["serial_port"]
baud_rate = settings["baud_rate"]
sensor_topic = settings["topic"]
url = settings["url"]

with open(devices_file_path, 'r') as file:
    devices = json.load(file)



# Create MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
#mqtt_client.on_publish = on_publish

# Connect to MQTT Broker
mqtt_client.connect(mqtt_broker, 1883, 60)
mqtt_client.loop_start()

# Open serial port
ser = serial.Serial(serial_port, baud_rate)

#device = find_object_by_id( devices, "3398534" )
#print( devices )
#print( device )
#exit()

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

        id = json_data["id"]
        interval = -1

        device = find_object_by_id( devices, id )
        if device != None:
            id = device.topic
            interval = device.interval

        if interval > 0:
            ser.writelines( f"{{\"id\":\"{id}\",\"interval\":{interval}}}\n".encode() )
            ser.flush()

        type="NONE"

        if "type" in json_data:
           type = json_data["type"]

        if type == "agri":

              topic_id = sensor_topic + "/" + id

              if  "delta" in json_data:
                 delta = json_data["delta"]
                 topic =  topic_id + "/delta"
                 command = f"{{\"value\":{delta},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "hum" in json_data:
                 hum = json_data["hum"]
                 topic =  topic_id + "/humidity"
                 command = f"{{\"value\":{hum},\"type\":\"humidity\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "usb" in json_data:
                 usb = str( json_data["usb"] ).lower()
                 topic =  topic_id + "/is_battery_charging"
                 command = f"{{\"value\":{usb},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "lum" in json_data:
                 lum  = json_data["lum"]
                 topic =  topic_id + "/luminosity"
                 command = f"{{\"value\":{lum},\"type\":\"luminosity\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "temp" in json_data:
                 temp  = json_data["temp"]
                 topic =  topic_id + "/temperature"
                 command = f"{{\"value\":{temp},\"type\":\"temperature\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "soil" in json_data:
                 soil  = json_data["soil"]
                 topic =  topic_id + "/soil_moisture"
                 command = f"{{\"value\":{soil},\"type\":\"soil\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "bl" in json_data:
                 batt_lvl  = json_data["bl"]
                 topic =  topic_id + "/battery_level"
                 command = f"{{\"value\":{batt_lvl},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "bv" in json_data:
                 batt_volt = json_data["bv"]
                 topic =  topic_id + "/battery_voltage"
                 command = f"{{\"value\":{batt_volt},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
                 mqtt_client.publish(topic, command )

              if "charge" in json_data:
                 charge = str( json_data["charge"] ).lower()
                 topic =  topic_id + "/is_charging"
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

