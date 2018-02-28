# POCloud Report Generators

Developed by Patrick McDonagh @patrickjmcd, Henry pump

## Setup

System variables must be set up for the script to run. Add the following lines to /etc/environment
```
SMTP_EMAIL="<yourSMTPemailAddress>"
SMTP_PASSWORD="<yourSMTPpassword>"
MESHIFY_USERNAME="<yourMeshifyUsername>"
MESHIFY_PASSWORD="<yourMeshifyPassword>"
```

Create a "files" in the script's directory.

### Install Python Modules

```
pip install xlsxwriter
```

## Configuration Files

The script relies heavily on configuration files based on the Meshify devicetype. To configure a device, create a file
named <devicetype>_channels.json file. The file should hold a JSON list.

### Example Configuration File

```
# testdevice_channels.json

[
    {
    "meshify_name": "yesterday_volume",
    "vanity_name": "Yesteday Volume"
    },
    {
    "meshify_name": "volume_flow",
    "vanity_name": "Flow Rate"
    },
    ...
]
```

## Recipients File

In order to send emails containing the reports, configure a recipients json file named <devicetype>_to.json. The
file should hold a JSON object.

### Example Recipients File

```
# testdevice_to.json

{
  "Company 1 Name": [
    "email1@company.com",
    "email2@company.com"
  ],
  "Company 2 Name": [
    "email3@company2.com",
    "email4@company2.com"
  ],
  ...
}
```

## Running the script

```
usage: reports_xlsx.py [-h] [-s] [-p CONFIG_PATH] [-o OUTPUT_PATH] deviceType

positional arguments:
  deviceType            Meshify device type

optional arguments:
  -h, --help            show this help message and exit
  -s, --send            Send emails to everyone in the _to.json file
  -p CONFIG_PATH, --config-path CONFIG_PATH
                        The folder path that holds the configuration files
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        The folder path that holds the output files
```

## Configuring the script to be run via crontab

Open the crontab file with `crontab -e`.

Add the following contents:
```
00 07 * * * /usr/bin/python3 /home/ubuntu/POCloud-Scraper/reports_xlsx.py advvfdipp --send
01 07 * * * /usr/bin/python3 /home/ubuntu/POCloud-Scraper/reports_xlsx.py ipp --send
02 07 * * * /usr/bin/python3 /home/ubuntu/POCloud-Scraper/reports_xlsx.py abbflow --send
```


# POCloud-Scraper
Scrape production data from POCloud to push to accounting servers

## Setup
System variables must be set up for the script to run. Add the following lines to /etc/environment
```
HP_SQL_USER="<yourSQLusername>"
HP_SQL_PASSWORD="<yourSQLpassword>"
HP_SQL_SERVER="<yourSQLserverAddress>"
MESHIFY_USERNAME="<yourMeshifyUsername>"
MESHIFY_PASSWORD="<yourMeshifyPassword>"
```

## Usage
It is useful to run the script and store the output in a log file.

## Test Mode
The script has a test mode which will only retrieve the data. Test mode will not write date to the database.

To run the script in test mode:
```
python3 henryPetroleumMeshifyAPI.pt True >> output.log
```

## Normal Mode
In normal mode, the data will be grabbed from the Meshify API and inserted into the Production database.

To run the script:
```
python3 henryPetroleumMeshifyAPI.pt >> output.log
```
