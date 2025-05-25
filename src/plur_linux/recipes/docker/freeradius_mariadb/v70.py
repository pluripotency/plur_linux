#! /usr/bin/env python
from plur import base_shell
from plur import output_methods
from recipes.docker import dock_util
from recipes.docker import mariadb
from recipes.docker.freeradius_mariadb import db_queries
from recipes.docker.freeradius_mariadb import freeradius
from recipes.docker.freeradius_mariadb import nginx
from recipes.docker.phpmyadmin import phpmyadmin_setup
from recipes import firewalld


def create_params(mysql_root_password, db_container_name):
    def func(seed):
        db_params = {
            'mysql_root_password': mysql_root_password,
            'db_name': seed['name'],
            'db_user': seed['name'],
            'db_pass': seed['pass'],
            'users': [
                {'username': 'user_'+seed['name'], 'password': 'password'},
            ],
            'clients': seed['clients']
        }
        radius_params = {
            'container_name': 'rad_' + seed['name'],
            'db_address': db_container_name,
            'db_port': '3306',
            'db_name': db_params['db_name'],
            'db_user': db_params['db_user'],
            'db_pass': db_params['db_pass'],
        }
        front_net_params = seed['net']
        phpmyadmin_params = {
            'container_name': seed['name'],
            'db_address': db_container_name,
            'db_user': db_params['db_user'],
            'db_pass': db_params['db_pass'],
        }
        return [db_params, radius_params, front_net_params, phpmyadmin_params]
    return func


def run(session):
    # no firewalld is needed for macvlan front net

    back_net = 'back_net'
    back_net_params = f'--net {back_net}'

    db_container_name = 'mariadb'
    mysql_root_password = 'P@55w0rd!'

    param_list = list(map(create_params(mysql_root_password, db_container_name), [
        {
            'name': 'elem',
            'pass': 'P@55w0rd!',
            'net': {
                'net_name': 'elem_net',
                'subnet': '172.16.70.0/24',
                'gateway': '172.16.70.254',
                'address': '172.16.70.77',
                'iface': 'eth0',
            },
            'clients': [
                {
                    'client_name': 'elem_client',
                    'ipaddr': '172.16.1.38',
                    'secret': 'P@55w0rd!',
                },
                {
                    'client_name': 'elem_local',
                    'ipaddr': '172.16.70.0/24',
                    'secret': 'P@55w0rd!',
                }
            ]
        },
        {
            'name': 'juni',
            'pass': 'P@55w0rd!',
            'net': {
                'net_name': 'juni_net',
                'subnet': '172.16.80.0/24',
                'gateway': '172.16.80.254',
                'address': '172.16.80.78',
                'iface': 'eth1',
            },
            'clients': [
                {
                    'client_name': 'juni_client',
                    'ipaddr': '172.16.1.39',
                    'secret': 'P@55w0rd!',
                },
                {
                    'client_name': 'juni_local',
                    'ipaddr': '172.16.80.0/24',
                    'secret': 'P@55w0rd!',
                }
            ]
        }
    ]))

    firewalld.configure(['http'], add=True)(session)
    base_shell.run(session, f'docker network create {back_net}')

    if not dock_util.is_running(session, db_container_name):
        dock_util.work_on(db_container_name)(session)
        mariadb.start_docker(db_container_name, back_net_params, mysql_root_password)(session)
        # wait for db is ready
        session.do(base_shell.create_sequence(f'docker logs `docker ps -q -f name={db_container_name}` -f', [
            [': MySQL init process done. Ready for start up.', output_methods.new_send_control('c'), ''],
            ['', output_methods.waitprompt, ''],
        ]))
        dock_util.prepare_file(session, 'schema.sql')

        for param in param_list:
            db_params = param[0]
            db_queries.run(db_container_name, db_params, db_params['clients'], db_params['users'])(session)

    proxy_list = []
    for num, param in enumerate(param_list):
        radius_params = param[1]
        net_p = param[2]
        pma_p = param[3]
        rad_container_name = radius_params['container_name']
        pma_container_name = pma_p['container_name']

        freeradius.run(rad_container_name, back_net, net_p, radius_params)(session)

        phpmyadmin_setup.run(pma_container_name, back_net_params, pma_p)(session)
        proxy_list.append(pma_container_name)

    nginx.run('nginx', f'-p 80:80 {back_net_params}', proxy_list)(session)
