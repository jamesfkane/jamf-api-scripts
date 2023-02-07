#!/opt/relocatable_python/bin/python3

## This is template for the credential file for all scripts contained in this folder.
##
## In jamfAPI replace AUTH with the basic authorization base64-encoded string.
##
## In jamfProAPI replace JAMF_API_USERNAME and JAMF_API_PASSWORD with a Jamf Pro
## local account username and password that has appropriate access.
##
## Once you've made changes, save the file as "credentials.py" so it won't be pushed
## back to the git repository (it's in the .gitignore) and so it's correctly called
## in scripts.

jamfAPI = {
    'Accept': 'application/json',
    'Content-Type': 'application/xml',
    'Authorization': 'Basic AUTH'
}

jamfProAPI = ('JAMF_API_USERNAME', 'JAMF_API_PASSWORD')