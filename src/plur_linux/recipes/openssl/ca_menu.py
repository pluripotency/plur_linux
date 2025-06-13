import copy
from mini.ansi_colors import green, yellow 
from mini.menu import choose_num, select_2nd
from mini import misc
from plur_linux.lib.lib_selection import get_obj_by_definition
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
DEFAULT_CA_CERT_TOML = r"""
country_name = 'JP'
state = 'Tokyo'
city = 'FakeCity'
organization = 'FakeOrg'
org_unit = 'FakeOrgUnit'
common_name = 'FakeCA'
passphrase = 'password'
expiration_days = 365
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
DEFAULT_SERVER_CERT_TOML = r"""
country_name = 'JP'
state = 'Tokyo'
city = 'FakeCity'
organization = 'FakeOrg'
org_unit = 'FakeOrgUnit'
common_name = 'server1.test.local'
passphrase = ''
p12_password = 'password'
"""


def input_ca_params(ca_params):
    return get_obj_by_definition(misc.toml.loads(CA_CERT_DEFINITION_TOML_STR), ca_params)


def input_server_params(server_params):
    return get_obj_by_definition(misc.toml.loads(SERVER_CERT_DEFINITION_TOML_STR), server_params)


def input_params(self):
    if not hasattr(self, 'ca_params'):
        self.ca_params = misc.toml.loads(DEFAULT_CA_CERT_TOML)
    if not hasattr(self, 'server_parasm_list'):
        server_name_list = [
            'okta-wlan.test.local',
            'emailauth-wlan.test.local',
            'okta-forti.test.local',
            # 'server1.test.local',
            # 'server2.test.local',
            # 'server3.test.local',
        ]
        default_server_params = misc.toml.loads(DEFAULT_SERVER_CERT_TOML)
        server_params_list = []
        for server_name in server_name_list:
            server_params = copy.deepcopy(default_server_params)
            server_params['common_name'] = server_name
            server_params_list += [server_params]
        self.server_params_list = server_params_list
    while True:
        menu_list = [
            'Change CA params',
            f'Change Server params({",".join(server_name_list)})',
            'Next',
        ]
        num = choose_num(menu_list)
        if num == len(menu_list) - 1:
            break
        elif num == 0:
            ca_params = input_ca_params(ca_params)
        elif num == 1:
            print(yellow('Not implemented yet.'))

    return {
        'ca_params': self.ca_params,
        'server_params_list': self.server_params_list,
    }


def run_params(ca_params, server_params_list):
    ca_root_dir = '/etc/pki/CA'
    ca_passphrase = ca_params['passphrase']
    server_name_list = []
    for server_params in server_params_list:
        server_name_list += [server_params['common_name']]

    @session_wrap.sudo
    def func(session):
        ca.create_ca(ca_root_dir, ca_params, alt_names=server_name_list)(session)
        for server_params in server_params_list:
            ca.create_server_cert(ca_root_dir, server_params)(session)
            server_name = server_params['common_name']
            p12_password = server_params['p12_password']
            ca.sign_csr(ca_root_dir, server_name, ca_passphrase)(session)
            ca.create_p12(ca_root_dir, server_name, p12_password)(session)
    return func


@session_wrap.sudo
def setup_serverx_test_local(session):

    ca_root_dir = '/etc/pki/CA'
    ca_passphrase = 'password'
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

    server_name_list = [f'server{num}.test.local' for num in range(1, 5)]
    ca.create_ca(ca_root_dir, ex_ca_params, alt_names=server_name_list)(session)
    for server_name in server_name_list:
        ex_server_cert_params = {
            'country_name': 'JP',
            'state': 'Tokyo',
            'city': 'FakeCity',
            'organization': 'FakeOrg',
            'org_unit': 'FakeOrgUnit',
            'common_name': server_name,
            'passphrase': '',
        }
        ca.create_server_cert(ca_root_dir, ex_server_cert_params)(session)
        ca.sign_csr(ca_root_dir, server_name, ca_passphrase)(session)
        ca.create_p12(ca_root_dir, server_name, 'password')(session)


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

    main_menu_list = [
        ['Input params', input_params],
        ['serverx.test.local on a8desk', on_a8(setup_serverx_test_local)],
    ]
    select_2nd(main_menu_list, green('Select from FortiGate Recipes'), vertical=True)
