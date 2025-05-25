#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell


def ntp_patch(session, node):
    if hasattr(node, 'ntpservers') and session.username == 'root':
        ntpservers = node.ntpservers

        shell.work_on(session, '/etc/')

        patch = [
            '*** ntp.conf',
            '--- ntp.conf',
            '***************',
            '*** 20,27 ****',
            '  # Use public servers from the pool.ntp.org project.',
            '  # Please consider joining the pool (http://www.pool.ntp.org/join.html).',
            '! server 0.centos.pool.ntp.org iburst',
            '! server 1.centos.pool.ntp.org iburst',
            '! server 2.centos.pool.ntp.org iburst',
            '! server 3.centos.pool.ntp.org iburst',
            '  ',
            '  #broadcast 192.168.1.255 autokey\t# broadcast server'
        ]
        line_count = 23
        servers = []
        for srv in ntpservers:
            line_count = line_count + 1
            servers += [
                '! server %s iburst' % srv
            ]

        patch += [
            '--- 20,%d ----' % line_count,
            '  # Use public servers from the pool.ntp.org project.',
            '  # Please consider joining the pool (http://www.pool.ntp.org/join.html).'
        ]
        patch += servers
        patch += [
            '  ',
            '  #broadcast 192.168.1.255 autokey\t# broadcast server'
        ]

        patch_file = '/root/ntp_patch'
        shell.here_doc(session, patch_file, patch)
        shell.patch(patch_file)
        shell.run('rm -rf ' + patch_file)


def configure(session, node):
    if hasattr(node, 'ntpservers'):
        ntp_patch(session, node)

    capture = shell.run(session, 'service ntpd start')

    capture = shell.run(session, 'chkconfig ntpd on')

