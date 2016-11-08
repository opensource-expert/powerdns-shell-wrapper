#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:

"""
Command line wrapper to manage pdns zone (usable with salt)

Usage:
 ./pdns_zone.py create ZONE [JSON_EXTRA]
 ./pdns_zone.py delete ZONES ...
 ./pdns_zone.py missing ZONE
 ./pdns_zone.py list
 ./pdns_zone.py dump ZONE
 ./pdns_zone.py json ZONE
 ./pdns_zone.py json_records ZONE
 ./pdns_zone.py (enable|disable|update) ZONE
 ./pdns_zone.py add_slave_zone ZONE MASTER_IP
 ./pdns_zone.py gen_template TEMPLATE ZONE [JSON_EXTRA]
 ./pdns_zone.py show_SOA ZONE
 ./pdns_zone.py api METHOD URL [JSON_EXTRA]
 ./pdns_zone.py (help | -h | --help)

Options:
  JSON_EXTRA    is a JSON string passed to gen_template
  ZONE          is a tdl domain name

Note:
  json_records dont keep NS records
"""
# See API for pdns 3.4: https://doc.powerdns.com/3/httpapi/README/


# empty line above required ^^
from __future__ import print_function
# docopt: pip install --user docopt
from docopt import docopt
import re
import requests
import sys
import json

import gen_template

class pdns_zone:
    def __init__(self, key=None):
        # reflect your powerdns config here
        self.url_base = "http://127.0.0.1:8081"
        # api key
        self.key = key

    def read_apikey(self, pdns_conf=None):
        ## fetch from local config
        #key=$(sed -n -e '/experimental-api-key=/ s///p' /etc/powerdns/pdns.conf)
        if pdns_conf == None:
            pdns_conf = '/etc/powerdns/pdns.conf'
        f = open(pdns_conf)
        regxep = r'experimental-api-key=(.+)'
        for l in f:
            m = re.search(regxep, l)
            if m:
                self.key= m.groups()[0]

                break

        f.close()
        return self.key

    def exec_pdns_api(self, action, url, json_data=None, text=False):

        # remove double: //
        url = url.replace(r'//', '/')
        # remove extra ^/
        if url[0] == '/':
            url = url[1:]

        call_url = self.url_base + '/' + url

        headers = {'X-API-Key': self.key} 

        if action == 'GET':
            r = requests.get(call_url, headers=headers)
        elif action == 'POST':
            r = requests.post(call_url, data=json_data, headers=headers)
        elif action == 'PATCH':
            r = requests.patch(call_url, data=json_data, headers=headers)
        elif action == 'DELETE':
            r = requests.delete(call_url, headers=headers)
        else:
            raise ValueError('action unknown: %s' % action)

        if r.ok:
            if action == 'GET':
                if text:
                    return r.text
                else:
                    return r.json()
            else:
                return r
        else:
            raise ValueError('url returned an error: %s:\n%s\n---\n%s' % (call_url, r.headers, r.text))

    def list_zones(self):
        l = self.exec_pdns_api('GET', '/servers/localhost/zones')
        for z in l:
            zone_info = self.get_json_zone(z['name'])
            txt = ''

            # look if SOA record is disabled or not
            try:
                # happen on slave zone not yet fetched
                disabled = self.get_SOA_from_json(zone_info)['disabled']
            except IndexError as e:
                txt = " (failed SOA lookup)"
                disabled = False

            if disabled:
                txt = ' \033[31;1m disabled\033[0m'

            print('%s%s' % (z['name'], txt))

    def dump_zone(self, zone):
        print(self.exec_pdns_api('GET', '/servers/localhost/zones/%s/export' % zone, text=True))

    def get_SOA_from_json(self, zone_info):
        return list(filter(lambda r : r['type'] == 'SOA', zone_info['records']))[0]

    def get_json_zone(self, zone):
        return self.exec_pdns_api('GET', '/servers/localhost/zones/%s' % zone)

    def dump_json(self, zone):
        print(self.exec_pdns_api('GET', '/servers/localhost/zones/%s' % zone, text=True))

    def create_zone(self, zone, json_data=None):
        if not isinstance(zone, (str, unicode)):
            raise ValueError("only string")

        gen = gen_template.gen_template()
        gen.load_config()
        zone_data = gen.generate(zone, json_data)

        r = self.exec_pdns_api('POST', '/servers/localhost/zones', json_data=zone_data)

        return {'status_code' : r.status_code, 'json_data' : zone_data }

    def delete_zone(self, zone):
        try:
            r = self.exec_pdns_api('DELETE', '/servers/localhost/zones/%s' % zone)
        except ValueError as e:
            print(e)
            return 1

        return 0

    def test_missing_zone(self, zone):
        try:
            r = self.exec_pdns_api('GET', '/servers/localhost/zones/%s' % zone)
        except ValueError as e:
            r = {}

        if r.get('name') == zone:
            print('PRESENT')
            return 1
        else:
            print('MISSING')
            return 0

    def add_slave_zone(self, zone, json_data=None):
        gen = gen_template.gen_template()
        gen.load_config('config.yaml')
        gen.zonetemplate = 'zonetemplate_slave.json'
        zone_data = gen.generate(zone, json_data)

        r = self.exec_pdns_api('POST', '/servers/localhost/zones', json_data=zone_data)

        return {'status_code' : r.status_code, 'json_data' : zone_data }

    def get_serial(self, soa):
