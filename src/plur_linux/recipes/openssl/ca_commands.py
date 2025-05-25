from plur.base_shell import run, create_sequence, sed_pipe
from plur.output_methods import waitprompt, success_f, send_line, new_send_line, send_pass, wait


def create_ca_conf(ca_root, ca_openssl_cnf, alt_names):
    def func(session):
        openssl_cnf = '/etc/pki/tls/openssl.cnf'
        sed_pipe(session, openssl_cnf, ca_openssl_cnf, [
            [
                '= /etc/pki/CA',
                f'= {ca_root}'
            ], [
                '^# req_extensions = v3_req # The extensions to add to a certificate request$',
                'req_extensions = v3_req'
            ], [
                '^. v3_req .$',
                r'subjectAltName = @alt_names\n\n[ v3_req ]'
            ], [
                '^. v3_ca .$',
                r'subjectAltName = @alt_names\n\n[ v3_ca ]'
            ]
        ])
        dns_altnames = [f'DNS.{i} = {name}' for i, name in enumerate(alt_names)]
        [run(session, f'echo {line} >> {ca_openssl_cnf}') for line in [
            '',
            '[alt_names]'
        ] + dns_altnames]
    return func


def generate_private_key(private_key_full_path):
    return lambda session: run(session, f'openssl genrsa -out {private_key_full_path} 2048')


def generate_certificate_request(private_key_full_path, csr_full_path, ca_openssl_cnf, params):
    def func(session):
        action = f'openssl req -new -sha256 -key {private_key_full_path} -out {csr_full_path} -config {ca_openssl_cnf}'
        rows = [
            [r'Country Name \(2 letter code\).+$', send_line, params['country_name'], ''],
            [r'State or Province Name \(full name\).+$', send_line, params['state'], ''],
            [r'Locality Name \(eg, city\).+$', send_line, params['city'], ''],
            [r'Organization Name \(eg, company\).+$', send_line, params['organization'], ''],
            ['Organizational Unit Name.+$', send_line, params['org_unit'], ''],
            [r"Common Name \(eg, your name or your server's hostname\).+$", send_line, params['common_name'], ''],
            ['Email Address.+$', send_line, '', ''],
            ['A challenge password.+$', send_line, '', ''],
            ['An optional company name.+$', wait([[session.nodes[-1].waitprompt, success_f(True)]], new_send_line('')), '', '']
        ]
        return session.do(create_sequence(action, rows))
    return func


def generate_aes256_private_key(private_key_full_path, passphrase):
    def func(session):
        # PRIVATE KEY
        action = 'openssl genrsa -aes256 -out %s 2048' % private_key_full_path
        rows = [
            ['Enter PEM pass phrase:', send_pass, passphrase],
            ['Enter pass phrase for %s:' % private_key_full_path, send_pass, passphrase, 'Entering Passphrase'],
            ['Verifying - Enter pass phrase for %s:' % private_key_full_path, send_pass, passphrase, 'Verifying Passphrase'],
            ['', waitprompt, '', '%s generated' % private_key_full_path]
        ]
        return session.do(create_sequence(action, rows))
    return func


def rows_pem(key, passphrase, params):
    rows = [
        ['Enter pass phrase for %s:' % key, send_pass, passphrase, ''],
        [r'Country Name \(2 letter code\).+$', send_line, params['country_name'], ''],
        [r'State or Province Name \(full name\).+$', send_line, params['state'], ''],
        [r'Locality Name \(eg, city\).+$', send_line, params['city'], ''],
        [r'Organization Name \(eg, company\).+$', send_line, params['organization'], ''],
        ['Organizational Unit Name.+$', send_line, params['org_unit'], ''],
        [r"Common Name \(eg, your name or your server's hostname\).+$", send_line, params['common_name'], ''],
        ['Email Address.+$', send_line, '', ''],
        ['', waitprompt, '', 'cacert generated']
    ]
    return rows


def generate_x509_pem(private_key_full_path, passphrase, pem_full_path, params, expiration_days=365):
    def func(session):
        # CERTIFICATE
        action = f'openssl req -new -sha256 -x509 -key {private_key_full_path} -out {pem_full_path} -days {expiration_days}'
        return session.do(create_sequence(action, rows_pem(private_key_full_path, passphrase, params)))
    return func


def create_index_serial(session):
    run(session, 'touch index.txt')
    run(session, 'echo "01" > serial')


def sign_certificate_request(csr_full_path, cert_full_path, openssl_crt, passphrase):
    def func(session):
        action = f'openssl ca -config {openssl_crt} -md sha256 -out {cert_full_path} -infiles {csr_full_path}'
        rows = [
            ['Enter pass phrase for .+:', send_pass, passphrase, ''],
            [r'Sign the certificate\? \[y/n\]:', send_line, 'y', ''],
            [r'1 out of 1 certificate requests certified, commit\? \[y/n\]', send_line, 'y', ''],
            ['', waitprompt, '', 'created client cer']
        ]
        return session.do(create_sequence(action, rows))
    return func


def export_pkcs12(cert_path, key_path, ca_cert_path, pfx_path, export_password):
    def func(session):
        action = f'openssl pkcs12 -export -in {cert_path} -inkey {key_path} -certfile {ca_cert_path} -out {pfx_path}'
        rows = [
            ['Verifying - Enter Export Password', send_pass, export_password],
            ['Enter Export Password', send_pass, export_password],
            ['', waitprompt, '']
        ]
        return session.do(create_sequence(action, rows))
    return func


def is_valid_cert(ca_root, server_name):
    def func(session):
        action = f'grep {server_name} {ca_root}/index.txt' + "| awk '{print $1}'"
        rows = [
            ['V', wait([[session.nodes[-1].waitprompt, success_f(True)]], new_send_line('')), True, ''],
            ['R', wait([[session.nodes[-1].waitprompt, success_f(True)]], new_send_line('')), True, '']
        ]
        return session.do(create_sequence(action, rows))
    return func


def revoke(ca_root, server_name, cacrl_pem):
    def func(session):
        server_crt = f'{ca_root}/certs/{server_name}/server.crt'
        action = f'openssl ca -gencrl -revoke {server_crt} -out {cacrl_pem}'
        run(session, action)
    return func

