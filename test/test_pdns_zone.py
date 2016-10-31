# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
import sys
sys.path.append('..')
import requests

import pdns_zone

def test_read_apikey():
    p = pdns_zone.pdns_zone()
    k = p.read_apikey()
    assert len(k) > 0

def test_exec_pdns_api(mocker):
    p = pdns_zone.pdns_zone()
    p.read_apikey()
    mocker.patch('requests.get')

    k = p.key
    h = { "X-API-Key" : k }

    # list
    rest_url = '/servers/localhost/zones'
    r = p.exec_pdns_api('GET', rest_url)
    url = p.url_base + rest_url

    requests.get.assert_called_once_with(url, headers=h)

    r = p.exec_pdns_api('GET', rest_url, text=True)

    assert r == 'get().text'

