from plur import base_shell
from recipes import repos
from recipes.source_install import git as git_source_install


def remove_package(session):
    if base_shell.check_command_exists(session, 'git'):
        base_shell.yum_y(['remove', 'git'])


dict_git = {
    'centos7': {
        'package': base_shell.yum_y(['git']),
        'source': git_source_install.install,
        'ius': lambda session: [func(session) for func in [
            remove_package,
            repos.install_repo('centos7', 'ius'),
            repos.install_repo('centos7', 'epel'),
            base_shell.yum_y([
                'install'
                , 'libsecret'
                , 'pcre2'
                , 'perl-Error'
                , 'perl-TermReadKey'
                , 'emacs-filesystem'
            ]),
            # base_shell.yum_y([
            #     'install'
            #     , 'perl-Git'
            #     , '--enablerepo=ius'
            #     , '--disablerepo=base,epel,extras,updates']),
            base_shell.yum_y(['install', 'git', '--enablerepo=ius', '--disablerepo=base,epel,extras,updates']),
        ]]
    }
}
