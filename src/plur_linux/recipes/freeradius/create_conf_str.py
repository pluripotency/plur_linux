from mini import misc

ex_client_list = [
    {
        'ip': '192.168.0.11',
        'secret': 'password',
        'name': 'example1',
    },
    {
        'ip': '192.168.0.12',
        'secret': 'password',
    }
]


def create_clients_conf_str(client_list):
    """
    >>> print(create_clients_conf_str(ex_client_list))
    client 192.168.0.11 {
      secret = password
      shortname = example1
    }
    client 192.168.0.12 {
      secret = password
    }
    <BLANKLINE>
    """
    clients_conf_str = ''
    for client in client_list:
        ip = client['ip']
        secret = client['secret']
        client_str = f'client {ip} ' + '{\n' + f'  secret = {secret}\n'
        if 'name' in client:
            client_str += f'  shortname = {client["name"]}\n'
        clients_conf_str += client_str + '}\n'
    return clients_conf_str


ex_user_list = [
    {
        'username': '525400abcdef',
        'password': 'password',
        'vid': 4084
    },
    {
        'username': '525400123456',
        'password': 'password',
        'vid': 2
    }
]


def create_users_str(user_list):
    """
    >>> print(create_users_str(ex_user_list))
    525400abcdef Cleartext-Password := "password"
      Tunnel-Type = VLAN,
      Tunnel-Medium-Type = IEEE-802,
      Tunnel-Private-Group-Id = 4084
    525400123456 Cleartext-Password := "password"
      Tunnel-Type = VLAN,
      Tunnel-Medium-Type = IEEE-802,
      Tunnel-Private-Group-Id = 2
    <BLANKLINE>
    """
    users_str = ''
    for user_dict in user_list:
        username = user_dict['username']
        password = user_dict['password']
        user_str = f'{username} Cleartext-Password := "{password}"\n'
        if 'vid' in user_dict:
            vid = user_dict['vid']
            user_str += misc.del_indent(f"""
              Tunnel-Type = VLAN,
              Tunnel-Medium-Type = IEEE-802,
              Tunnel-Private-Group-Id = {vid}
            
            """)
        users_str += user_str
    return users_str


ex_proxy_list = [
    {
        'name': 'proxy1',
        'ip': '192.168.0.11',
        'secret': 'password'
    },
    {
        'name': 'proxy2',
        'ip': '192.168.0.12',
        'secret': 'password'
    },
    {
        'name': 'test_failover',
        'pool': [
            'proxy1'
            , 'proxy2'
        ]
    },
    {
        'realm': r'~.*\.local$',
        'auth_pool': 'test_failover',
    },
    {
        'realm': 'NULL',
        'auth_pool': 'test_failover'
    },
    {
        'realm': r'DEFAULT',
        'auth_pool': 'test_failover'
    }
]


def create_home_server_str(proxy_dict):
    """
    >>> print(create_home_server_str(ex_proxy_list[0]))
    home_server proxy1 {
        type = auth
        ipaddr = 192.168.0.11
        port = 1812
        secret = password
        require_message_authenticator = yes
        response_window = 20
        zombie_period = 40
        revive_interval = 120
        #status_check = status-server
        status_check = none
        check_interval = 30
        num_answers_to_alive = 3
        max_outstanding = 65536
        coa {
            irt = 2
            mrt = 16
            mrc = 5
            mrd = 30
        }
    }
    <BLANKLINE>
    """
    name = proxy_dict['name']
    ip = proxy_dict['ip']
    secret = proxy_dict['secret']
    proxy_str = f'home_server {name} ' + '{\n'
    proxy_str += f'    type = auth\n    ipaddr = {ip}\n    port = 1812\n    secret = {secret}\n'
    return proxy_str + misc.del_indent("""
        require_message_authenticator = yes
        response_window = 20
        zombie_period = 40
        revive_interval = 120
        #status_check = status-server
        status_check = none
        check_interval = 30
        num_answers_to_alive = 3
        max_outstanding = 65536
        coa {
            irt = 2
            mrt = 16
            mrc = 5
            mrd = 30
        }
    }
    
    """)


ex_home_server_pool = {
    'name': 'test_failover',
    'pool': [
        'proxy1'
        , 'proxy2'
    ]
}


def create_home_server_pool_str(proxy_dict):
    """
    >>> print(create_home_server_pool_str(ex_home_server_pool))
    home_server_pool test_failover {
        type = fail-over
        home_server = proxy1
        home_server = proxy2
    }
    <BLANKLINE>
    """
    pool_str = f'home_server_pool {proxy_dict["name"]} ' + '{\n    type = fail-over\n'
    for member in proxy_dict['pool']:
        pool_str += f'    home_server = {member}\n'
    pool_str += '}\n'
    return pool_str


ex_realm = {
    'realm': r'~.*\.local$',
    'auth_pool': 'test_failover',
}


def create_realm_str(proxy_dict):
    """
    >>> print(create_realm_str(ex_realm))
    realm ~.*\.local$ {
        auth_pool = test_failover
        nostrip
    }
    <BLANKLINE>
    """
    realm_str = f'realm {proxy_dict["realm"]} ' + '{\n'
    return realm_str + f'    auth_pool = {proxy_dict["auth_pool"]}\n    nostrip\n' + '}\n'


def create_proxy_conf_str(proxy_list):
    """
    >>> print(create_proxy_conf_str(ex_proxy_list))
    proxy server {
        default_fallback = no
    }
    <BLANKLINE>
    home_server proxy1 {
        type = auth
        ipaddr = 192.168.0.11
        port = 1812
        secret = password
        require_message_authenticator = yes
        response_window = 20
        zombie_period = 40
        revive_interval = 120
        #status_check = status-server
        status_check = none
        check_interval = 30
        num_answers_to_alive = 3
        max_outstanding = 65536
        coa {
            irt = 2
            mrt = 16
            mrc = 5
            mrd = 30
        }
    }
    home_server proxy2 {
        type = auth
        ipaddr = 192.168.0.12
        port = 1812
        secret = password
        require_message_authenticator = yes
        response_window = 20
        zombie_period = 40
        revive_interval = 120
        #status_check = status-server
        status_check = none
        check_interval = 30
        num_answers_to_alive = 3
        max_outstanding = 65536
        coa {
            irt = 2
            mrt = 16
            mrc = 5
            mrd = 30
        }
    }
    home_server_pool test_failover {
        type = fail-over
        home_server = proxy1
        home_server = proxy2
    }
    realm ~.*\.local$ {
        auth_pool = test_failover
        nostrip
    }
    realm NULL {
        auth_pool = test_failover
        nostrip
    }
    realm DEFAULT {
        auth_pool = test_failover
        nostrip
    }
    <BLANKLINE>
    """
    proxy_conf_str = misc.del_indent("""
    proxy server {
        default_fallback = no
    }\n\n
    """)
    for proxy_dict in proxy_list:
        if 'pool' in proxy_dict:
            proxy_conf_str += create_home_server_pool_str(proxy_dict)
        elif 'realm' in proxy_dict:
            proxy_conf_str += create_realm_str(proxy_dict)
        else:
            proxy_conf_str += create_home_server_str(proxy_dict)
    return proxy_conf_str
