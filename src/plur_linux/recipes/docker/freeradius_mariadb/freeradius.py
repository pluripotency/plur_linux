import os
from plur import base_shell

from recipes.docker import dock_util
from recipes.docker import dock_net


def copy_scripts(session):
    cwd = os.path.dirname(__file__)
    to_copy = [
        [f'{cwd}/init.sh', 'init.sh'],
        [f'{cwd}/Dockerfile', 'Dockerfile'],
    ]
    [base_shell.heredoc_from_local(f[0], f[1])(session) for f in to_copy]


def create_docker_image(session):
    tag = 'freeradius'
    base_shell.run(session, 'chmod +x init.sh')
    base_shell.run(session, f'docker build . -t {tag}')


def create_start_docker_compose_lines(container_name, back_net, net_p, db_address, db_port, db_name, db_user, db_pass, log_output='stdout', radius_debug='no'):
    """
    >>> create_start_docker_compose_lines('rad_elem', 'back_net', { \
        'net_name': 'elem_net', 'address': '172.16.70.77', 'gateway': '172.16.70.254'}, \
        'mariadb', '3306', 'elem', 'elem', 'P@55w0rd!')
    """
    net_name = net_p['net_name']
    address  = net_p['address']
    gateway  = net_p['gateway']

    script = f"""
    version: "3.7"
    services:
      {container_name}:
        image: freeradius
        container_name: {container_name}
        restart: always
        cap_add:
          - NET_ADMIN
        command: /init.sh
        environment:
          - TZ=Asia/Tokyo
          - DB_ADDRESS={db_address}
          - DB_PORT={db_port}
          - DB_NAME={db_name}
          - DB_USER={db_user}
          - DB_PASS={db_pass}
          - LOG_OUTPUT={log_output}
          - RADIUS_DEBUG='{radius_debug}'
          - DEFAULT_GW={gateway}
        logging:
          driver: "syslog"
          options:
            syslog-address: "udp://localhost:514"
            tag: {container_name}
            syslog-facility: local1
        networks:
          {back_net}: ~
          {net_name}:
            ipv4_address: {address}
    networks:
      {back_net}:
        external:
          name: '{back_net}'
      {net_name}:
        external:
          name: '{net_name}'
    """.split('\n')[1:]
    script_lines = [s[4:] for s in script]
    return script_lines


def log_conf_reference():
    rsyslog = """
    if $syslogfacility-text='local1' then @172.16.9.165
    local1.*    /var/log/freeradius/radius.log
    & ~
    """

    script = """
    /var/log/freeradius/radius.log
    {
        daily
        dateext
        missingok
        rotate 93
        compress
        delaycompress
        sharedscripts
        postrotate
        /bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true
        endscript
    }
    """.split('\n')[1:]
    script_lines = [s[4:] for s in script]
    return script_lines


# def create_start_docker_lines(container_name, net_params, db_address, db_port, db_name, db_user, db_pass, log_output='stdout', radius_debug='no'):
#     script = f"""
#     #! /bin/sh
#     docker rm -f `docker ps -q -f name={container_name}` 2>/dev/null
#
#     docker run -d --name {container_name} \\
#         {net_params} \\
#         --restart=always \\
#         -e TZ=Asia/Tokyo \\
#         --log-driver syslog \\
#         --log-opt syslog-address=udp://$HOSTNAME:514 \\
#         --log-opt tag="{container_name}" \\
#         --log-opt syslog-facility=local1 \\
#         -e DB_ADDRESS={db_address} \\
#         -e DB_PORT={db_port} \\
#         -e DB_NAME={db_name} \\
#         -e DB_USER={db_user} \\
#         -e DB_PASS={db_pass} \\
#         -e LOG_OUTPUT={log_output} \\
#         -e RADIUS_DEBUG='{radius_debug}' \\
#         freeradius
#     """.split('\n')[1:]
#     script_lines = [s[4:] for s in script]
#     return script_lines
#
#
# def create_and_atach_macvlan_lines(container_name, subnet, gateway, iface, netname, address):
#     create_macvlan = dock_net.create_macvlan_str(subnet, gateway, iface, netname)
#     attach_macvlan = dock_net.attach_net_str(container_name, netname, address)
#     return [
#         create_macvlan,
#         attach_macvlan,
#     ] + dock_net.create_postup_str_list(container_name, [
#         'ip r d default',
#         f'ip r a default via {gateway}',
#         "sudo ip netns exec $CONT_NS ip r",
#         f"sudo ip netns exec $CONT_NS ping {gateway} -c 4",
#     ])
#
#
# def create_service_file_lines(container_name):
#     script = f"""
#     [Unit]
#     Description=FreeRADIUS by Docker
#     After=multi-user.target.wants
#
#     [Service]
#     Type=simple
#     RemainAfterExit=yes
#     ExecStart=/home/worker/Docker/start_{container_name}.sh
#
#     [Install]
#     WantedBy=multi-user.target
#     """.split('\n')[1:]
#     script_lines = [s[4:] for s in script]
#     return script_lines


def run(container_name, back_net, net_p, rad_params):
    db_address = rad_params['db_address']
    db_port = rad_params['db_port']
    db_name = rad_params['db_name']
    db_user = rad_params['db_user']
    db_pass = rad_params['db_pass']

    def func(session):
        tag = 'freeradius'
        rad_dir = f'~/Docker/{tag}'
        base_shell.work_on(session, rad_dir)

        if not dock_util.is_built(session, tag):
            copy_scripts(session)
            create_docker_image(session)

        if not dock_util.is_running(session, container_name):
            compose_dir = f'~/Docker/{tag}/{container_name}'
            base_shell.work_on(session, compose_dir)

            create_macvlan = dock_net.create_macvlan_str(net_p['subnet'], net_p['gateway'], net_p['iface'], net_p['net_name'])
            base_shell.run(session, create_macvlan)
            base_shell.here_doc(session, 'preup.sh', [
                "#! /bin/sh",
                create_macvlan,
            ])

            compose_lines = create_start_docker_compose_lines(container_name, back_net, net_p, db_address, db_port, db_name, db_user, db_pass)
            compose = 'docker-compose.yml'
            base_shell.here_doc(session, compose, compose_lines)
            base_shell.run(session, 'docker-compose up -d')

    return func

