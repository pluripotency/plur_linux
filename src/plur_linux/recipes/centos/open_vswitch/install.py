#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell


def from_openstack(session):
    stein = "centos-release-openstack-stein"
    current_openstack = stein

    base_shell.yum_install(session, {'packages': [current_openstack]})
    base_shell.yum_install(session, {'packages': ['openvswitch']})

    # openstack stein dpdk has bug for dependency with openvswitch
    # https://bugzilla.redhat.com/show_bug.cgi?id=1658141
    # Need counter
    base_shell.yum_install(session, {'packages': ['libibverbs']})

    base_shell.service_on(session, 'openvswitch')


def from_rpm(session):
    rpm = 'openvswitch-2.1.2-1.el6.x86_64.rpm'
    # url = session.nodes[0].download_source + 'pkgs/' + rpm
    url = 'http://repo/setups/' + rpm
    base_shell.run(session, 'sudo rpm -ivh ' + url)
    base_shell.service_on(session, 'openvswitch')
