#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lifted heavily from https://github.com/mikemackintosh/py-keysword - converted to gather device lock passcodes
using the -csv argument. CSV must contain a column of serial numbers with the header 'Serial Number'.
This was intended to make it easy to use an exported CSV from the JAMF console to feed into this script.
"""

import requests
from http.cookiejar import CookieJar
import argparse
import csv
from datetime import datetime
import auth.creds
from auth.bearer_auth import get_token
import json
from lxml import html

__VERSION__ = "1.0"

JAMF_HOST = auth.creds.instance_id
JAMF_USERNAME = auth.creds.username
JAMF_PASSWORD = auth.creds.password

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {get_token()}',
    'Content-Type': 'application/json',
}

"""
getSessionToken
-------------
Gets a session token from the legacy pages to get access to the ajax API
  :param s requests.Session
  :param jar cookie jar
  :param id
  :return token string
"""
def getSessionToken(s, jar, id):
    resp = s.post('https://{}/?failover'.format(JAMF_HOST), cookies=jar, data={'username':JAMF_USERNAME, 'password':JAMF_PASSWORD, 'resetUsername':''})
    if resp.status_code != 200:
        print("Look's like you failed to authenticate")
        exit(1)

    params = {"id": id, "o": "r", "v": "inventory"}
    resp = s.get('https://{}/legacy/computers.html'.format(JAMF_HOST), params=params, cookies=jar)
    if resp.status_code == 404:
        print("No device for that ID")
        exit()
    session_token = ""

    # TODO: add error checking here
    for line in resp.content.splitlines():
        linestr = str(line)
        if "session-token" in linestr:
            replaced = str(linestr.encode('utf-8')).replace('<', "").replace('>', "").replace('"', "").replace('\\', "").replace("'", "")
            return replaced.split('=')[-1]

"""
main
-------------
Connects to the JAMF JSS API and extracts the device lock passcode for the CSV provided devices
  :param file csv
"""
def main(file):
    def get_today():
        return datetime.now().strftime("%Y%m%d-%H.%M.%S")

    filename = "%s_%s.%s" % (get_today() , "device_lock_passcodes_complete","csv")

    """ Create the cookie jar and session for requests """
    jar = CookieJar()
    s = requests.Session()
    s.cookies = jar

    if file is not None and len(file) > 0:
        with open(file, 'r', newline='', encoding='utf-8-sig') as infile, open(filename, 'w', newline='', encoding='utf-8-sig') as outfile:
            serialnumber = []
            csv_reader = csv.DictReader(infile)
            for row in csv_reader:
                serialnumber.append(row['Serial Number'])
            CSVHEADERS = [ 'serialnumber', 'device lock passcode' ]
            csv_writer = csv.writer(outfile)
            csv_writer.writerow(CSVHEADERS)
            resp = requests.get("https://{}/JSSResource/computers/serialnumber/{}".format(JAMF_HOST, serialnumber[0]), headers=headers)
            id = resp.json()["computer"]["general"]["id"]
            session_token = getSessionToken(s, jar, id)
            if session_token is None or len(session_token) == 0:
                print("Unable to find session token")
                exit()
            for serial in serialnumber:
                resp = requests.get("https://{}/JSSResource/computers/serialnumber/{}".format(JAMF_HOST, serial), headers=headers)
                computer_id = resp.json()["computer"]["general"]["id"]
                """ Make the request against the computers.ajax endpoint """
                data = "&ajaxAction=AJAX_ACTION_LOAD_MANAGEMENT_HISTORY&session-token={}".format(session_token)
                resp = s.post('https://{}/computers.ajax?id={}&o=r&v=history'.format(JAMF_HOST, computer_id), data="{}".format(data), cookies=jar, headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": 'https://{}'.format(JAMF_HOST),
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "*/*",
                    "Content-Length": "{}".format(len(data)),
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",
                    "Referer": "https://{}/legacy/computers.html?id={}&o=r".format(JAMF_HOST, computer_id)
                    })
                # TODO: add error checking here
                json_data = json.loads(resp.content)
                response = json_data['aaData0']

                # Initialize a variable to store the info
                info = None

                # Iterate over all elements in the response
                for item in response:
                    # Check if the first element of the list is 'Lock Device'
                    if item[0] == 'Lock Device':
                        # The info is in the last element of the 'Lock Device' list
                        html_content = item[-1]

                        # Parse the HTML content
                        tree = html.fromstring(html_content)

                        # Find the divs with the class 'additionalInfo' and get its text
                        info_divs = tree.xpath('//div[@class="additionalInfo"]')

                        # Loop through the divs and store the text of the first one that contains a number
                        for div in info_divs:
                            # Check if the text is a number
                            if div.text.strip().isdigit():
                                # Store the number
                                info = div.text
                                break

                        # If the info was found, break the outer loop as well
                        if info is not None:
                            break

                # Check if the info was found
                if info is not None:
                    csv_writer.writerow([serial, info])
                    print("Device lock passcode for serial number: {} is {}".format(serial, info))
                else:
                    print("No device lock passcode found for serial number: {}".format(serial))

""" main """
if __name__ == "__main__":

    """ Create Argparser """
    parser = argparse.ArgumentParser(prog='device-lock')
    parser.add_argument('-csv', dest="file")
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__VERSION__))
    results = parser.parse_args()

    """ Quick validation of arguments """
    if len(results.file) == 0:
        print("Please provide the file path to a CSV with a single column of serial numbers, with the header 'Serial Number'")
        exit()

    if len(JAMF_USERNAME) == 0 \
            or len(JAMF_USERNAME) == 0 \
            or len(JAMF_HOST) == 0:
        print("Please set your environment variables appropriately")
        exit()

    """ run main """
    main(results.file)