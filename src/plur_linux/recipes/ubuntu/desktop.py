from mini import misc
from plur import base_shell
from . import ops


script = """
#new_cursorsの無効化
sudo sed -e 's/^new_cursors=true/new_cursors=false/g' -i /etc/xrdp/xrdp.ini
 
#xrdpサービスの再起動
sudo systemctl restart xrdp
 
#xsessionファイルの作成
D=/usr/share/ubuntu:/usr/local/share:/usr/share:/var/lib/snapd/desktop
cat <<EOF > ~/.xsessionrc
 export GNOME_SHELL_SESSION_MODE=ubuntu
 export XDG_CURRENT_DESKTOP=ubuntu:GNOME
 export XDG_DATA_DIRS=${D}
 export XDG_CONFIG_DIRS=/etc/xdg/xdg-ubuntu:/etc/xdg
EOF
 
#Authentication Requiredダイアログの回避
cat <<EOF | sudo tee /etc/polkit-1/localauthority/50-local.d/xrdp-color-manager.pkla
 [NetworkManager]
 Identity=unix-user:*
 Action=org.freedesktop.color-manager.create-device
 ResultAny=no
 ResultInactive=no
 ResultActive=yes
EOF
 
sudo systemctl restart polkit
"""


def setup_xrdp(session):
    ops.sudo_apt_install_y(['xrdp'])(session)
    # [base_shell.run(session, a) for a in script.split('\n')]


def install_desktop_ja_support(session):
    ja_pkgs_lines = misc.del_indent_lines("""
    language-pack-ja-base language-pack-ja
    task-japanese-gnome-desktop language-pack-gnome-ja-base language-pack-gnome-ja
    fonts-noto-cjk-extra gnome-user-docs-ja
    """)
    # ja_pkgs += ' libreoffice-help-ja libreoffice-l10n-ja thunderbird-locale-ja'
    ops.sudo_apt_install_y(ja_pkgs_lines, update=False)(session)


def install_desktop(session, no_recommends=True, ja_support=True, desktop_pkg='ubuntu-desktop'):
    session.set_timeout(1800)
    options = '--no-install-recommends' if no_recommends else ''
    ops.sudo_apt_install_y([options, desktop_pkg])(session)

    if ja_support:
        install_desktop_ja_support(session)
    # base_shell.run(session, 'sudo snap install firefox')
    ops.sudo_apt_install_y(['firefox'], update=False)(session)
    session.set_timeout()


def install_xubuntu(session, no_recommends=True, ja_support=True):
    install_desktop(session, no_recommends, ja_support, 'xubuntu-desktop')


def install_lubuntu(session, no_recommends=True, ja_support=True):
    install_desktop(session, no_recommends, ja_support, 'lubuntu-desktop')


def install_i3(session, ja_support=True):
    commands = misc.del_indent_lines("""
    /usr/lib/apt/apt-helper download-file https://debian.sur5r.net/i3/pool/main/s/sur5r-keyring/sur5r-keyring_2024.03.04_all.deb keyring.deb SHA256:f9bb4340b5ce0ded29b7e014ee9ce788006e9bbfe31e96c09b2118ab91fca734
    sudo apt install -y ./keyring.deb
    echo "deb http://debian.sur5r.net/i3/ $(grep '^DISTRIB_CODENAME=' /etc/lsb-release | cut -f2 -d=) universe" | sudo tee /etc/apt/sources.list.d/sur5r-i3.list
    """)
    [base_shell.run(session, cmd) for cmd in commands]
    ops.sudo_apt_install_y(['i3'])
    if ja_support:
        install_desktop_ja_support(session)
    base_shell.run(session, 'reset')
