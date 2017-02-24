import requests
import json
from os import getenv
from sys import exit, argv
from datetime import datetime

MESHIFY_BASE_URL = "https://henrypump.meshify.com/api/v3/"
MESHIFY_USERNAME = getenv("MESHIFY_USERNAME")
MESHIFY_PASSWORD = getenv("MESHIFY_PASSWORD")
MESHIFY_AUTH = requests.auth.HTTPBasicAuth(MESHIFY_USERNAME, MESHIFY_PASSWORD)

SQL_SERVER = getenv("HP_SQL_SERVER")
SQL_USER = getenv("HP_SQL_USER")
SQL_PASSWORD = getenv("HP_SQL_PASSWORD")

SQL_DB = "POCCLoud"
SQL_TABLE = "Production"


def find_by_name(name, list_of_stuff):
    for x in list_of_stuff:
        if x['name'] == name:
            return x
    return False


def query_meshify_api(endpoint):
    q_url = MESHIFY_BASE_URL + endpoint
    q_req = requests.get(q_url, auth=MESHIFY_AUTH)
    return json.loads(q_req.text) if q_req.status_code == 200 else []


def main(test_mode=False):
    if not MESHIFY_USERNAME or not MESHIFY_PASSWORD:
        print("Be sure to set the meshify username and password as environment variables MESHIFY_USERNAME and MESHIFY_PASSWORD")
        exit()

    if (not SQL_SERVER or not SQL_USER or not SQL_PASSWORD) and not test_mode:
        print("Be sure to set the SQL Server, username, and password as enviroment variables HP_SQL_SERVER, HP_SQL_USER, and HP_SQL_PASSWORD")
        exit()

    if not test_mode:
        import pymssql

    devicetypes = query_meshify_api("devicetypes")
    companies = query_meshify_api("companies")
    henrypetroleum_company = find_by_name("Henry Petroleum", companies)
    devices = query_meshify_api("devices")
    gateways = query_meshify_api("gateways")

    abbflow_devicetype = find_by_name("abbflow", devicetypes)
    abbflow_devices = list(filter(lambda x: x['deviceTypeId'] == abbflow_devicetype['id'] and x['companyId'] == henrypetroleum_company['id'], devices))
    abbflowchannels = query_meshify_api("devicetypes/{}/channels".format(abbflow_devicetype['id']))

    abbflow_yesterdaytotal_channel = find_by_name("yesterday_volume", abbflowchannels)

    query_params = []
    for abbflow_dev in abbflow_devices:
        abbflowdevvalues = query_meshify_api("devices/{}/values".format(abbflow_dev['id']))
        try:
            yest_volume = float(abbflowdevvalues['yesterday_volume']['value'])
            gateway_id = abbflow_dev['gatewayId']
            unix_ts = float(abbflowdevvalues['yesterday_volume']['timestamp'])
            local_time = datetime.utcfromtimestamp(unix_ts)
            midn_time = datetime(local_time.year, local_time.month, local_time.day, 0, 1)
            query_params.append((gateway_id, yest_volume, midn_time))
        except ValueError:
            pass
    if not test_mode:
        conn = pymssql.connect(SQL_SERVER, SQL_USER, SQL_PASSWORD, SQL_DB)
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO Production (well_id, yesterday_production, timestamp) VALUES (%d, %d, %s)", query_params)
        conn.commit()

        cursor.execute("SELECT * FROM Production")
        print("Fetching from db at {}".format(datetime.now()))
        row = cursor.fetchone()
        while row:
            print(row)
            row = cursor.fetchone()
        print("==============")
        conn.close()
    else:
        print("Fake Fetching from db at {}".format(datetime.now()))
        for q in query_params:
            print(q)
        print("==============")

if __name__ == '__main__':
    test_mode = False
    if len(argv) > 1:
        if argv[1].lower() == "true":
            test_mode = True
    main(test_mode=test_mode)
