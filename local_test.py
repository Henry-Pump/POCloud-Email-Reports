"""Run a test of the lambda function locally."""
import argparse
from reports_s3_xlsx import get_s3_device_types, read_s3_tofiles, read_s3_device_config, prep_emails, send_ses_email


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--send', action='store_true', help="Actually send the emails.")

    args = parser.parse_args()
    SEND_EMAIL = args.send

    device_type_list = get_s3_device_types()
    to_lists = list(map(lambda x: read_s3_tofiles(x), device_type_list))
    channel_configs = list(map(lambda x: read_s3_device_config(x), device_type_list))

    for i in range(0, len(device_type_list)):
        emails = prep_emails(device_type_list[i], channel_configs[i], to_lists[i])
        for email in emails:
            if SEND_EMAIL:
                send_ses_email(email)
                print("Sent email for {} to {}".format(device_type_list[i], email['To']))
            else:
                print("Would have sent email for {} to {}".format(device_type_list[i], email['To']))
