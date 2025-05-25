from plur.base_shell import *
from plur.output_methods import *
from plur import session_wrap

pki_certs_dir = '/etc/pki/tls/certs'
ex_cert_params = {
    'country_name': 'JP',
    'state': 'Tokyo',
    'city': 'Shinjuku',
    'organization': 'TED',
    'org_unit': 'std',
    'common_name': 'ldaps.local',
    'email': '',
}


def rows_pem(params):
    rows = [
        ['Country Name \(2 letter code\).+$', send_line, params["country_name"]],
        ['State or Province Name \(full name\).+$', send_line, params["state"]],
        ['Locality Name \(eg, city\).+$', send_line, params["city"]],
        ['Organization Name \(eg, company\).+$', send_line, params["organization"]],
        ['Organizational Unit Name.+$', send_line, params["org_unit"]],
        ["Common Name \(eg, your name or your server's hostname\).+$", send_line, params["common_name"]],
        ['Email Address.+$', send_line, params['email']],
        ['A challenge password', send_line, ''],
        ['An optional company name', send_line, ''],
        ['', waitprompt, '']
    ]
    return rows


def create_cert(cert_params):
    def func(session):
        run(session, f'cd {pki_certs_dir}')

        cert_head = cert_params['common_name']
        key = f'{cert_head}.key'
        temp_password = 'password' # this is used for deleting passphrase
        session.do(create_sequence(f'make {key}', [
            ['Enter pass phrase:', send_pass, temp_password],
            ['', waitprompt, True],
        ]))
        session.do(create_sequence(f'openssl rsa -in {key} -out {key}', [
            [f'Enter pass phrase for {key}', send_pass, temp_password],
            ['', waitprompt, True],
        ]))

        csr = f'{cert_head}.csr'
        session.do(create_sequence(f'make {csr}', rows_pem(cert_params)))

        crt = f'{cert_head}.crt'
        run(session, f'openssl req -x509 -days 3650 -in {csr} -key {key} -out {crt}')

        ldap_cert_dir = '/etc/openldap/certs'
        run(session, f'cp ca-bundle.crt {ldap_cert_dir}')
        run(session, f'mv {cert_head}.* {ldap_cert_dir}')
        run(session, f'chown ldap:ldap {ldap_cert_dir}/{cert_head}.*')
    return func


def load_cert_ldif(session):
    run(session, 'cd')

    cert_head = 'server'
    cert_ldif_file = 'tls_cert.ldif'
    cert_ldif_contents = f"""
dn: cn=config
changetype: modify
add: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/openldap/certs/ca-bundle.crt
-
replace: olcTLSCertificateFile
olcTLSCertificateFile: /etc/openldap/certs/{cert_head}.crt
-
replace: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/openldap/certs/{cert_head}.key
"""
    here_doc(session, cert_ldif_file, cert_ldif_contents.split('\n')[1:])
    run(session, f'ldapadd -Y EXTERNAL -H ldapi:// -f {cert_ldif_file}')


def add_config(session):
    slapd_path = '/etc/sysconfig/slapd'
    if not check_test(session, f'if egrep -q "SLAPD_URLS=.+ ldaps:///" {slapd_path};'):
        sed_replace(session,
                    'SLAPD_URLS="ldapi:/// ldap:///"',
                    'SLAPD_URLS="ldapi:/// ldap:/// ldaps:///"',
                    slapd_path)

    ldap_conf_path = '/etc/openldap/ldap.conf'
    reqcert = '"TLS_REQCERT never"'
    if not check_line_exists_in_file(session, ldap_conf_path, reqcert):
        run(session, f'echo {reqcert} >> {ldap_conf_path}')


def setup(cert_params=None):
    if cert_params is None:
        cert_params = ex_cert_params

    @session_wrap.sudo
    def func(session):
        if 'common_name' in cert_params:
            from recipes import firewalld
            # port 636
            firewalld.configure(
                services=['ldaps'],
                ports=[], add=True)(session)
            if not check_file_exists(session, f'{pki_certs_dir}/{cert_params["common_name"]}.key'):
                create_cert(cert_params)(session)
                add_config(session)
                load_cert_ldif(session)
                service_on(session, 'slapd')
    return func
