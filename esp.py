import serial, os, json
import paho.mqtt.client as mqtt
from datetime import datetime
import struct
import time
import base64


# Get the current epoch time in seconds
current_epoch_time = int(time.time())

# Convert epoch time to a datetime object
datetime_object = datetime.utcfromtimestamp(current_epoch_time)

# Format the datetime object as a string in the desired format
formatted_time = datetime_object.strftime("%d/%m/%Y %H:%M:%S")

print("Started at: ", formatted_time)

def is_jetson_nano():
    return True #os.path.isfile('/etc/nv_tegra_release')


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print(f"Connection to MQTT Broker failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {userdata} Published")

# MQTT configuration & serial port configuration 
mqtt_broker = "10.0.128.128"
serial_port="/dev/ttyS0"
SENSORS_TOPIC = "/ufficio28/acquario/sensors"

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

        #Read HEADER ( C sizeof message_struct )
        encoded_data = ser.readline( ).strip()
        if len( encoded_data ) == 0:
           continue

        current_epoch_time = int(time.time())
        print("Current Epoch Time (in seconds):", current_epoch_time)

        raw_data = base64.b64decode(encoded_data)
        #print( raw_data )

        format_string = '20sB'

        id_str, type_byte = struct.unpack(format_string, raw_data[:struct.calcsize(format_string)])

        id_str = id_str.decode('utf-8')
        print( id_str )
        print( type_byte )

        data_bytes = raw_data[struct.calcsize(format_string):]
        #print( data_bytes )

        if type_byte == 0:   # Define the format string for agrumino_data
              print("decoding agrumino" )

#              agrumino_format_string = '??'
              agrumino_format_string = 'fIffI??'

              temp, soil, lum, batt_volt, batt_lvl, usb_conn, charging = struct.unpack(agrumino_format_string, data_bytes[:struct.calcsize( agrumino_format_string )] )

              print ( temp, soil, lum, batt_volt, batt_lvl, usb_conn, charging )

              hum = 22

              if is_jetson_nano():
                  USE_TOPIC = SENSORS_TOPIC
              else:
                  USE_TOPIC = SENSORS_TOPIC + "/" + id

              charging= "true" if charging != 0 else "false"

              topic =  USE_TOPIC + "/is_battery_charging"
              command = f"{{\"value\":{charging},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
              mqtt_client.publish(topic, command )

              topic =  USE_TOPIC + "/is_usb_attached"
              command = f"{{\"value\":{usb_conn},\"type\":\"status\",\"epoch\":{current_epoch_time}}}"
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
              #"{\"id\":\"bagno\",\"command\":\"toggle\"}"
              #topic =  "homeassistant/light/" + id + "/set"
              #mqtt_client.publish(topic, command )
              #print("Data published to MQTT:", json_data)
              print("TODO")


    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            print(f"Error : {e}")
        else:
            break


print("Exiting program.")
ser.close()
mqtt_client.disconnect()
mqtt_client.loop_stop()

