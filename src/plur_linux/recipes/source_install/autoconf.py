
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell
import recipes.source_install.base as src_base


def sanitize(str):
    return str.replace('.', '\.')


def check(session, version):
    import re
    capture = base_shell.run(session, 'autoconf --version')
    if re.match('autoconf \(GNU Autoconf\) ' + sanitize(version), capture):
        return True


def source_install(session, version="2.69"):
    if check(session, version):
        return
    src_dir = 'autoconf-' + version
    src_file = src_dir + '.tar.gz'
    src_url = 'ftp://ftp.gnu.org/gnu/autoconf/' + src_file

    # check if previous build environment exists
    build_env = src_base.check_build_env(session, src_dir)
    work_dir = build_env['work_dir']
    src_parent_dir = build_env['src_parent_dir']
    download_dir = build_env['download_dir']

    if build_env['dir_not_exists']:
        # Download source and extract
        src_base.wget_and_extract(session, src_url, src_file, src_dir, download_dir=download_dir)

        # create working directory
        src_base.mk_src_dir(session, src_dir, src_parent_dir=src_parent_dir, extracted_dir=download_dir)

    conf_options = [
        '--prefix=/usr/local'
    ]
    src_base.source_install(session, conf_options, work_dir=work_dir)
