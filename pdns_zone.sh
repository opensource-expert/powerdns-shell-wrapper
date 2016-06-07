#!/bin/bash

url_base="http://127.0.0.1:8081"
key=changeme

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


  # remove // 
  local url="${1//\/\///}"
  # remove extra ^/
  url="$url_base/${url#/}"
  #echo "url: $url"
  local tmp=/tmp/pdns_api.out
  curl -H "X-API-Key: $key" $extra "$url" | \
    tee $tmp | jq .
    #W2> /dev/null
  if [[ $? -ne 0 ]]
  then
    cat $tmp
  fi
}

case $1 in
  list)
    pdns_api /servers/localhost/zones | jq -r '.[].name'
    ;;
  dump)
    zone=$2
    pdns_api /servers/localhost/zones/$zone/export
    ;;
  json)
    zone=$2
    pdns_api /servers/localhost/zones/$zone
    ;;
  create)
    zone=$2
    pdns_api POST zonetemplate.json /servers/localhost/zones
    ;;
  delete)
    zone=$2
    pdns_api DELETE /servers/localhost/zones/$zone
    ;;
  
  *)
    pdns_api "$1"
    ;;
esac
