# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4 sts=4:
import sys
sys.path.append('..')

from tempfile import NamedTemporaryFile

# pip intall httpmock
from httmock import HTTMock, all_requests, response

import json

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
