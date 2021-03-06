#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
#
# class generate a JSON output for powerdns for creating a zone using API, for powerdns V3.4
#
# Note: See config.yaml for override the value in the template, or json_data
#
# json_data can be:
# { "master_ip" : "12.2.2.4" , "mailserver" : "mail.domain.tld" }
# { "soa" : "string from show_SOA" }
#
# you can mix multiple override in the json. use same names as in template
# templates are looked up in the same folder as this code.

from __future__ import absolute_import

import os
from jinja2 import Environment, FileSystemLoader
import yaml
import time
import json

class gen_template:
    def __init__(self, cmd_line_json=None):
        self.d = {}
        self.cmd_line_json = cmd_line_json

        self.d['domain'] = None

        modif_count = 1

        #self.default, you can override with config.yaml
        # See config_example.yaml and load_config()
        self.d['ns1'] = 'ns2.example.net'
        self.d['ns2'] = 'ns2.example.net'
        self.d['hostmaster'] = 'hostmaster.example.net'
        self.d['web_ip'] = '10.0.0.2'
        self.d['mailserver'] = 'mail.example.net'
        self.d['spf'] = 'v=spf1 mx a ~all'

        self.d['date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.d['serial'] = '%s%02d' % (time.strftime('%Y%m%d'), modif_count)
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
        # compute local script location to find template_dir
        me = os.path.realpath(__file__)
        template_dir = os.path.dirname(me) + '/.'

        self.d['domain'] = zone

        # override with json
        if json_data:
            self.d.update(json.loads(json_data))

        env = Environment(loader=FileSystemLoader(template_dir))
        # add to_json filer in jinja2
        # so json can be dumped with in jinja2: {{ var | to_json }}
        env.filters['to_json'] = json.dumps

        template = env.get_template(self.zonetemplate)
        json_str = template.render(self.d)
        return json_str
