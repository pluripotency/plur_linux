from plur import base_shell


def command_count_restart():
    return 'docker inspect --format "ID: {{.ID}} RESTARTS: {{.RestartCount}} NAME: {{.Name}}" $(docker ps -aq)'


def create_script_to_count_restart(session):
    script_name = 'count_container_restart.sh'
    save_file_path = f'$HOME/{script_name}'
    base_shell.here_doc(session, save_file_path, [
        '#! /bin/bash\n',
        command_count_restart()
    ])


if __name__ == "__main__":
    from plur import base_node
    from plur import session_wrap

    node = base_node.Linux('wfc7181', 'worker', '', platform='centos7')

    @session_wrap.ssh(node)
    def run(session):
        create_script_to_count_restart(session)

    run()
