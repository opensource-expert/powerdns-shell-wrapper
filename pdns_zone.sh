#!/bin/bash
#
# command line wrapper to manage pdns zone
#
# Usage:
#  ./pdns_zone.sh create example.net    --> create a new zone
#  ./pdns_zone.sh delete example.net    --> delete without confirm
#  ./pdns_zone.sh list                  --> list all zone
#  ./pdns_zone.sh dump somedomaine.com  --> dump zone in bind format
#
# Require: curl + jq + python + jinaj2

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

case $1 in
  list)
    pdns_api /servers/localhost/zones | jq -r '.[].name'
    ;;
  dump)
    # dump zone in bind format
    zone=$2
    pdns_api /servers/localhost/zones/$zone/export
    ;;
  json)
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
  *)
    pdns_api "$1"
    ;;
esac
