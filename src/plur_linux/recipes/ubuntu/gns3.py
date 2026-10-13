from mini import misc
from plur import base_shell
from . import docker_ce
from . import ops

send_line = base_shell.output_methods.send_line
waitprompt = base_shell.output_methods.waitprompt


def install_gns3(session):
    session.do(base_shell.create_sequence('sudo add-apt-repository ppa:gns3/ppa', [
        [r'Press \[ENTER] to continue or Ctrl-c to cancel.', send_line, '']
        , ['', waitprompt, '']
    ]))
    ops.sudo_apt_install_y(['gns3-gui gns3-server'])


def install_gns3_iou(session):
    base_shell.run(session, 'sudo dpkg --add-architecture i386')
    ops.sudo_apt_install_y(['gns3-iou'])


def create_install_script(session):
    base_shell.here_doc(session, '~/install_gns3.sh', misc.del_indent_lines("""
    #! /bin/sh
    sudo add-apt-repository ppa:gns3/ppa
    sudo apt update
    sudo apt install -y gns3-gui gns3-server
    
    sudo dpkg --add-architecture i386
    sudo apt update
    sudo apt install -y gns3-iou
    
    sudo usermod -aG ubridge,kvm,wireshark,docker $(whoami)
    """))


def install(session):
    docker_ce.install(session)
    create_install_script(session)

    # install_gns3(session)
    # install_gns3_iou(session)
    # base_shell.run(session, 'sudo usermod -aG ubridge,kvm,wireshark,docker $(whoami)')
