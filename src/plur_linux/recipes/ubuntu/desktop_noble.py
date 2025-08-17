import re
from mini import misc
from plur import base_shell
from . import ops

def uncomment(contents, key):
    found_index = misc.find_index(contents, lambda line: re.search(key, line))
    if found_index > -1  and len(contents[found_index]) > 3:
        contents[found_index] = contents[found_index][2:]
    return contents

def create_startwm(deskdist):
    startwm_path = '~/startwm.sh'
    contents = misc.del_indent_lines("""
    #!/bin/sh
    # GNOME
    # dbus-launch --exit-with-session /usr/bin/gnome-session
    # GNOME Classic
    # dbus-launch --exit-with-session /usr/bin/gnome-session-classic
    # KDE
    # dbus-launch --exit-with-session /usr/bin/startplasma-x11
    # Cinnamon
    # dbus-launch --exit-with-session /usr/bin/cinnamon-session
    # MATE
    # dbus-launch --exit-with-session /usr/bin/mate-session
    # Xfce
    # dbus-launch --exit-with-session /usr/bin/startxfce4
    # LXDE
    # dbus-launch --exit-with-session /usr/bin/startlxde
    # LXQt
    # dbus-launch --exit-with-session /usr/bin/startlxqt
    # Budgie
    # env GNOME_SHELL_SESSION_MODE=Budgie:GNOME dbus-launch --exit-with-session /usr/bin/budgie-desktop
    # i3
    # exec i3
    """)
    if deskdist == 'xfce':
        contents = uncomment(contents, 'startxfce4')
    elif deskdist == 'gnome':
        contents = uncomment(contents, 'gnome-session')
    elif deskdist == 'mate':
        contents = uncomment(contents, 'mate-session')
    elif deskdist == 'cinamon':
        contents = uncomment(contents, 'cinamon-session')
    elif deskdist == 'lxde':
        contents = uncomment(contents, 'startlxde')
    elif deskdist == 'i3wm':
        contents = uncomment(contents, 'exec i3')

    def func(session):
        base_shell.here_doc(session, startwm_path, contents)
        base_shell.run(session, f'chmod 755 {startwm_path}')
    return func

def setup_xrdp(session, deskdist):
    ops.sudo_apt_install_y(['xrdp'])(session)
    create_startwm(deskdist)(session)

def install_desktop(pkgs):
    def func(session):
        session.set_timeout(1800)
        ops.sudo_apt_install_y(pkgs)(session)
        session.set_timeout()
    return func

def install_gnome(session, enable_xrdp=False):
    pkgs = misc.del_indent_lines("""
    ubuntu-desktop
    task-gnome-desktop
    """)
    install_desktop(pkgs)(session)
    if enable_xrdp:
        setup_xrdp(session, 'gnome')

def install_xubuntu(session, enable_xrdp=False):
    pkgs = misc.del_indent_lines("""
    xubuntu-desktop
    task-xfce-desktop
    """)
    install_desktop(pkgs)(session)
    if enable_xrdp:
        setup_xrdp(session, 'xfce')

def install_mate(session, enable_xrdp=False):
    pkgs = misc.del_indent_lines("""
    task-mate-desktop
    """)
    install_desktop(pkgs)(session)
    if enable_xrdp:
        setup_xrdp(session, 'mate')

def install_cinamon(session, enable_xrdp=False):
    pkgs = misc.del_indent_lines("""
    task-cinamon-desktop
    """)
    install_desktop(pkgs)(session)
    if enable_xrdp:
        setup_xrdp(session, 'cinamon')

def install_lubuntu(session, enable_xrdp=False):
    pkgs = misc.del_indent_lines("""
    lubuntu-desktop
    task-lxde-desktop
    task-lxqt-desktop
    """)
    install_desktop(pkgs)(session)
    if enable_xrdp:
        setup_xrdp(session, 'lxde')

def install_i3wm(session, enable_xrdp=False):
    install_desktop(['i3wm'])(session)
    if enable_xrdp:
        setup_xrdp(session, 'i3wm')
        base_shell.here_doc(session, '~/.xinitrc', misc.del_indent('''
        xset s off
        xset -dpms
        xset s noblank

        '''))
