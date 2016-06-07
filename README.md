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

**Note:** it requires curl, jq and the powerDNS API to be enabled.

## Enable powerDNS API for v3.4

pdns.conf

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
