import os
from plur import base_shell
from plur import output_methods
from plur import session_wrap
from plur_linux.recipes.ops import ops


def install_packages(session):
    base_shell.yum_install(session, {'packages': [
        'freeradius',
        'freeradius-utils',
        'freeradius-mysql',

        'mariadb-server',
    ]})


def backup_to_dir(file_path, dst_dir_path):
    def func(session):
        file_name = os.path.basename(file_path)
        if not base_shell.check_dir_exists(session, dst_dir_path):
            base_shell.create_dir(session, dst_dir_path)
        if not base_shell.check_file_exists(session, f'{dst_dir_path}/{file_name}.org'):
            base_shell.create_backup(session, file_path)
            base_shell.run(session, f'mv {file_path}.org {dst_dir_path}')
    return func


def conf_mysql(mysql_root_password, db_name, db_user_name, db_user_pass):
    def set_mycnf(session):
        backup_dir = '~/mysql'
        my_cnf_path = "/etc/my.cnf"
        append_text = "character-set-server=utf8"
        backup_to_dir(my_cnf_path, backup_dir)(session)

        base_shell.run(session, f"sed -i -e 's/{append_text}//g' {my_cnf_path}")
        base_shell.run(session, f"echo {append_text} >> {my_cnf_path}")

        base_shell.service_on(session, 'mariadb')

    def set_root_password(session):
        nonlocal mysql_root_password
        queries = f"""\"
        UPDATE mysql.user SET Password=PASSWORD('{mysql_root_password}') WHERE User='root';
        FLUSH PRIVILEGES;\"
        """
        session.do(base_shell.create_sequence(f'mysql -u root -p -e {queries}', [
            ['Enter password: ', output_methods.new_send_line(''), ''],
            ['', output_methods.waitprompt, ''],
        ]))

    def delete_default(session):
        nonlocal mysql_root_password
        queries = f"""\"
        DELETE FROM mysql.user WHERE User='';
        DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
        DROP DATABASE test;
        DELETE FROM mysql.db WHERE Db='test' OR Db='test\\\\_%';
        FLUSH PRIVILEGES;\"
        """
        session.do(base_shell.create_sequence(f'mysql -u root -p -e {queries}', [
            ['Enter password: ', output_methods.new_send_line(mysql_root_password), ''],
            ['', output_methods.waitprompt, ''],
        ]))

    def create_radius_db(session):
        nonlocal mysql_root_password
        nonlocal db_name
        nonlocal db_user_name
        nonlocal db_user_pass
        queries = f"""\"
        CREATE DATABASE {db_name};
        grant all privileges on {db_name}.* to {db_user_name}@localhost identified by '{db_user_pass}';
        FLUSH PRIVILEGES;\"
        """
        session.do(base_shell.create_sequence(f'mysql -u root -p -e {queries}', [
            ['Enter password: ', output_methods.new_send_line(mysql_root_password), ''],
            ['', output_methods.waitprompt, ''],
        ]))

    def conf_mysql_for_radius(session):
        schema = "/etc/raddb/mods-config/sql/main/mysql/schema.sql"
        session.do(base_shell.create_sequence(f"mysql -u root -p radius < {schema}", [
            ['Enter password: ', output_methods.new_send_line(mysql_root_password), ''],
            ['', output_methods.waitprompt, ''],
        ]))

    @session_wrap.sudo
    def func(session):
        [f(session) for f in [
            set_mycnf,
            set_root_password,
            delete_default,
            create_radius_db,
            conf_mysql_for_radius,
        ]]
    return func


