from mini import misc
from plur import base_shell
from plur.output_methods import send_line_f, send_pass_f, waitprompt
from plur_linux.recipes import firewalld
create_sequence = base_shell.create_sequence

"""
# sudo dnf install gnome-remote-desktop

sudo -u gnome-remote-desktop mkdir -p ~gnome-remote-desktop/.local/share/gnome-remote-desktop
sudo -u gnome-remote-desktop openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.key \
  -out ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.crt \
  -days 3650 \
  -subj "/CN=$(hostname)" \
  -addext "extendedKeyUsage=serverAuth"

sudo grdctl --system rdp set-tls-key ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.key
sudo grdctl --system rdp set-tls-cert ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.crt
sudo grdctl --system rdp set-credentials

# message: Init TPM credentials failed because Failed to initialize transmission
# username and password are asked

sudo grdctl --system rdp enable

sudo systemctl enable --now gnome-remote-desktop.service
sudo systemctl status gnome-remote-desktop.service

firewall-cmd --permanent --add-port=3389/tcp
firewall-cmd --reload

"""

def search_not_root_node(session):
    for node in reversed(session.nodes):
        if node.username != 'root':
            return node
    return False

def enable_rdp(session):
    user_node = search_not_root_node(session)
    if not user_node:
        print(misc.ansi_colors.red('abort enable rdp: user_node not found'))
        return

    base_shell.run(session, 'sudo -u gnome-remote-desktop mkdir -p ~gnome-remote-desktop/.local/share/gnome-remote-desktop')
    base_shell.run(session, misc.del_indent(r"""
        sudo -u gnome-remote-desktop openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.key \
      -out ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.crt \
      -days 3650 \
      -subj "/CN=$(hostname)" \
      -addext "extendedKeyUsage=serverAuth"
    """))
    [base_shell.run(session, a) for a in misc.del_indent_lines("""
    sudo grdctl --system rdp set-tls-key ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.key
    sudo grdctl --system rdp set-tls-cert ~gnome-remote-desktop/.local/share/gnome-remote-desktop/tls.crt
    """)]

    username = user_node.username
    password = user_node.password
    session.do(create_sequence(
    'sudo grdctl --system rdp set-credentials',
    [
        ['[Uu]sername:', send_line_f(username)],
        ['[Pp]assword:', send_pass_f(password)],
        ['', waitprompt],
    ]))
    base_shell.run(session, 'sudo grdctl --system rdp enable')
    firewalld.configure(ports=['3389/tcp'], add=True)(session)
