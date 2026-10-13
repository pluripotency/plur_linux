from plur import base_shell
from . import redhat


def install_xwindow(session):
    # base_shell.yum_install(session, {
    #     'packages': [
    #         '@base-x',
    #         'gnome-shell',
    #         'gnome-terminal',
    #         'vlgothic-fonts',
    #     ]
    # })
    _ = [base_shell.run(session, a) for a in [
        'sudo dnf -y group install gnome-desktop',
        'sudo dnf -y install firefox',
        'sudo systemctl set-default graphical.target'
    ]]
    redhat.gsettings(session)

def install_ghostty(session):
    [base_shell.run(session, a) for a in [
        'sudo dnf -y copr enable scottames/ghostty',
        'sudo dnf -y install ghostty',
    ]]
