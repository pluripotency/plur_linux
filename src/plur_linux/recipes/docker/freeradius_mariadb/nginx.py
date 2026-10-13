from plur import base_shell
from plur_linux.recipes.docker import dock_util


def default_conf(proxy_list):
    conf = """server {
    listen       80;
    server_name  cdr;

    charset utf-8;
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
    
    auth_basic "Auth Required.";
    auth_basic_user_file /etc/nginx/.htpasswd;
    """

    for p in proxy_list:
        server = """
    location /%s {
        rewrite ^/%s(/.*)$ $1 break;
        proxy_pass http://%s:80;
    }
    """ % (p, p, p)
        conf += server

    conf += """
    location / {
        proxy_pass http://radmin-ui:3000;
    }
}
    """
    return conf.split('\n')


def gen_htpasswd(username, password):
    conf = f"""
    #! /bin/sh
    USER={username}
    PASS={password}
    printf "$USER:$(openssl passwd -crypt $PASS)\\n" >> conf/htpasswd
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


def run(container_name, net_params, proxy_list):
    def func(session):
        if not dock_util.is_running(session, container_name):
            docker_dir = f'~/Docker/{container_name}'
            conf_dir = f'{docker_dir}/conf'
            if not base_shell.check_dir_exists(session, conf_dir):
                base_shell.create_dir(session, conf_dir)
            base_shell.work_on(session, docker_dir)

            base_shell.here_doc(session, f'{conf_dir}/default.conf', default_conf(proxy_list))
            base_shell.here_doc(session, f'{conf_dir}/gen_pass.sh', gen_htpasswd('user', 'password'))
            base_shell.run(session, 'sh conf/gen_pass.sh')
            start_docker(container_name, net_params)(session)
    return func
