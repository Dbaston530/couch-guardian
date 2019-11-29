from datetime import datetime
import json
from bson import json_util
#import bson.json_util
import re
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

class IBMDatabase:
    #constructor: IAM credentials
    def __init__(self,deviceID,username,apikey):
        self.deviceID=deviceID
        self.username=username
        self.apikey=apikey
        
    #connect to database
    def connect(self):
        try:
            self.client = Cloudant.iam(self.username, self.apikey)
            self.client.connect()
        except:
            print("IBM Database connection error.")
        
    def disconnect(self):
        try:
            self.client.disconnect()
        except:
            print("IBM Database disconnection error.")
        
    def createDatabase(self,dbName):
        try:
            self.dbName=dbName
            self.myDB=self.client.create_database(self.dbName)
            if self.myDB.exists():    
                print(f"{self.dbName} successfully created")
        except:
            print("Database creation error.")
            
    def selectDatabase(self,dbName):     
        try:
            self.myDB=self.client[dbName]
            self.dbName=dbName
        except:
            print("Database selection error.")
            
    def addData(self,args):
        self.connect()
        self.selectDatabase(self.dbName)
        time = datetime.now()
        timeJson=json.dumps(time,default=json_util.default)
        timeSerial=int(re.findall('\d+',timeJson)[0])
        motion = args[0]
        pet = args[1]
        
        jsonDoc = {
            "deviceID": self.deviceID,
            "timestamp": timeSerial,
            "timeformat": time.strftime("%Y-%m-%d %X"),
            "motion": motion,
            "pet": pet
        }
        try:
            newDoc=self.myDB.create_document(jsonDoc)
            if newDoc.exists():
                print(f"Document {motion} and {pet} successfully created.")
        except:
            print("Document creation error.")
        self.disconnect()
        
'''
result_collection=Result(my_database.all_docs, include_docs=True)
print(f"Retrieved minimal document: \n{result_collection[0]}\n")

try:
    client.delete_database(database_name)
except CloudantException:
    print(f"There was a problem deleting '{database_name}'.\n")
else:
    print(f"'{database_name}' successfully deleted.\n")
    
client.disconnect()
'''