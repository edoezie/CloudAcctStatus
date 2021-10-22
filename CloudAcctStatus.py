from __future__ import print_function
import json
import requests
import configparser
from requests import api

# Parser config file for mandatory variables - global var
config = configparser.ConfigParser() 

# Function to parse the config.ini file and see if all is OK.
def validateConfigParser():
    try:
        config.read('config.ini')
    except configparser.Error as e:
        raise SystemExit('!!! Error parsing config.ini file!\n %s' % e)
    return

# Function to execute a call to Prisma Cloud. Returns json body of Prisma Cloud's response.
def doPrismaAPICall (APIType, APIEndpoint, APIHeaders, APIData = "", APIParams = ""):
    PRISMA_CLOUD_API_URL = config.get('URL','URL')
    full_URL = PRISMA_CLOUD_API_URL + APIEndpoint
    try:
        response_raw = requests.request(APIType, full_URL, headers=APIHeaders, data=APIData, params=APIParams)
    except requests.exceptions.RequestException as e:
        raise SystemExit('!!! Error doing API call to Prisma Cloud!\n %s' % e)
    if (response_raw.status_code != 200):
        print("!!! API Call returned not-OK! Exiting script.")
        print(f"Request-ID: %s", response_raw.headers['x-redlock-request-id'])
        exit(-1)
    return response_raw.json()

# Function to authenticate to Prisma Cloud. Returns token as obtained.
def authenticatePrismaCloud ():
    print("\n--- Authenticating to Prisma Cloud via provided token.")
    api_headers = {'Content-Type': 'application/json'}
    api_endpoint = "/login"
    api_data = {}
    api_data['username'] = config.get('AUTHENTICATION','ACCESS_KEY_ID')
    api_data['password'] = config.get('AUTHENTICATION','SECRET_KEY')
    data_json = json.dumps(api_data)
    response = doPrismaAPICall("POST", api_endpoint, api_headers, data_json, "")
    return response['token']

def fetchPrismaCloudAccounts(token,ExclAG = True):
    action = "GET"
    endpoint =  "/cloud"
    headers = {'x-redlock-auth':token}
    querystring = {"excludeAccountGroupDetails":ExclAG}
    response = doPrismaAPICall(action, endpoint, headers, "", querystring)
    return response

def fetchPrismaAccountInfo(AccountId, token):
    action = "GET"
    endpoint =  "/account/" + AccountId + "/config/status"
    headers = {'x-redlock-auth':token}
    response = doPrismaAPICall(action, endpoint, headers, "", "")
    return response

def printAccountInfo(AccountData, token):
    print("---Found Cloud account in wrong state")
    print("   ",AccountData['name'], AccountData['accountId'], " with status ",AccountData['status'])
    print("   Status details for ",AccountData['name'])
    response_info = fetchPrismaAccountInfo(AccountData['accountId'], token)
    for item in response_info:
        print("   ",item['name'],item['status'],item['message'])
    print("---Cloud Account Check Done")
    print("")

def main ():
    auth_token = ""

    validateConfigParser()
    auth_token = authenticatePrismaCloud()

    # Fetch all basic cloud account info including overall status, exclude account groups set to True
    response = fetchPrismaCloudAccounts(auth_token,"True")
    
    for k in response:
        if k['status'] != "ok":
            printAccountInfo(k, auth_token)

if __name__ == "__main__":
    main()