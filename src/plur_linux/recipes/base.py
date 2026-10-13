import os
import re
from plur import base_shell
import plur.session_wrap as wrap
import plur.base_node as node

def sanitize(message):
    return re.sub('\s|\.', '_', re.sub('/|:|', '', message))

def rst2html(kwargs):
    @wrap.bash(node.Me())
    def func(session=None):
        work_dir = kwargs['work_dir']
        src_file = kwargs['src_file']
        dst_file = kwargs['dst_file']
        css = kwargs['css_path']
        base_shell.work_on(session, work_dir)
        command = 'rst2html --stylesheet=%s' % css if css else 'rst2html'
        base_shell.run(session, command + ' %s %s' %(src_file, dst_file))

    return func

def ping_from_me(hostname):
    @wrap.bash(node.Me())
    def ping_host(session=None):
        return base_shell.run(session, f'ping -c 2 {hostname}')
    return ping_host

def resolve_path(_path):
    if _path.startswith('~/'):
        return os.path.expanduser(_path)
    return _path

def copy(session, src_path, dst_path, over_write=False):
    abs_src_path = resolve_path(src_path)
    abs_dst_path = resolve_path(dst_path)
    if not over_write:
        if base_shell.check_dir_exists(session, abs_dst_path):
            exit(1)
        if base_shell.check_file_exists(session, abs_dst_path):
            exit(1)
    base_shell.run(session, 'cp -rf %s %s' % (abs_src_path, abs_dst_path))

def update(session):
    node = session.nodes[-1]
    if node.username != 'root':
        session.sudo_i()
    base_shell.yum_install(session, {'update': True})

def package_install(session, packages=None):
    base_shell.yum_install(session, {'packages', packages})
