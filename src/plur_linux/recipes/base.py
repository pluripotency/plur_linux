#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
import re

import plur.session_wrap as wrap
import plur.base_node as node


def sanitize(message):
    return re.sub('\s|\.', '_', re.sub('/|:|', '', message))


def rst2html(kwargs):
    @wrap.bash(node.Me())
    def run(session=None, args=None):
        work_dir = kwargs['work_dir']
        src_file = kwargs['src_file']
        dst_file = kwargs['dst_file']
        css = kwargs['css_path']
        shell.work_on(session, work_dir)
        command = 'rst2html --stylesheet=%s' % css if css else 'rst2html'
        shell.run(session, command + ' %s %s' %(src_file, dst_file))

    run(args=kwargs)


def ping_from_me(hostname, report=None, log_params=None):
    @wrap.bash(node.Me())
    def ping_host(session=None, args=None, log_params={}):
        return shell.ping(session, hostname, 2)

    return ping_host(log_params=log_params)


def resolve_path(_path):
    if _path.startswith('~/'):
        return os.path.expanduser(_path)
    return _path


def copy(session, src_path, dst_path, over_write=False):
    abs_src_path = resolve_path(src_path)
    abs_dst_path = resolve_path(dst_path)
    if not over_write:
        if shell.check_dir_exists(session, abs_dst_path):
            exit(1)
        if shell.check_file_exists(session, abs_dst_path):
            exit(1)
    shell.run(session, 'cp -rf %s %s' % (abs_src_path, abs_dst_path))


def update(session):
    node = session.nodes[-1]
    if node.username != 'root':
        session.sudo_i()

    shell.yum_install(session, {'update': True})


def package_install(session, packages=None):
    shell.yum_install(session, {'packages', packages})
