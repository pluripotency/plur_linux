from plur import session_wrap
from plur.base_shell import *
from plur.output_methods import *
from plur import ansi_colors


def exit_session(session):
    run(session, 'exit')
    nodes_len = len(session.nodes)
    rows = [
        ['Do you want to log out', new_send_line('y')],
    ]
    if nodes_len > 1:
        session.pop_node()
        rows += [[session.waitprompt, success, '']]
    else:
        rows += [['', 'EOF']]

    session.do(create_sequence('exit', rows))


def telnet_session(session):
    node = session.nodes[-1]
    node.exit_session = exit_session

    username = node.username if hasattr(node, 'username') else None
    password = node.password if hasattr(node, 'password') else None
    if username is None or password is None:
        print(ansi_colors.red('err in telnet_session: node.username is needed.'))
        exit(1)

    rows = [
        ['Username: ', new_send_line(username)],
        ["[Pp]assword:", new_send_pass(password)],
        [node.waitprompt, success, ''],
    ]
    session.do(create_sequence(f'telnet {node.access_ip}', rows))


def run_aruba_session(node):
    def receive_func(func):
        @session_wrap.run_session(node, custom_method=telnet_session)
        def aruba_run(session):
            return func(session)
        return aruba_run
    return receive_func


class ArubaNode:
    def __init__(self, prompt_name, access_ip, password, username='manager'):
        self.access_ip = access_ip
        self.username = username
        self.password = password
        self.waitprompt = prompt_name + '(|\(config\))[>#]'


# class ArubaConfigNode:
#     def __init__(self, prompt_name, access_ip, password, username='manager'):
#         self.access_ip = access_ip
#         self.username = username
#         self.password = password
#         self.waitprompt = prompt_name + '\(confign\)[>#]'


if __name__ == '__main__':
    from . import parser
    from . import cli
    import json
    prompt_name = 'Aruba-2930F-24G-PoEP-4SFPP'
    access_ip = '192.168.10.63'
    username = 'manager'
    password = 'manager'
    node = ArubaNode(prompt_name, access_ip, password, username)

    # @session_wrap.bash()
    @run_aruba_session(node)
    def func(session):
        run(session, 'configure')
        run(session, cli.add_vlan_str('4084', 'trk1'))
        # run(session, cli.del_vlan_str('4084', 'trk1'))
        run(session, 'exit')

        run(session, 'no page')
        result = run(session, 'disp vlan all')
        return result

    result = func()
    # print(f'result: ')
    print(json.dumps(parser.parse_disp_vlan_all(result), indent=2))
