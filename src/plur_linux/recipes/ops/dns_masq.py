#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell


def update_dnsmasq(session, host_dict_list):
    hosts = [host['ip'] + ' ' + host['hostname'] for host in host_dict_list]
    base_shell.here_doc(session, '/etc/hosts', hosts)
    base_shell.run(session, 'service dnsmasq restart')


