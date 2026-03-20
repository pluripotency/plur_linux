from plur import base_shell
from . import ca_commands as cmd

def resolve_path_on_session(org_path='$HOME/Downloads/ca'):
    def func(session):
        if org_path.startswith('$HOME') or org_path.startswith('~'):
            capt_list = base_shell.run(session, f'echo {org_path}').splitlines()
            return capt_list[0]
        return org_path
    return func

def create_ca_path_params(ca_root_dir='/etc/pki/CA'):
    return {
        'openssl_cnf': ca_root_dir + '/ca.conf',
        'ca_root_dir': ca_root_dir,
        'cakey_pem':   ca_root_dir + '/private/cakey.pem',
        'cacert_pem':  ca_root_dir + '/cacert.pem',
        'cacrl_pem':   ca_root_dir + '/ca.crl',
        'server_cert_dir': ca_root_dir + '/certs',
        'newcerts_dir': ca_root_dir + '/newcerts'
    }

def create_ca(ca_files, ca_params):
    def func(session):
        ca_root_dir = ca_files['ca_root_dir']
        cakey_pem = ca_files['cakey_pem']
        cacert_pem = ca_files['cacert_pem']
        ca_passphrase = ca_params['passphrase']
        ca_expiration_days = ca_params['expiration_days']

        if base_shell.check_file_exists(session, cakey_pem):
            print('CA key already exists.')
        else:
            base_shell.create_dir(session, cakey_pem, is_file_path=True)
            base_shell.create_dir(session, ca_files['newcerts_dir'])

            cmd.create_ca_conf(ca_root_dir, ca_files['openssl_cnf'])(session)
            base_shell.work_on(session, ca_root_dir)
            cmd.generate_aes256_private_key(cakey_pem, ca_passphrase)(session)
            cmd.generate_x509_pem(cakey_pem, ca_passphrase, cacert_pem, ca_params, ca_expiration_days)(session)
            cmd.create_index_serial(session)
    return func

def create_server_cert(ca_root_dir, server_cert_params):
    def func(session):
        ca_files = create_ca_path_params(ca_root_dir)
        openssl_cnf = ca_files['openssl_cnf']
        cert_dir = ca_files['server_cert_dir']
        server_dir = cert_dir + '/' + server_cert_params['common_name']

        server_key = server_dir + '/server.key'
        server_csr = server_dir + '/server.csr'

        base_shell.work_on(session, server_dir)
        cmd.generate_private_key(server_key)(session)
        cmd.generate_certificate_request(server_key, server_csr, openssl_cnf, server_cert_params)(session)
    return func

def sign_csr(ca_root_dir, server_name, ca_passphrase):
    def func(session):
        ca_files = create_ca_path_params(ca_root_dir)
        openssl_cnf = ca_files['openssl_cnf']
        cert_dir = ca_files['server_cert_dir']

        server_dir = cert_dir + '/' + server_name
        server_csr = server_dir + '/server.csr'
        server_crt = server_dir + '/server.crt'

        base_shell.work_on(session, server_dir)
        cmd.sign_certificate_request(server_csr, server_crt, openssl_cnf, ca_passphrase)(session)
    return func

def create_p12(ca_root_dir, server_name, export_password):
    def func(session):
        ca_files = create_ca_path_params(ca_root_dir)
        cacert_pem = ca_files['cacert_pem']
        cert_dir = ca_files['server_cert_dir']

        server_dir = cert_dir + '/' + server_name
        server_key = server_dir + '/server.key'
        server_crt = server_dir + '/server.crt'
        server_pfx = server_dir + '/server.p12'

        base_shell.work_on(session, server_dir)
        cmd.export_pkcs12(server_crt, server_key, cacert_pem, server_pfx, export_password)(session)
    return func