def conf_radius(db_name, db_user_name, db_user_pass, radius_clients, mysql_addr='127.0.0.1'):
    def set_sql(session):
        nonlocal db_user_name
        nonlocal db_user_pass
        nonlocal mysql_addr

        sql_availble_path = "/etc/raddb/mods-available/sql"
        sql_enabled_path = "/etc/raddb/mods-enabled/sql"
        base_shell.run(session, f"\cp -f {sql_availble_path} {sql_enabled_path}")
        base_shell.sed_pipe(session, sql_availble_path, sql_enabled_path, [
            ['driver = "rlm_sql_null"', 'driver = "rlm_sql_mysql"'],
            ['dialect = "sqlite"', 'dialect = "mysql"'],
            [r'#\tserver = "localhost"', f'\\tserver = "{mysql_addr}"'],
            [r'#\tport = 3306', r'\tport = 3306'],
            [r'#\tlogin = "radius"', f'\\tlogin = "{db_user_name}"'],
            [r'#\tpassword = "radpass"', f'\\tpassword = "{db_user_pass}"'],
            [r'#\tread_clients = yes', r'\tread_clients = yes'],
        ])

        base_shell.run(session, f"chgrp -h radiusd {sql_enabled_path}")

    def set_radius_conf(session):
        bk_dir = '~/raddb'
        rad_conf = '/etc/raddb/radiusd.conf'
        rad_conf_org = f'{bk_dir}/radiusd.conf.org'
        backup_to_dir(rad_conf, bk_dir)(session)
        base_shell.sed_pipe(session, rad_conf_org, rad_conf, [
            ['auth = no', 'auth = yes'],
            ['auth_badpass = no', 'auth_badpass = yes'],
            ['auth_goodpass = no', 'auth_goodpass = yes'],
        ])

    def set_clients_conf(session):
        nonlocal db_name
        nonlocal db_user_name
        nonlocal db_user_pass
        nonlocal mysql_addr
        bk_dir = '~/raddb'
        clients_conf = '/etc/raddb/clients.conf'
        backup_to_dir(clients_conf, bk_dir)(session)

        # erase clients.conf
        base_shell.run(session, f'echo > {clients_conf}')

        # add cliens to mysql
        insert_queries = []
        for cl in radius_clients:
            insert_queries += [
                f"DELETE FROM nas WHERE nasname='{cl['ipaddr']}';",
                f"INSERT INTO nas (nasname, shortname, ports, secret) VALUES ('{cl['ipaddr']}', '{cl['name']}', 0, '{cl['secret']}');",
            ]
        insert_str = '\n'.join(insert_queries)
        queries = f'"{insert_str}"'
        base_shell.run(session, f"mysql -h {mysql_addr} -u{db_user_name} -p{db_user_pass} {db_name} -e {queries}")

    def enable_service_after_mariadb(session):
        radiusd_conf = '/etc/systemd/system/multi-user.target.wants/radiusd.service'
        base_shell.service_off(session, 'radiusd')
        base_shell.run(session, f'rm -f {radiusd_conf}')
        base_shell.service_on(session, 'radiusd')
        append_mariadb = 'After=mariadb.service'
        base_shell.run(session, f'sed -i 3a{append_mariadb} {radiusd_conf}')

    @session_wrap.sudo
    def func(session):
        [f(session) for f in [
            set_sql,
            set_radius_conf,
            set_clients_conf,
            enable_service_after_mariadb,
        ]]
    return func


