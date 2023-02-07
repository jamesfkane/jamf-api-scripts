#!/opt/relocatable_python/bin/python3
# -*- coding: utf-8 -*-

"""
Lifted heavily from https://github.com/mikemackintosh/py-keysword - converted to gather Activation Lock Bypass Codes 
and add multi-device searching using the -csv argument. CSV must contain a single column, with no header, of serial numbers.
"""

import requests
from http.cookiejar import CookieJar
import argparse
import csv
from datetime import datetime
from xml.dom.minidom import parseString
import auth.creds
from auth.bearer_auth import get_token

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
getComputerID
-------------
Converts a computer name to a computer ID using the JAMF API
  :param name string
  :return id string
"""

def getComputerID(name):
    resp = requests.get("https://{}/JSSResource/computers/name/{}".format(JAMF_HOST, name), headers=headers)

    # TODO: add error checking here
    return resp.json()["computer"]["general"]["id"]


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
Connects to the JAMF JSS API and extracts the activation lock bypass code for the provided device
  :param id string
  :param name string
  :param file csv
"""
def main(id, name, file):
    def get_today():
        return datetime.now().strftime("%Y%m%d-%H.%M.%S")

    filename = "%s_%s.%s" % (get_today() , "activation_lock_bypass_codes_complete","csv")

    """ Create the cookie jar and session for requests """
    jar = CookieJar()
    s = requests.Session()
    s.cookies = jar

    """ Get the computer id if a hostname was provided """
    if len(name) > 0:
        id = getComputerID(name)

    if len(file) > 0:
        with open(file, 'r', newline='', encoding='utf-8-sig') as infile, open(filename, 'w', newline='', encoding='utf-8-sig') as outfile:
            serialnumber = []
            #csv_reader = csv.reader(infile)
            csv_reader = csv.DictReader(infile)
            for row in csv_reader:
                serialnumber.append(row['Serial Number'])
            CSVHEADERS = [ 'serialnumber', 'activation lock bypass code' ]
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
                data = "&ajaxAction=AJAX_ACTION_READ_BYPASS_CODE&session-token={}".format(session_token)
                resp = s.post('https://{}/computers.ajax?id={}&o=r&v=management'.format(JAMF_HOST, computer_id), data="{}".format(data), cookies=jar, headers={
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
                e = parseString(resp.content)
                if str(e.getElementsByTagName("userBasedCode")[0].childNodes) != "[]":
                    for n in e.getElementsByTagName("userBasedCode")[0].childNodes:
                        if n.nodeType == n.TEXT_NODE:
                            csv_writer.writerow([serial, n.data])
                            #print(n.data)
                else:
                    csv_writer.writerow([serial, 'Not available'])
    else:
        """ Get the session token """
        session_token = getSessionToken(s, jar, id)
        if session_token is None or len(session_token) == 0:
            print("Unable to find session token")
            exit()
        """ Make the request against the computers.ajax endpoint """
        data = "&ajaxAction=AJAX_ACTION_READ_BYPASS_CODE&session-token={}".format(session_token)
        resp = s.post('https://{}/computers.ajax?id={}&o=r&v=management'.format(JAMF_HOST, id), data="{}".format(data), cookies=jar, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Origin": 'https://{}'.format(JAMF_HOST),
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Content-Length": "{}".format(len(data)),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",
            "Referer": "https://{}/legacy/computers.html?id={}&o=r".format(JAMF_HOST, id)
            })
        # TODO: add error checking here
        e = parseString(resp.content)
        if len(e.getElementsByTagName("userBasedCode")) > 0:
            for n in e.getElementsByTagName("userBasedCode")[0].childNodes:
                if n.nodeType == n.TEXT_NODE:
                    print(n.data)
                    return
        print("Unable to find activation lock bypass code")


""" main """
if __name__ == "__main__":

    """ Create Argparser """
    parser = argparse.ArgumentParser(prog='activation-lock')
    parser.add_argument('-id', action="store", default="", dest="id")
    parser.add_argument('-name', action="store", default="", dest="name")
    parser.add_argument('-csv', dest="file")
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__VERSION__))
    results = parser.parse_args()

    """ Quick validation of arguments """
    if len(results.id) == 0 and len(results.name) == 0 and len(results.file) == 0:
        print("Please provide a computer id with -id, computer name with -name, or csv of computer id(s)")
        exit()

    elif len(results.id) != 0 and len(results.name) != 0:
        print("Please provide only one computer id with -id or with -name, but not both")
        exit()

    if len(JAMF_USERNAME) == 0 \
            or len(JAMF_USERNAME) == 0 \
            or len(JAMF_HOST) == 0:
        print("Please set your environment variables appropriately")
        exit()

    """ run main """
    main(results.id, results.name, results.file)
