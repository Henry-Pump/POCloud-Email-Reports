"""Prepare and send daily reports for Advanced VFD IPP devices in Meshify."""
import meshify
import json
from os import getenv
from sys import exit, argv
from smtplib import SMTP
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from time import sleep, time
from tzlocal import get_localzone

VALUES_TO_INCLUDE = [
    {'meshify_name': 'yesterday_volume', 'vanity_name': 'Yesteday Volume'},
    {'meshify_name': 'volume_flow', 'vanity_name': 'Flow Rate'},
    {'meshify_name': 'differential_pressure', 'vanity_name': 'Diff. Pressure'},
    {'meshify_name': 'static_pressure', 'vanity_name': 'Static Pressure'},
    {'meshify_name': 'temperature', 'vanity_name': 'Temperature'},
    {'meshify_name': 'battery_voltage', 'vanity_name': 'Battery Voltage'},
    {'meshify_name': 'last_calculation_period_volume', 'vanity_name': 'Last Calc. Period'},
]

MESHIFY_NAMES = [m['meshify_name'] for m in VALUES_TO_INCLUDE]

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


def main(device_type_name, sendEmail=False):
    """Get the data and optionally send an email."""
    if sendEmail:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("[{}] Be sure to set the SMTP email and password as environment variables SMTP_EMAIL and SMTP_PASSWORD".format(datetime.now().isoformat()))
            exit()

    devicetypes = meshify.query_meshify_api("devicetypes")
    filtered_devicetype = meshify.find_by_name(device_type_name, devicetypes)

    companies = meshify.query_meshify_api("companies")
    company_lookup = {}
    for x in companies:
        company_lookup[x['id']] = x

    devices = meshify.query_meshify_api("devices")
    filtered_devices = filter(lambda x: x['deviceTypeId'] == filtered_devicetype['id'], devices)
    filtered_devices = [join_company_info(x, company_lookup) for x in filtered_devices]

    for i in range(0, len(filtered_devices)):
        filtered_devices[i]['values'] = filter_object_parameters(
            meshify.query_meshify_api("devices/{}/values".format(filtered_devices[i]['id'])), MESHIFY_NAMES)
    filtered_devices = group_by_company(filtered_devices)

    totals = {}
    for comp in filtered_devices:
        total = {}
        average = {}
        for v in MESHIFY_NAMES:
            total[v] = 0.0
            average[v] = 0.0
        for dev in filtered_devices[comp]:
            for v in MESHIFY_NAMES:
                try:
                    total[v] += float(dev['values'][v]['value'])
                except ValueError:
                    # print("Can't make a total for {}".format(v))
                    pass
        totals[comp] = total

    for comp in filtered_devices:
        local_tz = get_localzone()
        now_t = time()
        now_dt = datetime.utcfromtimestamp(now_t)
        now = local_tz.localize(now_dt)

        total = []
        average = []

        header = "Well Name,"
        for v in VALUES_TO_INCLUDE:
            header += "{},".format(v['vanity_name'])
        header = header[:-1] + "\n"

        values = ""
        for dev in sorted(filtered_devices[comp], key=lambda x: x['vanityName']):
            values += dev['vanityName'] + ","
            for v in MESHIFY_NAMES:
                dt_ts = datetime.utcfromtimestamp(dev['values'][v]['timestamp'])
                dt_loc = local_tz.localize(dt_ts)
                stale = (now - dt_loc) > timedelta(hours=24)

                try:
                    v = str(round(float(dev['values'][v]['value']), 3))
                    if stale:
                        v += " (STALE)"
                    values += '{},'.format(v)
                except ValueError:
                    v = str(dev['values'][v]['value'])
                    if stale:
                        v += " (STALE)"
                    values += '{},'.format(v)

                # values += '{},'.format(dt)
            values = values[:-1] + "\n"

        if sendEmail:

            with open("{}_to.json".format(device_type_name), 'r') as to_file:
                to_lookup = json.load(to_file)
            try:
                email_to = to_lookup[comp]
            except KeyError:
                print("[{}] No recipients for that company ({})!".format(datetime.now().isoformat(), comp))
                continue
            # part1 = MIMEText(header + values, "plain")
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(header + values)
            encoders.encode_base64(attachment)

            now = datetime.now()
            datestr = now.strftime("%a %b %d, %Y")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "{} SAMPLE Daily ABB Flowmeter Report for {}".format(comp, datestr)
            msg['From'] = "alerts@henry-pump.com"
            msg['To'] = ", ".join(email_to)

            filename = "{} {}.csv".format(comp, datestr)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)

            # msg.attach(part1)
            # msg.attach(part2)
            msg.attach(attachment)

            s = SMTP(host="email-smtp.us-east-1.amazonaws.com", port=587)
            s.starttls()
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.sendmail(from_addr="alerts@henry-pump.com", to_addrs=email_to, msg=msg.as_string())
            print("[{}] Email sent to {} for {}".format(datetime.now().isoformat(), email_to, comp))
            sleep(2)

        with open('{}-{}.csv'.format(comp, device_type_name), 'w') as csvfile:
            csvfile.write(header + values)

    filtered_devices["totals"] = totals
    with open("current_{}.json".format(device_type_name), 'w') as jsonfile:
        json.dump(filtered_devices, jsonfile, indent=4)


if __name__ == '__main__':
    if len(argv) > 1:
        s = argv[1] == "true"
        main("abbflow", sendEmail=s)
    else:
        main("abbflow", sendEmail=False)