def conf_daloradius(db_name, db_user_name, db_user_pass):
    @session_wrap.sudo
    def func(session):
        nonlocal db_name
        nonlocal db_user_name
        nonlocal db_user_pass

        base_shell.work_on(session, '/tmp')
        base_shell.yum_install(session, {'packages': [
            'epel-release',
        ]})
        base_shell.yum_install(session, {'packages': [
            'httpd',
            'wget',
            'unzip',

            'php mod_php php-cli php-mysqlnd php-devel php-gd php-mcrypt',
            'php-pear-DB php-mbstring php-xml php-pear',
        ]})
        dalo_root = '/var/www/html/daloradius'
        if not base_shell.check_dir_exists(session, dalo_root):
            if not base_shell.check_dir_exists(session, '/tmp/master.zip'):
                url = "https://github.com/lirantal/daloradius/archive/master.zip"
                base_shell.run(session, f"wget {url}")
            base_shell.run(session, 'unzip master.zip')
            base_shell.run(session, 'mv -f daloradius-master daloradius')
            schema1 = "daloradius/contrib/db/fr2-mysql-daloradius-and-freeradius.sql"
            session.do(base_shell.create_sequence(f"mysql -u {db_user_name} -p radius < {schema1}", [
                ['Enter password: ', output_methods.new_send_line(db_user_pass), ''],
                ['', output_methods.waitprompt, ''],
            ]))
            schema2 = "daloradius/contrib/db/mysql-daloradius.sql"
            session.do(base_shell.create_sequence(f"mysql -u {db_user_name} -p radius < {schema2}", [
                ['Enter password: ', output_methods.new_send_line(db_user_pass), ''],
                ['', output_methods.waitprompt, ''],
            ]))

            base_shell.run(session, 'mv -f daloradius /var/www/html/')
            base_shell.run(session, f'chown -R apache.apache {dalo_root}')
            base_shell.run(session, f'chmod 664 {dalo_root}/library/daloradius.conf.php')

            bk_dir = '~/dalo'
            dalo_conf = f'{dalo_root}/library/daloradius.conf.php'
            backup_to_dir(dalo_conf, bk_dir)(session)

            escaped_db_user_pass = db_user_pass.replace('!', r'\!')

            sed_list = [
                f"sed -i \"s/$configValues\['CONFIG_DB_USER'\] = 'root';/$configValues\['CONFIG_DB_USER'\] = '{db_user_name}';/\" {dalo_conf}",
                f"sed -i \"s/$configValues\['CONFIG_DB_PASS'\] = '';/$configValues\['CONFIG_DB_PASS'\] = '{escaped_db_user_pass}';/\" {dalo_conf}",
                f"sed -i \"s/$configValues\['CONFIG_DB_NAME'\] = 'radius';/$configValues\['CONFIG_DB_NAME'\] = '{db_name}';/\" {dalo_conf}",
            ]
            [base_shell.run(session, a) for a in sed_list]

        base_shell.service_on(session, 'httpd')
    return func


def grant_remote_access(mysql_root_password, db_name, remote_grant_target, remote_grant_password):
    def func(session):
        nonlocal mysql_root_password
        nonlocal db_name
        nonlocal remote_grant_target
        nonlocal remote_grant_password
        queries = f"""\"
        use {db_name}
        GRANT ALL PRIVILEGES ON {db_name}.* TO {remote_grant_target} IDENTIFIED BY '{remote_grant_password}' with grant option;
        FLUSH PRIVILEGES;\"
        """
        session.do(base_shell.create_sequence(f'mysql -u root -p -e {queries}', [
            ['Enter password: ', output_methods.new_send_line(mysql_root_password), ''],
            ['', output_methods.waitprompt, ''],
        ]))
    return func


def radtest(user_list):
    return lambda session: [base_shell.run(session, 'radtest %s %s 127.0.0.1 0 testing123' % (u[0], u[1])) for u in user_list]


def setup(dalo=True):
    def func(session):
        mysql_root_password = "P@55w0rd!"
        db_name = 'radius'
        db_user_name = "radius"
        db_user_pass = "P@55w0rd!"

        grant_ip = '192.168.122.%'
        remote_grant_target = f"{db_user_name}@'{grant_ip}'"
        remote_grant_password = 'P@55w0rd!'

        radius_clients = [
            {
                'name': 'localnet',
                'ipaddr': '192.168.122.0/24',
                'secret': 'P@55w0rd!',
            }
        ]

        func_list = [
            install_packages,
            conf_mysql(mysql_root_password, db_name, db_user_name, db_user_pass),
            conf_radius(db_name, db_user_name, db_user_pass, radius_clients),
            grant_remote_access(mysql_root_password, db_name, remote_grant_target, remote_grant_password)
        ]
        if dalo:
            func_list += [
                conf_daloradius(db_name, db_user_name, db_user_pass)
            ]
        [f(session) for f in func_list]

    return func


if __name__ == '__main__':
    from plur import base_node
    node = base_node.Linux('dalo', password='', platform='centos7')
    node.access_ip = '192.168.122.240'
    session_wrap.ssh(node)(setup(False))()
