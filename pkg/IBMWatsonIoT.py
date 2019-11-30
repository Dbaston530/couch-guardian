import wiotp.sdk.device
import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

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
        "ip" : get_ip()
    }
    try:
        client = wiotp.sdk.device.DeviceClient(config=myConfig)
        client.connect()
        client.publishEvent(eventId="motion", msgFormat="json", data=myData, qos=0)
        client.disconnect()
    except:
        print("WatsonIoT connection error.")
