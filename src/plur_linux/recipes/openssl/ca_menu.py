import copy
from mini.ansi_colors import yellow 
from mini.menu import choose_num, get_obj_by_definition, get_input
from mini import misc
from plur import session_wrap
from plur_linux.recipes.openssl import ca
CA_CERT_DEFINITION_TOML_STR = r"""
[country_name]
type = 'string'
message = 'Input Country Name(ex: JP)'
exp = '\w.'
[state]
type = 'string'
message = 'Input State(ex: Tokyo)'
exp = '\w.'
[city]
type = 'string'
message = 'Input City(ex: Shibuya)'
exp = '\w.'
[organization]
type = 'string'
message = 'Input Organization(ex: Company)'
exp = '\w.'
[org_unit]
type = 'string'
message = 'Input Organization Unit(ex: Sales1)'
exp = '\w.'
[common_name]
type = 'string'
message = 'Input Common Name(ex: SalesUser1)'
exp = '\w.'
[passphrase]
message = 'Input Passphrase'
type = 'string'
exp = '\w.'
[expiration_days]
message = 'Input Expiration Days(ex: 365)'
type = 'int'
exp = '\d{1,5}'
"""
SERVER_CERT_DEFINITION_TOML_STR = r"""
[country_name]
type = 'string'
message = 'Input Country Name(ex: JP)'
exp = '\w.'
[state]
type = 'string'
message = 'Input State(ex: Tokyo)'
exp = '\w.'
[city]
type = 'string'
message = 'Input City(ex: Shibuya)'
exp = '\w.'
[organization]
type = 'string'
message = 'Input Organization(ex: Company)'
exp = '\w.'
[org_unit]
type = 'string'
message = 'Input Organization Unit(ex: Eng1)'
exp = '\w.'
[common_name]
type = 'string'
message = 'Input Common Name(ex: server1.test.local)'
exp = '\w.'
[passphrase]
message = 'Input Passphrase'
type = 'string'
exp = '\w.'
[p12_password]
message = 'Input p12 password'
type = 'string'
exp = '\w.'
"""
DEFAULT_CERT_TOML = r"""
country_name = 'JP'
state = 'Tokyo'
city = 'FakeCity'
organization = 'FakeOrg'
org_unit = 'FakeOrgUnit'
"""
DEFAULT_CA_CERT_TOML = DEFAULT_CERT_TOML + r"""
common_name = 'FakeCA'
passphrase = 'password'
expiration_days = 365
"""
DEFAULT_SERVER_CERT_TOML = DEFAULT_CERT_TOML + r"""
common_name = 'server1.test.local'
passphrase = ''
p12_password = 'password'
"""
DEFAULT_SERVER_NAME_LIST = [
    'okta-wlan.test.local',
    'emailauth-wlan.test.local',
    'okta-forti.test.local',
    'server1.test.local',
    'server2.test.local',
    'server3.test.local',
]
DEFAULT_ALT_NAMES = [
    '*.test.local'
]

def create_default_ca_params():
    return misc.toml.loads(DEFAULT_CA_CERT_TOML)

def create_default_server_params():
    default_server_params = misc.toml.loads(DEFAULT_SERVER_CERT_TOML)
    server_params_list = []
    for server_name in DEFAULT_SERVER_NAME_LIST:
        server_params = copy.deepcopy(default_server_params)
        server_params['common_name'] = server_name
        server_params_list += [server_params]
    return server_params_list

def input_ca_params(ca_params):
    return get_obj_by_definition(misc.toml.loads(CA_CERT_DEFINITION_TOML_STR), ca_params)

def input_server_params(server_params):
    return get_obj_by_definition(misc.toml.loads(SERVER_CERT_DEFINITION_TOML_STR), server_params)

def input_params(self):
    if not hasattr(self, 'ca_root_dir'):
        self.ca_root_dir = '$HOME/Downloads/ca'
    if not hasattr(self, 'ca_params'):
        self.ca_params = create_default_ca_params()
    if not hasattr(self, 'server_parasm_list'):
        self.server_params_list = create_default_server_params()
    server_name_list = [item['common_name'] for item in self.server_params_list]
    while True:
        menu_list = [
            f'Change CA dir({self.ca_root_dir})',
            'Change CA params',
            f'Change Server params({",".join(server_name_list)})',
            'Next',
        ]
        num = choose_num(menu_list)
        if num == len(menu_list) - 1:
            break
        elif num == 0:
            self.ca_root_dir = get_input(expression='.+', message='Input CA dir by abs path: ')
        elif num == 1:
            self.ca_params = input_ca_params(self.ca_params)
        elif num == 2:
            print(yellow('Not implemented yet.'))

    return {
        'ca_root_dir': self.ca_root_dir,
        'ca_params': self.ca_params,
        'server_params_list': self.server_params_list,
    }

def run_params(ca_params, server_params_list, ca_root_dir):
    server_name_list = []
    for server_params in server_params_list:
        server_name_list += [server_params['common_name']]

    def func(session):
        nonlocal ca_root_dir
        ca_root_dir = ca.resolve_path_on_session(ca_root_dir)(session)
        ca_files = ca.create_ca_path_params(ca_root_dir)
        ca_openssl_cnf = ca_files['openssl_cnf']
        ca_passphrase = ca_params['passphrase']
        ca.create_ca(ca_files, ca_params)(session)
        ca.cmd.append_alt_names(ca_openssl_cnf, alt_names=DEFAULT_ALT_NAMES)(session)
        for server_params in server_params_list:
            ca.create_server_cert(ca_root_dir, server_params)(session)
            server_name = server_params['common_name']
            p12_password = server_params['p12_password']
            ca.sign_csr(ca_root_dir, server_name, ca_passphrase)(session)
            ca.create_p12(ca_root_dir, server_name, p12_password)(session)
    if ca_root_dir.startswith('/home') or ca_root_dir.startswith('$HOME') or ca_root_dir.startswith('~'):
        return func
    else:
        return session_wrap.sudo(func)

if __name__ == '__main__':
    def on_a8(func):
        import getpass
        from plur import base_node
        hostname = 'a8dev'
        username = 'worker'
        access_ip = '192.168.10.8'
        password = getpass.getpass("Password: ")
        node = base_node.Linux(hostname, username, password, platform='almalinux8')
        node.access_ip = access_ip
        session_wrap.ssh(node)(func)

    ca_root_dir = '/etc/pki/CA'
    ca_params = create_default_ca_params()
    server_params_list = create_default_server_params()
    on_a8(run_params(ca_params, server_params_list, ca_root_dir))
