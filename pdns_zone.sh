#!/bin/bash
#
# command line wrapper to manage pdns zone
#
# Usage:
#  ./pdns_zone.sh create example.net                       --> create a new zone
#  ./pdns_zone.sh delete example.net                       --> delete without confirm
#  ./pdns_zone.sh list                                     --> list all zones
#  ./pdns_zone.sh dump somedomaine.com                     --> dump zone in bind format
#  ./pdns_zone.sh json somedomaine.com                     --> dump zone in json format
#  ./pdns_zone.sh add_slave_zone somedomaine.com master_ip --> add as slave of master_ip
#
# Require: curl + jq + python + jinaj2
# See API for pdns 3.4: https://doc.powerdns.com/3/httpapi/README/

# reflect your powerdns config here
url_base="http://127.0.0.1:8081"
# api key
#key=changeme
# fetch from local config
key=$(sed -n -e '/experimental-api-key=/ s///p' /etc/powerdns/pdns.conf)

pdns_api() {
  local data=""
  local extra=""

  case $1 in
  POST)
    data=$2
    shift 2
    extra="--data @$data"
    ;;
  DELETE)
    shift 1
    extra="-X DELETE"
    ;;
  PATCH)
    data=$2
    shift 2
    extra="-X PATCH --data @$data"
    ;;
  esac

  # remove double: //
  local url="${1//\/\///}"
  # remove extra ^/
  url="$url_base/${url#/}"
  #echo "url: $url"
  local tmp=/tmp/pdns_api.out
  # tee is used for dump, jq error discard
  curl -s -H "X-API-Key: $key" $extra "$url" | \
    tee $tmp | jq .  2> /dev/null
  if [[ $? -ne 0 ]]
  then
    cat $tmp
  fi
  rm -f $tmp
}

usage() {
  # auto help with top comment
  sed -n -e '/^# Usage:/,/^$/ s/^# \?//p' < $0
}

if [[ -z "$1" || "$1" == --help ]]
then
  usage
  exit 0
fi


case $1 in
  list)
    for z in $(pdns_api /servers/localhost/zones | jq -r '.[].name')
    do
      active=""
      pdns_api "/servers/localhost/zones/$z/export" | grep -q SOA || active=disabled
      # colored TERM disabled entry
      echo -e "$z \033[31;1m$active\033[0m"
    done
    ;;
  dump)
    # dump zone in bind format
    zone=$2
    pdns_api /servers/localhost/zones/$zone/export
    ;;
  json)
    # dump zone in json format, suitable to be inputed back
    zone=$2
    pdns_api /servers/localhost/zones/$zone
    ;;
  create)
    zone=$2
    python gen_template.py $zone > zone.tmp
    pdns_api POST zone.tmp /servers/localhost/zones
    rm zone.tmp
    ;;
  delete)
    zone=$2
    pdns_api DELETE /servers/localhost/zones/$zone
    ;;
  missing)
    zone=$2
    r=$(pdns_api /servers/localhost/zones/$zone | jq -r ".name")
    if [[ "$r" == "$zone" ]]
    then
      echo PRESENT
      exit 1
    else
      echo MISSING
      exit 0
    fi
    ;;
  add_slave_zone)
    # insert given zone as a simple slave zone (useful for transfer)
    zone=$2
    master_ip=$3
    python gen_template.py $zone zonetemplate_slave.json $3 > zone.tmp
    pdns_api POST zone.tmp /servers/localhost/zones
    rm zone.tmp
    ;;
  disable|enable)
    zone=$2
    # fetch SOA record for the zone
    soa="$(pdns_api /servers/localhost/zones/$zone | jq '.records[]|select(.type=="SOA")')"
    python gen_template.py $zone ${1}_zone.json "$soa" > zone.tmp
    pdns_api PATCH zone.tmp /servers/localhost/zones/$zone
    rm zone.tmp
    ;;
  *)
    # free pdns_api command
    pdns_api "$@"
    ;;
esac
