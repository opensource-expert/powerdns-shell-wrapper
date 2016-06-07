# pdns_zone.sh

A small command line wrapper to manage zone via powerdns API, powerdns V3.4.

This wrapper is designed to work with [powerDNS api](https://doc.powerdns.com/3/httpapi/README/).

## Usage

~~~
./pdns_zone.sh create example.net
./pdns_zone.sh delete example.net
./pdns_zone.sh list
./pdns_zone.sh dump somedomaine.com
~~~

## Install

~~~
git clone https://github.com/opensource-expert/powerdns-shell-wrapper.git
~~~

**Note:** it requires curl, jq, and python + jinja2 (which is installed on salt minion)
**Note 2:** the powerDNS API need to be enabled, of course

## configure gen_template.py

`gen_template.py` is a python script that build a JSON template (See: `zonetemplate.json`) to be send to powerDNS API.

`gen_template.py` embed some dumy variable for the template, but you can configure your own value with `config.yaml`

~~~yaml
# example, copy to config.yaml and put your change here
ns1: 'your.master.dns.example.com'
ns2: 'ns2.example.net'
hostmaster: 'hostmaster.contact.domain.com'
web_ip: '10.0.0.2'
mailserver: 'mailserver.domain.com'
spf: 'v=spf1 mx a ~all'
~~~

you can preview the JSON on stdout with:

~~~
python gen_template.py somedomain.com
~~~

## Enable powerDNS API for v3.4

/etc/powerdns/pdns.conf

~~~
# API enable
webserver=yes
webserver-address=0.0.0.0
webserver-allow-from=127.0.0.1/32
webserver-port=8081

experimental-api-readonly=no
experimental-json-interface=yes
experimental-api-key=changeme
~~~

## Enhancement

`pdns_zone.sh` and `gen_template.py` could be merged.
