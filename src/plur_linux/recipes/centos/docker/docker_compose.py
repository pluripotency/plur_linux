from plur import base_shell
import re


def install(version="latest", install_dir_path = "/usr/local/lib/docker/cli-plugins"):
    def func(session):
        if not base_shell.check_file_exists(session, install_dir_path + '/docker-compose'):
            base_shell.run(session, f'sudo mkdir -p {install_dir_path}')
            ver_local = version
            if version == 'latest':
                base_shell.run(session, r'COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d\" -f4)')
                capt = base_shell.run(session, 'echo $COMPOSE_VERSION')
                for line in capt.split('\n'):
                    if line.startswith('v'):
                        ver_local = line.strip()

            url = f'https://github.com/docker/compose/releases/download/{ver_local}/docker-compose-linux-x86_64'
            tmp_file_path = '/tmp/docker-compose'
            actions = [
                f'curl -L {url} > {tmp_file_path}',
                f'chmod +x {tmp_file_path}',
                f'sudo mv {tmp_file_path} {install_dir_path}'
            ]
            [base_shell.run(session, action) for action in actions]
    return func
