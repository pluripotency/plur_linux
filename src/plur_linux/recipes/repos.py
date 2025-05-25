from plur import base_shell

repos_attr = {
    'centos7': {
        'install_command': 'sudo yum -y install ',
        'epel': {
            'name': 'epel-release',
            'file_path': '/etc/yum.repos.d/epel.repo'
        },
        'ius': {
            'name': 'https://repo.ius.io/ius-release-el7.rpm',
            'file_path': '/etc/yum.repos.d/ius.repo'
        }
    },
    'almalinux8': {
        'install_command': 'sudo dnf -y install ',
        'epel': {
            'name': 'epel-release',
            'file_path': '/etc/yum.repos.d/epel.repo'
        },
    }
}


def install_repo(platform, repo_name):
    def func(session):
        if platform in repos_attr:
            if 'install_command' in repos_attr[platform]:
                install_command = repos_attr[platform]['install_command']
            else:
                return
            if repo_name in repos_attr[platform]:
                target_repo = repos_attr[platform][repo_name]
                if 'file_path' in target_repo:
                    if base_shell.check_file_exists(session, target_repo['file_path']):
                        return

                base_shell.run(session, install_command + target_repo['name'])
    return func


def install_with_repo(package_list, platform, repo_name):
    def func(session):
        install_repo(platform, repo_name)(session)
        install_command = repos_attr[platform]['install_command']
        base_shell.run(session, install_command + ' '.join(package_list))
    return func


dict_repos = {
    'centos7': {
        'epel': install_repo('centos7', 'epel'),
        'ius': install_repo('centos7', 'ius')
    },
    'almalinux8': {
        'epel': install_repo('almalinux8', 'epel'),
    }
}



