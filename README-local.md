# POCloud Local Report Generators

Developed by Patrick McDonagh @patrickjmcd, Henry pump

## Setup

System variables must be set up for the script to run. Add the following lines to /etc/environment

```Shell
MESHIFY_USERNAME="<yourMeshifyUsername>"
MESHIFY_PASSWORD="<yourMeshifyPassword>"
```

### Setup a Virtual Environment and Install Python Modules

```Shell
python3 -m venv env  # Creates the virtual environment in a folder ./env
source env/bin/activate  # activates the virtual environment
pip install xlsxwriter requests tzlocal meshify  # installs the python modules
```

### Preparing an S3 Bucket

This section will show you how to configure the S3 Bucket within AWS. It assumes a strong knowledge of AWS platforms.

1. Sign in to your AWS Console and open the S3 dashboard.
2. Create a bucket named "pocloud-email-reports". You may choose to name your bucket differently, but you must update the variable BUCKET_NAME within reports_s3_xlsx.py
3. Open the newly-created bucket and create 3 folders. These names cannot be changed without doing some serious hacking of the reports_s3_xlsx.py file.
    - channel_config
    - created_reports
    - to_files

### Populating Channel Configs

Populating channel config files tells the Lambda function which devices to prepare reports for and which channels to include data from. **Devices will not be recognized unless they have both a Channel Config file and a To file.**

1. Prepare a file named devicetype_channels.json where "devicetype" is the Meshify name for the devicetype.

    ```touch <devicetype>_channels.json```

2. In the text editor of your choice, develop a JSON **list of objects** that contains properties "meshify_name" and "vanity_name".

    ```JSON
    [
        {

            "meshify_name": "<channel name in meshify>",
            "vanity_name": "<vanity name for report header>"
        },

        {

            "meshify_name": "<another channel name in meshify>",
            "vanity_name": "<another vanity name for report header>"
        },

    ]
    ```

3. Upload this file to the "channel_config" folder in the S3 Bucket.

### Populating To Files

Populating To files tells the Lambda function which devices to prepare reports for and whom to send the reports for each company. **Devices will not be recognized unless they have both a Channel Config file and a To file.**

1. Prepare a file named devicetype_to.json where "devicetype" is the Meshify name for the devicetype.

    ```touch <devicetype>_to.json```

2. In the text editor of your choice, develop a JSON **object** that contains properties of the format below. CompanyA and CompanyB should be replaced by the full name of the company as recorded in Meshify.

    ```JSON
    {
      "CompanyA": [
        "person@email.com",
        "place@email.com"
      ],
      "CompanyB": [
        "person@email.com",
        "thing@email.com"
      ]
    }
    ```

3. Upload this file to the "to_files" folder in the S3 Bucket.

## Running the Script

As long as everything has been setup correctly, all it takes is running:

```Shell
python local_test.py
```

This performs a "dry-run" where it will generate the reports and print to the console the list of recipients, but it will not actually send the reports. The script can trigger the sending of reports by running:

```Shell
python local_test.py --send
```