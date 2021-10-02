
from datetime import datetime, timedelta
import hashlib
import json
import base64
import os
from urllib import request, parse, error

cloud_url = 'https://storage.googleapis.com'
twilio_url = 'https://api.twilio.com/2010-04-01/Accounts'
gov_url = 'https://ttp.cbp.dhs.gov'
wait_hours = 1
max_log = 100
max_stat = 1000
location_id = 5446 # SF
timezone_offset = -7 # PDT
date_format = '%Y-%m-%dT%H:%M'

def parse_date(stamp):
    return datetime.strptime(stamp, date_format)

def to_stamp(date):
    return date.strftime(date_format)

def now_date():
    return datetime.utcnow() + timedelta(hours=timezone_offset)

def get_env(key):
    return os.environ.get(key, None)

def hash_keys(keys):
    key = get_env('hash_salt').join(('',) + keys + ('',))
    return hashlib.sha256(key.encode()).hexdigest()

def string_dict(dict):
    return ' '.join(f'{key}:{dict[key]}' for key in dict)

def fetch_data(keys, default):
    name = hash_keys(keys)
    url = '/'.join((cloud_url, get_env('cloud_path'), name))
    req = request.Request(url)
    try:
        res = request.urlopen(req)
    except error.HTTPError as e:
        if e.code == 404:
            return default
        raise
    return json.loads(res.read())

def store_data(value, keys):
    name = hash_keys(keys)
    headers = {'Content-type': 'application/json', 'Cache-Control': 'private, max-age=0'}
    url = '/'.join((cloud_url, get_env('cloud_path'), name))
    data = json.dumps(value).encode()
    req = request.Request(url, method='PUT', data=data, headers=headers)
    request.urlopen(req)

def send_text(phone, body):
    params = {
        'To': phone,
        'MessagingServiceSid': get_env('service_sid'),
        'Body': body,
    }
    data = parse.urlencode(params).encode()
    url = '/'.join((twilio_url, get_env('account_sid'), 'Messages.json'))
    req = request.Request(url, data=data)
    auth = base64.b64encode(':'.join((get_env('account_sid'), get_env('auth_token'))).encode()).decode()
    req.add_header('Authorization', f'Basic {auth}')
    request.urlopen(req)

def notify_phone(phone, body):
    last = fetch_data(('unique', phone, body), None)
    if last:
        date = parse_date(last['date'])
        if date > now_date() - timedelta(hours = wait_hours):
            return
    store_data({
        'date': to_stamp(now_date()),
    }, ('unique', phone, body))
    send_text(phone, body)
    add_log('send', { 'phone': phone, 'body': body })
    increment_recipient(phone)

def notify_all(soonest):
    recipients = fetch_data(('recipients',), {})
    on = str(soonest).replace(' ', ' at ')
    for phone in recipients:
        recipient = recipients[phone]
        name = recipient['name']
        phone = recipient['phone']
        date = parse_date(recipient['stamp'])
        if soonest < date:
            body = f'{name}, I found an appointment on {on}. Visit {gov_url}/dashboard to book.'
            notify_phone(phone, body)

def add_log(type, item):
    logs = fetch_data(('logs',), [])
    logs.append({ 'type': type, 'date': to_stamp(now_date()), **item })
    store_data(logs[-max_log:], ('logs',))

def print_logs():
    logs = fetch_data(('logs',), [])
    for item in logs:
        print(string_dict(item))

def add_stat(soonest):
    stats = fetch_data(('stats',), [])
    stamp = to_stamp(soonest)
    if len(stats) > 0:
        if stats[-1][1] == stamp:
            return
        minutes = round((now_date() - parse_date(stats[-1][0])).total_seconds() / 60)
        stats[-1].append(minutes)
    days = round((soonest - now_date()).total_seconds() / 86400)
    stats.append([to_stamp(now_date()), stamp, days])
    store_data(stats[-max_stat:], ('stats',))

def print_stats():
    stats = fetch_data(('stats',), [])
    for item in stats:
        print(','.join(str(i) for i in item))

def add_recipient(phone, name, stamp):
    recipients = fetch_data(('recipients',), {})
    recipients[phone] = {
        'phone': phone,
        'name': name,
        'stamp': stamp,
        'count': 0,
    }
    store_data(recipients, ('recipients',))
    add_log('add', { 'phone': phone, 'name': name, 'stamp': stamp })

def remove_recipient(phone):
    recipients = fetch_data(('recipients',), {})
    recipients.pop(phone, None)
    store_data(recipients, ('recipients',))
    add_log('remove', { 'phone': phone })

def increment_recipient(phone):
    recipients = fetch_data(('recipients',), {})
    recipients[phone]['count'] += 1
    store_data(recipients, ('recipients',))

def print_recipients():
    recipients = fetch_data(('recipients',), {})
    for phone in recipients:
        print(string_dict(recipients[phone]))

def fetch_soonest():
    url = f'{gov_url}/schedulerapi/slots?orderBy=soonest&limit=1&locationId={location_id}&minimum=1'
    res = request.urlopen(url)
    result = json.loads(res.read())
    stamp = result[0]['startTimestamp']
    date = parse_date(stamp)
    return date

def handle(request):
    soonest = fetch_soonest()
    notify_all(soonest)
    add_stat(soonest)
    return 'OK'

if __name__ == '__main__':
    # add_recipient('+1..', '..', '2021-10-15T09:00')
    # remove_recipient('+1..')
    print('[recipients]')
    print_recipients()
    print('[logs]')
    print_logs()
    print('[stats]')
    print_stats()
    # handle({})
