from __future__ import print_function
import json
import requests
import time

PRISMA_CLOUD_API_ACCESS_KEY_ID = ""
PRISMA_CLOUD_API_SECRET_KEY = ""
PRISMA_CLOUD_API_URL = "https://api2.eu.prismacloud.io"

headers = {'Content-Type': 'application/json'}
api_url = PRISMA_CLOUD_API_URL+"/login"
action = "POST"
data = {}
data['username'] = PRISMA_CLOUD_API_ACCESS_KEY_ID
data['password'] = PRISMA_CLOUD_API_SECRET_KEY

data_json = json.dumps(data)
response_raw = requests.request(action, api_url, headers=headers, data=data_json)
response_data = response_raw.json()

# Pull the token from the response package
token = response_data['token']

#print(token)

# Fetch all basic cloud account info including overall status
url = PRISMA_CLOUD_API_URL+"/cloud"
headers = {"x-redlock-auth":token}
querystring = {"excludeAccountGroupDetails":"true"}
response_raw = requests.request("GET", url, headers=headers, params=querystring)
response_data = response_raw.json()
status = response_raw.status_code

if (status == 401):
    print("Call failed")
else:
    url2 = PRISMA_CLOUD_API_URL+"/account/"
    headers2 = {"x-redlock-auth":token}
    querystring2 = ""
    
    for k in response_data:
        if k['status'] != "ok":
            print("---Found Cloud account in wrong state")
            print("   ",k['name'], k['accountId'], " with status ",k['status'])
            querystring2 = k['accountId']+"/config/status"
            finalurl = url2+querystring2
            response_raw2 = requests.request("GET", finalurl, headers=headers2)
            response_data2 = response_raw2.json()
            print("   Status details for ",k['name'])
            for m in response_data2:
                print("   ",m['name'],m['status'],m['message'])
            print("---Cloud Account Check Done")
            print("")

