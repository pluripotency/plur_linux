#! /usr/bin/env python
import os
from plur import base_shell
from plur import session_wrap


@session_wrap.sudo
def install_packages(session):
    base_shell.yum_install(session, {'packages': [
        'freeradius',
        'freeradius-utils',
        'freeradius-ldap',
    ]})
    base_shell.work_on(session, '/etc/raddb/certs')
    base_shell.run(session, './bootstrap')


# def configure(session):
#     script_dir = os.path.dirname(__file__)
#     current_node = session.nodes[-1]
#     base_shell.run(session, 'sudo cp /etc/raddb/sites-available/default /root/')
#
#     @session_wrap.bash()
#     def func(session2):
#         from plur_linux.recipes.ops import ssh
#         ssh.scp(session2, os.path.join(script_dir, 'ldap'), 'root@%s:/etc/raddb/mods-enabled/' % current_node.access_ip)
#         ssh.scp(session2, os.path.join(script_dir, 'default'), 'root@%s:/etc/raddb/sites-available/' % current_node.access_ip)
#     func()


@session_wrap.sudo
def copy_config(session):
    cwd = os.path.dirname(__file__)
    to_copy = [
        [f'{cwd}/ldap', '/etc/raddb/mods-enabled/ldap'],
        # [f'{cwd}/default', '/etc/raddb/sites-enabled/default'],
    ]
    [base_shell.heredoc_from_local(f[0], f[1])(session) for f in to_copy]


def radtest(user_list):
    return lambda session: [base_shell.run(session, f'radtest {u[0]} {u[1]} 127.0.0.1 0 testing123') for u in user_list]


def setup():
    olc_suffix_local = 'dc=example,dc=org'
    ldap_params = {
        'organization': 'ABC Organization',
        'bindDN': 'cn=manager,' + olc_suffix_local,
        'bindDNCredential': 'managerpass',
        'olcRootPW': 'managerpass',
        'olcSuffix': olc_suffix_local,
        'enable_ssl': True,
    }
    user_list = [
        ['user001', 'pass001', 100],
        ['user002', 'pass002', 200]
    ]
    from plur_linux.recipes.centos.openldap import radius as ldap_server_radius

    def func(session):
        ldap_server_radius.setup(ldap_params, user_list=user_list)(session)
        install_packages(session)
        # configure,
        copy_config(session)
        base_shell.service_on(session, 'radiusd')
        radtest(user_list)(session)
    return func
