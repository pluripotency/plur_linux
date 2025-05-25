#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
import re
from plur import base_shell
from plur import session_wrap


def catalogue_dir(session, dir_path, expression='.+'):
    if not re.match('.+/$', dir_path):
        dir_path = dir_path + '/'
    action = 'for dir in %s*; do echo "$dir"; done' % dir_path
    all_files = base_shell.run(session, action).replace(dir_path, '').split('\n')
    out = []
    for f in all_files:
        if re.match(expression, f):
            out.append(f)
    return out


def backup(path):
    def func(session):
        username = session.username
        if username != 'root':
            HOME = '/home/%s' % username
        else:
            HOME = '/root'
        backup_root_path = '%s/backup' % HOME
        backed_up_path = backup_root_path + path

        @session_wrap.sudo
        def backup_by_root(session):
            backup_dir = backup_root_path + '`dirname %s`' % path

            # only when backup doesn't exist.
            if not base_shell.check_file_exists(session, backed_up_path):
                # backup
                base_shell.run(session, 'mkdir -p %s' % backup_dir)
                base_shell.run(session, '\cp -f %s %s' % (path, backup_dir))

                # index
                if not base_shell.check_file_exists(session, '%s/index' % backup_root_path):
                    base_shell.run(session, 'echo "%s" > %s/index' % (path, backup_root_path))
                else:
                    base_shell.run(session, "sed '/^%s$/d'" % path)
                    base_shell.run(session, 'echo "%s" >> %s/index' % (path, backup_root_path))

                # owner is user
                base_shell.run(session, 'chown -R %s. %s' % (username, backup_root_path))

        base_shell.work_on(session, backup_root_path)
        backup_by_root(session)

        return backed_up_path
    return func


