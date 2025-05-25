#! /bin/sh
#DB_ADDRESS=192.168.0.1
#DB_PORT=3306
#DB_NAME=radius
#DB_USER=radius
#DB_PASS=P@55w0rd!
##LOG_OUTPUT=files
#LOG_OUTPUT=stdout
#RADIUS_DEBUG=no
#DEFAULT_GW=192.168.0.254

ip r d default
ip r a default via $DEFAULT_GW

echo > /etc/raddb/clients.conf

cp -f /etc/raddb/mods-available/sql /etc/raddb/mods-enabled/
sed -i 's/driver = "rlm_sql_null"/driver = "rlm_sql_mysql"/' /etc/raddb/mods-enabled/sql
sed -i 's/dialect = "sqlite"/dialect = "mysql"/' /etc/raddb/mods-enabled/sql

sed -i 's/#\tserver = "localhost"/\tserver = "'$DB_ADDRESS'"/' /etc/raddb/mods-enabled/sql
sed -i 's/#\tport = 3306/\tport = '$DB_PORT'/' /etc/raddb/mods-enabled/sql
sed -i 's/#\tlogin = "radius"/\tlogin = "'$DB_USER'"/' /etc/raddb/mods-enabled/sql
sed -i 's/#\tpassword = "radpass"/\tpassword = "'$DB_PASS'"/' /etc/raddb/mods-enabled/sql
sed -i 's/\tradius_db = "radius"/\tradius_db = "'$DB_NAME'"/' /etc/raddb/mods-enabled/sql

sed -i 's/#\tread_clients = yes/\tread_clients = yes/' /etc/raddb/mods-enabled/sql

sed -i -e 's|auth = no|auth = yes|g' /etc/raddb/radiusd.conf
sed -i -e 's|auth_badpass = no|auth_badpass = yes|g' /etc/raddb/radiusd.conf
sed -i -e 's|auth_goodpass = no|auth_goodpass = yes|g' /etc/raddb/radiusd.conf
sed -i -e 's|destination = files|destination = '$LOG_OUTPUT'|g' /etc/raddb/radiusd.conf

if [ "${RADIUS_DEBUG}" = "yes" ]
then
  radiusd -X -f -d /etc/raddb
else
  radiusd -f -d /etc/raddb
fi

