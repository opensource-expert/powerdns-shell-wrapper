# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
import sys
sys.path.append('..')

from tempfile import NamedTemporaryFile

# pip intall httpmock
from httmock import HTTMock, all_requests, response

import json
import re

# lib to test
import pdns_zone

# catch all_requests and answer with the function
@all_requests
def fake_powerdns_mock(url, request):
    url = url.geturl()
    content = '{"url" : "%s" }' % url
    return response(
        status_code=200,
        content=content,
        headers=request.headers,
        reason=None, elapsed=1,
        request=request,
        stream=False)

def _create_pdns_conf(name):
    f = open(name, "wt")
    f.write("experimental-api-key=some-test-key")
    f.close()

def test_read_apikey():
    fname = NamedTemporaryFile()
    _create_pdns_conf(fname.name)
    p = pdns_zone.pdns_zone()
    assert p.key == None
    k = p.read_apikey(fname.name)
    assert len(k) > 0
    assert k == 'some-test-key'

def test_exec_pdns_api():
    p = pdns_zone.pdns_zone()

    # fake key : p.read_apikey()
    k = 'some-key'
    p.key = k
    h = { "X-API-Key" : k }

    # list
    rest_url = '/servers/localhost/zones'
    with HTTMock(fake_powerdns_mock):
        r = p.exec_pdns_api('GET', rest_url)

    url = p.url_base + rest_url
    assert isinstance(r, dict)
    assert r['url'] == url

    with HTTMock(fake_powerdns_mock):
        r = p.exec_pdns_api('GET', rest_url, text=True)

    assert isinstance(r, (str, unicode))

def test_create_zone():
    p = pdns_zone.pdns_zone()
    # fake key : p.read_apikey()
    k = 'some-key'
    p.key = k

    zone = 'pipo.com'
    with HTTMock(fake_powerdns_mock):
        r = p.create_zone(zone)
    assert r['status_code'] == 200
    assert json.loads(r['json_data'])['name'] == zone

def test_test_missing_zone():
    p = pdns_zone.pdns_zone()
    zone = 'pipo.com'
    with HTTMock(fake_powerdns_mock):
        r = p.test_missing_zone(zone)
    assert r == 0


def test_get_json_zone():
    p = pdns_zone.pdns_zone()
    zone = 'pipo.com'
    with HTTMock(fake_powerdns_mock):
        r = p.get_json_zone(zone)

    assert isinstance(r, dict)


def _create_soa(serial):
    return json.loads("""
{
    "content": "dns0.some.com. hostmaster.some.com. %d 1800 900 604800 86400", 
    "disabled": true, 
    "name": "annecy-viande.fr", 
    "priority": 0, 
    "ttl": 86400, 
    "type": "SOA"
}
""" % serial)

def test_get_serial():
    p = pdns_zone.pdns_zone()
    soa = _create_soa(33)
    assert p.get_serial(soa) == 33

def test_get_serial():
    p = pdns_zone.pdns_zone()
    soa = _create_soa(888)

    soa2 = p.set_serial(soa)
    assert p.get_serial(soa2) == 889

    soa2 = p.set_serial(soa, 8990)
    assert p.get_serial(soa2) == 8990

    assert re.match(r'^dns0.some.com.', soa2['content'])
    assert soa != soa2
