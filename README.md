# pdns_zone.py

**/!\** refactoring to full python code, some bash version code may not work yet.

A small command line wrapper to manage zone via powerdns, use only API, powerdns V3.4.

This wrapper is designed to work with [powerDNS api](https://doc.powerdns.com/3/httpapi/README/).

**Note:** Find other PowerDNS Frontends (graphic or command line) [here](https://github.com/PowerDNS/pdns/wiki/WebFrontends).

**Lecteur Francophone:** Demandez moi la traduction si nécessaire.

## Usage

~~~bash
./pdns_zone.py create example.net                       # --> create a new zone from template
./pdns_zone.py delete example.net                       # --> delete without confirm
./pdns_zone.py list                                     # --> list all zones
./pdns_zone.py dump somedomaine.com                     # --> dump zone in bind format
./pdns_zone.py json somedomaine.com                     # --> dump zone in json format
./pdns_zone.py add_slave_zone somedomaine.com 1.2.3.4   # --> add as slave of master_ip
~~~

Save and restore a zone in json (does it works as is?)

~~~bash
# dump json
./pdns_zone.py json somedomaine.com > somedomaine_com.json
# delete
./pdns_zone.py delete somedomaine.com
# restore (free API call) NOT YET in Python
./pdns_zone.py POST somedomaine_com.json /servers/localhost/zones
~~~

## Install

~~~
git clone https://github.com/opensource-expert/powerdns-shell-wrapper.git
pip install docopt
~~~

* **Note:** it requires `docopt`, others: `requests`, `jinja2` + `json` + `yaml` are all installed on a salt minion.
* **Note 2:** the powerDNS API need to be enabled, of course. (See: Enable powerDNS API for v3.4)

## Configure `config.yaml`


~~~yaml
# example, copy to config.yaml and put your change here
ns1: 'your.master.dns.example.com'
ns2: 'ns2.example.net'
hostmaster: 'hostmaster.contact.domain.com'
web_ip: '10.0.0.2'
mailserver: 'mailserver.domain.com'
spf: 'v=spf1 mx a ~all'
~~~

## Preview the pdns API JSON on stdout

**TODO:** to be done with main wrapper

~~~
./pdns_zone.py gen_template somedomain.com
~~~

It also supports extra template and an optional IP as argument: (used for `add_slave_zone`)

~~~
./pdns_zone.py gen_template somedomain.com '{ "template" : "zonetemplate_slave.json", "master_ip" : "1.22.3.4" }'
~~~


## PowerDNS JSON examples

### disabling a domain
JSON for Disabling a domain (by disabling its SOA record)

~~~bash
./pdns_zone.py create somedomaine.com
# extract the SOA
./pdns_zone.py json somedomaine.com | jq '.records[]|select(.type=="SOA")' > soa

./pdns_zone.py gen_template somedomain.com '{ "template" : "disable_zone.json", "soa" : "$(cat soa)" }'
~~~

will output:
~~~json
{ "rrsets":
  [
    {
      "name": "somedomaine.com",
      "type": "SOA",
      "changetype": "REPLACE",
      "records":
        [
          {"disabled": true, "name": "somedomaine.com", "priority": 0, "ttl": 86400, "content": "ns2.example.net. hostmaster.example.net. 1 1800 900 604800 86400", "type": "SOA"}
        ],
      "comments":
        [
          {
            "account": "salt master",
            "content": "domain is disabled",
            "modfied_at": 1474133154
          }
        ]
    }
  ]
}
~~~

Enabling a zone :
~~~
./pdns_zone.py gen_template somedomain.com '{ "template" : "enable_zone.json", "soa" : "$(cat soa)" }'
~~~


## Enable powerDNS API for v3.4

`/etc/powerdns/pdns.conf`

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

* Some data are still hardcoded in the code: pdns url
* Allow fullpath excution and temporary file stored in /tmp


## salt integration

This frist state clones the repository and configure it with your own `config.yaml`.


### `state/powerdns.sls`

~~~yaml
# install the command line wrapper for creating/managing domains
{% set pdns_zone_dir = '/root/pdns_zone' %}
pdns_zone:
  # git clone the code
  git.latest:
    - name: https://github.com/opensource-expert/powerdns-shell-wrapper.git
    - target: {{ pdns_zone_dir }}
  file.managed:
    - name: {{ pdns_zone_dir }}/config.yaml
    - source: salt://powerdns/config/pdns_zone_config.yaml
    - user: root
    - group: root
    - mode: 644
~~~

This second state, run `pdns_zone.py` with your pillar data in order to create managed domains.

### `state/powerdns/customers_domains.sls`
~~~yaml
# pdns_zone created by state/powerdns.sls above
# customers:domains pillar listing domain to be managed

# loop over managed domain and create them if needed
{% set customers_domains = salt['pillar.get']('customers:domains', {}) -%}
{% for domain in customers_domains %}
{{ domain}}:
  cmd.run:
    - name: ./pdns_zone.py create "{{ domain }}"
    - cwd: /root/pdns_zone
    - onlyif:
      - ./pdns_zone.py missing "{{ domain }}"
{% endfor %}
~~~

pillar used:

~~~yaml
customers:
  # Managed domains for customers
  domains:
    - client1-domain.fr
    - more-domain.com
    - somedomain.fr
    - somedomain4.fr
~~~
