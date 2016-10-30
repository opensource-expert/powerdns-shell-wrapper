#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
#
# generate a JSON output for powerdns for creating a zone
# using API, for powerdns V3.4
#
# Usage: gen_template.py somedomain.com [TEMPLATE_NAME]
#   gen_template.py somedomain.com > some_file
#   gen_template.py somedomain.com zonetemplate_slave.json ["json_string_config"]
#   gen_template.py somedomain.com disable_zone.json "json_string_SOA"
#   gen_template.py somedomain.com enable_zone.json "json_string_SOA"
#
# Note: See config.yaml for override the value in the template
#
# json_string_config can be:
#
# { "master_ip" : "12.2.2.4" , "mailserver" : "mail.domain.tld" }
# ""
# one or both

from __future__ import absolute_import

import os
#import re
import sys
from jinja2 import Environment, FileSystemLoader
import yaml
import time
import json

#re.UNICODE
#re.LOCALE


class gen_template:
    def __init__(self, cmd_line_json=None):
        self.d = {}
        self.cmd_line_json = cmd_line_json

        self.d['domain'] = None

        #self.default, you can override with config.yaml
        # See config_example.yaml and load_config()
        self.d['ns1'] = 'ns2.example.net'
        self.d['ns2'] = 'ns2.example.net'
        self.d['hostmaster'] = 'hostmaster.example.net'
        self.d['web_ip'] = '10.0.0.2'
        self.d['mailserver'] = 'mail.example.net'
        self.d['spf'] = 'v=spf1 mx a ~all'

        self.d['date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.d['soa'] = None
        self.d['cmd_line_json'] = None

        # set masters must be in array form
        self.d['masters'] = '[ "10.0.2.22" ]'

        self.d['timestamp'] = int(time.time())
        self.zonetemplate = 'zonetemplate.json'

    def load_config(self, config_yaml=None):
        if config_yaml == None:
            config_yaml = 'config.yaml'

        config_exists = False

        # load local config, for override dumy default parameter
        try:
            f = open(config_yaml)
            d2 = yaml.safe_load(f)
            f.close()
            config_exists = True
        except IOError as e:
            d2 = {}

        # merge defaut and local data
        self.d.update(d2)

        return config_exists

    def generate(self, zone, json_data=None):
        me = os.path.realpath(__file__)
        template_dir = os.path.dirname(me) + '/.'
        #print("# me: %s" % me)

        self.d['domain'] = zone

        env = Environment(loader=FileSystemLoader(template_dir))
        # add to_json filer in jinja2
        env.filters['to_json'] = json.dumps
        template = env.get_template(self.zonetemplate)

        json_str = template.render(self.d)

        print(json_str)

        return json_str


    def override_if(self, json_key):
        if self.cmd_line_json.get(json_key):
            self.d[json_key] = self.cmd_line_json[json_key]
            return True
        else:
            return False

def main():
    if len(sys.argv) == 1:
        print("missing argument")
        return False

    if len(sys.argv) >= 3:
      # create zone
      template_file = sys.argv[2]
    else:
      template_file = 'zonetemplate.json'

    # MASTER_IP is optional
    cmd_line_json = {}
    soa = {}
    if len(sys.argv) == 4:
      if template_file == 'disable_zone.json':
        soa = json.loads(sys.argv[3])
        soa['disabled'] = True
      elif template_file == 'enable_zone.json':
        soa = json.loads(sys.argv[3])
        soa['disabled'] = False
      else:
        if len(sys.argv[3]) > 0:
          cmd_line_json = json.loads(sys.argv[3])

    g = gen_template()
    d = {}
    g.d['domain'] = sys.argv[1]
    g.d['soa'] = soa
    g.d['cmd_line_json'] = cmd_line_json

    # final command line overwrite
    if self.override('master_ip'):
      # not the same name and it is a list
      self.d['masters'] = self.d['master_ip'].split(',')

    self.override('mailserver')
    self.override('web_ip')

    g.generate()


if __name__ == '__main__':
    main()
