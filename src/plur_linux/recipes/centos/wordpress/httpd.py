from plur import base_shell


def backup_and_sed_pipe(file_path, lines):
    def func(session):
        base_shell.create_backup(session, file_path)
        base_shell.sed_pipe(session, file_path + '.org', file_path, lines)
    return func


def etc_httpd_conf(server_name):

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

    def configure_httpd_conf():
        lines = [
            ['^#ServerName www.example.com:80$', 'ServerName %s:80' % server_name]
        ]
        lines += base_security()
        return backup_and_sed_pipe('/etc/httpd/conf/httpd.conf', lines)

    def func(session):
        configure_httpd_conf()(session)

    return func


def configure(server_name):
    def func(session):
        etc_httpd_conf(server_name)(session)
        base_shell.service_on(session, 'httpd')
    return func

