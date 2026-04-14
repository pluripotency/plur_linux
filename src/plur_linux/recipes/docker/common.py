from mini import misc
from plur import base_shell
from plur import session_wrap


def configure_docker(default_bridge_ip='10.192.192.254/26'):
    @session_wrap.sudo
    def func(session):
        docker_dir = '/etc/docker'
        if not base_shell.check_dir_exists(session, docker_dir):
            base_shell.run(session, 'mkdir -p ' + docker_dir)
            base_shell.run(session, 'chmod 700 ' + docker_dir)
        base_shell.here_doc(session, f'{docker_dir}/daemon.json', misc.del_indent_lines(f"""
        {{
          "bip": "{default_bridge_ip}",
          "log-driver": "json-file",
          "log-opts": {{
            "max-size": "10m",
            "max-file": "3"
          }}
        }}
        """))
        base_shell.run(session, 'systemctl restart docker')
    return func


def join_group(session):
    if session.nodes[-1].username != 'root':
        [base_shell.run(session, a) for a in misc.del_indent_lines("""
        sudo groupadd docker
        sudo usermod -aG docker $(whoami)
        """)]
