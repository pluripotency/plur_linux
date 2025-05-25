from plur import base_shell
from recipes.docker import dock_util


def start_docker(container_name, net_params, mysql_ipaddr, mysql_user, mysql_password):
    def func(session):
        script = f"""
        #! /bin/sh
        docker run -d --name {container_name} \\
            {net_params} \\
            --restart=always \\
            -e TZ=Asia/Tokyo \\
            -e PMA_ARBITRARY=1 \\
            -e PMA_HOST={mysql_ipaddr} \\
            -e PMA_USER={mysql_user} \\
            -e PMA_PASSWORD={mysql_password} \\
            phpmyadmin/phpmyadmin
        """.split('\n')[1:]
        script_lines = [s[8:] for s in script]
        base_shell.here_doc(session, 'start_docker.sh', script_lines)
        base_shell.run(session, 'chmod +x start_docker.sh')
        base_shell.run(session, './start_docker.sh')
    return func


def run(container_name, net_params, db_params):
    db_address = db_params['db_address']
    db_user = db_params['db_user']
    db_pass = db_params['db_pass']

    def func(session):
        docker_dir = f'~/Docker/{container_name}'
        base_shell.work_on(session, docker_dir)
        if not dock_util.is_running(session, container_name):
            start_docker(container_name, net_params, db_address, db_user, db_pass)(session)
    return func

