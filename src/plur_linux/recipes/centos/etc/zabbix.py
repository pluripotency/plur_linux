
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell
from plur import output_methods


def install_zabbix_repo(session):
    repo = [
        'http://repo.zabbix.com/zabbix/2.4/rhel/6/x86_64/zabbix-release-2.4-1.el6.noarch.rpm'
    ]
    shell.yum_install(session, {'packages': repo})


def setup_zabbix_server(session, password):
    zabbix_server_conf = '/etc/zabbix/zabbix_server.conf'
    shell.create_backup(session, zabbix_server_conf)
    shell.sed_pipe(session,
        zabbix_server_conf + '.org',
        zabbix_server_conf,
        [
            ['# DBHost=localhost', 'DBHost=localhost'],
            # ['PidFile=/var/run/zabbix/zabbix_server.pid', 'PidFile=/var/run/zabbix/zabbix_server_mysql.pid'],
            ['# DBPassword=', 'DBPassword=%s' % password]
        ]
    )
    shell.service_on(session, 'zabbix-server')


def setup_zabbix_agent(session, server_ip='127.0.0.1'):
    zabbix_agentd_conf = '/etc/zabbix/zabbix_agentd.conf'
    shell.create_backup(session, zabbix_agentd_conf)
    shell.sed_pipe(session,
        zabbix_agentd_conf + '.org',
        zabbix_agentd_conf,
        [
            ['Server=127.0.0.1', 'Server=%s' % server_ip],
            ['ServerActive=127.0.0.1', 'ServerActive=%s' % server_ip],
            ['Hostname=Zabbix server', 'Hostname=%s' % session.nodes[-1].fqdn]
        ]
    )
    shell.service_on(session, 'zabbix-agent')


def setup_zabbix_httpd(session):
    zabbix_httpd_conf = '/etc/httpd/conf.d/zabbix.conf'
    shell.create_backup(session, zabbix_httpd_conf)
    shell.sed_pipe(session,
        zabbix_httpd_conf + '.org',
        zabbix_httpd_conf,
        [
            ['    # php_value date.timezone Europe/Riga', '    php_value date.timezone Asia/Tokyo']
        ]
    )
    shell.service_on(session, 'httpd')


def setup_zabbix(session, password='zabbix'):
    setup_zabbix_server(session, password)
    setup_zabbix_httpd(session)


def install_php(session):
    shell.yum_install(session, {'packages': [
        'php',
        'php-mbstring',
        'php-pear'
    ]})
    php_ini = '/etc/php.ini'
    shell.create_backup(session, php_ini)
    shell.sed_pipe(session,
        php_ini + '.org',
        php_ini,
        [
            [';date.timezone =', 'date.timezone = "Asia/Tokyo"']
        ]
    )
    httpd_conf = '/etc/httpd/conf/httpd.conf'
    shell.create_backup(session, httpd_conf)
    shell.sed_pipe(session,
        httpd_conf + '.org',
        httpd_conf,
        [
            ['DirectoryIndex indes.html index.html.var', 'DirectoryIndex indes.html index.php']
        ]
    )


def install_httpd(session):
    shell.yum_install(session, {'packages': [
        'httpd'
    ]})

    shell.run(session, 'rm -f /etc/httpd/conf.d/welcome.conf /var/www/error/noindex.html')
    shell.service_on(session, 'httpd')


def install_mysql(session):
    shell.yum_install(session, {'packages': [
        'mysql-server'
    ]})
    mycnf = '/etc/my.cnf'
    settings = ['', 'character-set-server=utf8']
    if not shell.count_by_egrep(session, settings[1], mycnf):
        shell.append_lines(session, mycnf, settings)
    shell.service_on(session, 'mysqld')


def mysql_login(session, user='root', password=''):
    action = 'mysql -u %s -p' % user
    rows = [['Enter password:', output_methods.send_line, password, '']]
    rows += [['mysql> ', output_methods.success, '', '']]
    session.do(shell.create_sequence(action, rows))


def mysql_passwd(session, user='root', current_password='', change_password='zabbix'):
    action = 'mysql -u %s -p' % user
    rows = [['Enter password:', output_methods.send_line, current_password, '']]
    rows += [['mysql> ', output_methods.success, True, '']]
    rows += [['', output_methods.waitprompt, False, '']]
    if session.do(shell.create_sequence(action, rows)):
        action = "set password for '%s'@'localhost' = password('%s');" % (user, change_password)
        rows = [['mysql> ', output_methods.success, '', '']]
        session.do(shell.create_sequence(action, rows))
        shell.run(session, 'exit')


def setup_zabbix_mysql1(session, user='zabbix', password='zabbix'):
    mysql_login(session, 'root', password)

    # "grant all privileges on zabbix.* to '%s'@'localhost' identified by '%s';" % (user, password),
    # "grant all privileges on zabbix.* to '%s'@" % user + "'%'" + " identified by '%s';" % password,
    actions = [
        'create database zabbix;',
        "grant all privileges on zabbix.* to %s@'localhost' identified by '%s';" % (user, password),
        "grant all privileges on zabbix.* to %s@" % user + "'%'" + " identified by '%s';" % password,
        'flush privileges;'
    ]
    rows = [['mysql> ', output_methods.success, '', '']]
    [session.do(shell.create_sequence(action, rows)) for action in actions]
    shell.run(session, 'exit')


def setup_zabbix_mysql2(session, user='root', password='zabbix'):
    shell.work_on(session, '/usr/share/doc/zabbix-server-mysql-*/create/')
    actions = [
        'mysql -u %s -p %s < schema.sql' % (user, password),
        'mysql -u %s -p %s < images.sql' % (user, password),
        'mysql -u %s -p %s < data.sql' % (user, password)
    ]
    rows = [['Enter password:', output_methods.send_line, password, '']]
    rows += [['', output_methods.waitprompt, '', '']]
    for action in actions:
        session.do(shell.create_sequence(action, rows))
    shell.work_on(session, '~')


def install_zabbix_agentd(server_ip):
    def func(session):
        sudo = False
        if session.nodes[-1].username != 'root':
            sudo = True
            session.sudo_i()
        install_zabbix_repo(session)
        shell.yum_install(session, {'packages': ['zabbix-agent']})
        setup_zabbix_agent(session, server_ip)
        if sudo:
            session.su_exit()
    return func


def install_zabbix_server(session):
    sudo = False
    if session.nodes[-1].username != 'root':
        sudo = True
        session.sudo_i()

    install_php(session)
    install_httpd(session)
    install_mysql(session)

    packages = [
        'php-mysql',
        'php-gd',
        'php-xml',
        'php-bcmath'
    ]
    shell.yum_install(session, {'packages': packages})

    install_zabbix_repo(session)

    zabbix_server_packages = [
        'zabbix-server-mysql',
        'zabbix-web-mysql',
        'zabbix_get',
        'zabbix-agent'
    ]
    shell.yum_install(session, {'packages': zabbix_server_packages})

    mysql_passwd(session, 'root', '', 'zabbix')
    setup_zabbix_mysql1(session)
    setup_zabbix_mysql2(session)
    setup_zabbix_agent(session, server_ip='127.0.0.1')
    setup_zabbix(session)

    if sudo:
        session.su_exit()
