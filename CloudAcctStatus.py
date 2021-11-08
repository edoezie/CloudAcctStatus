from __future__ import print_function
import json
import requests
import configparser
from requests import api

requests.packages.urllib3.disable_warnings() # Added to avoid warnings in output if proxy

# Parser config file for mandatory variables - global var
config = configparser.ConfigParser()

class API_Object():
    def __init__(self, API_Endpoint, API_Action, API_Token_Required, API_Header = {}, API_Data = {}, API_Params = {}):
        self.API_Endpoint = API_Endpoint
        self.API_Action = API_Action
        self.API_Token_Required = API_Token_Required
        self.API_Header = API_Header
        self.API_Data = API_Data
        self.API_Params = API_Params
    def __repr__(self):
        return "API Object holding all information regarding an API call to Prisma Cloud"
    def __str__(self):
        print("Endpoint      =", self.API_Endpoint)
        print("Action        =", self.API_Action)
        print("Token enabled =", self.API_Token_Required)
        print("Header        =", self.API_Header)
        print("Data          =", self.API_Data)
        print("Params        =", self.API_Params)
        return ""
    def doCall(self):
        print ("Being called for:", self.API_Endpoint)

# Function to parse the config.ini file and see if all is OK.
def validateConfigParser():
    try:
        config.read('config.ini')
    except configparser.Error as e:
        raise SystemExit('!!! Error parsing config.ini file!\n %s' % e)
    return

# Function to execute a call to Prisma Cloud. Returns json body of Prisma Cloud's response.
def doPrismaAPICall (AuthInfo, APIInfo):
    full_URL = AuthInfo['URL_base'] + APIInfo.API_Endpoint
    if AuthInfo['authMethod'] == 1 and APIInfo.API_Token_Required == True:
        APIInfo.API_Header['x-redlock-auth'] = AuthInfo['token']
    try:
        response_raw = requests.request(APIInfo.API_Action, full_URL, headers=APIInfo.API_Header, data=APIInfo.API_Data, params=APIInfo.API_Params, verify=AuthInfo['sslverify'])
    except requests.exceptions.RequestException as e:
        raise SystemExit('!!! Error doing API call to Prisma Cloud!\n %s' % e)
    if (response_raw.status_code != 200):
        print("!!! API Call returned not-OK! Exiting script.")
        print(f"Request-ID: %s", response_raw.headers['x-redlock-request-id'])
        exit(-1)
    return response_raw.json()

def initializeAuthObject ():
    auth_info = {}
    auth_info['username']  = config.get('AUTHENTICATION','ACCESS_KEY_ID')
    auth_info['password']  = config.get('AUTHENTICATION','SECRET_KEY')
    auth_info['sslverify'] = config.get('SSL_VERIFY','ENABLE_VERIFY')
    auth_info['URL_base']  = config.get('URL','URL')
    auth_info['authMethod'] = 0
    auth_info['sslverify'] = (auth_info['sslverify'].lower() != "false" )
    if (not auth_info['sslverify']):
        print ("--- WARNING: Not using SSL verification as configured in config.ini file.")
    return auth_info

# Function to authenticate to Prisma Cloud. Returns token as obtained.
def authenticatePrismaCloud ():
    auth = {}
    auth_info = initializeAuthObject()
    auth['username'] = auth_info['username']
    auth['password'] = auth_info['password']
    auth_body = json.dumps(auth)
    API_Info = API_Object("/login", "POST", False, {'Content-Type': 'application/json'}, API_Data=auth_body)
    print("\n--- Authenticating to Prisma Cloud via provided token.")
    response = doPrismaAPICall(auth_info, API_Info)
    print (f"-   Successfully authenticated to Prisma Cloud with SSL verification set to:", auth_info['sslverify'])
    auth_info['token'] = response['token']
    auth_info['authMethod'] = 1 # Use token for authentication from here on
    return auth_info

def fetchPrismaCloudAccounts(authInfo, ExclAG = True):
    API_Info = API_Object("/cloud", "GET", True, API_Params={"excludeAccountGroupDetails":ExclAG})
    response = doPrismaAPICall(authInfo, API_Info)
    return response

def fetchPrismaAccountInfo(authInfo, AccountId):
    endpoint =  "/account/" + AccountId + "/config/status"
    API_Info = API_Object(endpoint, "GET", True)
    response = doPrismaAPICall(authInfo, API_Info)
    return response

def initializeCSV (fileName):
    CSVFile=open(fileName, "a+")
    CSVFile.write("AccountName, AccountId, Status, ConfigStatus, EventStatus, FlowLogStatus\n")
    return CSVFile

def printAccountInfo(authInfo, AccountData):
    print("---Found Cloud account in wrong state")
    print("   ",AccountData['name'], AccountData['accountId'], " with status ",AccountData['status'])
    print("   Status details for ",AccountData['name'])
    response_info = fetchPrismaAccountInfo(authInfo, AccountData['accountId'])
    for item in response_info:
        print("   ",item['name'],item['status'],item['message'])
    print("---Cloud Account Check Done")
    print("")

def printAccountInfoCSV(authInfo, outputFile, accountData):
    outputFile.write(f"{accountData['name']}, {accountData['accountId']}, {accountData['status']}")
    response_info = fetchPrismaAccountInfo(authInfo, accountData['accountId'])
    for item in response_info:
        outputFile.write(f",\"{item['name']},{item['status']},{item['message']}\"")
    outputFile.write("\n")

def main ():
    EXCLUDE_AGS = True
    auth_info = {}
    validateConfigParser()
    CSVFile = initializeCSV(config.get('FILES', 'CSV_FILENAME'))
    auth_info = authenticatePrismaCloud()

    allCloudAccounts = fetchPrismaCloudAccounts(auth_info, EXCLUDE_AGS)
    for cloudAccount in allCloudAccounts:
        if cloudAccount['status'] != "ok":
            printAccountInfoCSV(auth_info, CSVFile, cloudAccount)
            # DEBUG printAccountInfo(auth_info, cloudAccount)

if __name__ == "__main__":
    main()