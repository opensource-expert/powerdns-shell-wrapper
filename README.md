# pdns_zone.py

Shell command line wrapper to manage DNS zones for PowerDNS, use only API, for powerdns V3.4.

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

See full arguments available with:

~~~bash
./pdns_zone.py --help
~~~


## Install

~~~
git clone https://github.com/opensource-expert/powerdns-shell-wrapper.git
pip install docopt
~~~

* **Note:** it requires `docopt`, others: `requests`, `jinja2` + `json` + `yaml` are all installed on a salt minion.
* **Note 2:** the powerDNS API need to be enabled, of course. (See: Enable powerDNS API for v3.4)

## Configure `config.yaml`

yaml keys are used in jinja templates.

~~~yaml
# example, copy to config.yaml and put your change here
ns1: 'your.master.dns.example.com'
ns2: 'ns2.example.net'
hostmaster: 'hostmaster.contact.domain.com'
web_ip: '10.0.0.2'
mailserver: 'mailserver.domain.com'
spf: 'v=spf1 mx a ~all'
~~~


## Tips

### Save and restore a zone in json

~~~bash
# dump json records, Note json_records remove actual NS records
./pdns_zone.py json_records somedomain.fr > somedomain.fr-records
# delete
./pdns_zone.py delete somedomain.fr
# build retore template
./pdns_zone.py gen_template restore_zone.json somedomain.fr \
    "{\"records\" : $(cat somedomain.fr-records) }" \
    > somedomain.fr-restore.json
# use API to restore
./pdns_zone.py api POST /servers/localhost/zones "$(cat somedomain.fr-restore.json)"
~~~

### Preview the pdns API JSON on stdout

~~~
./pdns_zone.py gen_template zonetemplate.json somedomain.com
~~~

You can pass any override argument in JSON:

~~~
./pdns_zone.py gen_template restore_zone.json somedomain.com \
    "{ \"records\" : $(cat somefile), \"ns1\" : \"ns1.my.net\" }"
~~~


## PowerDNS JSON examples

### disabling a domain
JSON for Disabling a domain (by disabling its SOA record)

~~~bash
./pdns_zone.py create somedomaine.com
# extract the SOA
./pdns_zone.py json somedomaine.com | jq '.records[]|select(.type=="SOA")' > soa

# edit soa and disable

# generating JSON
./pdns_zone.py gen_template disable_zone.json somedomain.com "{ \"soa\" : $(cat soa) }"
~~~

will output:
~~~json
{ "rrsets":
  [
    {
      "name": "somedomain.com",
      "type": "SOA",
      "changetype": "REPLACE",
      "records":
        [
          {"disabled": false, "name": "somedomaine.com", "priority": 0, "ttl": 86400, "content": "dns0.webannecy.com. hostmaster.webannecy.com. 1 1800 900 604800 86400", "type": "SOA"}
        ],
      "comments":
        [
          {
            "account": "salt master",
            "content": "domain is disabled",
            "modfied_at": 1478010986
          }
        ]
    }
  ]
}
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
