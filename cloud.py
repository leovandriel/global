
from datetime import datetime
import json
import base64
from urllib import request, parse

account_sid = '..'
service_sid = '..'
auth_token = '..'
recipient_phone = '+1..'
appointment_stamp = '2021-00-00T00:00'

def parse_date(stamp):
    return datetime.strptime(stamp, '%Y-%m-%dT%H:%M')

def send_text(text):
    params = {
        'To': recipient_phone,
        'MessagingServiceSid': service_sid,
        'Body': text,
    }
    data = parse.urlencode(params).encode()
    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
    req = request.Request(url, data=data)
    auth = base64.b64encode(f'{account_sid}:{auth_token}'.encode('utf-8')).decode()
    req.add_header('Authorization', f'Basic {auth}')
    request.urlopen(req)

def fetch_soonest():
    url = 'https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=1&locationId=5446&minimum=1'
    with request.urlopen(url) as response:
        result = json.loads(response.read())
        stamp = result[0]['startTimestamp']
        date = parse_date(stamp)
        return date

def poll_soonest():
    soonest = fetch_soonest()
    appointment = parse_date(appointment_stamp)
    diff = appointment - soonest
    if diff.days > 0:
        message = f'found earlier appointment! {diff.days} days earlier, on {soonest}'
        print(message)
        send_text(message)

def handle(request):
    poll_soonest()
    return 'OK'
