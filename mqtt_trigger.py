import paho.mqtt.client as mqtt
import time 
import json
from datetime import datetime
import requests

api_key = 'YOUR_MERAKI_API_KEY'
MV_Camera_SN = "YOUR_MV-CAMERA_SERIAL_NUMBER"
base_url = f"https://api.meraki.com/api/v1/devices/{MV_Camera_SN}/camera/generateSnapshot"
aws_api_url = "YOUR_AWS_API_ENDPOINT"
broker_address = "YOUR_MQTT_BROKER_ADDRESS"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+ str(rc))
    print("\n")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/merakimv/#/0")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    payload_dict= json.loads(payload)

    if msg.topic == "/merakimv/#/0":
        if payload_dict['counts']['person'] > 0:
            print(f"Qty of people detected: {payload_dict['counts']['person']}")
            print("Found a person!!")

            #Waits for two seconds it grabs a better picture of the person in front of the camera
            time.sleep(2)
            headers = {
            'X-Cisco-Meraki-API-Key' : api_key,
            "timestamp": datetime.now().isoformat()
            } 

            image_url = requests.post(url= base_url, headers=headers).json()["url"]

            payload = {
                "image_url": image_url
            }
            
            print("Waiting for image to be renderized")
            time.sleep(6)

            # TRIGGER LAMBDA FUNCTION
            print("FUNCTION TRIGGERED!")
            
            requests.post(url= aws_api_url, data=json.dumps(payload)).json()
            time.sleep(60)

        else:
            print(f"Qty of people detected: {payload_dict['counts']['person']}")
            print(str(time.ctime(payload_dict['ts']/1000)))
            dt = datetime.utcfromtimestamp(payload_dict['ts']/1000)
            iso_format = dt.isoformat() + 'Z'
            print(iso_format)

        print("----------------------------------------------")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)

client.loop_forever()