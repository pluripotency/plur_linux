#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell

from plur_linux.recipes.ops import ssh
from plur_linux.recipes import firewalld

shinjuku_password = 'password'


def install_splunk(session):
    splunk = 'splunk-6.5.0-59c8927def0f-Linux-x86_64'
    shell.work_on(session, '~/Downloads/')
    ssh.scp(session, 'worker@192.168.10.15:/mnt/MC/work_space/Downloads/%s.tgz' % splunk, './', shinjuku_password)
    actions = [
        'tar xvzf %s.tgz' % splunk,
        'sudo mv splunk /opt/',
        'sudo chown -R worker:worker /opt/splunk'
    ]
    [shell.run(session, a) for a in actions]


def enable_443redirection(session):
    firewalld.register_service('splunk', 'SPLUNK', 'Splunk on Linux', tcp_ports=['8443'])(session),

    # enable iptables rule by firewalld
    # iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 8443
    rule = '--direct --add-rule ipv4 nat PREROUTING 0 -p tcp -m tcp --dport 443 -j REDIRECT --to-ports 8443'
    actions = [
        'sudo firewall-cmd --permanent ' + rule,
        'sudo firewall-cmd ' + rule,
        ]
    [shell.run(session, a) for a in actions]

    # web_conf permission is 444.
    # so rm and chmod is needed
    web_conf = '/opt/splunk/etc/system/default/web.conf'
    shell.create_backup(session, web_conf)
    shell.run(session, 'rm -f %s' % web_conf)
    shell.sed_pipe(session, web_conf + '.org', web_conf, [
        ['^httpport = 8000$', 'httpport = 8443'],
        ['^enableSplunkWebSSL = false$', 'enableSplunkWebSSL = true']
    ])
    shell.run(session, 'chmod 444 %s' % web_conf)


def enable_splunk(session):
    actions = [
        '/opt/splunk/bin/splunk start --accept-license',
        'sudo /opt/splunk/bin/splunk enable boot-start -user worker'
    ]
    [shell.run(session, a) for a in actions]


def install(session):
    if session.platform == 'centos7':
        [func(session) for func in [
            firewalld.register_service('rsyslog', 'RSYSLOG', 'Syslog', tcp_ports=['514'], udp_ports=['514']),
            install_splunk,
            enable_443redirection,
            enable_splunk
        ]]
