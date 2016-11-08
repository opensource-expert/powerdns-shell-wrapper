#!/bin/bash
#
# functionnal testing for ../pdns_zone.py see README.md
#


# global variables
zone=test.myzone
pdns_zone=../pdns_zone.py
# assuming the dns server is on the same server
dns=$(hostname -f)
log=./bats.log

# for some debuging
test_zone() {
  local regexp=[^a-z.-]
  if [[ "$1" =~ $regexp ]]
  then
    echo "zone error: $1" >> $log
    exit 1
  fi
}

setup() {
  # test_zone should always log nothing
  test_zone "$zone"
  $pdns_zone create $zone
}

teardown() {
  test_zone "$zone"
  # test present
  if $pdns_zone api GET "/servers/localhost/zones/$zone" > /dev/null
  then
    $pdns_zone api DELETE "/servers/localhost/zones/$zone"
  fi
}

@test "delete non existing zone" {
  run $pdns_zone delete $$${zone}
  [ $status -eq 1 ]
  [[ ! -z "$output" ]]
}

@test "delete multiples zones" {
  # array
  all_zone=()
  for i in $(seq 1 5)
  do
    somezone="${i}-${zone}"
    $pdns_zone create $somezone
    all_zone+=($somezone)
  done

  # ${all_zone[@]} => array all values
  run $pdns_zone delete ${all_zone[@]}
  [[ $status -eq 0 ]]
  [[ -z "$output" ]]
}

@test "create and delete zone $zone" {
  [[ ! -z "$dns" ]]
  # ./pdns_zone.py create ZONE [JSON_EXTRA]
  somezone=$$${zone}
  run $pdns_zone create $somezone
  dig +short $somezone @$dns | grep '10.0.0.2'
  run $pdns_zone delete $somezone
  [[ $status -eq 0 ]]
  [[ -z "$output" ]]
  [[ "$dns" =~ ^dns0 ]]
  # not always right, we must test a distinct record
  [[ -z "$(dig +short www.$somezone @$dns)" ]]
}

@test "zone is missing" {
  # ./pdns_zone.py missing ZONE
  run $pdns_zone missing $$${zone}
  [[ $status -eq 0 ]]
  [[ "$output" == MISSING ]]
}

@test "listing zones" {
  # ./pdns_zone.py list
  run $pdns_zone list
  [[ ! -z "$output" ]]
  [[ $status -eq 0 ]]
}

@test "dumping a zone in bind fromat" {
  # ./pdns_zone.py dump ZONE
  # without argument must fail
  run $pdns_zone dump
  [[ $status -eq 1 ]]
  
  run $pdns_zone dump $zone
  [[ $status -eq 0 ]]
  [[ ! -z "$output" ]]
  regexp="^${zone}\."
  # extract SOA record line
  [[ "$(echo "$output" | grep SOA)" =~ $regexp ]]
}

@test "dumping zone in json format" {
  # ./pdns_zone.py json ZONE
  run $pdns_zone json $zone
  echo "$output" | jq . 
}

@test "dump only records without NS" {
  # ./pdns_zone.py json_records ZONE
  run $pdns_zone json_records $zone
  [[ ! -z "$(echo "$output" | jq '.[]|select(.type == "SOA")')" ]]
  [[ -z "$(echo "$output" | jq '.[]|select(.type == "NS")')" ]]
}

@test "show_SOA records in json of a zone" {
  # ./pdns_zone.py show_SOA ZONE
  [[ "$($pdns_zone show_SOA $zone | jq '.|select(.type == "SOA").disabled')" == "false" ]]
}


@test "enabling disabling udating SOA of a zone" {
  # ./pdns_zone.py (enable|disable|update) ZONE
  run $pdns_zone enable $zone
  [[ $status -eq 0 ]]
  [[ "$(echo "$output" | jq '.|select(.type == "SOA").disabled')" == "false" ]]
  regexp='[^ ]+ [^ ]+ ([0-9]+)'
  [[ "$(echo "$output" | jq '.content')" =~ $regexp ]]
  serial=${BASH_REMATCH[1]}

  run $pdns_zone disable $zone
  [[ "$(echo "$output" | jq '.|select(.type == "SOA").disabled')" == "true" ]]

  [[ "$(echo "$output" | jq '.content')" =~ $regexp ]]
  serial2=${BASH_REMATCH[1]}
  [[ "$serial" != "$serial2" ]]
}

@test "add a zone as a slave, no data" {
  # ./pdns_zone.py add_slave_zone ZONE MASTER_IP
  # MASTER_IP is required
  somezone=$$${zone}
  run $pdns_zone add_slave_zone $somezone
  [[ $status -eq 1 ]]

  run $pdns_zone add_slave_zone $somezone 1.2.3.4
  [[ $status -eq 0 ]]
  [[ "$(echo "$output" | jq -r .kind)" == Slave ]]

  run $pdns_zone delete $somezone
}

@test "call gen_template with a template and json and api" {
  # ./pdns_zone.py gen_template TEMPLATE ZONE [JSON_EXTRA]
  # Backup tips from ../README.md
  outfile=${zone}-records
  restorefile=${zone}-restore_zone.json
  $pdns_zone json_records $zone > $outfile
  $pdns_zone delete $zone
  $pdns_zone gen_template restore_zone.json $zone \
    "{\"records\" : $(cat $outfile) }" \
    > $restorefile

  # validate json
  jq . < $restorefile

  # restore!
  $pdns_zone api POST /servers/localhost/zones "$(cat $restorefile)"

  run dig +short $zone @$dns
  [[ "$output" == "10.0.0.2" ]]

  rm -f $outfile $restorefile
}

@test "api wrapper direct call" {
  # ./pdns_zone.py api <args>...
  # also done in test gen_template above

  run $pdns_zone api GET /servers/localhost/zones
  [[ $status -eq 0 ]]
  [[ ! -z "$(echo "$output" | jq -r '.[].name')" ]]

  run $pdns_zone api GET /servers/localhost/zones/$zone
  [[ $status -eq 0 ]]
  [[ ! -z "$(echo "$output" | jq '.records[]|select(.type == "SOA")')" ]]
}

@test "show help" {
  # ./pdns_zone.py (help | -h | --help)
  run $pdns_zone help
  [[ $status -eq 0 ]]
  [[ ! -z "$output" ]]
}
