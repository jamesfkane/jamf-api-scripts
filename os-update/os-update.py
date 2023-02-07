#!/opt/relocatable_python/bin/python3

import csv
from datetime import datetime
import requests
import json
import credentials

api_url_base = "https://jamf.domain.com:8443/api/v1"
get_computer = "{}/computers-inventory?section=GENERAL&page=0&page-size=100&sort=id%3Aasc&filter=hardware.serialNumber==".format(api_url_base)
os_update = "{}/macos-managed-software-updates/send-updates".format(api_url_base)

def authenticate(api_url_base):
    auth_url = "{}/auth/token".format(api_url_base)
    response = session.post(auth_url)
    response.raise_for_status()
    auth_response = response.json()
    token = auth_response["token"]
    return token

def get_today():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

filename = "%s_%s.%s" % (get_today() , "osupdate_serialnumber_complete","csv")

with open('osupdate_serialnumber.csv', 'r') as infile, open(filename, 'w') as outfile:
    CSVHEADERS = [ 'serialnumber', 'api response' ]
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
            response = session.get(get_computer+lines['serialnumber']).json()
            for i in response['results']:
                session.headers.update({"Content-Type": "application/json"})
                payload = json.dumps({
                    "deviceIds": [ i['id'] ],
                    "maxDeferrals": 0,
                    "version": "12.4.0",
                    "skipVersionVerification": True,
                    "applyMajorUpdate": True,
                    "updateAction": "DOWNLOAD_AND_INSTALL",
                    "forceRestart": True
                    })
                response = session.post(os_update, data=payload)
            if response.status_code == 200:
                csv_writer.writerow([lines['serialnumber'], 'OK'])
            else:
                csv_writer.writerow([lines['serialnumber'], 'X'])
        except Exception:
            csv_writer.writerow([lines['serialnumber'], 'No associated device ID'])
            continue