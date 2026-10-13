#! /usr/bin/env python
from plur import base_shell
from plur import output_methods
from plur_linux.recipes.docker import dock_net
from plur_linux.recipes.docker import dock_util
from plur_linux.recipes.docker import mariadb
from plur_linux.recipes.docker.freeradius_mariadb import db_queries
from plur_linux.recipes.docker.freeradius_mariadb import freeradius
from plur_linux.recipes.docker.phpmyadmin import phpmyadmin_setup


def create_params(mysql_root_password, db_container_name):
    def func(seed):
        db_params = {
            'mysql_root_password': mysql_root_password,
            'db_name': seed['name'],
            'db_user': 'radius',
            'db_pass': 'P@55w0rd!',
            'users': [
                {'username': 'user_'+seed['name'], 'password': 'password'},
            ],
            'clients': [{
                'client_name': 'auth_net',
                'ipaddr': '192.168.122.0/24',
                'secret': 'P@55w0rd!',
            }]
        }
        radius_params = {
            'container_name': seed['name'],
            'db_address': db_container_name,
            'db_port': '3306',
            'db_name': db_params['db_name'],
            'db_user': db_params['db_user'],
            'db_pass': db_params['db_pass'],
        }
        front_net_params = {
            'net_name': 'localnet',
            'subnet': '192.168.122.0/24',
            'gateway': '192.168.122.1',
            'address': '192.168.122.' + seed['ip_seed'],
            'iface': 'eth0',
        }
        return [db_params, radius_params, front_net_params]
    return func


def run(session):
    # no firewalld is needed for macvlan front net

    back_net = 'back_net'
    back_net_params = f'--net {back_net}'

    db_container_name = 'mariadb'
    mysql_root_password = 'P@55w0rd!'

    param_list = list(map(create_params(mysql_root_password, db_container_name), [
        {
            'name': 'radius1',
            'ip_seed': '100',
        },
        {
            'name': 'radius2',
            'ip_seed': '101',
        }
    ]))
    phpmyadmin_params = {
        'db_address': db_container_name,
        'db_user': param_list[0][0]['db_user'],
        'db_pass': param_list[0][0]['db_pass'],
    }
    base_shell.run(session, f'docker network create {back_net}')

    if not dock_util.is_running(session, db_container_name):
        mariadb.start_docker(db_container_name, back_net_params, mysql_root_password)(session)
        # wait for db is ready
        session.do(base_shell.create_sequence(f'docker logs `docker ps -q -f name={db_container_name}` -f', [
            [': MySQL init process done. Ready for start up.', output_methods.new_send_control('c'), ''],
            ['', output_methods.waitprompt, ''],
        ]))
        dock_util.work_on(db_container_name)(session)
        dock_util.prepare_file(session, 'schema.sql')

        for param in param_list:
            db_params = param[0]
            db_queries.run(db_container_name, db_params, db_params['clients'], db_params['users'])(session)

    for num, param in enumerate(param_list):
        radius_params = param[1]
        net_p = param[2]
        contaner_name = radius_params['container_name']

        freeradius.run(contaner_name, back_net_params, radius_params)(session)
        if num == 0:
            base_shell.run(session, dock_net.create_macvlan_str(net_p['subnet'], net_p['gateway'], net_p['iface'], net_p['net_name']))
        base_shell.run(session, dock_net.attach_net_str(contaner_name, net_p['net_name'], net_p['address']))

    phpmyadmin_setup.run(phpmyadmin_params, '', back_net)(session)

