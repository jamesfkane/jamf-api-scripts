# jamf-api-scripts

## get-activation-lock-bypass-code

Scrapes the Jamf console for activation lock bypass codes. Single devices can be pulled used the arguments -name (computer name), -id (device id). Multiple devices can be pulled using -csv (serial numbers).

## get-prestage-serialnumbers

Gets serial numbers assigned to a PreStage Enrollment using the PreStage Enrollment id.

## get-recovery-lock-password

Gets recovery lock passwords for devices by csv (serial numbers).

## os-update

Sends MDM OS update command to devices by csv (serial numbers). Unable to get major OS updates to work, API request body needs to by modified.

## recovery-lock

Lifted heavily from https://github.com/shbedev/jamf-recovery-lock, which should be used instead.

## self-heal

Sends a Jamf binary self-heal to devices by csv (serial numbers).
