# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
import sys
sys.path.append('..')
import requests
from tempfile import NamedTemporaryFile


import pdns_zone

def _create_pdns_conf(name):
    f = open(name, "wt")
    f.write("experimental-api-key=some-test-key")
    f.close()

def test_read_apikey(mocker):
    fname = NamedTemporaryFile()
    _create_pdns_conf(fname.name)
    p = pdns_zone.pdns_zone()
    k = p.read_apikey(fname.name)
    assert len(k) > 0
    assert k == 'some-test-key'

def test_exec_pdns_api(mocker):
    p = pdns_zone.pdns_zone()
    mocker.patch('requests.get')

    # fake key : p.read_apikey()
    k = 'some-key'
    p.key = k
    h = { "X-API-Key" : k }

    # list
    rest_url = '/servers/localhost/zones'
    r = p.exec_pdns_api('GET', rest_url)
    url = p.url_base + rest_url

    requests.get.assert_called_once_with(url, headers=h)

    r = p.exec_pdns_api('GET', rest_url, text=True)


