# ! /usr/bin/env python
import os
import sys

sys.path.append(os.pardir)

from plur import base_shell as shell


def prepare_build_env(session, extracted_dir, prefix_dir='/usr/local/'):
    package_dir = extracted_dir.strip('/').split('/')[-1]
    src_dir = prefix_dir + 'src/'
    bin_dir = prefix_dir + 'bin/'
    work_dir = src_dir + package_dir
    build_env = {
        'work_dir': work_dir
        , 'prefix_dir': prefix_dir
        , 'src_dir': src_dir
        , 'bin_dir': bin_dir
    }
    # create src_parent_dir if not exists
    if not shell.check_dir_exists(session, src_dir):
        shell.run(session, 'sudo mkdir -p ' + src_dir)

    # mv src_dir to src_parent_dir and give permission to current user
    if not shell.check_dir_exists(session, work_dir):
        shell.run(session, 'sudo cp -rf %s %s' % (extracted_dir, work_dir))
        shell.run(session, 'sudo chown -R $USER %s' % work_dir)
        shell.run(session, 'sudo chgrp -R `id -g $USER` %s' % work_dir)

    # move into work_dir
    shell.work_on(session, work_dir)
    return build_env


def check_build_env(session, src_dir, prefix_dir='/usr/local/', download_dir='$HOME/Downloads/'):
    work_dir = prefix_dir + 'src/' + src_dir
    build_env = {
        'work_dir': work_dir
        , 'prefix_dir': prefix_dir
        , 'src_parent_dir': prefix_dir + 'src/'
        , 'download_dir': download_dir
        , 'bin_dir': prefix_dir + '/bin'
    }
    if shell.check_dir_exists(session, work_dir):
        build_env['dir_not_exists'] = False
        return build_env
    else:
        build_env['dir_not_exists'] = True
        return build_env


def git_clone(session, url, download_dir='$HOME/Downloads/'):
    shell.work_on(session, download_dir)
    repo_dir = download_dir + url.split('/')[-1]

    if not shell.check_dir_exists(session, repo_dir):
        shell.run(session, 'git clone ' + url)
        shell.work_on(session, repo_dir)
    else:
        shell.work_on(session, repo_dir)
        shell.run(session, 'git pull origin master')


def wget_and_extract(session, url, filename, extracted_file_or_dir, download_dir='$HOME/Downloads/', wget_option=None):
    shell.work_on(session, download_dir)

    if not shell.check_file_exists(session, filename):
        shell.yum_install(session, {'packages': ['wget']})
        shell.wget(session, url, wget_option)
    if not shell.check_dir_exists(session, download_dir + extracted_file_or_dir):
        shell.run(session, 'tar xvzf ' + filename)


def mk_src_dir(session, package_dir, src_parent_dir='/usr/local/src/', extracted_dir='$HOME/Downloads/'):
    # create src_parent_dir if not exists
    if not shell.check_dir_exists(session, src_parent_dir):
        shell.run(session, 'sudo mkdir -p ' + src_parent_dir)

    # mv src_dir to src_parent_dir and give permission to current user
    work_dir = src_parent_dir + package_dir
    if not shell.check_dir_exists(session, work_dir):
        shell.run(session, 'sudo mv %s %s' % (extracted_dir + package_dir, work_dir))
        shell.run(session, 'sudo chown -R $USER %s' % work_dir)
        shell.run(session, 'sudo chgrp -R `id -g $USER` %s' % work_dir)

    # move into src_dir
    shell.work_on(session, work_dir)


def prepare_work_dir(session, src_dir, src_file, src_url):
    # check if previous build environment exists
    build_env = check_build_env(session, src_dir)
    work_dir = build_env['work_dir']
    src_parent_dir = build_env['src_parent_dir']
    download_dir = build_env['download_dir']

    shell.yum_install(session, {'packages': ['wget']})

    if build_env['dir_not_exists']:
        # Download source and extract
        wget_and_extract(session, src_url, src_file, src_dir, download_dir=download_dir)

        # create working directory
        mk_src_dir(session, src_dir, src_parent_dir=src_parent_dir, extracted_dir=download_dir)

    shell.work_on(session, work_dir)
    return work_dir


def configure(session, conf_options, work_dir=None):
    if work_dir:
        shell.work_on(session, work_dir)

    conf_command = ['./configure']
    conf_command += conf_options
    conf_command += ['> _configure.log', '2> _configureErr.log']
    shell.run(session, ' '.join(conf_command))
    return shell.check_yes_or_no(session,
        '`wc -l _configureErr.log | awk \'BEGIN{FS=" "}{print $1}\'` -eq 0'
    )


def make(session, options=[''], sudo=False, stdout=False):
    command = 'make ' + ' '.join(options)
    fname = '_make_' + '_'.join(options)

    if stdout:
        run_make = [command]
    else:
        run_make = [
            command
            , '> %s.log' % fname
            , '2> %sErr.log' % fname
        ]

    cmd = ' '.join(run_make)
    if sudo:
        cmd = 'sudo ' + cmd
    shell.run(session, cmd)


def make_only(session):
    make(session)


def make_and_install(session, stdout=False):
    make(session, stdout=stdout)
    make(session, options=['install'], sudo=True, stdout=stdout)


def make_and_altinstall(session, stdout=False):
    make(session, stdout=stdout)
    make(session, options=['altinstall'], sudo=True, stdout=stdout)


def source_install(session, conf_options, work_dir=None):
    if configure(session, conf_options, work_dir):
        make_and_install(session)
