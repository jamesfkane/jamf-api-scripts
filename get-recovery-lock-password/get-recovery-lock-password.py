#!/opt/relocatable_python/bin/python3


## this script will take the serial number from recovery_lock_serialnumber.csv and using an API call
## to Jamf retrieve the device ID and get the recovery lock password, then output whether the
## command was successful and the recovery lock password to a CSV (%Y%m%d-%H%M%S_recovery_password_serialnumber_complete.csv)

import argparse
import csv
from datetime import datetime
import requests
import credentials

parser = argparse.ArgumentParser(prog='activation-lock')
parser.add_argument('-csv', dest="file")
results = parser.parse_args()

api_url_base = "https://jamf.domain.com:8443/api/v1"
get_computer = "{}/computers-inventory/?section=GENERAL&page=0&page-size=100&sort=id%3Aasc&filter=hardware.serialNumber==".format(api_url_base)
get_recovery_lock_password = "/view-recovery-lock-password"

def authenticate(api_url_base):
    auth_url = "{}/auth/token".format(api_url_base)
    response = session.post(auth_url)
    response.raise_for_status()
    auth_response = response.json()
    token = auth_response["token"]
    return token

def get_today():
    return datetime.now().strftime("%Y%m%d-%H.%M.%S")

filename = "%s_%s.%s" % (get_today() , "recovery_password_serialnumber_complete","csv")

with open(results.file, 'r') as infile, open(filename, 'w') as outfile:
    CSVHEADERS = [ 'serialnumber', 'recovery lock password' ]
    session = requests.Session()
    session.auth = credentials.jamfProAPI
    session.headers.update({"Accept": "application/json"})
    token = authenticate(api_url_base)
    # Need to clear out authentication headers and use token only.
    session.auth = ()
    session.headers.update({"Authorization": "Bearer {}".format(token)})
    csv_writer = csv.writer(outfile)
    csv_reader = csv.DictReader(infile, delimiter=',')
    csv_writer.writerow(CSVHEADERS)
    for lines in csv_reader:
        try:
            response = session.get(get_computer+lines['Serial Number']).json()
            if response['totalCount'] == 0:
                csv_writer.writerow([lines['Serial Number'], 'No associated Device ID'])
            else:
                for i in response['results']:
                    response = session.get(api_url_base+"/computers-inventory/"+i['id']+get_recovery_lock_password)
                    if response.status_code == 200:
                        data = response.json()
                        csv_writer.writerow([lines['Serial Number'], data['recoveryLockPassword']])
                    else:
                        csv_writer.writerow([lines['Serial Number'], 'X'])
        except Exception:
            continue