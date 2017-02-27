# POCloud-Scraper
Scrape production data from POCloud to push to accounting servers

# Setup
System variables must be set up for the script to run. Add the following lines to /etc/environment
```
HP_SQL_USER="<yourSQLusername>"
HP_SQL_PASSWORD="<yourSQLpassword>"
HP_SQL_SERVER="<yourSQLserverAddress>"
MESHIFY_USERNAME="<yourMeshifyUsername>"
MESHIFY_PASSWORD="<yourMeshifyPassword>"
```

# Usage
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
