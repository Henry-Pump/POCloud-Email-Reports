"""Prepare and send daily reports for Advanced VFD IPP devices in Meshify."""
import meshify
import json
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from time import time
from tzlocal import get_localzone
import xlsxwriter
import logging

# S3 Shiz
import boto3
# import botocore

s3 = boto3.resource('s3')
ses = boto3.client('ses')

BUCKET_NAME = "pocloud-email-reports"
EMAIL_FROM_ADDRESS = "alerts@henry-pump.com"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_s3_device_types():
    """Get device types from s3 objects."""
    """Each object must have a _to.json file and a _channels.json file."""
    device_types = []
    report_bucket = s3.Bucket(BUCKET_NAME)

    to_bucket_files = sorted(map(lambda x: x.key.split("/")[1], filter(lambda x: x.key[-1] != "/", report_bucket.objects.filter(Prefix='to_files'))))
    channel_config_bucket_files = sorted(map(lambda x: x.key.split("/")[1], filter(lambda x: x.key[-1] != "/", report_bucket.objects.filter(Prefix='channel_config'))))

    for i in range(0, len(to_bucket_files)):
        to_part = to_bucket_files[i].split("_")[0]
        config_part = channel_config_bucket_files[i].split("_")[0]
        if to_part == config_part:
            device_types.append(to_part)

    return device_types


def read_s3_device_config(device_type):
    """Get the JSON object config for a device_type."""
    obj = s3.Object(BUCKET_NAME, "channel_config/{}_channels.json".format(device_type))
    return json.loads(obj.get()['Body'].read().decode('utf-8'))


def read_s3_tofiles(device_type):
    """Get the JSON object _to file for a device_type."""
    obj = s3.Object(BUCKET_NAME, "to_files/{}_to.json".format(device_type))
    return json.loads(obj.get()['Body'].read().decode('utf-8'))


def send_ses_email(msg):
    """Send an email using AWS SES."""
    response = ses.send_raw_email(
        Source=EMAIL_FROM_ADDRESS,
        RawMessage={
            'Data': msg.as_string()
        },
        FromArn='',
        SourceArn='',
        ReturnPathArn=''
    )
    return response


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


def prep_emails(device_type, channel_config_list, to_list):
    """Prepare a message for sending for a devicetype."""
    messages = []
    meshify_channelnames = [m['meshify_name'] for m in channel_config_list]
    all_devicetypes = meshify.query_meshify_api("devicetypes")
    this_devicetype = meshify.find_by_name(device_type, all_devicetypes)
    companies = meshify.query_meshify_api("companies")

    company_lookup = {}
    for x in companies:
        company_lookup[x['id']] = x

    devices = meshify.query_meshify_api("devices")
    this_devices = filter(lambda x: x['deviceTypeId'] == this_devicetype['id'], devices)
    this_devices = [join_company_info(x, company_lookup) for x in this_devices]

    for i in range(0, len(this_devices)):
        this_devices[i]['values'] = filter_object_parameters(
            meshify.query_meshify_api("devices/{}/values".format(this_devices[i]['id'])), meshify_channelnames)
    this_devices = group_by_company(this_devices)

    for comp in this_devices:
        local_tz = get_localzone()
        now_t = time()
        now_dt = datetime.utcfromtimestamp(now_t)
        now = local_tz.localize(now_dt)
        filename_datestring = datetime.now().strftime("%Y%m%d")

        workbook = xlsxwriter.Workbook("/tmp/{}_{}_{}.xlsx".format(device_type, comp, filename_datestring))
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 20)

        bold = workbook.add_format({'bold': True})
        red = workbook.add_format({'font_color': 'red'})

        worksheet.write(0, 0, "Well Name", bold)
        for i in range(0, len(channel_config_list)):
            worksheet.write(0, i+1, channel_config_list[i]['vanity_name'], bold)

        sorted_company_devices = sorted(this_devices[comp], key=lambda x: x['vanityName'])
        for j in range(0, len(sorted_company_devices)):
            dev = sorted_company_devices[j]
            worksheet.write(j+1, 0, dev['vanityName'])
            for k in range(0, len(meshify_channelnames)):
                v = meshify_channelnames[k]
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
        s3.Object(BUCKET_NAME, 'created_reports/{}_{}_{}.xlsx'.format(device_type, comp, filename_datestring)).put(Body=open('/tmp/{}_{}_{}.xlsx'.format(device_type, comp, filename_datestring), 'rb'))

        try:
            email_to = to_list[comp]
        except KeyError:
            logger.error("No recipients for that company({})!".format(comp))
            continue
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(open("/tmp/{}_{}_{}.xlsx".format(device_type, comp, filename_datestring), "rb").read())
        encoders.encode_base64(attachment)

        now = datetime.now()
        datestr = now.strftime("%a %b %d, %Y")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "{} Daily {} Report for {}".format(comp, device_type.upper(), datestr)
        msg['From'] = "alerts@henry-pump.com"
        msg['To'] = ", ".join(email_to)

        filename = "{} {}.xlsx".format(comp, datestr)
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)

        msg.attach(attachment)

        messages.append(msg)

    return messages


def lambda_handler(event, context):
    """Handle the lambda function call."""
    device_type_list = get_s3_device_types()
    to_lists = list(map(lambda x: read_s3_tofiles(x), device_type_list))
    channel_configs = list(map(lambda x: read_s3_device_config(x), device_type_list))

    for i in range(0, len(device_type_list)):
        emails = prep_emails(device_type_list[i], channel_configs[i], to_lists[i])
        for email in emails:
            send_ses_email(email)
            logger.info("Sent email for {} to {}".format(device_type_list[i], email['To']))
