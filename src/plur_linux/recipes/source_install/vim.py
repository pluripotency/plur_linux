from plur.base_shell import *
from plur import session_wrap


def is_installed(session):
    if check_command_exists(session, 'vim'):
        return True
    else:
        return False


@session_wrap.sudo
def install_dependency(session):
    packages = [
        "make",
        "gcc-c++",
        "ncurses-devel",
    ]
    run(session, f'yum install -y {" ".join(packages)}')


def make_dir_usable(target_dir, user_group='worker:worker'):
    @session_wrap.sudo
    def func(session):
        work_on(session, target_dir)
        actions = [
            f'chown {user_group} {target_dir}'
        ]
        [run(session, a) for a in actions]
    return func


def curl_master_then_work_on(rep_name, pkg_name, src_dir='/usr/local/src'):
    def func(session):
        make_dir_usable(src_dir)(session)

        extract_dir_head = f'{rep_name}-{pkg_name}'
        work_on(session, src_dir)
        run(session, f'rm -rf {extract_dir_head}*')

        tarball_master_url = f'https://github.com/{rep_name}/{pkg_name}/tarball/master'
        actions = [
            f'curl -L {tarball_master_url} | tar xz'
            , f'cd {extract_dir_head}\t'
        ]
        [run(session, a) for a in actions]
    return func


def make_install(session):
    actions = [
        './configure --prefix=/usr/local'
        , 'sudo make install'
        , 'sudo ln -s /usr/local/bin/vim /usr/local/sbin/vim'
    ]
    [run(session, a) for a in actions]


@session_wrap.sudo
def clean(session):
    src_dir = '/usr/local/src'
    [run(session, a) for a in [
        'yum remove -y vim gvim'
        , f'cd {src_dir}/vim-vim\t'
        , "rm -f /usr/local/sbin/vim"
        , "make uninstall"
        , "make distclean"
    ]]


def install(session):
    clean(session)
    if not is_installed(session):
        install_dependency(session)
        curl_master_then_work_on('vim', 'vim')(session)
        make_install(session)


