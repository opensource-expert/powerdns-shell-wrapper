# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
import sys
sys.path.append('..')

import pdns_zone

def test_read_apikey():
    p = pdns_zone.pdns_zone()
    k = p.read_apikey()
    assert len(k) > 0

def test_exec_pdns_api():
    p = pdns_zone.pdns_zone()
    p.read_apikey()
    l = p.exec_pdns_api('GET', '/servers/localhost/zones')
    assert len(l[0]['name']) > 0
