#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell
from plur import session_wrap

from plur_linux.recipes import repos, firewalld
from plur_linux.recipes.ops import ops
from plur_linux.recipes.centos import chrony

ceph_repos = """[ceph-noarch]
name=Ceph noarch packages
baseurl=https://download.ceph.com/rpm/el7/noarch
enabled=1
gpgcheck=1
type=rpm-md
gpgkey=https://download.ceph.com/keys/release.asc
"""


@session_wrap.sudo
def ceph_deploy(session):
    chrony.configure(session)
    ops.disable_selinux(session)
    firewalld.configure(services=['ceph-mon', 'ceph', 'ssh'])
    repos.install_repo('centos7', 'epel')
    base_shell.here_doc(session, '/etc/yum.repos.d/ceph.repos', ceph_repos.split('\n'))
    base_shell.yum_install(session, {'update': True, 'packages': ['ceph-deploy']})

