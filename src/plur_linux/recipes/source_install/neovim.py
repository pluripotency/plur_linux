
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell
import recipes.source_install.base as src_base


def prepare(session):
    shell.yum_install(session, {'packages': [
        'autoconf',
        'automake',
        'cmake',
        'gcc',
        'gcc-c++',
        'libtool',
        'make',
        'pkgconfig',
        'unzip'
    ]})

    from plur_linux.recipes.source_install import autoconf
    autoconf.source_install(session, version='2.69')

    shell.run(session, '. ~/.bashrc')


def source_install(session):
    prepare(session)
    src_url = 'https://github.com/neovim/neovim'
    src_base.git_clone(session, src_url)
    make_options =[
        'CMAKE_BUILD_TYPE=Release',
        'CMAKE_EXTRA_FLAGS="-DCMAKE_INSTALL_PREFIX:PATH=/usr/local"'
    ]
    actions = [
        'rm -r build',
        'make clean',
        'make ' + ' '.join(make_options),
    ]
    [shell.run(session, action) for action in actions]
    shell.run(session, 'sudo make install')

    shell.run(session, '. ~/.bashrc')
