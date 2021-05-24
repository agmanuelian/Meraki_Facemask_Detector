import boto3
import json
import time
from urllib.request import urlopen
import requests

#### HARD CODE CREDENTIALS HERE

# AWS
a_key = 'YOUR_AWS_ACCESS_KEY'
s_key = 'YOUR_AWS_SECRET_KEY'

# WEBEX
access_token = "YOUR_AWS_ACCESS_KEY"
teams_room = "YOUR_WEBEX_ROOM" 

# MERAKI
api_key = 'YOUR_MERAKI_API_KEY'
MV_Camera_SN = "YOUR_MV-CAMERA_SERIAL_NUMBER"
base_url = f"https://api.meraki.com/api/v1/devices/{MV_Camera_SN}/camera/generateSnapshot"


# Default Handler function, receives webhook events posted to AWS API Gateway
def handle(event, context):
    # Perform connection to AWS Rekognition service
    rekog = boto3.client('rekognition', region_name= 'us-east-2', aws_access_key_id = a_key, aws_secret_access_key = s_key)

    snapshot_url = event['image_url']

    response = rekog.detect_protective_equipment(
        Image={
            'Bytes': image_encoder(snapshot_url)
        },
        SummarizationAttributes={
            'MinConfidence': 80,
            'RequiredEquipmentTypes': [
                'FACE_COVER','HAND_COVER','HEAD_COVER'
            ]
        }
    )

    # Perform image analysis

    msg = "\nQuantity of detected people: **"+ str(len(response["Persons"])) + "**\n"
    print(msg)
    item = 1

    # Parse analysis results
    for person in response["Persons"]:
        for bodypart in person["BodyParts"]:
            if bodypart["Name"] == "FACE":
                if len(bodypart["EquipmentDetections"])>0:
                    if bodypart["EquipmentDetections"][0]["Type"] == "FACE_COVER":
                        if bodypart["EquipmentDetections"][0]["CoversBodyPart"]["Value"] == True:
                            msg += "Person Nº"+ str(item) + " is wearing a facemask, with the nose covered\n"
                        else:
                            msg += "Person Nº"+ str(item) +" is wearing a facemask, with the nose **UNcovered**\n"
                else:
                    msg += "Person Nº" + str(item) + " **IS NOT** wearing a facemask \n"
        item+=1  

    # Post results into a Webex Teams room
    messenger(snapshot_url, msg)
    
def image_encoder(url):
    contents = urlopen(url).read()
    return contents

def messenger(url_snapshot, msg):
    url = 'https://webexapis.com/v1/messages'

    headers =  {'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'}
    
    body = {
    "roomId": teams_room,
    "markdown": msg,
    "files": [url_snapshot]
 }

    action = requests.post(url=url, headers=headers, data=json.dumps(body))
    print(action.status_code)
