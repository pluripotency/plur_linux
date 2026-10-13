from plur import base_shell


def start_docker(container_name, net_params, mysql_root_password):
    def func(session):
        script = f"""
        #! /bin/sh
        docker run -d --name {container_name} \\
            {net_params} \\
            --restart=always \\
            -e TZ=Asia/Tokyo \\
            -e MYSQL_ROOT_PASSWORD={mysql_root_password} \\
            mariadb:10.4.11
        """.split('\n')[1:]
        script_lines = [s[8:] for s in script]
        base_shell.here_doc(session, 'start_docker.sh', script_lines)
        base_shell.run(session, 'chmod +x start_docker.sh')
        base_shell.run(session, './start_docker.sh')
    return func


def load_sql_file(container_name, mysql_root_password, db_name, sql_file_path):
    def func(session):
        mysql_script = f"sh -c 'mysql -uroot -p{mysql_root_password} {db_name}' < {sql_file_path}"
        base_shell.run(session, f"docker exec -i `docker ps -q -f name={container_name}` {mysql_script}")
    return func


def load_query(container_name, mysql_root_password, db_name, query):
    def func(session):
        mysql_script = f"mysql -uroot -p{mysql_root_password} {db_name} -e \"{query}\""
        base_shell.run(session, f"docker exec -i `docker ps -q -f name={container_name}` {mysql_script}")
    return func
