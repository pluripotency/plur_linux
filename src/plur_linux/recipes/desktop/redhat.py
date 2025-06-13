from mini import misc
from plur import base_shell
from plur import session_wrap
from plur_linux.recipes import firewalld

def search_not_root(session):
    for node in reversed(session.nodes):
        if node.username != 'root':
            return node.username
    return False

@session_wrap.sudo
def install_xrdp(session):
    _ = [base_shell.run(session, a) for a in [
        'dnf -y install epel-release',
        'dnf -y install xrdp tigervnc-server',
        'systemctl enable xrdp --now'
    ]]
    firewalld.configure(ports=['3389/tcp'], add=True)(session)


@session_wrap.sudo
def install_gui(session):
    session.set_timeout(3600)
    _ = [base_shell.run(session, a) for a in [
        'dnf -y groupinstall "Server with GUI" --nobest',
        'systemctl set-default graphical'
    ]]
    session.set_timeout()


@session_wrap.sudo
def install_vbox_additions_libs(session):
    base_shell.run(session, 'dnf update -y')
    base_shell.run(session, 'dnf install -y ' + ' '.join([
        'bzip2',
        'make',
        'kernel-devel',
        'kernel-headers',
        'gcc-c++'
    ]))


def gsettings(session):
    """
    to disable screen lock, run this in user session
    """
    sh_path = '/tmp/gsettings.sh'
    base_shell.here_doc(session, sh_path, misc.del_indent_lines("""
    #! /bin/sh
    gsettings set org.gnome.desktop.session idle-delay 0
    gsettings set org.gnome.desktop.screensaver lock-delay 0
    gsettings set org.gnome.desktop.screensaver lock-enabled false
    """))
    base_shell.run(session, f'sh {sh_path}')


def install_xrdp_a8(session):
    install_xrdp(session)
    # this is needed to avoid 'SELinux is preventing spice-vdagentd'
    # base_shell.run(session, 'sudo dnf remove -y spice-vdagent')


def install_gui_a8a9(session):
    install_gui(session)
    username = search_not_root(session)
    if username:
        session_wrap.su(username)(gsettings)(session)


dict_desktop = {
    'almalinux8': {
        'desktop': install_gui_a8a9,
        'xrdp': install_xrdp_a8,
        'vbox': install_vbox_additions_libs
    },
    'almalinux9': {
        'desktop': install_gui_a8a9,
        'xrdp': install_xrdp,
        'vbox': install_vbox_additions_libs
    },
}
