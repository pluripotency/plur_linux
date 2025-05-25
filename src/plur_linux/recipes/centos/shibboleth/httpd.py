from plur import base_shell


def backup_and_sed_pipe(file_path, lines):
    def func(session):
        base_shell.create_backup(session, file_path)
        base_shell.sed_pipe(session, file_path + '.org', file_path, lines)
    return func


def add_lines_for_httpd_certs(httpd_certs):
    def func(session):
        nonlocal httpd_certs
        lines = []
        if 'server_crt' in httpd_certs:
            if base_shell.check_file_exists(session, httpd_certs['server_crt']):
                server_crt_path = '/etc/pki/tls/certs/server.crt'
                base_shell.run(session, '\cp -f %s %s' % (httpd_certs['server_crt'], server_crt_path))
                lines += [
                    [
                        '^SSLCertificateFile /etc/pki/tls/certs/localhost.crt$',
                        'SSLCertificateFile %s' % server_crt_path
                    ]
                ]
        if 'server_key' in httpd_certs:
            if base_shell.check_file_exists(session, httpd_certs['server_key']):
                server_key_path = '/etc/pki/tls/private/server.key'
                base_shell.run(session, '\cp -f %s %s' % (httpd_certs['server_key'], server_key_path))
                lines += [
                    [
                        '^SSLCertificateKeyFile /etc/pki/tls/private/localhost.key$',
                        'SSLCertificateKeyFile %s' % server_key_path
                    ]
                ]
        if 'chain_crt' in httpd_certs:
            if base_shell.check_file_exists(session, httpd_certs['chain_crt']):
                chain_crt_path = '/etc/pki/tls/certs/server-chain.crt'
                base_shell.run(session, '\cp -f %s %s' % (httpd_certs['chain_crt'], chain_crt_path))
                lines += [
                    [
                        '^#SSLCertificateChainFile /etc/pki/tls/certs/server-chain.crt$',
                        'SSLCertificateChainFile %s' % chain_crt_path
                    ]
                ]
        return lines

    return func


def etc_httpd_conf_d(server_name, httpd_certs=None, shib_type='idp'):
    def blank_unneeded(session):
        dir_path = '/etc/httpd/conf.d/'
        unneeded = [
            'welcome.conf',
            'autoindex.conf',
            'userdir.conf'
        ]
        [base_shell.create_backup(session, dir_path + u) for u in unneeded]
        [base_shell.run(session, 'echo > %s' % (dir_path + u)) for u in unneeded]

    def create_proxy_to_ajp(session):
        base_shell.here_doc(session, '/etc/httpd/conf.d/virtualhost-localhost80.conf', [
            '<VirtualHost localhost:80>',
            'ProxyPass /idp/ ajp://localhost:8009/idp/',
            '</VirtualHost>',
        ])

    def configure_ssl_conf(server_name, httpd_certs):
        def set_name(server_name):
            return [
                ['^#ServerName www.example.com:443$', 'ServerName %s:443' % server_name]
            ]

        def set_proxy_from_443_to_ajp(server_name):
            return [
                [
                    '^#ServerName www.example.com:443$',
                    'ServerName %s:443\\nProxyPass /idp/ ajp://localhost:8009/idp/' % server_name
                ]
            ]

        def base_security():
            ssl_cipher_suite = 'SSLCipherSuite ' + ':'.join([
                'ALL',
                '!aNULL',
                '!eNULL',
                '!EXP',
                '!RC4',
                '!DES',
                '!IDEA',
                '!MD5',
                '!SEED'
            ])
            ssl_cipher_suite_2017 = 'SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH'
            return [
                [
                    '^SSLCipherSuite HIGH:MEDIUM:!aNULL:!MD5:!SEED:!IDEA$',
                    '#SSLCipherSuite HIGH:MEDIUM:!aNULL:!MD5:!SEED:!IDEA\\n' + ssl_cipher_suite
                ],
                [
                    '^SSLProtocol all -SSLv2$',
                    'SSLProtocol all -SSLv2 -SSLv3'
                ]

            ]

        def fun(session):
            nonlocal server_name
            nonlocal httpd_certs
            nonlocal shib_type
            pipe_lines = base_security()
            if shib_type == 'idp':
                pipe_lines += set_proxy_from_443_to_ajp(server_name)
            elif shib_type == 'sp':
                pipe_lines += set_name(server_name)
            # selinux does not allow certs path is different from default
            if httpd_certs is not None:
                pipe_lines += add_lines_for_httpd_certs(httpd_certs)(session)
            backup_and_sed_pipe('/etc/httpd/conf.d/ssl.conf', pipe_lines)(session)
        return fun

    def func(session):
        nonlocal server_name
        nonlocal httpd_certs
        nonlocal shib_type
        configure_ssl_conf(server_name, httpd_certs)(session)
        if shib_type == 'idp':
            blank_unneeded(session)
            create_proxy_to_ajp(session)
        elif shib_type == 'sp':
            blank_unneeded(session)

    return func


def etc_httpd_conf(server_name):

    def set_server_name(server_name):
        return [
            ['^#ServerName www.example.com:80$', 'ServerName %s:80' % server_name]
        ]

    def base_security():
        return [
            ['^    Options Indexes FollowSymLinks$', '    Options FollowSymLinks'],
            [
                '^IncludeOptional conf\.d/\*\.conf$',
                'IncludeOptional conf\.d/*\.conf\\n\\n' +
                'TraceEnable off\\n' +
                'ServerTokens ProductOnly\\n' +
                'ServerSignature off\\n'
            ]
        ]

    def configure_httpd_conf(server_name):
        lines = set_server_name(server_name)
        lines += base_security()
        return backup_and_sed_pipe('/etc/httpd/conf/httpd.conf', lines)

    def func(session):
        configure_httpd_conf(server_name)(session)

    return func


def etc_httpd_conf_modules_d():
    def blank_unneeded(session):
        dir_path = '/etc/httpd/conf.modules.d/'
        unneeded = [
            '00-dav.conf',
            '00-lua.conf',
            '00-cgi.conf',
            '01-cgi.conf'
        ]
        [base_shell.create_backup(session, dir_path + u) for u in unneeded]
        [base_shell.run(session, 'echo > %s' % (dir_path + u)) for u in unneeded]

    def func(session):
        blank_unneeded(session)

    return func


def configure(server_name, httpd_certs=None):
    def func(session):
        etc_httpd_conf(server_name)(session)
        etc_httpd_conf_d(server_name, httpd_certs)(session)
        etc_httpd_conf_modules_d()(session)
        base_shell.service_on(session, 'httpd')
    return func


def configure_for_sp(server_name, httpd_certs=None):
    def func(session):
        etc_httpd_conf(server_name)(session)
        etc_httpd_conf_d(server_name, httpd_certs, shib_type='sp')(session)
    return func
