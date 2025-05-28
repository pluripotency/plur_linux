from mini import misc
from plur import base_shell
"""
snap firefox can't use fileupload
use mozilla firefox:
https://askubuntu.com/questions/1399383/how-to-install-firefox-as-a-traditional-deb-package-without-snap-in-ubuntu-22
"""


def setup(session):
    base_shell.run(session, "sudo add-apt-repository -y ppa:mozillateam/ppa")
    base_shell.run(session, misc.del_indent("""
    echo '
    Package: *
    Pin: release o=LP-PPA-mozillateam
    Pin-Priority: 1001

    Package: firefox
    Pin: version 1:1snap*
    Pin-Priority: -1
    ' | sudo tee /etc/apt/preferences.d/mozilla-firefox
    """))
    [base_shell.run(session, a) for a in misc.del_indent_lines(r"""
    sudo rm /etc/apparmor.d/usr.bin.firefox 
    sudo rm /etc/apparmor.d/local/usr.bin.firefox
    """)]
    base_shell.run(session, 'sudo snap remove firefox')
    [base_shell.run(session, a) for a in misc.del_indent_lines(r"""
    sudo systemctl stop var-snap-firefox-common-host\\x2dhunspell.mount
    sudo systemctl disable var-snap-firefox-common-host\\x2dhunspell.mount
    sudo snap remove firefox
    """)]
    base_shell.run(session, 'sudo apt install -y firefox')
    base_shell.run(session, "echo 'Unattended-Upgrade::Allowed-Origins:: \"LP-PPA-mozillateam:${distro_codename}\";' | sudo tee /etc/apt/apt.conf.d/51unattended-upgrades-firefox")

