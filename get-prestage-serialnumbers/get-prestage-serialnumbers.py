#!/opt/relocatable_python/bin/python3

import argparse
import csv
import requests
from datetime import datetime
import credentials

parser = argparse.ArgumentParser()
parser.add_argument("-id", "--prestageid", type=str, required=True, action="store", help='input prestage enrollment ID')
args = parser.parse_args()

prestageID = args.prestageid

api_url_base = "https://jamf.domain.com:8443/api"
get_prestage_scope = "{}/v2/computer-prestages/".format(api_url_base)

def get_today():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

filename = "%s_%s.%s" % (get_today() , "prestage_serialnumbers","csv")

def authenticate(api_url_base):
    auth_url = "{}/v1/auth/token".format(api_url_base)
    response = session.post(auth_url)
    response.raise_for_status()
    auth_response = response.json()
    token = auth_response["token"]
    return token

with open(filename, 'w') as outfile:
    CSVHEADERS = [ 'serialnumber' ]
    session = requests.Session()
    session.auth = credentials.jamfProAPI
    session.headers.update({"Accept": "application/json"})
    token = authenticate(api_url_base)
    # Need to clear out authentication headers and use token only.
    session.auth = ()
    session.headers.update({"Authorization": "Bearer {}".format(token)})
    csv_writer = csv.writer(outfile)
    csv_writer.writerow(CSVHEADERS)
    session.headers.update({"Content-Type": "application/json"})
    response = session.get(get_prestage_scope+prestageID+"/scope").json()
    for r in response['assignments']:
        csv_writer.writerow([r['serialNumber']])