#{
#    "content": "dns0.some.com. hostmaster.some.com. 1 1800 900 604800 86400", 
#    "disabled": true, 
#    "name": "annecy-viande.fr", 
#    "priority": 0, 
#    "ttl": 86400, 
#    "type": "SOA"
#}
        content = soa['content']
        regxep = r'^\S+\s+\S+\s+(\d+)'
        m = re.search(regxep, content)
        if m:
            serial = int(m.groups()[0])

        return serial 

    def set_serial(self, soa, serial=None):
        if serial == None:
            serial = self.get_serial(soa)
            serial += 1

        content = soa['content']
        new_soa = soa.copy()
        regxep = r'^(\S+)\s+(\S+)\s+(\d+)'
        new_content = re.sub(regxep, r'\1 \2 %s' % serial, content)

        new_soa['content'] = new_content

        return new_soa

    def change_SOA(self, zone, enable):
        gen = gen_template.gen_template()
        gen.load_config()

        soa = self.get_SOA_from_json(self.get_json_zone(zone))
        serial = self.get_serial(soa)
        soa2 = self.set_serial(soa, serial + 1)

        if enable:
            gen.zonetemplate = 'enable_zone.json'
            soa2['disabled'] = False
        else:
            gen.zonetemplate = 'disable_zone.json'
            soa2['disabled'] = True


        zone_data = gen.generate(zone, '{ "soa" : %s }' % json.dumps(soa2))

        r = self.exec_pdns_api('PATCH', '/servers/localhost/zones/%s' % zone, json_data=zone_data)

        return {'status_code' : r.status_code, 'json_data' : zone_data }

    def show_SOA(self, zone):
        z = p.get_json_zone(zone)
        print(json.dumps(p.get_SOA_from_json(z), indent=4, sort_keys=True))

############################# main code

if __name__ == '__main__':
    arguments = docopt(__doc__, version='pdns_zone.py 2.0')

    if arguments['help']:
        print(__doc__.strip("\n"))
        sys.exit()

    p = pdns_zone()
    p.read_apikey()

    if arguments['list']:
        p.list_zones()
    elif arguments['dump']:
        p.dump_zone(arguments['ZONE'])
    elif arguments['json']:
        p.dump_json(arguments['ZONE'])
    elif arguments['json_records']:
        z = p.get_json_zone(arguments['ZONE'])
        # remove NS records
        z2 = list(filter(lambda r : r['type'] not in ('NS'), z['records']))
        print(json.dumps(z2, indent=4, sort_keys=True))
    elif arguments['create']:
        p.create_zone(arguments['ZONE'])
    elif arguments['delete']:
        error = 0
        for z in arguments['ZONES']:
            r = p.delete_zone(z)
            error += r
        sys.exit(r)
    elif arguments['missing']:
        r = p.test_missing_zone(arguments['ZONE'])
        sys.exit(r)
    elif arguments['add_slave_zone']:
        json_data = '{ "master_ip" : "%s"}' % arguments['MASTER_IP'] 
        r = p.add_slave_zone(arguments['ZONE'], json_data)
        print(r['json_data'])
    elif arguments['enable'] or arguments['update']:
        p.change_SOA(arguments['ZONE'], enable=True)
        p.show_SOA(arguments['ZONE'])
    elif arguments['disable']:
        p.change_SOA(arguments['ZONE'], enable=False)
        p.show_SOA(arguments['ZONE'])
    elif arguments['gen_template']:
        gen = gen_template.gen_template()
        gen.load_config()
        gen.zonetemplate = arguments['TEMPLATE']
        print(gen.generate(arguments['ZONE'], json_data=arguments['JSON_EXTRA']))
    elif arguments['show_SOA']:
        p.show_SOA(arguments['ZONE'])
    elif arguments['api']:
        # free API call
        r = p.exec_pdns_api(arguments['METHOD'], arguments['URL'], json_data=arguments['JSON_EXTRA'])
        if type(r) in (dict, list):
            print(json.dumps(r, indent=4, sort_keys=True))
        else:
            print('"no error, response not json"')

    sys.exit()
