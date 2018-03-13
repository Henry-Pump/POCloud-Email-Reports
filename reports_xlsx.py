"""Prepare and send daily reports for Advanced VFD IPP devices in Meshify."""
import meshify
import json
from os import getenv
from sys import exit, stdout
from smtplib import SMTP
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from time import sleep, time
from tzlocal import get_localzone
import xlsxwriter
import argparse
import logging
from logging.handlers import RotatingFileHandler

logger = ""
DEVICE_TYPE_NAME = ""
datestring = datetime.now().strftime("%Y%m%d")

VALUES_TO_INCLUDE = []
MESHIFY_NAMES = []
CONFIG_PATH = ""
OUTPUT_PATH = ""

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
            logger.error("Be sure to set the SMTP email and password as environment variables SMTP_EMAIL and SMTP_PASSWORD")
            exit()

    devicetypes = meshify.query_meshify_api("devicetypes")
    this_devicetype = meshify.find_by_name(DEVICE_TYPE_NAME, devicetypes)

    companies = meshify.query_meshify_api("companies")
    company_lookup = {}
    for x in companies:
        company_lookup[x['id']] = x

    devices = meshify.query_meshify_api("devices")
    this_devices = filter(lambda x: x['deviceTypeId'] == this_devicetype['id'], devices)
    this_devices = [join_company_info(x, company_lookup) for x in this_devices]

    for i in range(0, len(this_devices)):
        this_devices[i]['values'] = filter_object_parameters(
            meshify.query_meshify_api("devices/{}/values".format(this_devices[i]['id'])), MESHIFY_NAMES)
    this_devices = group_by_company(this_devices)

    for comp in this_devices:
        local_tz = get_localzone()
        now_t = time()
        now_dt = datetime.utcfromtimestamp(now_t)
        now = local_tz.localize(now_dt)

        workbook = xlsxwriter.Workbook("{}/{}_{}_{}.xlsx".format(OUTPUT_PATH, DEVICE_TYPE_NAME, comp, datestring))
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 20)

        bold = workbook.add_format({'bold': True})
        red = workbook.add_format({'font_color': 'red'})

        worksheet.write(0, 0, "Well Name", bold)
        for i in range(0, len(VALUES_TO_INCLUDE)):
            worksheet.write(0, i+1, VALUES_TO_INCLUDE[i]['vanity_name'], bold)

        sorted_company_devices = sorted(this_devices[comp], key=lambda x: x['vanityName'])
        for j in range(0, len(sorted_company_devices)):
            dev = sorted_company_devices[j]
            worksheet.write(j+1, 0, dev['vanityName'])
            for k in range(0, len(MESHIFY_NAMES)):
                v = MESHIFY_NAMES[k]
                dt_ts = datetime.utcfromtimestamp(dev['values'][v]['timestamp'])
                dt_loc = local_tz.localize(dt_ts)
                stale = (now - dt_loc) > timedelta(hours=24)

                try:
                    v = round(float(dev['values'][v]['value']), 3)
                    if stale:
                        worksheet.write_number(j+1, 1+k, v, red)
                    else:
                        worksheet.write_number(j+1, 1+k, v)
                except ValueError:
                    v = str(dev['values'][v]['value'])
                    if stale:
                        worksheet.write(j+1, 1+k, v, red)
                    else:
                        worksheet.write(j+1, 1+k, v)

        workbook.close()

        if sendEmail:

            with open("{}/{}_to.json".format(CONFIG_PATH, DEVICE_TYPE_NAME), 'r') as to_file:
                to_lookup = json.load(to_file)
            try:
                email_to = to_lookup[comp]
            except KeyError:
                logger.error("No recipients for that company({})!".format(comp))
                continue
            # part1 = MIMEText(header + values, "plain")
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(open("{}/{}_{}_{}.xlsx".format(OUTPUT_PATH, DEVICE_TYPE_NAME, comp, datestring), "rb").read())
            encoders.encode_base64(attachment)

            now = datetime.now()
            datestr = now.strftime("%a %b %d, %Y")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "{} Daily {} Report for {}".format(comp, DEVICE_TYPE_NAME.upper(), datestr)
            msg['From'] = "alerts@henry-pump.com"
            msg['To'] = ", ".join(email_to)

            filename = "{} {}.xlsx".format(comp, datestr)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)

            # msg.attach(part1)
            # msg.attach(part2)
            msg.attach(attachment)

            # s = SMTP(host="secure.emailsrvr.com", port=25)
            s = SMTP(host="email-smtp.us-east-1.amazonaws.com", port=587)
            s.starttls()
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.sendmail(from_addr="alerts@henry-pump.com", to_addrs=email_to, msg=msg.as_string())
            logger.info("Email sent to {} for {}".format(email_to, comp))
            sleep(2)


def setup_logger():
    """Setup and return the logger module."""
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    logFile = '{}/emailreports.log'.format(CONFIG_PATH)
    my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=500*1024, backupCount=2, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.INFO)
    logger = logging.getLogger("emailreports")
    logger.setLevel(logging.INFO)
    logger.addHandler(my_handler)

    console_out = logging.StreamHandler(stdout)
    console_out.setFormatter(log_formatter)
    logger.addHandler(console_out)

    return logger


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('deviceType', help="Meshify device type")
    parser.add_argument('-s', '--send', action='store_true', help="Send emails to everyone in the _to.json file")
    parser.add_argument('-c', '--config-path', default="channel_config", help="The folder path that holds the configuration files")
    parser.add_argument('-o', '--output-path', default="files", help="The folder path that holds the output files")

    args = parser.parse_args()
    DEVICE_TYPE_NAME = args.deviceType
    SEND_EMAIL = args.send

    CONFIG_PATH = args.config_path
    if CONFIG_PATH[-1] == '/':
        CONFIG_PATH = CONFIG_PATH[:-1]

    OUTPUT_PATH = args.output_path
    if OUTPUT_PATH[-1] == '/':
        OUTPUT_PATH = OUTPUT_PATH[:-1]

    logger = setup_logger()

    try:
        with open("{}/{}_channels.json".format(CONFIG_PATH, DEVICE_TYPE_NAME), 'r') as channel_file:
            VALUES_TO_INCLUDE = json.load(channel_file)
            MESHIFY_NAMES = [m['meshify_name'] for m in VALUES_TO_INCLUDE]
    except IOError:
        logger.error("No channel file named {}_channels.json".format(DEVICE_TYPE_NAME))
        exit()
    except ValueError as e:
        logger.error("Channel file {}_channels.json is misformed: {}".format(DEVICE_TYPE_NAME, e))
        exit()

    main(sendEmail=SEND_EMAIL)
