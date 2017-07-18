"""Query Meshify for data."""
import requests
import json
from os import getenv
from sys import exit

MESHIFY_BASE_URL = "https://henrypump.meshify.com/api/v3/"
MESHIFY_USERNAME = getenv("MESHIFY_USERNAME")
MESHIFY_PASSWORD = getenv("MESHIFY_PASSWORD")
MESHIFY_AUTH = requests.auth.HTTPBasicAuth(MESHIFY_USERNAME, MESHIFY_PASSWORD)

if not MESHIFY_USERNAME or not MESHIFY_PASSWORD:
    print("Be sure to set the meshify username and password as environment variables MESHIFY_USERNAME and MESHIFY_PASSWORD")
    exit()


def find_by_name(name, list_of_stuff):
    """Find an object in a list of stuff by its name parameter."""
    for x in list_of_stuff:
        if x['name'] == name:
            return x
    return False


def query_meshify_api(endpoint):
    """Make a query to the meshify API."""
    q_url = MESHIFY_BASE_URL + endpoint
    q_req = requests.get(q_url, auth=MESHIFY_AUTH)
    return json.loads(q_req.text) if q_req.status_code == 200 else []


def post_meshify_api(endpoint, data):
    """Post data to the meshify API."""
    q_url = MESHIFY_BASE_URL + endpoint
    q_req = requests.post(q_url, data=json.dumps(data), auth=MESHIFY_AUTH)
    if q_req.status_code != 200:
        print(q_req.status_code)
    return json.loads(q_req.text) if q_req.status_code == 200 else []
