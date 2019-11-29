import wiotp.sdk.device

def sendSignalToWatsonIoT(orgId,typeId,deviceId,token,petType):
    myConfig = { 
        "identity": {
            "orgId": orgId,
            "typeId": typeId,
            "deviceId": deviceId
        },
        "auth": {
            "token": token
        }
    }
    myData = {
        "pet" : petType
    }
    try:
        client = wiotp.sdk.device.DeviceClient(config=myConfig)
        client.connect()
        client.publishEvent(eventId="motion", msgFormat="json", data=myData, qos=0)
        client.disconnect()
    except:
        print("WatsonIoT connection error.")
