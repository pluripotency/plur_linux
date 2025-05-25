from plur import base_shell
from recipes.docker import dock_util


def reverse_proxy_conf(proxy_list, htpasswd_path, port=80, logname='proxy'):
    """
    >>> proxy_list = [['docs', 'localhost', '3001'], ['', 'localhost', '3000']]
    >>> li = reverse_proxy_conf(proxy_list, 'pass')
    >>> '\\n'.join(li)

    :param proxy_list:
    :param htpasswd_path:
    :param port:
    :param logname:
    :return:
    """
    if htpasswd_path:
        htpasswd_conf = f"""
        auth_basic "Auth Required.";
        auth_basic_user_file {htpasswd_path};"""
    else:
        htpasswd_conf = ''

    routes = ''
    for p in proxy_list:
        path = p[0]
        url = p[1]
        port = p[2]

        if path is '':
            routes += """
        location / {
            proxy_pass http://%s:%s;
        }""" % (url, port)
        else:
            routes += """
        location /%s {
            rewrite ^/%s(/.*)$ $1 break;
            proxy_pass http://%s:%s;
        }""" % (path, path, url, port)

    conf = f"""
    server {{
        listen       {port};
        server_name  {logname};

        charset utf-8;
        access_log /var/log/nginx/access_{logname}.log;
        error_log /var/log/nginx/error{logname}.log;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    {htpasswd_conf}
    {routes}
    }}
    """

    return [line[4:] for line in conf.split('\n')[1:]]


def gen_htpasswd(username, password, htpasswd_path='conf/htpasswd'):
    conf = f"""
    #! /bin/sh
    USER={username}
    PASS={password}
    printf "$USER:$(openssl passwd -crypt $PASS)\\n" > {htpasswd_path}
    """
    return [line[4:] for line in conf.split('\n')[1:]]


def start_docker(container_name, net_params):
    def func(session):
        script = f"""
        #! /bin/sh
        docker run -d --name {container_name} \\
            {net_params} \\
            --restart=always \\
            -e TZ=Asia/Tokyo \\
            -v `pwd`/conf/default.conf:/etc/nginx/conf.d/default.conf \\
            -v `pwd`/conf/htpasswd:/etc/nginx/.htpasswd \\
            nginx:alpine 
        """.split('\n')[1:]
        script_lines = [s[8:] for s in script]
        base_shell.here_doc(session, 'start_docker.sh', script_lines)
        base_shell.run(session, 'chmod +x start_docker.sh')
        base_shell.run(session, './start_docker.sh')
    return func


def create_compose(service_name, container_name, networks, volumes, syslog='local1'):
    """
    >>> li = create_compose('nginx', 'nginx', '', ['vol'])
    >>> '\\n'.join(li)
    """
    conf = f"""
    version: "3.7"
    services:
      {service_name}:
        image: nginx:alpine
        container_name: {container_name}
        restart: always
        environment:
          - TZ=Asia/Tokyo
    """
    if syslog:
        conf += f"""
        logging:
          driver: "syslog"
          options:
            syslog-address: "udp://localhost:514"
            tag: {container_name}
            syslog-facility: {syslog}
    """
    if isinstance(volumes, list):
        conf += """    
        volumes:
    """
        for v in volumes:
            conf += " "*6 + "- " + v + '\n'

    if networks:
        conf += networks
    return [line[4:] for line in conf.split('\n')[1:]]


def create_files(container_name="nginx_v0699", proxy_list=[['', '127.0.0.1', '3000']]):

    def func(session):
        if not dock_util.is_running(session, container_name):
            docker_dir = f'~/Docker/{container_name}'
            conf_dir = f'{docker_dir}/conf'
            base_shell.work_on(session, conf_dir)
            base_shell.work_on(session, docker_dir)

            htpasswd_conf_path = 'conf/htpasswd'
            htpasswd_dock_path = '/etc/nginx/.htpasswd'
            volumes = [
                f'./{htpasswd_conf_path}:{htpasswd_dock_path}',
            ]
            base_shell.here_doc(session, f'{conf_dir}/gen_pass.sh', gen_htpasswd('user', 'password', htpasswd_conf_path))
            base_shell.run(session, 'sh conf/gen_pass.sh')

            proxy_conf_path = 'conf/proxy.conf'
            proxy_dock_path = '/etc/nginx/conf.d/proxy.conf'
            base_shell.here_doc(session, f'{docker_dir}/{proxy_conf_path}', reverse_proxy_conf(proxy_list, htpasswd_dock_path))
            volumes += [
                f'./{proxy_conf_path}:{proxy_dock_path}',
            ]

            networks = """
    networks:
      v0699:
        ipv4_address: 192.168.113.100
networks:
  v0699:
    external:
      name: 'v0699'
                """
            base_shell.here_doc(session, f'{docker_dir}/docker-compose.yml', create_compose('reverse_proxy', container_name, networks, volumes))
            from .. import dock_net
            dock_net.create_macvlan_str('192.168.113.0/24', '192.168.113.254', 'eth0.699', 'v0699')

    return func


