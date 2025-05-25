import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell
from recipes.source_install import base as src_base


def runnable():
    return [
        s3fs_install_centos
        , s3fs_install_ubuntu
    ]


def fuse_s3fs_prepare_ubuntu(session):
    # preparation to compile fuse and s3fs
    packages = [
        'build-essential',
        'libcurl4-openssl-dev',
        'libxml2-dev',
        'libfuse-dev',
        'comerr-dev',
        'libfuse2',
        'libidn11-dev',
        'libkrb5-dev',
        'libldap2-dev',
        'libselinux1-dev',
        'libsepol1-dev',
        'pkg-config',
        'fuse-utils',
        'sshfs',
        'curl',
        'wget'
    ]
    shell.yum_install(session, {'packages': packages})


def s3fs_fuse_prepare_centos(session):
    # preparation to compile fuse and s3fs
    packages = [
        'gcc-c++'
        , 'libcurl-devel'
        , 'libxml2-devel'
        , 'openssl-devel'
    ]
    shell.yum_install(session, {'packages': packages})


def fuse_install(session):
    # fuse
    fuse_ver = '2.9.3'
    fuse_file = 'fuse-%s.tar.gz' % fuse_ver

    # fuse download and extract
    fuse_file_url = 'http://sourceforge.net/projects/fuse/files/fuse-2.X/%s/%s/download' % (fuse_ver, fuse_file)
    # # downloaded file name is 'download', after extracted, folder name is fuse-x.x.x
    src_name = 'fuse-%s' % fuse_ver
    src_base.wget_and_extract(session, fuse_file_url, 'download', src_name)

    # fuse create dir
    src_base.mk_src_dir(session, src_name)

    # fuse configure, make and make install
    conf_options = ['--prefix=/usr']
    src_base.source_install(session, conf_options)


def fuse_ldconfig_centos(session):
    shell.run(session, "ldconfig")
    shell.run(session, 'export PKG_CONFIG_PATH=/usr/lib/pkgconfig')
    shell.run(session, 'pkg-config --modversion fuse')


def s3fs_install_ubuntu(session):
    # s3fs
    s3fs_ver = '1.74'
    s3fs_file = 's3fs-%s.tar.gz' % s3fs_ver

    # s3fs download
    s3fs_file_url = 'http://s3fs.googlecode.com/files/%s' % (s3fs_file)
    src_name = 's3fs-%s' % s3fs_ver
    src_base.wget_and_extract(session, s3fs_file_url, s3fs_file, src_name)

    # s3fs create dir
    src_base.mk_src_dir(session, src_name)

    # s3fs configure, make and make install
    src_parent_dir = '/usr/local/src/'
    src_base.mk_src_dir(session, src_name, src_parent_dir)

    conf_options = ['--prefix=/usr']
    src_base.source_install(session, conf_options)


def s3fs_install_centos(session):
    import recipes.ops.git as git

    git_repos = 'https://github.com/s3fs-fuse/s3fs-fuse.git'
    shell.work_on(session, '$HOME/Downloads/')
    git.clone(session, git_repos)

    src_base.mk_src_dir(session, 's3fs-fuse')
    shell.run(session, './autogen.sh')
    src_base.source_install(session, ['--prefix=/usr'])


