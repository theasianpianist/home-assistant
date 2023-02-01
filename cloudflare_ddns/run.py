#!/usr/bin/with-contenv python3

import json
import http.client
import logging
import sys
import urllib.request

from time import sleep

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger("DNSUpdater")

class DNSUpdater:

    def __init__(self, config_file):
        self.load_config(config_file)
        self._headers = None
        self.public_ip = None
        self.ip_changed = False
        self.update_domains = []

    def load_config(self, file):
        with open(file) as f:
            config = json.load(f)

        for key, value in config.items():
            setattr(self, key, value)

    def check_public_ip(self):
        new_ip = urllib.request.urlopen('https://v4.ident.me').read().decode('utf8')
        if new_ip == self.public_ip:
            self.ip_changed = False
        else:
            self.ip_changed = True
            self.public_ip = new_ip
        logger.info(f"IP is {self.public_ip}, changed is {self.ip_changed}")

    @property
    def headers(self):
        if not getattr(self, "_headers", False):
            self._headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
                }
        return self._headers
    def gen_payload(self, domain, proxy):
        payload_dict = {
            "type": "A",
            "content": self.public_ip,
            "name": domain,
            "proxied": proxy,
            "ttl": 300
        }
        return json.dumps(payload_dict)

    def update_dns_record(self, domain, dns_id, proxy):
        endpoint = f"/client/v4/zones/{self.zone_id}/dns_records/{dns_id}"
        payload = self.gen_payload(domain, proxy)
        conn.request("PUT", endpoint, payload, headers=self.headers)

        res = conn.getresponse()
        data = res.read()

        result = json.loads(data.decode("utf-8"))
        if not result["success"]:
            logger.error(f"Error updating DNS record for {domain}")
            logger.debug(result)
        else:
            logger.info(f"Successfully updated DNS record for {domain}")

    def create_dns_record(self, domain, proxy):
        endpoint = f"/client/v4/zones/{self.zone_id}/dns_records"
        payload = self.gen_payload(domain, proxy)
        self.conn.request("POST", endpoint, payload, headers=self.headers)

        res = self.conn.getresponse()
        data = res.read()

        result = json.loads(data.decode("utf-8"))
        if not result["success"]:
            logger.error(f"Error creating DNS record for {domain}")
            logger.debug(result)
        else:
            logger.info(f"Successfully created DNS record for {domain}")

    def process_domain_updates(self):
        for domain, dns_id, proxy in self.update_domains:
            if dns_id:
                logger.info(f"Updating DNS record for {domain}")
                self.update_dns_record(domain, dns_id, proxy)
            else:
                logger.info(f"Creating DNS record for {domain}")
                self.create_dns_record(domain, proxy)

    def process_domain_list(self, domains, proxy):
        for domain in domains:
            dns_record = self.get_dns_record(domain)
            if not dns_record:
                self.update_domains.append((domain, None, proxy))
            elif dns_record["content"] != self.public_ip:
                self.update_domains.append((domain, dns_record["id"], proxy))
            else:
                logger.info(f"Skipping update for {domain}")
    

    def check_dns_update_needed(self):
        self.process_domain_list(self.domains, False)
        self.process_domain_list(self.proxy_domains, True)

    def get_dns_record(self, domain):
        endpoint = f"/client/v4/zones/{self.zone_id}/dns_records?type=A&name={domain}"
        self.conn.request("GET", endpoint, headers=self.headers)
        res = self.conn.getresponse()
        data = res.read()

        
        result = json.loads(data.decode("utf-8"))["result"]

        if result:
            return result[0]

        return None

    def run(self):
        logger.info("Starting DNS update service")
        while True:
            self.check_public_ip()
            if self.ip_changed:
                self.conn = http.client.HTTPSConnection("api.cloudflare.com")
                self.check_dns_update_needed()
                self.process_domain_updates()
                self.conn.close()
                logger.info("Connection closed")
            logger.info(f"Sleeping for {self.update_interval} seconds")
            sleep(self.update_interval)


updater = DNSUpdater("/data/options.json")
updater.run()
