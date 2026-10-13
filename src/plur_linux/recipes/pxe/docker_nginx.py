from mini import misc
from plur import base_shell
from plur_linux.recipes import firewalld

def prepare_default_conf(nginx_dir):
    content_lines = misc.del_indent_lines(r"""
    server {
        listen       80;

        server_name  pxe;
        client_max_body_size 10000M;

        charset utf-8;
        access_log /dev/stdout main;
        error_log /dev/stderr warn;

        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
        }
    }
    """)
    file_path = f'{nginx_dir}/conf.d/default.conf'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def prepare_start_sh(nginx_dir):
    content_lines = misc.del_indent_lines(r"""
    #! /bin/sh
    CONTAINER_NAME=nginx_pxe
    IMAGE_NAME=nginx

    CURRENT=$(cd $(dirname $0);pwd)

    $CURRENT/stop.sh
    echo "starting $CONTAINER_NAME"

    docker run -d --restart=always \
      --net host \
      --name $CONTAINER_NAME \
      -v $CURRENT/conf.d:/etc/nginx/conf.d:ro \
      -v /var/www/html/:/usr/share/nginx/html:ro \
      $IMAGE_NAME
    """)
    file_path = f'{nginx_dir}/start.sh'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def prepare_stop_sh(nginx_dir):
    content_lines = misc.del_indent_lines("""
    #! /bin/sh
    CONTAINER_NAME=nginx_pxe
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
      docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
    fi
    """)
    file_path = f'{nginx_dir}/stop.sh'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def start(set_fw=False):
    nginx_dir = '~/Downloads/nginx_pxe'
    def func(session):
        if set_fw:
            firewalld.configure(services=['http'], add=True)
        base_shell.work_on(session, f'{nginx_dir}/conf.d')
        base_shell.run(session, 'cd ..')
        prepare_default_conf(nginx_dir)(session)
        prepare_start_sh(nginx_dir)(session)
        prepare_stop_sh(nginx_dir)(session)
        base_shell.run(session, 'chmod +x *.sh')
        base_shell.run(session, './start.sh')
    return func

