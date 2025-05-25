#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell
from plur import session_wrap

from recipes import repos, firewalld


@session_wrap.sudo
def add_polkit_color(session):
    """
    not needed
    """
    policy = """
    [Allow colord for all users]
    Identity=unix-user:*
    Action=org.freedesktop.color-manager.create-device;org.freedesktop.color-manager.create-profile;org.freedesktop.color-manager.delete-device;org.freedesktop.color-manager.delete-profile;org.freedesktop.color-manager.modify-device;org.freedesktop.color-manager.modify-profile
    ResultAny=yes
    ResualtInactive=auth_admin
    ResultActive=yes
    """
    path = "/etc/polkit-1/localauthority/50-local.d/allow-colord.pkla"
    shell.here_doc(session, path, policy.replace('\n    ', '\n').split('\n'))


@session_wrap.sudo
def avoid_xrdp_broken(session):
    actions = [
        'chcon --type=bin_t /usr/sbin/xrdp',
        'chcon --type=bin_t /usr/sbin/xrdp-sesman',
        'systemctl reenable xrdp.service',
        'systemctl restart xrdp.service',
        'systemctl status xrdp.service'
    ]
    [shell.run(session, a) for a in actions]


def install(session):
    if session.platform == 'centos7':
        [func(session) for func in [
            repos.install_with_repo(['xrdp'], 'centos7', 'epel'),
            firewalld.configure(ports=['3389/tcp'], add=True),
            avoid_xrdp_broken,
        ]]
    elif session.platform == 'centos6':
        session.sudo_i()
        url = 'http://192.168.10.61/setups/'
        shell.yum_install(session, {'packages': ['tigervnc-server']})
        shell.yum_install(session, {'packages': [url + 'xrdp-0.6.1-4.el6.x86_64.rpm']})

        shell.work_on(session, '~/Downloads')
        src_dir = 'xrdp_dict'
        src_file = src_dir + '.tgz'
        src_url = url + src_file
        shell.wget(session, src_url)
        shell.run(session, 'cp * /etc/xrdp/')
        shell.run(session, 'service xrdp start')
        shell.run(session, 'chkconfig xrdp on')
        session.su_exit()

