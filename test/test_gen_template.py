# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
import sys
sys.path.append('..')

import os
import json

import gen_template


def _create_config(name=None):
    if not name:
        name = 'config.yaml'

    conf = """
# vim: set ft=yaml:
#
# DON'T EDIT THIS FILE: salt managed file
#
ns1: 'ns0.some.com'
ns2: 'ns6.bis.net'
hostmaster: 'hostmaster.some.com'
web_ip: '2.22.33.83'
mailserver: 'mta0.some.com'
spf: 'v=spf1 mx a ~all'
    """.strip()

    f = open(name, 'wt')
    f.write(conf)
    f.close()

    return name

def test_gen_template():
    g = gen_template.gen_template()
    assert g.zonetemplate == 'zonetemplate.json'

def test_load_config():
    g = gen_template.gen_template()
    conff = 'config.yaml'
    assert not os.path.isfile(conff)
    assert not g.load_config()
    assert g.zonetemplate == 'zonetemplate.json'

    _create_config(conff)
    assert os.path.isfile(conff)
    assert g.load_config()
    os.remove(conff)
    assert g.d['ns1'] == 'ns0.some.com'

def test_generate():
    g = gen_template.gen_template()
    conff = _create_config()
    assert g.load_config()
    domain = 'pipo.com'
    json_str = g.generate(domain)
    assert json.loads(json_str)['name'] == domain
    os.remove(conff)

