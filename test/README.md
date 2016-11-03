# unit testing

## Run

### python unittests
~~~
cd test
py.test
~~~

## bats functionnal testings

**WARNING**: it will try to run tests against a local powerdns server

~~~
cd test
./bats/bin/bats test.bats
~~~


## Install 


Depend on python packages: `httmock`, `pytest`, `pytest-mock`


### bats is a git submodule

~~~
cd test
git submodule init
git submodule update
~~~

## TODO

add a way to create the powerdns server for testing


## Helpers

hit API directly

~~~bash
pdns_api() {
  url_base="http://127.0.0.1:8081"
  key=$(sed -n -e '/experimental-api-key=/ s///p' /etc/powerdns/pdns.conf)
  wget -S --header "X-API-Key: $key" $extra "${url_base}$1" -O-
}
~~~
