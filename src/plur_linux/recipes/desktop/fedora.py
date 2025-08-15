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
        'sudo dnf -y group install gnome-desktop base-x',
        'sudo dnf -y install firefox',
        # 'sudo dnf -y group install "Basic Desktop" GNOME',
        'sudo systemctl set-default graphical.target'
    ]]
    redhat.gsettings(session)

def install_ghostty(session):
    [base_shell.run(session, a) for a in [
        'sudo dnf -y copr enable scottames/ghostty',
        'sudo dnf -y install ghostty',
    ]]

def install_xrdp(session):
    base_shell.yum_install(session, {
        'packages': [
            'xrdp',
        ]
    })
    base_shell.service_on(session, 'xrdp')


"""
to disable screen lock, run this in user session
#! /bin/sh
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.desktop.screensaver lock-delay 0
gsettings set org.gnome.desktop.screensaver lock-enabled false
"""


