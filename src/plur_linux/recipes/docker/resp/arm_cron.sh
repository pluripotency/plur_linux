#! /bin/bash
echo "*/5 * * * * cd /home/worker/resp/; sh start_plur3_sniff_runner.sh > /tmp/plur3_sniff_runner.log 2>&1" >  mycron
crontab mycron
rm mycron
