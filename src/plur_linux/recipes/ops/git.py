#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur.base_shell import *
from plur.output_methods import *


def recover_variable(session, variable, temp_variable='TEMP_VAR'):
    actions = [
        'echo $%s > %s' % (temp_variable, variable),
        '%s=' % temp_variable
    ]
    [run(session, action) for action in actions]


def escape_variable(session, variable, temp_variable='TEMP_VAR'):
    actions = [
        'echo $%s > %s' % (variable, temp_variable),
        '%s=' % variable
    ]
    [run(session, action) for action in actions]


def init(session, options=''):
    action = 'git init ' + options
    run(session, action)


def config(session, name=None, email=None):
    actions = ['']
    if name is not None:
        actions += ['git config --global user.name "%s"' % name]
    if email is not None:
        actions += ['git config --global user.email "%s"' % email]

    actions += ['git config --global color.ui true']
    [run(session, action) for action in actions]


def config_cache(session):
    run(session, 'git config --global credential.helper cache')


def add(session, filepath):
    action = 'git add %s' % filepath
    run(session, action)


def commit(session, message):
    action = 'git commit -m "%s"' % message
    run(session, action)


def clone(session, repo, password=None):
    pass_func = get_pass
    if password:
        pass_func = send_pass_f(password)
    escape_variable(session, 'SSH_ASKPASS')
    rows = [
        ['s password:', pass_func, '', 'getting password'],
        ["Password for '.+': ", pass_func, '', 'getting password'],
        ['Permission denied, please try again.+s password:', get_pass, None, 'getting password'],
        ['Are you sure you want to continue connecting \(yes/no\)\?', send_line, 'yes', 'Adding known hosts.'],
        ['', waitprompt, ''],
    ]
    session.do(create_sequence(f'git clone {repo}', rows))
    recover_variable(session, 'SSH_ASKPASS')


def push(session, short_name, branch, password=None):
    pass_func = get_pass
    if password:
        pass_func = send_pass_f(password)
    escape_variable(session, 'SSH_ASKPASS')
    rows = [
        ['s password:', pass_func, '', 'getting password'],
        ["Password for '.+': ", pass_func, '', 'getting password'],
        ['Permission denied, please try again.+s password:', get_pass, None, 'getting password'],
        ['Are you sure you want to continue connecting \(yes/no\)\?', send_line, 'yes', 'Adding known hosts.'],
        ['', waitprompt, ''],
    ]
    session.do(create_sequence(f'git push {short_name} {branch}', rows))
    recover_variable(session, 'SSH_ASKPASS')


def pull(session, source='origin', branch='master'):
    escape_variable(session, 'SSH_ASKPASS')
    actions = 'git pull %s %s' % (source, branch)
    rows = [['s password:', send_pass, None, 'getting password']]
    rows += [['Permission denied, please try again.+s password:', get_pass, None, 'getting password']]
    rows += [['Are you sure you want to continue connecting \(yes/no\)\?', send_line, 'yes', 'Adding known hosts.']]
    rows += [['', waitprompt, '', actions[0]]]
    session.do(create_sequence(actions, rows))
    recover_variable(session, 'SSH_ASKPASS')


def add_remote(remote_url, short_name):
    def func(session):
        [run(session, a) for a in [
            f'git remote rm {short_name}',
            f'git remote add {short_name} {remote_url}'
        ]]
    return func


def migrate_repos(work_dir, repo_url, repo_pass, repo_list, to_url, to_pass):
    def func(session):
        short_name = 'origin'
        branch= 'master'
        work_on(session, work_dir)
        for repo in repo_list:
            if not check_dir_exists(session, repo):
                clone(session, f'{repo_url}/{repo}', repo_pass)
            run(session, f'cd {repo}')
            add_remote(f'{to_url}/{repo}', short_name)(session)
            push(session, short_name, branch, to_pass)
            run(session, f'cd ..')
    return func


