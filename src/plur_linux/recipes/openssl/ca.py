from plur import base_shell
from . import ca_commands as cmd


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


def create_ca(ca_root_dir, ca_params, alt_names):
    def func(session):
        ca_files = create_ca_path_params(ca_root_dir)
        cakey_pem = ca_files['cakey_pem']
        cacert_pem = ca_files['cacert_pem']
        ca_passphrase = ca_params['passphrase']
        ca_expiration_days = ca_params['expiration_days']

        if base_shell.check_file_exists(session, cakey_pem):
            print('CA key already exists.')
        else:
            base_shell.create_dir(session, cakey_pem, is_file_path=True)
            base_shell.create_dir(session, ca_files['newcerts_dir'])

            cmd.create_ca_conf(ca_root_dir, ca_files['openssl_cnf'], alt_names)(session)
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


if __name__ == "__main__":
    import getpass
    from plur import base_node
    from plur import session_wrap
    def setup_example(session):

        ca_passphrase = 'c@p@sw0rd'
        ex_ca_params = {
            'country_name': 'JP',
            'state': 'Tokyo',
            'city': 'FakeCity',
            'organization': 'FakeOrg',
            'org_unit': 'FakeOrgUnit',
            'common_name': 'FakeCA',
            'passphrase': ca_passphrase,
            'expiration_days': 365,
        }

        server_name = 'test.local'
        ex_server_cert_params = {
            'country_name': 'JP',
            'state': 'Tokyo',
            'city': 'FakeCity',
            'organization': 'FakeOrg',
            'org_unit': 'FakeOrgUnit',
            'common_name': server_name,
            'passphrase': '',
            'p12_password': 'password',
        }

        ca_root_dir = '/etc/pki/CA'

        create_ca(ca_root_dir, ex_ca_params, alt_names=[server_name])(session)
        create_server_cert(ca_root_dir, ex_server_cert_params)(session)
        sign_csr(ca_root_dir, server_name, ca_passphrase)(session)

        p12_password = ex_server_cert_params['p12_password']
        create_p12(ca_root_dir, server_name, p12_password)

    hostname = 'a8desk'
    username = 'worker'
    access_ip = '192.168.10.192'
    password = getpass.getpass("Password: ")
    node = base_node.Linux(hostname, username, password, platform='almalinux8')
    node.access_ip = access_ip

    session_wrap.ssh(node)(setup_example)()

