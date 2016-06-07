#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# genenate a JSON output for powerdns for creating a zone
# using API, for powerdns V3.4
#
# Usage: gen_template.py somedomain.com
#   gen_template.py somedomain.com > some_file
#
# Note: See config.yaml for override the value in the template

from __future__ import absolute_import

import os
#import re
import sys
from jinja2 import Environment, FileSystemLoader
import yaml
import time

#re.UNICODE
#re.LOCALE

def main():
    if len(sys.argv) == 1:
        print("missing argument")
        sys.exit(1)

    d = {}
    d['domain'] = sys.argv[1]

    # default, you can override with config.yaml
    # See config_example.yaml
    d['ns1'] = 'ns2.example.net'
    d['ns2'] = 'ns2.example.net'
    d['hostmaster'] = 'hostmaster.example.net'
    d['web_ip'] = '10.0.0.2'
    d['mailserver'] = 'mail.example.net'
    d['spf'] = 'v=spf1 mx a ~all'

    d['date'] = time.strftime('%Y-%m-%d %H:%M:%S')

    # load local config, for override dumy default parameter
    try:
        f = open('config.yaml')
        d2 = yaml.safe_load(f)
        f.close()
    except IOError as e:
        d2 = {}

    # merge defaut and local data
    d.update(d2)

    me = os.path.realpath(__file__)
    template_dir = os.path.dirname(me) + '/.'
    #print("# me: %s" % me)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('zonetemplate.json')

    print(template.render(d))

if __name__ == '__main__':
    main()
