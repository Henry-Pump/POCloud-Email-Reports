import requests
import json
from os import getenv
from sys import exit, argv
from datetime import datetime
import meshify

SQL_SERVER = getenv("HP_SQL_SERVER")
SQL_USER = getenv("HP_SQL_USER")
SQL_PASSWORD = getenv("HP_SQL_PASSWORD")

SQL_DB = "POCCLoud"
SQL_TABLE = "Production"


def main(test_mode=False):
    if not MESHIFY_USERNAME or not MESHIFY_PASSWORD:
        print("Be sure to set the meshify username and password as environment variables MESHIFY_USERNAME and MESHIFY_PASSWORD")
        exit()

    if (not SQL_SERVER or not SQL_USER or not SQL_PASSWORD) and not test_mode:
        print("Be sure to set the SQL Server, username, and password as enviroment variables HP_SQL_SERVER, HP_SQL_USER, and HP_SQL_PASSWORD")
        exit()

    if not test_mode:
        import pymssql

    devicetypes = meshify.query_meshify_api("devicetypes")
    companies = meshify.query_meshify_api("companies")
    henrypetroleum_company = meshify.find_by_name("Henry Petroleum", companies)
    devices = meshify.query_meshify_api("devices")
    gateways = meshify.query_meshify_api("gateways")

    abbflow_devicetype = meshify.find_by_name("abbflow", devicetypes)
    abbflow_devices = list(filter(lambda x: x['deviceTypeId'] == abbflow_devicetype['id'] and x['companyId'] == henrypetroleum_company['id'], devices))
    abbflowchannels = meshify.query_meshify_api("devicetypes/{}/channels".format(abbflow_devicetype['id']))

    abbflow_yesterdaytotal_channel = meshify.find_by_name("yesterday_volume", abbflowchannels)

    query_params = []
    for abbflow_dev in abbflow_devices:
        abbflowdevvalues = meshify.query_meshify_api("devices/{}/values".format(abbflow_dev['id']))
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
