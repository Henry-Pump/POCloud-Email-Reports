# POCloud Email Report Generator

Send daily reports of Meshify Data via AWS functions.

## Using the Generator

Reports will be generated on a schedule by AWS Lambda, a serverless, event-driven computing platform. Each report will contain all devices of a specified type that the user has been granted access to in Meshify. If a user has access to multiple device types and is configured to receive reports for multiple device types, the user will receive one report for each device type. The Lambda function will mark in red any data that is more than 24 hours old in order to denote devices that have not updated. Values reported are the latest values at the time of report generation (12:00 GMT / 07:00 CST by default).

If you would like to run the reports locally without the AWS Lambda Function, refer to [README-local.md](README-local.md)

## Setting it up yourself

### Prerequisites

- Amazon Web Services account
- Sufficient knowledge of S3, Lambda, and SES within Amazon Web Services
- Python 3

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

### Preparing the Lambda function

1. Clone this repository and open it

    ```Shell
    git clone https://github.com/Henry-Pump/POCloud-Email-Reports.git
    cd POCloud-Email-Reports
    ```

2. Setup a Python Virtual environment and activate the environment

    ```Shell
    python3 -m venv env
    source env/bin/activate
    ```

3. Install necessary python packages in the virtual environment.

    ```Shell
    pip install requests tzlocal xlsxwriter
    ```

4. Create a folder for deploying the lambda function

    ```Shell
    mkdir -p deploy```

5. To build the lambda file automatically, allow execution permissions on the build script and execute it. To build manually, examine the [build_lambda.sh](https://github.com/Henry-Pump/POCloud-Email-Reports/blob/master/build_lambda.sh) file and execute commands at your own peril.

    ```Shell
    chmod +x build_lambda.sh
    ./build_lambda.sh
    ```

    You should now have a file named lambda.zip in the main directory of the repo. This is the file to upload into your Lambda function.

### Creating the Lambda Function in AWS

This section will show you how to configure the Lambda function within AWS. It assumes a strong knowledge of AWS platforms.

1. Sign in to your AWS Console and open the Lambda dashboard.
2. Click "Create function".
3. Select "Author from scratch" and fill in the info
    - Name: give your function a name
    - Runtime: select Python 3.6
    - Role: either choose an existing role with S3, SES, and Lambda permissions or create one.
    - Existing role: select the existing or created role name.
4. Click "Create Function".
5. In the function code section, set the following:
    - Code entry type: "Upload a .ZIP file"
    - Runtime: Python 3.6
    - Handler: reports_s3_xlsx.lambda_handler
    - Function package: upload the created lambda.zip
6. In Environment Variables, two variables are needed:
    - MESHIFY_PASSWORD: your meshify password
    - MESHIFY_USERNAME: your meshify username
7. Drag a CloudWatch Events trigger in the Designer to the trigger section of your function.
8. Configure a new CloudWatch event with the schedule expression:

    ```cron(0 12 * * ? *)```

    This will schedule the event to be triggered at 12:00 PM GMT (7:00 AM CST) every day of the week.
9. Save and test your function.

## Contributors

- [Patrick McDonagh](@patrickjmcd) - Owner
