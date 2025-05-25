from plur import base_shell
from plur import output_methods


def install_build_tools_ubuntu(session):
    action = 'sudo apt install pkg-config libasound2-dev libssl-dev cmake libfreetype6-dev libexpat1-dev libxcb-composite0-dev'
    base_shell.run(session, action)


def install(session):
    if not base_shell.check_command_exists(session, 'rustup'):
        action = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        session.do(base_shell.create_sequence(action, [
            [r'Cancel installation.+>', output_methods.send_line, ''],
            [session.waitprompt, output_methods.success],
        ]))
        base_shell.run(session, 'source "$HOME/.cargo/env"')
