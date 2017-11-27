#!/usr/bin/env python3

"""Parse-ATT-Data-SMS.py: Reads an AT&T Data SMS message, sends formatted data to Home-Assistant"""

__author__    = "Edward Boal"
__email__     = "ed.boal@edwork.org"
__version__   = "1.0"
__licence__   = "MIT"

import datetime
import json
from urllib.request import Request, urlopen
from urllib import parse
import re

## HASS Configuration
hass_url = 'https://home-assistant.foo.bar' ## No Trailing Slash Please
hass_api = 'foobar'

## Sample Message - for debugging without actual data
debug_message = """Next Bill Cycle: 12/20/18
             Group Data Usage [MB]: 9,124.32 of 10,690
             Usage By Device [MB]:
             1111[You]: 320.88
             2222: 0
             3333: 333.35
             4444: 1,697.09
             5555: 0
             Data Overage: 0
             May include rollover
             Messaging: 123 of Unlimited
             For detail usage go to att.com/myATT"""

try:
    ## If on Android, import the sl4a library and get the clipboard contacts.
    import sl4a
    droid = sl4a.Android()
    message = str(droid.getClipboard().result)
except:
    print('sl4a Library not found, are you running on the computer?')
    ## Since we are not likely on a phone, use the debug message
    message = debug_message

## Get time for posting when data was last gathered
now = datetime.datetime.now()

## List of users and their siffixes we wish to parse from the message
people = {"user1":"1111[You]", "user2":"2222", "user3":"3333", "user4":"4444", "user5":"5555"}

## Pull non-user-specific data from message
used_data = round(float((re.search((r"[\n\r].*\[MB\]:\s*([^\n\r]*)(?=\sof)"), message)).group(1).replace(',', '')), 2)
data_bucket = round(float((re.search((r"[\n\r].*of\s*([^\n\r]*)"), message)).group(1).replace(',', '')), 2)
data_date = str((re.search((r"\d{1,2}\/\d{1,2}\/\d{2}"), message)).group(0))

## Calculations
data_percent = str(round((((used_data / data_bucket) * 100)), 2))

## Create array of JSON strings for POSTing
http_generic_data =  [{"state": str(data_percent), "attributes": {"icon":"mdi:percent", "unit_of_measurement": "%", "friendly_name": "Percent of Used Data"}},
                     {"state": (str(used_data) + ' of ' + str(data_bucket)), "attributes": {"icon":"mdi:chart-donut", "unit_of_measurement": "MB", "friendly_name": "Used Data"}},
                     {"state": (str(now.month) + '/' + str(now.day) + '/' + (str(now.year)[2:])), "attributes": {"icon":"mdi:calendar-range", "unit_of_measurement": "", "friendly_name": "Last Updated"}},
                     {"state": str(data_date), "attributes": {"icon":"mdi:update", "unit_of_measurement": "", "friendly_name": "Billing Cycle End Date"}}]

## Variables used to cycle through sensor types
http_generic_types = ['percent_used', 'data_used', 'current_date', 'rollover_date']
http_generic_types_count = 0

## Loop through generic data and POST to HASS
for generic_data in http_generic_data:
    generic_attr = (http_generic_types[http_generic_types_count])
    http_generic_types_count += 1
    postme_data = json.dumps(generic_data).encode('utf8')
    hass_url_full = (hass_url + '/api/states/sensor.' + generic_attr + '_data_usage')
    req = Request(hass_url_full, data=postme_data)
    req.add_header('x-ha-access', hass_api)
    req.add_header('Content-Type', 'application/json')
    resp = urlopen(req)
    content = resp.read()

## Loop through user data and POST to HASS
for name in people:
    number = people[name]
    regex_query = r"[\n\r].*" + re.escape(number) + r":\s*([^\n\r]*)"
    regex_search = re.search(regex_query, message)
    data_used = regex_search.group(1)
    print(name + "\'s data usage: " + data_used + ' Megabytes')
    http_data = {"state": data_used, "attributes": {"icon":"mdi:cellphone-android", "unit_of_measurement": "MB", "friendly_name": ((name.title()) + '\'s Data Usage')}}
    parsed_http_data = json.dumps(http_data).encode('utf8')
    hass_url_full = (hass_url + '/api/states/sensor.' + name + '_data_usage')
    req = Request(hass_url_full, data=parsed_http_data)
    req.add_header('x-ha-access', hass_api)
    req.add_header('Content-Type', 'application/json')
    resp = urlopen(req)
    content = resp.read()

## A printout of the data to see in the console
print('You have used: ' + str(used_data) + ' of ' + str(data_bucket))
print('which is ' + str(data_percent) + '%')
print('Today is: ' + (str(now.month) + '/' + str(now.day) + '/' + (str(now.year)[2:])))
print('your date will roll over on: ' + data_date)
