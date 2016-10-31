#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:

"""
Command line wrapper to manage pdns zone (usable with salt)

Usage:
 ./pdns_zone.sh create ZONE [JSON_EXTRA]
 ./pdns_zone.sh delete ZONE
 ./pdns_zone.sh list
 ./pdns_zone.sh dump ZONE
 ./pdns_zone.sh json ZONE
 ./pdns_zone.sh add_slave_zone ZONE MASTER_IP
 ./pdns_zone.sh help | -h | --help
"""
# Require: curl + jq + python + jinaj2
# See API for pdns 3.4: https://doc.powerdns.com/3/httpapi/README/


# empty line above required ^^
from __future__ import print_function
# docopt: pip install --user docopt
from docopt import docopt
import re
import requests

import gen_template

class pdns_zone:
    def __init__(self):
        # reflect your powerdns config here
        self.url_base = "http://127.0.0.1:8081"
        # api key
        self.key = None

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
            if text:
                return r.text
            else:
                return r.json()
        else:
            raise ValueError('url returned an error: %s:\n%s\n---\n%s' % (call_url, r.headers, r.text))

    def list_zones(self):
        l = self.exec_pdns_api('GET', '/servers/localhost/zones')
        for z in l:
            zone_info = self.exec_pdns_api('GET', '/servers/localhost/zones/' + z['name'])
            # look if SOA record is disabled or not
            disabled = list(filter(lambda r : r['type'] == 'SOA', zone_info['records']))[0]['disabled']
            if disabled:
                txt = ' \033[31;1m disabled\033[0m'
            else:
                txt = ''
            print('%s%s' % (z['name'], txt))

    def dump_zone(self, zone):
        print(self.exec_pdns_api('GET', '/servers/localhost/zones/%s/export' % zone, text=True))

    def dump_json(self, zone):
        print(self.exec_pdns_api('GET', '/servers/localhost/zones/%s' % zone, text=True))

    def create_zone(self, zone, json_data=None):
        gen = gen_template.gen_template()
        gen.load_config('config.yaml')
        zone_data = gen.generate(zone, json_data)

        r = self.exec_pdns_api('POST', '/servers/localhost/zones', json_data=zone_data)

    def delete_zone(self, zone):
        try:
            r = self.exec_pdns_api('DELETE', '/servers/localhost/zones/%s' % zone, text=True)
        except ValueError as e:
            print(e)

#case $1 in
#  create)
#    zone=$2
#    extra="$3"
#    if [[ -z "$extra" ]]
#    then
#      extra="{}"
#    fi
#    python gen_template.py $zone zonetemplate.json "$extra" > zone.tmp
#    pdns_api POST zone.tmp /servers/localhost/zones
#    rm zone.tmp
#    ;;
#  delete)
#    zone=$2
#    pdns_api DELETE /servers/localhost/zones/$zone
#    ;;
#  missing)
#    zone=$2
#    r=$(pdns_api /servers/localhost/zones/$zone | jq -r ".name")
#    if [[ "$r" == "$zone" ]]
#    then
#      echo PRESENT
#      exit 1
#    else
#      echo MISSING
#      exit 0
#    fi
#    ;;
#  add_slave_zone)
#    # insert given zone as a simple slave zone (useful for transfer)
#    zone=$2
#    master_ip=$3
#    python gen_template.py $zone zonetemplate_slave.json "{ \"master_ip\" : \"$master_ip\" }" > zone.tmp
#    pdns_api POST zone.tmp /servers/localhost/zones
#    rm zone.tmp
#    ;;
#  disable|enable)
#    template=${1}_zone.json
#    zone=$2
#    # fetch SOA record for the zone
#    soa="$(pdns_api /servers/localhost/zones/$zone | jq '.records[]|select(.type=="SOA")')"
#    python gen_template.py $zone $template "$soa" > zone.tmp
#    # excute and filter on comment
#    pdns_api PATCH zone.tmp /servers/localhost/zones/$zone | jq '.comments[]|select(.type=="SOA").content'
#    rm zone.tmp
#    ;;
#  update)
#    # inc soa serial record
#    template=update_zone.json
#    zone=$2
#    # fetch SOA record for the zone
#    soa="$(pdns_api /servers/localhost/zones/$zone | jq '.records[]|select(.type=="SOA")' | \
#      perl -p -e "if(/\"content\"/) { s/(\\.\\s+)(\\d+)/\$1.(\$2+1)/e;}")"
#    if python gen_template.py $zone $template "$soa" > zone.tmp
#    then
#      # excute and filter on comment
#      pdns_api PATCH zone.tmp /servers/localhost/zones/$zone
#    fi
#    rm zone.tmp
#    ;;
#  *)
#    # free pdns_api command
#    pdns_api "$@"
#    ;;
#esac

if __name__ == '__main__':
    arguments = docopt(__doc__, version='pdns_zone.py 2.0')
    print(arguments)
    p = pdns_zone()
    p.read_apikey()
    if arguments['list']:
        p.list_zones()
    elif arguments['dump']:
        p.dump_zone(arguments['ZONE'])
    elif arguments['json']:
        p.dump_json(arguments['ZONE'])
    elif arguments['create']:
        p.create_zone(arguments['ZONE'])
    elif arguments['delete']:
        p.delete_zone(arguments['ZONE'])
        
