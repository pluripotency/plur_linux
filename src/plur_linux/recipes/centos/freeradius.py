import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell


def create(session, filename, data):
    if not shell.check_file_exists(session, filename):
        shell.create_backup(session, filename)
        shell.here_doc(session, filename, data.split('\n'))


def set_raddb_params(session):
    raddb_dir = '/etc/raddb'
    session.sudo_i()

    shell.work_on(session, raddb_dir)

    functions = [
        eap_conf
    ]
    for func in functions:
        mode, filename, data = func()
        if mode is 'create':
            create(session, filename, data)

    session.su_exit()


def eap_conf():
    ### minimal? setting for EAP-TLS
    mode = 'create'
    filename = '/etc/raddb/eap.conf'
    data = """
eap {
    default_eap_type = tls
    timer_expire     = 60
    ignore_unknown_eap_types = no
    cisco_accounting_username_bug = no
    max_sessions = 4096
    tls {
            certdir = ${confdir}/certs
            cadir = ${confdir}/certs

            private_key_password = whatever
            private_key_file = ${certdir}/server.pem

            certificate_file = ${certdir}/server.pem

            CA_file = ${cadir}/ca.pem

            dh_file = ${certdir}/dh
            random_file = ${certdir}/random

            CA_path = ${cadir}
    #check_cert_issuer = "/C=GB/ST=Berkshire/L=Newbury/O=My Company Ltd"
    #       check_cert_cn = %{User-Name}
            cipher_list = "DEFAULT"
            ecdh_curve = "prime256v1"
    }
}
"""
    return mode, filename, data


def proxy_conf():
    mode = 'create'
    filename = '/etc/raddb/proxy.conf'
    data = """
proxy server {
    default_fallback = no
}

home_server localhost {
    ipaddr = 127.0.0.1

    port = 1812

    secret = testing123
    response_window = 20
    zombie_period = 40

    revive_interval = 120
    status_check = status-server
    check_interval = 30
    num_answers_to_alive = 3
    max_outstanding = 65536

    coa {
        # Initial retransmit interval: 1..5
        irt = 2

        # Maximum Retransmit Timeout: 1..30 (0 == no maximum)
        mrt = 16

        # Maximum Retransmit Count: 1..20 (0 == retransmit forever)
        mrc = 5

        # Maximum Retransmit Duration: 5..60
        mrd = 30
    }
}

home_server_pool my_auth_failover {
    type = fail-over
    home_server = localhost
}
realm LOCAL {
        #  If we do not specify a server pool, the realm is LOCAL, and
        #  requests are not proxied to it.
}
realm example.com {
    authhost = radius21.v50.local:1812
    accthost = radius21.v50.local:1813
    secret   = testing123
}
realm NULL {
    authhost = radius21.v50.local:1812
    accthost = radius21.v50.local:1813
    secret   = testing123
}
"""
    return mode, filename, data

"""
/etc/raddb/radiusd.conf
        auth = yes
        #  Log passwords with the authentication requests.
        #  auth_badpass  - logs password if it's rejected
        #  auth_goodpass - logs password if it's correct
        #
        #  allowed values: {no, yes}
        #
        auth_badpass = yes
        auth_goodpass = no
"""


def clients_conf():
    mode = 'append'
    filename = '/etc/raddb/clients.conf'
    data = """
client 10.50.0.0/24 {
        secret  = testing123
        shortname = vlan50
}
"""
    return mode, filename, data


def users():
    mode = 'append'
    filename = '/etc/raddb/users'
    data = """
"eaptest"       Auth-Type := EAP, Cleartext-Password := "eaptest"
        Reply-Message = "Hello, %{User-Name}",
        Session-Timeout = 120,
        Termination-Action = 1,
        Extreme-Netlogin-Only = Enabled,
        Extreme-Netlogin-Vlan = vlan127
"vpf12" Auth-Type := EAP, Cleartext-Password := "vpf12"
        Reply-Message = "Hello, %{User-Name}",
        Session-Timeout = 120,
        Termination-Action = 1,
        Extreme-Netlogin-Only = Enabled,
        Extreme-Netlogin-Vlan = vlan50

"user@v50.local" Auth-Type := EAP
        Reply-Message = "Hello, %{User-Name}",
        Session-Timeout = 120,
        Termination-Action = 1,
        Extreme-Netlogin-Only = Enabled,
        Extreme-Netlogin-Vlan = vlan50
"""
    return mode, filename, data
