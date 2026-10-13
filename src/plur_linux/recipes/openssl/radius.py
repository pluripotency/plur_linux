from plur import base_shell
from plur_linux.recipes.openssl import commands as cmd
from plur_linux.recipes.openssl import ca


def create_rad_files(rad_cert_dir='/etc/raddb/certs/', rad_ca_dir='/etc/raddb/certs/'):
    return {
        'rad_cert_dir': rad_cert_dir,
        'rad_ca_dir': rad_ca_dir,
        'radius_key': rad_cert_dir + 'server.key',
        'key_passphrase': 'radpass',
        'radius_csr': rad_cert_dir + 'server.csr',
        'radius_cert': rad_cert_dir + 'server.crt',
        'radius_p12': rad_cert_dir + 'server.p12',
        'p12_password': 'p12pass',
        'radius_pem': rad_cert_dir + 'server.pem',
        'pem_password': 'pempass',
        'cakey': rad_ca_dir + 'ca.key',
        'capem': rad_ca_dir + 'ca.pem',
        'cader': rad_ca_dir + 'ca.der',
        'rad_dh': rad_cert_dir + 'dh',
        'rad_random': rad_cert_dir + 'random',
        'rad_cert_issuer': "/C=jp/ST=Tokyo/L=Shinjuku/O=TED"
    }


def create_server_crt_params(server_name, passphrase=''):
    return {
        'country_name': 'JP',
        'state': 'Tokyo',
        'city': 'FakeCity',
        'organization': 'FakeOrg',
        'org_unit': 'FakeOrgUnit',
        'common_name': server_name,
        'passphrase': passphrase,
    }


def create_radius_keys(server_name):
    def func(session):
        ca_files = ca.create_ca_path_params('/etc/pki/CA/')
        rad_files = create_rad_files()
        rad_params = create_server_crt_params(server_name)

        session.sudo_i()
        if not base_shell.check_command_exists(session, 'radiusd'):
            base_shell.yum_install(session, {'packages': ['freeradius', 'freeradius-utils']})

        # Initialize freeradius certs base files
        base_shell.work_on(session, '/etc/raddb/certs/')
        base_shell.run(session, 'make destroycerts')
        base_shell.run(session, 'make index.txt')
        base_shell.run(session, 'make serial')
        base_shell.run(session, 'make random')
        base_shell.run(session, 'make dh')

        # init needed dir
        base_shell.create_dir(session, rad_files['rad_cert_dir'])
        base_shell.create_dir(session, rad_files['rad_ca_dir'])

        cakey = ca_files['cakey_pem']
        cakey_passphrase = ca_files['cakey_passphrase']
        cacert = ca_files['cacert_pem']

        radius_key = rad_files['radius_key']
        radius_csr = rad_files['radius_csr']
        key_passphrase = rad_files['key_passphrase']

        base_shell.work_on(session, rad_files['rad_cert_dir'])
        cmd.generate_server_key_and_csr(radius_key, radius_csr, key_passphrase, rad_params)(session)

        # need run on CA
        radius_crt = rad_files['radius_cert']
        cmd.generate_server_crt(radius_csr, radius_crt, cakey, cacert, cakey_passphrase)(session)

        radius_p12 = rad_files['radius_p12']
        p12_pass = rad_files['p12_password']
        radius_pem = rad_files['radius_pem']
        pem_pass = rad_files['pem_password']
        cmd.generate_server_p12(radius_key, key_passphrase, radius_crt, radius_p12, p12_pass)(session)
        cmd.generate_server_pem(radius_p12, radius_pem, p12_pass, pem_pass)(session)
        cmd.verify_server_pem(cacert, radius_pem)(session)
        session.su_exit()
    return func


def create_user_files(user, cert_dir):
    return {
        'cert_dir': cert_dir,
        'user_key': f'{user}.key',
        'user_csr': f'{user}.csr',
        'user_crt': f'{user}.crt',
        'user_p12': f'{user}.p12',
        'user_pem': f'{user}.pem',
        'key_pass': 'key_pass',
        'p12_pass': 'p12_pass',
        'pem_pass': 'pem_pass'
    }


def create_user(user_name, passphrase):
    def func(session):
        ca_files = ca.create_ca_path_params('/etc/pki/CA/')
        user_params = create_server_crt_params(user_name, passphrase)
        user_files = create_user_files(user_name, ca_files['server_cert_dir'])

        cakey = ca_files['cakey_pem']
        cakey_passphrase = ca_files['cakey_passphrase']
        cacert = ca_files['cacert_pem']

        user_dir = user_files['cert_dir']

        user_key = user_dir + '/' + user_files['user_key']
        user_csr = user_dir + '/' + user_files['user_csr']
        user_crt = user_dir + '/' + user_files['user_crt']
        user_p12 = user_dir + '/' + user_files['user_p12']
        user_pem = user_dir + '/' + user_files['user_pem']
        key_pass = user_files['key_pass']
        p12_pass = user_files['p12_pass']
        pem_pass = user_files['pem_pass']

        session.sudo_i()
        base_shell.work_on(session, user_dir)
        cmd.generate_server_key_and_csr(user_key, user_csr, key_pass, user_params)(session)
        cmd.generate_server_crt(user_csr, user_crt, cakey, cacert, cakey_passphrase)(session)
        cmd.generate_server_p12(user_key, key_pass, user_crt, user_p12, p12_pass)(session)
        cmd.generate_server_pem(user_p12, user_pem, p12_pass, pem_pass)(session)
        session.su_exit()
    return func

