"""Read a CSV file of channels and post them to Meshify via the API."""

import csv
import meshify
import sys


def main(csv_file, devicetype):
    """Main function."""
    csvfile = open(csv_file, 'rU')
    reader = csv.DictReader(csvfile, dialect=csv.excel)

    channels = []
    idx = 0
    for x in reader:
        channels.append(x)
        channels[idx]["fromMe"] = False
        channels[idx]["regex"] = ""
        channels[idx]["regexErrMsg"] = ""
        channels[idx]["dataType"] = int(channels[idx]["dataType"])
        channels[idx]["deviceTypeId"] = int(channels[idx]["deviceTypeId"])
        channels[idx]["channelType"] = int(channels[idx]["channelType"])
        channels[idx]["io"] = bool(channels[idx]["io"])
        idx += 1

    try:
        this_devicetype = meshify.find_by_name(devicetype, meshify.query_meshify_api("devicetypes"))
        for c in channels:
            print(meshify.post_meshify_api("devicetypes/{}/channels".format(this_devicetype['id']), c))
    except KeyError:
        print("Could not find key {}".format(devicetype))


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print("Syntax is python postChannels.py <filepath.csv> <devicetype name>")
