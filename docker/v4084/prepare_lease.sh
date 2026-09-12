#! /bin/bash
# need to run before docker-compose up, if you want see lease in docker host
mkdir -p ./leases
touch ./leases/dhcpd.leases
touch ./leases/dhcpd.leases~
