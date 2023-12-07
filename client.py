###############################################
##      Copyright, ARMOR Technologies, Inc.   ##
################################################

import requests
import urllib.parse
import json

class ApiReturn:
    status = 0
    body = None
    def __init__(self, status, body):
        self.status = status
        self.body = body

    def bodyJson(self):
        return json.dumps(self.body, indent=4)

    def bodyText(self):
        if type(self.body) is dict:
            return json.dumps(self.body, indent=4)
        else:
            return self.body

class ArmorClient:
    url = "https://app.armordata.io/api/v1/"
    bearer_token = ""
    debug = False

    requestHeaders = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    def __init__(self, url, token=None, user=None, password=None, debug=False):
        self.url = url
        self.debug = debug
        if token:
            self.bearer_token = token
            self.requestHeaders = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            }
        elif user and password:
            self.bearer_token = self.login(user, password)
            self.requestHeaders = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            }

    def login(self, user, password):
        response = self.request("POST", "login", query={"emailAddress": user, "password": password}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        #print(f"Body: {response} {response['token']}")
        return response.body['token']

    def request(self, method, uri, query=None, body=None, headers=None):
        requestHeaders = self.requestHeaders
        if headers:
            requestHeaders = headers
        if self.debug:
            print(f"Request: {method} {self.url + uri}")
            print(f"Body: {requestHeaders}")
            print(f"Query: {query}")
            print(f"Body: {body}")
        try:
            response = requests.request(method=method, url=self.url + uri, params=query, headers=requestHeaders, json=body, timeout=120)
            if response.status_code != 200:
                print(f"s:{response.status_code} h:{json.dumps(response.headers, indent=4)} b:{response.text}")
            response_body = response.json()  # Parse the response as JSON
            if self.debug:
                print("Response JSON:")
                #print(json.dumps(response_body, indent=4))  # Pretty-print the JSON response
        except Exception as e:
            try:
                response_body = response.text
                if self.debug:
                    print(f"Response exception: ({e}) {response_body}")
            except:
                response_body = None
                if self.debug:
                    print(f"Response exception: ({e}) (no body)")
        return ApiReturn(response.status_code,  response_body)
