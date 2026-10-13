import re
from plur import base_shell
from plur import session_wrap


def create_start_script(session, ip='192.168.1.10'):
    start_script_dir_path = '~/Desktop'
    start_script_path = f'{start_script_dir_path}/freerdp.sh'
    contents_str = rf"""
    #! /bin/sh

    USER=worker
    TARGET={ip}
    WI=1280
    HI=1024
    """ + """
    xfreerdp /u:${USER} -clipboard /bpp:24 /v:${TARGET} /w:${WI} /h:${HI}
    """
    contents = [line[4:] for line in contents_str.split('\n')[1:]]
    base_shell.work_on(session, start_script_dir_path)
    base_shell.here_doc(session, start_script_path, contents)
    base_shell.run(session, f'chmod +x {start_script_path}')


@session_wrap.sudo
def install(session):
    current_node = session.nodes[-1]
    if re.search('ubuntu', current_node.platform):
        base_shell.run(session, 'apt-get update && apt-get install -y xfreerdp')
    else:
        base_shell.yum_y_install(['xfreerdp'])(session)


def setup(session):
    install(session)
    create_start_script(session)
