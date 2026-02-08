import re
from plur import session_wrap
from plur import base_shell

def install_bun(session):
    if not base_shell.check_command_exists(session, 'unzip'):
        base_shell.run(session, 'sudo dnf install -y unzip')
    base_shell.run(session, 'curl -fsSL https://bun.sh/install | bash')
