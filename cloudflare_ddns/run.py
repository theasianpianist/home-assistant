#!/usr/bin/with-contenv python3

import json
import http.client
import urllib.request

def get_public_ip():
    public_ip = urllib.request.urlopen('https://v4.ident.me').read().decode('utf8')
    return public_ip

def update_dns_record(ip, api_token):

    conn = http.client.HTTPSConnection("api.cloudflare.com")

    payload = '{ \
                "comment": "Domain verification record", \
                "content": "{ip}", \
                "name": "{domain}", \
                "proxied": false, \
                "ttl": 3600 \
                }'

    headers = {
        'Content-Type': "application/json",
        'X-Auth-Email': api_token
        }

    conn.request("PUT", "/client/v4/zones/zone_identifier/dns_records/identifier", payload, headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8"))

def load_config(file):
    config = json.load(file)
    return config

print("Public IP is {}".format(get_public_ip()))
