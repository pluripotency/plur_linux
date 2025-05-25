
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell
import recipes.source_install.base as src_base


def install_nodejs(session, version='v4.5.0'):
    src_dir = 'node-%s' % version
    build_env = src_base.check_build_env(session, src_dir)

    if build_env['dir_not_exists']:
        work_dir = build_env['work_dir']
        src_parent_dir = build_env['src_parent_dir']
        download_dir = build_env['download_dir']

        src_file = src_dir + '.tar.gz'
        src_url = 'http://nodejs.org/dist/%s/%s' % (version, src_file)

        prepare_packages(session)
        # Download source and extract
        src_base.wget_and_extract(session, src_url, src_file, src_dir, download_dir=download_dir)

        # create working directory
        src_base.mk_src_dir(session, src_dir, src_parent_dir=src_parent_dir, extracted_dir=download_dir)

        # configure, make, make install
        prefix = '/usr/local/'
        conf_options = [
            '--prefix=%s' % prefix,
        ]
        src_base.source_install(session, conf_options, work_dir=work_dir)


def prepare_packages(session):
    packages = [
        'wget'
        , 'gcc-c++'
        , 'automake'
        , 'autoconf'
        , 'libtoolize'
        , 'make'
    ]
    shell.yum_install(session, {'packages': packages})

