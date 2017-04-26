"""Prepare and send daily reports for Advanced VFD IPP devices in Meshify."""
import meshify
import json
from os import getenv
from sys import exit
from smtplib import SMTP
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

VALUES_TO_INCLUDE = {
    'flowtotalyesterday': 'Flow Total (Yesterday)',
    'pidcontrolmode': 'PID Control Mode',
    'wellstatus': 'Well Status',
    'downholesensorstatus': 'DH Sensor Status',
    'fluidlevel': 'Fluid Level',
    'intaketemperature': 'Intake Temperature',
    'intakepressure': 'Intake Pressure',
    'energytotalyesterday': 'Energy Total (Yesterday)',
    'tubingpressure': 'Tubing Pressure',
    'flowrate': 'Flow Rate'
}

SMTP_EMAIL = getenv("SMTP_EMAIL")
SMTP_PASSWORD = getenv("SMTP_PASSWORD")

def join_company_info(obj_with_companyId, company_lookup_obj):
    """Add company information to an object with companyId property."""
    obj_with_companyId['company'] = company_lookup_obj[obj_with_companyId['companyId']]
    return obj_with_companyId


def filter_object_parameters(ob, list_of_parameters):
    """Return an object of just the list of paramters."""
    new_ob = {}
    for par in list_of_parameters:
        try:
            new_ob[par] = ob[par]
        except KeyError:
            new_ob[par] = None
    return new_ob


def group_by_company(devices):
    """Group a list of devices by company."""
    grouped = {}
    for dev in devices:
        try:
            grouped[dev['company']['name']].append(dev)
        except KeyError:
            grouped[dev['company']['name']] = [dev]
    return grouped


def main(sendEmail=False):
    """Get the data and optionally send an email."""
    if sendEmail:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("Be sure to set the SMTP email and password as environment variables SMTP_EMAIL and SMTP_PASSWORD")
            exit()

    devicetypes = meshify.query_meshify_api("devicetypes")
    advvfdipp_devicetype = meshify.find_by_name("advvfdipp", devicetypes)

    companies = meshify.query_meshify_api("companies")
    company_lookup = {}
    for x in companies:
        company_lookup[x['id']] = x

    devices = meshify.query_meshify_api("devices")
    advvfdipp_devices = filter(lambda x: x['deviceTypeId'] == advvfdipp_devicetype['id'], devices)
    advvfdipp_devices = [join_company_info(x, company_lookup) for x in advvfdipp_devices]

    for i in range(0, len(advvfdipp_devices)):
        advvfdipp_devices[i]['values'] = filter_object_parameters(
            meshify.query_meshify_api("devices/{}/values".format(advvfdipp_devices[i]['id'])), VALUES_TO_INCLUDE)
    advvfdipp_devices = group_by_company(advvfdipp_devices)

    totals = {}
    for comp in advvfdipp_devices:
        total = {}
        average = {}
        for v in VALUES_TO_INCLUDE:
            total[v] = 0.0
            average[v] = 0.0
        for dev in advvfdipp_devices[comp]:
            for v in VALUES_TO_INCLUDE:
                try:
                    total[v] += float(dev['values'][v]['value'])
                except ValueError:
                    print("Can't make a total for {}".format(v))
        totals[comp] = total

    for comp in advvfdipp_devices:
        total = []
        average = []

        header = "Well Name,"
        table_header = "<thead><tr><th>Well Name</th>"
        for v in VALUES_TO_INCLUDE:
            header += "{},".format(VALUES_TO_INCLUDE[v])
            table_header += "<th>{}</th>".format(VALUES_TO_INCLUDE[v])
        header = header[:-1] + "\n"
        table_header += "</tr></thead>"

        values = ""
        table_body = "<tbody>"
        for dev in advvfdipp_devices[comp]:
            values += dev['vanityName'] + ","
            table_body += "<tr><td>{}</td>".format(dev['vanityName'])
            for v in VALUES_TO_INCLUDE:
                values += dev['values'][v]['value'] + ","
                table_body += "<td>{}</td>".format(dev['values'][v]['value'])
            values = values[:-1] + "\n"
            table_body += "</tr>"
        table_body += "</tbody>"

        table = "<table>{}{}</table>".format(table_header, table_body)

        part1 = MIMEText(header + values, "plain")
        part2 = MIMEText(table, "html")

        now = datetime.now()
        datestr = now.strftime("%a %b %d, %Y")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "{} SAMPLE Daily Report for {}".format(comp, datestr)
        msg.attach(part1)
        msg.attach(part2)

        if sendEmail:
            s = SMTP(host="secure.emailsrvr.com", port=25)
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.sendmail(from_addr="alerts@henry-pump.com", to_addrs=["pmcdonagh@henry-pump.com"], msg=msg.as_string())
        else:
            print(msg)

        with open('{}.csv'.format(comp), 'wb') as csvfile:
            csvfile.write(header + values)

    advvfdipp_devices["totals"] = totals
    with open("currentAdvVFDIPP.json", 'wb') as jsonfile:
        json.dump(advvfdipp_devices, jsonfile, indent=4)


if __name__ == '__main__':
    main(sendEmail=False)