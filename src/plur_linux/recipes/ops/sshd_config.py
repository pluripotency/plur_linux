#! /usr/bin/env python
from plur import base_shell
from plur import session_wrap
listen_port = lambda port_num='22': [[r'^#\?Port [1-9][0-9]*', f'Port {port_num}']]
listen_address = lambda address='0.0.0.0': [[r'^#\?ListenAddress \([^:]\)\+', f'ListenAddress {address}']]
protocol = lambda num: [[r'^#\?Protocol \([0-9]\)', f'Protocol {num}']]
permit_root_login = lambda flag='no': [[r'^.\?PermitRootLogin .*', f'PermitRootLogin {flag}']]
strict_modes = lambda flag='yes': [[r'^#\?StrictModes .*', f'StrictModes {flag}']]
pubkey_authentication = lambda : [
    [r'^#\?PubkeyAuthentication .*', f'PubkeyAuthentication yes']
    , [r'^#\?AuthorizedKeysFile.*', r'AuthorizedKeysFile\t.ssh\/authorized_keys']
]
password_authentication = lambda flag='yes': [
    [r'^#\?PasswordAuthentication .*', f'PasswordAuthentication {flag}']
    , [r'^#\?PermitEmptyPasswords .*', 'PermitEmptyPasswords no']
]
gssapi_authentication = lambda flag='no': [[r'^#\?GSSAPIAuthentication .*', f'GSSAPIAuthentication {flag}']]
allow_tcp_forwarding = lambda flag='no': [[r'^#\?AllowTcpForwarding .*$', f'AllowTcpForwarding {flag}']]
x11_forwarding = lambda flag='no': [[r'^#\?X11Forwarding .*$', f'X11Forwarding {flag}']]
use_dns = lambda flag='no': [[r'^#\?UseDNS .*', f'UseDNS {flag}']]


def root_ok_server(listen='0.0.0.0'):
    return [
        listen_port('22')
        , listen_address(listen)
        , protocol('2')
        , permit_root_login('yes')
        , strict_modes('yes')
        , pubkey_authentication()
        , password_authentication('yes')
        , gssapi_authentication('no')
        , allow_tcp_forwarding('no')
        , x11_forwarding('no')
        , use_dns('no')
    ]


def root_without_password(listen='0.0.0.0'):
    return [
        listen_port('22')
        , listen_address(listen)
        , protocol('2')
        , permit_root_login('without-password')
        , strict_modes('yes')
        , pubkey_authentication()
        , password_authentication('yes')
        , gssapi_authentication('no')
        , allow_tcp_forwarding('no')
        , x11_forwarding('no')
        , use_dns('no')
    ]


def tcp_forwarding(listen='0.0.0.0'):
    return [
        listen_port('22')
        , listen_address(listen)
        , protocol('2')
        , permit_root_login('without-password')
        , strict_modes('yes')
        , pubkey_authentication()
        , password_authentication('yes')
        , gssapi_authentication('no')
        , allow_tcp_forwarding('yes')
        , x11_forwarding('no')
        , use_dns('no')
    ]


def strict_server(listen='0.0.0.0', port='22', pass_auth='no'):
    return [
        listen_port(port)
        , listen_address(listen)
        , protocol('2')
        , permit_root_login('no')
        , strict_modes('yes')
        , pubkey_authentication()
        , password_authentication(pass_auth)
        , gssapi_authentication('no')
        , allow_tcp_forwarding('no')
        , x11_forwarding('no')
        , use_dns('no')
    ]


def apply_policy(policy):
    @session_wrap.sudo
    def func(session):
        sshd_config_path = '/etc/ssh/sshd_config'
        base_shell.create_backup(session, sshd_config_path)
        src_file = sshd_config_path + '.org'
        exp_list = []
        for pol in policy:
            exp_list += pol
        base_shell.sed_pipe(session, src_file, sshd_config_path, exp_list)
        base_shell.service_on(session, 'sshd')
    return func


def apply_and_restart(sshd_config):
    """
    sshd_config = {
        'policy': 'strict_server',
        'listen': '0.0.0.0'
    }
    """
    listen = '0.0.0.0'
    if 'listen' in sshd_config:
        listen = sshd_config['listen']

    runs = strict_server(listen)
    if 'policy' in sshd_config:
        policy = sshd_config['policy']
        if policy == 'root_without_password':
            runs = root_without_password(listen)
        elif policy == 'tcp_forward_server':
            runs = tcp_forwarding(listen)
        elif policy == 'strict_server':
            runs = strict_server(listen)
        elif policy == 'root_ok_server':
            runs = root_ok_server(listen)
    return apply_policy(runs)

