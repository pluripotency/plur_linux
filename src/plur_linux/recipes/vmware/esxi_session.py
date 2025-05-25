import os
import sys
sys.path.append(os.pardir)
from plur import session_wrap
from plur.base_shell import *
from plur import output_methods
from plur import log_param_templates
from plur import ansi_colors
from lib import misc


def exit_session(session):
    nodes_len = len(session.nodes)
    if nodes_len > 1:
        session.pop_node()
        rows = [[session.waitprompt, output_methods.success, '']]
    else:
        rows = [['', 'EOF']]

    session.do(create_sequence('exit', rows))


def ssh_session(session):
    node = session.nodes[-1]
    node.exit_session = exit_session

    username = node.username if hasattr(node, 'username') else None
    password = node.password if hasattr(node, 'password') else None
    access_ip = node.access_ip if hasattr(node, 'access_ip') else None
    if username is None or password is None or access_ip is None:
        print(ansi_colors.red('err in ssh_session: username, password, access_ip is needed.'))
        exit(1)
    rows = [
        ['Are you sure you want to continue connecting \(yes/no\)\?', output_methods.send_line_f('yes')],
        ["[Pp]assword:", output_methods.send_pass_f(password)],
        ['verification failed', 'exit'],
        [node.waitprompt, output_methods.success_f('')],
    ]
    session.do(create_sequence(f'ssh {username}@{node.access_ip}', rows))


def run_esxi_session(node, log_params=None):
    if log_params is None:
        log_params = log_param_templates.normal()

    def receive_func(func):
        @session_wrap.run_session(node, custom_method=ssh_session, log_params=log_params)
        def esxi_run(session):
            return func(session)
        return esxi_run
    return receive_func


class ESXiNode:
    def __init__(self, access_ip, password, username='root', hostname='localhost'):
        self.access_ip = access_ip
        self.username = username
        self.password = password
        self.waitprompt = f'\[{username}@{hostname}:.+\] '


if __name__ == '__main__':
    esxi_node_conf = misc.read_toml('/mnt/MC/work_space/app_config/credentials/dev16.toml')
    node = ESXiNode(**esxi_node_conf)

    # @session_wrap.bash()
    @run_esxi_session(node)
    def func(session):
        result = run(session, 'esxcli network vswitch standard list')
        return result

    result = func()
    # import json
    # print(json.dumps(aruba_lib.parse_disp_vlan_all(result), indent=2))
